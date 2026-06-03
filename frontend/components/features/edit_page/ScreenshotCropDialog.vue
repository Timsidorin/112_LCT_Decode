<template>
	<q-dialog
		:model-value="modelValue"
		maximized
		full-width
		transition-show="fade"
		transition-hide="fade"
		@update:model-value="emit('update:modelValue', $event)"
		persistent
	>
		<q-card class="crop-dialog-card">
			<q-card-section class="crop-dialog-head row items-center q-py-sm">
				<div class="text-h6">Скриншот шага</div>
				<q-space />
				<q-btn flat round dense icon="close" v-close-popup />
			</q-card-section>
			<q-card-section class="crop-dialog-hint q-pt-none q-pb-sm text-body2 text-grey-7">
				Выделите фрагмент. Поля — белые отступы вокруг кадра.
			</q-card-section>

			<q-card-section class="crop-stage-wrap">
				<div v-if="loadError" class="text-negative q-pa-md">
					Не удалось загрузить скриншот. Проверьте вход в аккаунт и что URL картинки в шаге совпадает с
					настройками S3 на сервере (endpoint и имя бакета).
				</div>
				<div
					v-else-if="modelValue && !displaySrc && !loadError"
					class="crop-loading flex flex-center"
				>
					<q-spinner color="primary" size="48px" />
				</div>
				<div v-else-if="modelValue && displaySrc" class="crop-stage-inner">
					<div class="crop-stage" @mousedown.prevent="onBackdropDown">
						<img
							:key="`${trainingUuid}-${stepId}`"
							ref="imgRef"
							:src="displaySrc"
							alt=""
							class="crop-img"
							draggable="false"
							@load="onImgLoad"
							@error="onImgElementError"
						/>
						<div
							v-if="imgReady"
							class="crop-box"
							:style="boxStyle"
							@mousedown.stop.prevent="startMove"
						>
							<div class="crop-inner" />
							<div
								v-for="h in handles"
								:key="h"
								class="crop-handle"
								:class="`crop-handle--${h}`"
								@mousedown.stop.prevent="(e) => startResize(e, h)"
							/>
						</div>
					</div>
				</div>
			</q-card-section>

			<q-card-section class="crop-pad-section q-pt-none q-pb-sm">
				<div class="text-subtitle2 q-mb-xs">Поля вокруг кадра (px)</div>
				<div class="row q-col-gutter-sm">
					<div class="col-6 col-sm-3">
						<q-input v-model.number="padT" type="number" dense outlined label="Сверху" :min="0" :max="maxPad" />
					</div>
					<div class="col-6 col-sm-3">
						<q-input v-model.number="padR" type="number" dense outlined label="Справа" :min="0" :max="maxPad" />
					</div>
					<div class="col-6 col-sm-3">
						<q-input v-model.number="padB" type="number" dense outlined label="Снизу" :min="0" :max="maxPad" />
					</div>
					<div class="col-6 col-sm-3">
						<q-input v-model.number="padL" type="number" dense outlined label="Слева" :min="0" :max="maxPad" />
					</div>
				</div>
			</q-card-section>

			<q-card-actions align="right" class="crop-dialog-actions q-px-md q-py-sm">
				<q-btn flat label="Отмена" color="primary" v-close-popup />
				<q-btn
					color="primary"
					unelevated
					label="Сохранить"
					:loading="saving"
					:disable="!imgReady || loadError"
					@click="onSave"
				/>
			</q-card-actions>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from "vue";
import { useQuasar } from "quasar";
import { TrainingStepApi } from "@api";
import { transformAreaForCropPadding } from "@utils/stepScreenshotTransform.js";
import { useTrainingData } from "@store/editTraining.js";

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	trainingUuid: { type: String, default: "" },
	stepId: { type: Number, default: null },
});

const emit = defineEmits(["update:modelValue", "saved"]);

const $q = useQuasar();
const store = useTrainingData();
const api = new TrainingStepApi();

const imgRef = ref(null);

const displaySrc = ref("");
const loadError = ref(false);
const imgReady = ref(false);
const nw = ref(1);
const nh = ref(1);
const dw = ref(1);
const dh = ref(1);

/** кроп в координатах отображаемого размера (px) */
const cx = ref(0);
const cy = ref(0);
const cw = ref(100);
const ch = ref(100);

const padL = ref(0);
const padR = ref(0);
const padT = ref(0);
const padB = ref(0);

const maxPad = 200;
const saving = ref(false);

const handles = ["nw", "ne", "sw", "se"];

let dragMode = null;
let startClient = { x: 0, y: 0 };
let startCrop = { x: 0, y: 0, w: 0, h: 0 };

const boxStyle = computed(() => ({
	left: `${cx.value}px`,
	top: `${cy.value}px`,
	width: `${cw.value}px`,
	height: `${ch.value}px`,
}));

function resetState() {
	loadError.value = false;
	imgReady.value = false;
	nw.value = 1;
	nh.value = 1;
	dw.value = 1;
	dh.value = 1;
	cx.value = 0;
	cy.value = 0;
	cw.value = 100;
	ch.value = 100;
	padL.value = 0;
	padR.value = 0;
	padT.value = 0;
	padB.value = 0;
}

function revokeDisplaySrc() {
	if (displaySrc.value && displaySrc.value.startsWith("blob:")) {
		URL.revokeObjectURL(displaySrc.value);
	}
	displaySrc.value = "";
}

function onImgElementError() {
	loadError.value = true;
}

watch(
	() => props.modelValue,
	async (open) => {
		if (!open) {
			revokeDisplaySrc();
			resetState();
			return;
		}
		resetState();
		await loadScreenshotBlob();
	}
);

async function loadScreenshotBlob() {
	loadError.value = false;
	imgReady.value = false;
	revokeDisplaySrc();
	if (!props.trainingUuid || props.stepId == null) {
		loadError.value = true;
		return;
	}
	try {
		const res = await api.fetchStepScreenshotBlob(props.trainingUuid, props.stepId);
		const blob = res.data;
		if (!(blob instanceof Blob) || blob.size === 0) {
			loadError.value = true;
			return;
		}
		displaySrc.value = URL.createObjectURL(blob);
	} catch {
		loadError.value = true;
	}
}

function onImgLoad() {
	const el = imgRef.value;
	if (!el) return;
	void nextTick(() => {
		const e = imgRef.value;
		if (!e) return;
		nw.value = e.naturalWidth || 1;
		nh.value = e.naturalHeight || 1;
		dw.value = e.offsetWidth || 1;
		dh.value = e.offsetHeight || 1;
		cx.value = 0;
		cy.value = 0;
		cw.value = dw.value;
		ch.value = dh.value;
		imgReady.value = true;
	});
}

function dispToNat(x, y, w, h) {
	const sx = nw.value / dw.value;
	const sy = nh.value / dh.value;
	return {
		x: Math.round(x * sx),
		y: Math.round(y * sy),
		w: Math.round(w * sx),
		h: Math.round(h * sy),
	};
}

function clampCrop() {
	const minS = 24;
	cx.value = Math.max(0, Math.min(cx.value, dw.value - minS));
	cy.value = Math.max(0, Math.min(cy.value, dh.value - minS));
	cw.value = Math.max(minS, Math.min(cw.value, dw.value - cx.value));
	ch.value = Math.max(minS, Math.min(ch.value, dh.value - cy.value));
}

function onBackdropDown(e) {
	if (!imgRef.value || !imgReady.value) return;
	const r = imgRef.value.getBoundingClientRect();
	const lx = e.clientX - r.left;
	const ly = e.clientY - r.top;
	if (lx < cx.value || ly < cy.value || lx > cx.value + cw.value || ly > cy.value + ch.value) {
		cx.value = Math.max(0, Math.min(lx, dw.value - 40));
		cy.value = Math.max(0, Math.min(ly, dh.value - 40));
		cw.value = Math.min(120, dw.value - cx.value);
		ch.value = Math.min(120, dh.value - cy.value);
		clampCrop();
	}
}

function startMove(e) {
	dragMode = "move";
	startClient = { x: e.clientX, y: e.clientY };
	startCrop = { x: cx.value, y: cy.value, w: cw.value, h: ch.value };
	window.addEventListener("mousemove", onPointerMove);
	window.addEventListener("mouseup", onPointerUp);
}

function startResize(e, corner) {
	dragMode = corner;
	startClient = { x: e.clientX, y: e.clientY };
	startCrop = { x: cx.value, y: cy.value, w: cw.value, h: ch.value };
	window.addEventListener("mousemove", onPointerMove);
	window.addEventListener("mouseup", onPointerUp);
}

function onPointerMove(e) {
	const dx = e.clientX - startClient.x;
	const dy = e.clientY - startClient.y;
	const sc = startCrop;
	if (dragMode === "move") {
		let nx = sc.x + dx;
		let ny = sc.y + dy;
		nx = Math.max(0, Math.min(nx, dw.value - sc.w));
		ny = Math.max(0, Math.min(ny, dh.value - sc.h));
		cx.value = nx;
		cy.value = ny;
		return;
	}
	let nx = sc.x;
	let ny = sc.y;
	let nw0 = sc.w;
	let nh0 = sc.h;
	if (dragMode === "se") {
		nw0 = Math.max(24, sc.w + dx);
		nh0 = Math.max(24, sc.h + dy);
	} else if (dragMode === "sw") {
		nx = sc.x + dx;
		nw0 = Math.max(24, sc.w - dx);
		nh0 = Math.max(24, sc.h + dy);
	} else if (dragMode === "ne") {
		ny = sc.y + dy;
		nw0 = Math.max(24, sc.w + dx);
		nh0 = Math.max(24, sc.h - dy);
	} else if (dragMode === "nw") {
		nx = sc.x + dx;
		ny = sc.y + dy;
		nw0 = Math.max(24, sc.w - dx);
		nh0 = Math.max(24, sc.h - dy);
	}
	if (nx < 0) {
		nw0 += nx;
		nx = 0;
	}
	if (ny < 0) {
		nh0 += ny;
		ny = 0;
	}
	if (nx + nw0 > dw.value) nw0 = dw.value - nx;
	if (ny + nh0 > dh.value) nh0 = dh.value - ny;
	cx.value = nx;
	cy.value = ny;
	cw.value = Math.max(24, nw0);
	ch.value = Math.max(24, nh0);
	clampCrop();
}

function onPointerUp() {
	dragMode = null;
	window.removeEventListener("mousemove", onPointerMove);
	window.removeEventListener("mouseup", onPointerUp);
}

onUnmounted(() => {
	window.removeEventListener("mousemove", onPointerMove);
	window.removeEventListener("mouseup", onPointerUp);
	revokeDisplaySrc();
});

async function onSave() {
	if (!props.trainingUuid || props.stepId == null || !store.selectedStep) return;
	const nat = dispToNat(cx.value, cy.value, cw.value, ch.value);
	const pl = Math.min(maxPad, Math.max(0, Math.round(padL.value || 0)));
	const pr = Math.min(maxPad, Math.max(0, Math.round(padR.value || 0)));
	const pt = Math.min(maxPad, Math.max(0, Math.round(padT.value || 0)));
	const pb = Math.min(maxPad, Math.max(0, Math.round(padB.value || 0)));

	const outW = nat.w + pl + pr;
	const outH = nat.h + pt + pb;

	const img = imgRef.value;
	if (!img || !imgReady.value) return;

	let cvs;
	try {
		cvs = document.createElement("canvas");
		cvs.width = outW;
		cvs.height = outH;
		const ctx = cvs.getContext("2d");
		ctx.fillStyle = "#ffffff";
		ctx.fillRect(0, 0, outW, outH);
		ctx.drawImage(img, nat.x, nat.y, nat.w, nat.h, pl, pt, nat.w, nat.h);
	} catch (err) {
		console.error(err);
		$q.notify({
			color: "negative",
			message: "Не удалось собрать изображение",
			position: "top",
		});
		return;
	}

	const blob = await new Promise((resolve) => cvs.toBlob(resolve, "image/png", 0.92));
	if (!blob) {
		$q.notify({ color: "negative", message: "Ошибка PNG", position: "top" });
		return;
	}

	const step = store.selectedStep;
	const newArea = transformAreaForCropPadding(
		step.area,
		nat,
		{ left: pl, right: pr, top: pt, bottom: pb },
		outW,
		outH
	);

	saving.value = true;
	try {
		const upRes = await api.replaceStepScreenshot(
			props.trainingUuid,
			props.stepId,
			blob,
			"step-crop.png"
		);
		const uploaded = upRes.data;
		await api.editStep(props.trainingUuid, props.stepId, { area: newArea });

		const nextUrl = uploaded?.image_url || step.image_url;
		step.image_url = nextUrl;
		step.photo_dimensions = uploaded?.photo_dimensions || { width: outW, height: outH };
		step.area = newArea;
		const inList = store.steps?.find((s) => s.id === step.id);
		if (inList) {
			inList.image_url = nextUrl;
			inList.photo_dimensions = { ...step.photo_dimensions };
			inList.area = JSON.parse(JSON.stringify(newArea));
		}

		$q.notify({ color: "positive", message: "Скриншот обновлён", position: "bottom-right", timeout: 1800 });
		emit("update:modelValue", false);
		emit("saved");
	} catch (e) {
		console.error(e);
		$q.notify({ color: "negative", message: "Не удалось сохранить", position: "top" });
	} finally {
		saving.value = false;
	}
}
</script>

<style scoped>
.crop-dialog-card {
	width: 100%;
	max-width: 100vw;
	height: 100%;
	max-height: 100vh;
	display: flex;
	flex-direction: column;
	background: #f8fafc;
}

.crop-dialog-head,
.crop-dialog-hint {
	flex-shrink: 0;
}

.crop-stage-wrap {
	flex: 1;
	min-height: 0;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8px 12px;
	background: #0f172a;
	border-radius: 0;
}

.crop-stage-inner {
	width: 100%;
	height: 100%;
	min-height: 0;
	display: flex;
	align-items: center;
	justify-content: center;
}

.crop-stage {
	position: relative;
	display: inline-block;
	vertical-align: top;
	line-height: 0;
	max-width: 100%;
	max-height: 100%;
}

.crop-loading {
	width: 100%;
	height: 100%;
	min-height: 120px;
}

.crop-img {
	display: block;
	max-width: 100%;
	max-height: 100%;
	width: auto;
	height: auto;
	object-fit: contain;
	user-select: none;
}

.crop-pad-section {
	flex-shrink: 0;
}

.crop-dialog-actions {
	flex-shrink: 0;
	border-top: 1px solid rgba(15, 23, 42, 0.08);
	background: #f8fafc;
}

.crop-box {
	position: absolute;
	box-sizing: border-box;
	border: 2px solid #fff;
	box-shadow:
		0 0 0 1px rgba(80, 100, 247, 0.95),
		0 0 0 9999px rgba(0, 0, 0, 0.42);
	cursor: move;
	z-index: 2;
}

.crop-inner {
	position: absolute;
	inset: 0;
	cursor: move;
}

.crop-handle {
	position: absolute;
	width: 14px;
	height: 14px;
	background: #fff;
	border: 2px solid var(--q-primary);
	border-radius: 2px;
	z-index: 3;
}

.crop-handle--nw {
	left: -7px;
	top: -7px;
	cursor: nwse-resize;
}
.crop-handle--ne {
	right: -7px;
	top: -7px;
	cursor: nesw-resize;
}
.crop-handle--sw {
	left: -7px;
	bottom: -7px;
	cursor: nesw-resize;
}
.crop-handle--se {
	right: -7px;
	bottom: -7px;
	cursor: nwse-resize;
}
</style>
