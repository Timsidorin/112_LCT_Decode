<template>
	<div class="tool-dock-wrap">
		<div class="tool-dock glass-panel animate-fade-in-up">
			<div class="tool-dock__side">
				<q-btn
					class="tool-dock__nav"
					round
					dense
					flat
					icon="chevron_left"
					color="grey-8"
					:disable="!hasPreviousStep"
					@click="goToPreviousStep"
				>
					<q-tooltip>Предыдущий шаг</q-tooltip>
				</q-btn>
			</div>

			<div class="tool-dock__center">
			<div class="tool-bar">
				<q-btn
					v-for="event in events"
					:key="event.id"
					dense
					flat
					class="tool-btn"
					:class="{ 'tool-btn-active': store.selectedEvent?.id === event.id }"
					@click="selectEvent(event)"
				>
					<div class="tool-btn-inner">
						<Component :is="event.icon" />
						<span class="tool-btn-label">{{ event.shortName }}</span>
					</div>
					<q-tooltip class="bg-grey-9 text-body2">{{ event.name }}</q-tooltip>
				</q-btn>
			</div>

			<q-btn
				v-if="store.selectedStep"
				flat
				dense
				no-caps
				round
				class="tool-dock__substeps-btn"
				:color="chainLength > 1 ? 'primary' : 'grey-7'"
				icon="account_tree"
				:label="chainLength > 1 ? String(chainLength) : undefined"
			>
				<q-tooltip>Подшаги на этом кадре</q-tooltip>
				<q-menu anchor="top middle" self="bottom middle" class="substeps-menu">
					<div class="substeps-menu__body">
						<div class="substeps-menu__head row items-center justify-between">
							<span class="text-subtitle2">Подшаги</span>
							<q-btn
								dense
								no-caps
								unelevated
								color="primary"
								size="sm"
								icon="playlist_add"
								label="Добавить"
								@click="addChainAction"
							/>
						</div>

						<p v-if="chainLength <= 1" class="text-caption text-grey-7 q-mb-sm q-mt-xs">
							Несколько действий на одном скриншоте
						</p>

						<div v-if="chainLength > 1" class="substeps-menu__tabs row items-center q-gutter-xs q-mb-sm">
							<span class="text-caption text-grey-7">Текущий:</span>
							<q-btn-toggle
								v-model="slotTab"
								:options="slotOptions"
								dense
								no-caps
								unelevated
								rounded
								color="grey-2"
								text-color="grey-8"
								toggle-color="primary"
								toggle-text-color="white"
							/>
						</div>

						<div v-if="chainLength > 1" class="row items-center q-gutter-xs">
							<q-btn
								dense
								flat
								no-caps
								color="negative"
								size="sm"
								icon="remove_circle_outline"
								label="Удалить"
								@click="removeCurrentChainAction"
							/>
							<q-btn
								dense
								flat
								no-caps
								color="grey-8"
								size="sm"
								icon="playlist_remove"
								label="Оставить один"
								@click="collapseChain"
							/>
						</div>
					</div>
				</q-menu>
			</q-btn>

			<transition name="panel-slide">
				<div v-if="isKeyPressSelected" class="hotkey-chip">
					<span class="hotkey-chip__label">{{ hotkeyLabel }}</span>
					<q-btn
						dense
						no-caps
						unelevated
						color="primary"
						size="sm"
						label="Клавиша"
						@click="openHotkeyDialog"
					/>
				</div>
			</transition>
			</div>

			<div class="tool-dock__side tool-dock__side--right">
				<q-btn
					class="tool-dock__nav"
					round
					dense
					flat
					icon="chevron_right"
					color="grey-8"
					:disable="!hasNextStep"
					@click="goToNextStep"
				>
					<q-tooltip>Следующий шаг</q-tooltip>
				</q-btn>
			</div>

			<watch-key
				v-if="isKeyPressSelected"
				v-model="metaKeywords"
				v-model:open="isHotkeyDialogOpen"
			/>
		</div>
	</div>
</template>

<script setup>
import {
	RightClick,
	LeftClick,
	DoubleClick,
	Text,
	Mouseover,
	Keyboard,
} from "@components/features/edit_page/icons_tool_bar/index.js";
import WatchKey from "@components/features/edit_page/WatchKey.vue";
import { eventRequiresArea, isKeyPressType } from "@utils/actionTypes.js";
import {
	getExplicitActions,
	buildAreaWithActions,
	findToolbarEventById,
	sanitizeAreaForActionType,
	patchStepInStore,
	cloneJson,
} from "@utils/stepActionSequence.js";
import { trainingStepApi, TrainingApi } from "@api";
import { useTrainingData } from "@store/editTraining.js";
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { useQuasar } from "quasar";
import { trainingEvents } from "@utils/eventBus.js";
import { stepLabel } from "@utils/scenarioMapLayout.js";
import { useEditorSaveStatus } from "@composables/useEditorSaveStatus.js";

const $q = useQuasar();
const trainingApi = new TrainingApi();
const { markSaving, markSaved, markError } = useEditorSaveStatus();

const store = useTrainingData();
const isHotkeyDialogOpen = ref(false);
const duplicating = ref(false);

const sortedSteps = computed(() => store.sortedSteps());
const selectedStep = computed(() => store.selectedStep);

const hasPreviousStep = computed(() => {
	if (!selectedStep.value) return false;
	const idx = sortedSteps.value.findIndex((s) => s.id === selectedStep.value.id);
	return idx > 0;
});

const hasNextStep = computed(() => {
	if (!selectedStep.value) return false;
	const idx = sortedSteps.value.findIndex((s) => s.id === selectedStep.value.id);
	return idx >= 0 && idx < sortedSteps.value.length - 1;
});

const goToPreviousStep = () => store.goToPreviousStep();
const goToNextStep = () => store.goToNextStep();

const isKeyPressSelected = computed(() => isKeyPressType(store.selectedEvent));

function keywordsSlice() {
	const step = store.selectedStep;
	if (!step?.area) return null;
	const acts = step.area.actions;
	if (!Array.isArray(acts) || !acts.length) return null;
	const i = Math.min(Math.max(0, store.stepActionEditIndex ?? 0), acts.length - 1);
	if (!acts[i]) acts[i] = {};
	return acts[i];
}

const metaKeywords = computed({
	get() {
		const sl = keywordsSlice();
		if (sl) return sl.metaKeywords || [];
		return store.selectedStep?.area?.metaKeywords || [];
	},
	set(value) {
		if (!store.selectedStep) return;
		const sl = keywordsSlice();
		if (sl) {
			sl.metaKeywords = value;
			return;
		}
		if (!store.selectedStep.area) store.selectedStep.area = {};
		store.selectedStep.area.metaKeywords = value;
	},
});

const hotkeyLabel = computed(() =>
	metaKeywords.value?.length ? metaKeywords.value.join(" + ") : "Не назначено",
);

const saveKeyPress = async () => {
	if (!store.trainingData?.uuid || !store.selectedStep?.id || !store.selectedEvent?.id) return;
	const step = store.selectedStep;
	const seq = getExplicitActions(step);
	try {
		let body;
		if (seq?.length) {
			const idx = Math.min(
				Math.max(0, store.stepActionEditIndex ?? 0),
				seq.length - 1,
			);
			const actions = seq.map((x) => ({ ...x }));
			actions[idx] = {
				...actions[idx],
				action_type_id: 6,
				metaKeywords: metaKeywords.value || [],
			};
			body = {
				action_type_id: actions[0].action_type_id,
				area: buildAreaWithActions(actions, step.area),
			};
		} else {
			body = {
				action_type_id: store.selectedEvent.id,
				area: { metaKeywords: metaKeywords.value || [] },
			};
		}
		await trainingStepApi.editStep(store.trainingData.uuid, store.selectedStep.id, body);
		if (!store.selectedStep.area) store.selectedStep.area = {};
		Object.assign(store.selectedStep.area, body.area);
	} catch (e) {
		console.error(e);
	}
};

const openHotkeyDialog = () => {
	isHotkeyDialogOpen.value = true;
};

async function persistActionTypeForStep(event) {
	if (!store.trainingData?.uuid || !store.selectedStep?.id || !event?.id) return;
	const stepId = store.selectedStep.id;
	const trainingUuid = store.trainingData.uuid;
	const step = store.steps?.find((s) => s.id === stepId) || store.selectedStep;
	const seq = getExplicitActions(step);
	let body;
	if (seq?.length) {
		const idx = Math.min(
			Math.max(0, store.stepActionEditIndex ?? 0),
			seq.length - 1,
		);
		const actions = seq.map((x) => ({ ...x }));
		actions[idx] = { ...actions[idx], action_type_id: event.id };
		body = {
			action_type_id: actions[0].action_type_id,
			area: buildAreaWithActions(actions, step.area),
		};
	} else {
		body = {
			action_type_id: event.id,
			area: sanitizeAreaForActionType(step.area, event.id),
		};
	}
	await trainingStepApi.editStep(trainingUuid, stepId, body);
	patchStepInStore(store.steps, stepId, body);
}

const selectEvent = async (event) => {
	store.selectEvent(event);
	if (isKeyPressType(event)) {
		await saveKeyPress();
		openHotkeyDialog();
		return;
	}
	try {
		await persistActionTypeForStep(event);
	} catch (e) {
		console.error(e);
		$q.notify({
			color: "negative",
			message: "Не удалось сохранить тип действия",
			position: "top",
		});
	}
};

const chainLength = computed(() => getExplicitActions(store.selectedStep)?.length || 0);

const slotTab = computed({
	get: () => store.stepActionEditIndex,
	set: (v) => {
		const n = Number(v);
		store.stepActionEditIndex = Number.isFinite(n) ? Math.max(0, n) : 0;
	},
});

const slotOptions = computed(() =>
	Array.from({ length: chainLength.value }, (_, i) => ({
		label: String(i + 1),
		value: i,
	})),
);

async function addChainAction() {
	if (!store.trainingData?.uuid || !store.selectedStep?.id) return;
	const step = store.selectedStep;
	const ev = store.selectedEvent || findToolbarEventById(1);
	let actions = getExplicitActions(step);
	if (!actions?.length) {
		const aid = step.action_type?.id || ev.id;
		const a = step.area || {};
		actions = [
			{
				action_type_id: aid,
				x: Number(a.x) || 0,
				y: Number(a.y) || 0,
				width: Math.max(40, Number(a.width) || 120),
				height: Math.max(24, Number(a.height) || 48),
				...["metaText", "metaKeywords", "metaFontSize", "metaMatchMode", "metaPattern", "metaPatternPreset"].reduce(
					(o, k) => {
						if (a[k] != null) o[k] = a[k];
						return o;
					},
					{},
				),
			},
		];
	}
	const w = step.photo_dimensions?.width || 800;
	const h = step.photo_dimensions?.height || 600;
	actions = [
		...actions,
		{
			action_type_id: ev.id,
			x: Math.min(32, w - 180),
			y: Math.min(120, h - 80),
			width: 168,
			height: 44,
		},
	];
	const newArea = buildAreaWithActions(actions, step.area);
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, step.id, {
			action_type_id: actions[0].action_type_id,
			area: newArea,
		});
		Object.assign(step.area, newArea);
		step.action_type = { ...findToolbarEventById(actions[0].action_type_id) };
		store.stepActionEditIndex = actions.length - 1;
		store.selectEvent(ev);
		$q.notify({
			color: "positive",
			message: "Добавлено действие — нарисуйте область на скрине",
			position: "bottom-right",
			icon: "playlist_add",
			timeout: 2200,
		});
	} catch (e) {
		console.error(e);
		$q.notify({ color: "negative", message: "Не удалось сохранить цепочку", position: "top" });
	}
}

async function collapseChain() {
	if (!store.trainingData?.uuid || !store.selectedStep?.id) return;
	const step = store.selectedStep;
	const seq = getExplicitActions(step);
	if (!seq || seq.length < 2) return;
	const f = { ...seq[0] };
	const flat = {
		x: f.x,
		y: f.y,
		width: f.width,
		height: f.height,
	};
	for (const k of [
		"metaText",
		"metaKeywords",
		"metaFontSize",
		"metaMatchMode",
		"metaPattern",
		"metaPatternPreset",
		"metaTextScale",
	]) {
		if (f[k] != null) flat[k] = f[k];
	}
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, step.id, {
			action_type_id: f.action_type_id,
			area: { ...flat, actions: [] },
		});
		if (!step.area) step.area = {};
		Object.assign(step.area, flat);
		delete step.area.actions;
		step.action_type = { ...findToolbarEventById(f.action_type_id) };
		store.stepActionEditIndex = 0;
		$q.notify({ color: "positive", message: "Оставлено одно действие", position: "bottom-right", timeout: 1500 });
	} catch (e) {
		console.error(e);
	}
}

async function removeCurrentChainAction() {
	if (!store.trainingData?.uuid || !store.selectedStep?.id) return;
	const step = store.selectedStep;
	const seq = getExplicitActions(step);
	if (!seq || seq.length < 2) return;

	const idx = Math.min(
		Math.max(0, store.stepActionEditIndex ?? 0),
		seq.length - 1,
	);
	const actions = seq.filter((_, i) => i !== idx);
	const nextIdx = Math.min(idx, actions.length - 1);

	try {
		if (actions.length === 1) {
			const f = { ...actions[0] };
			const flat = {
				x: f.x,
				y: f.y,
				width: f.width,
				height: f.height,
			};
			for (const k of [
				"metaText",
				"metaKeywords",
				"metaFontSize",
				"metaMatchMode",
				"metaPattern",
				"metaPatternPreset",
				"metaTextScale",
			]) {
				if (f[k] != null) flat[k] = f[k];
			}
			await trainingStepApi.editStep(store.trainingData.uuid, step.id, {
				action_type_id: f.action_type_id,
				area: { ...flat, actions: [] },
			});
			if (!step.area) step.area = {};
			Object.assign(step.area, flat);
			delete step.area.actions;
			step.action_type = { ...findToolbarEventById(f.action_type_id) };
			store.stepActionEditIndex = 0;
			store.selectEvent(findToolbarEventById(f.action_type_id));
		} else {
			const newArea = buildAreaWithActions(actions, step.area);
			await trainingStepApi.editStep(store.trainingData.uuid, step.id, {
				action_type_id: actions[0].action_type_id,
				area: newArea,
			});
			if (!step.area) step.area = {};
			Object.assign(step.area, newArea);
			step.action_type = { ...findToolbarEventById(actions[0].action_type_id) };
			store.stepActionEditIndex = nextIdx;
			store.selectEvent(findToolbarEventById(actions[nextIdx].action_type_id));
		}
		$q.notify({
			color: "positive",
			message: "Подшаг удалён",
			position: "bottom-right",
			timeout: 1200,
		});
	} catch (e) {
		console.error(e);
		$q.notify({ color: "negative", message: "Не удалось удалить подшаг", position: "top" });
	}
}

watch(
	() => isHotkeyDialogOpen.value,
	async (isOpen) => {
		if (!isOpen && isKeyPressSelected.value) await saveKeyPress();
	},
);

const events = [
	{ type: "leftClick", name: "Левый клик", shortName: "ЛКМ", icon: LeftClick, id: 1 },
	{ type: "rightClick", name: "Правый клик", shortName: "ПКМ", icon: RightClick, id: 2 },
	{ type: "doubleClick", name: "Двойной клик", shortName: "2x", icon: DoubleClick, id: 3 },
	{ type: "hover", name: "Наведение курсора", shortName: "Hover", icon: Mouseover, id: 4 },
	{ type: "inputText", name: "Ввод текста", shortName: "Текст", icon: Text, id: 5 },
	{ type: "keyPress", name: "Нажатие клавиши", shortName: "Клав.", icon: Keyboard, id: 6 },
];

async function clearCurrentArea() {
	if (!store.trainingData?.uuid || !store.selectedStep?.id) return;
	const step = store.selectedStep;
	const event = store.selectedEvent || events[0];
	const body = {
		action_type_id: event.id,
		area: sanitizeAreaForActionType(null, event.id),
	};
	markSaving();
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, step.id, body);
		patchStepInStore(store.steps, step.id, body);
		markSaved();
		$q.notify({
			color: "info",
			message: "Область сброшена",
			position: "bottom-right",
			timeout: 1200,
		});
	} catch {
		markError("area");
		$q.notify({ color: "negative", message: "Не удалось сбросить область", position: "top" });
	}
}

async function duplicateCurrentStep() {
	const step = store.selectedStep;
	const uuid = store.trainingData?.uuid;
	if (!step || !uuid || duplicating.value) return;

	const list = sortedSteps.value;
	const idx = list.findIndex((s) => s.id === step.id);
	if (idx < 0) return;

	duplicating.value = true;
	markSaving();
	try {
		const baseName = stepLabel(step);
		const { data: created } = await trainingStepApi.addStep(uuid, {
			step_number: list.length + 1,
			image_url: step.image_url,
			photo_dimensions: step.photo_dimensions ? cloneJson(step.photo_dimensions) : null,
			action_type_id: step.action_type_id ?? step.action_type?.id ?? null,
			area: cloneJson(step.area),
			meta: { ...(step.meta || {}), name: `${baseName} (копия)` },
			annotation: step.annotation,
			hint: step.hint,
			instruction_html: step.instruction_html,
		});

		const orderPayload = [];
		let num = 1;
		for (let i = 0; i < list.length; i++) {
			orderPayload.push({ id: list[i].id, step_number: num++ });
			if (i === idx) orderPayload.push({ id: created.id, step_number: num++ });
		}
		await trainingStepApi.reorderSteps(uuid, { steps: orderPayload });

		const { data } = await trainingApi.getTrainingByUuid(uuid);
		store.setTrainingData(data, { preserveStepId: created.id });
		markSaved();
		$q.notify({ color: "positive", message: "Шаг продублирован", position: "bottom-right" });
	} catch {
		markError("duplicate");
		$q.notify({ color: "negative", message: "Не удалось дублировать шаг", position: "top" });
	} finally {
		duplicating.value = false;
	}
}

function onSelectActionById(actionId) {
	const event = events.find((e) => e.id === actionId);
	if (event) void selectEvent(event);
}

let offSelectAction;
let offClearArea;
let offDuplicate;

onMounted(() => {
	offSelectAction = trainingEvents.selectActionById.on(onSelectActionById);
	offClearArea = trainingEvents.clearCurrentArea.on(() => {
		void clearCurrentArea();
	});
	offDuplicate = trainingEvents.duplicateStep.on(() => {
		void duplicateCurrentStep();
	});
});

onUnmounted(() => {
	offSelectAction?.();
	offClearArea?.();
	offDuplicate?.();
});
</script>

<style scoped>
.tool-dock-wrap {
	position: absolute;
	left: 0;
	right: 0;
	bottom: 12px;
	z-index: 12;
	display: flex;
	justify-content: center;
	pointer-events: none;
}

.tool-dock {
	display: grid;
	grid-template-columns: 40px auto 40px;
	align-items: center;
	gap: 6px;
	max-width: calc(100% - 24px);
	padding: 6px 8px;
	border-radius: 18px;
	pointer-events: auto;
}

.tool-dock__side {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 40px;
}

.tool-dock__side--right {
	justify-content: center;
}

.tool-dock__center {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 6px;
	min-width: 0;
	flex-wrap: wrap;
}

.tool-bar {
	display: flex;
	gap: 2px;
	padding: 4px;
	border-radius: 14px;
	background: rgba(255, 255, 255, 0.55);
}

.tool-btn {
	border-radius: 10px;
	padding: 4px 6px;
	transition: all 0.2s ease;
	min-width: 46px;
}

.tool-btn:hover {
	background: rgba(80, 100, 247, 0.08);
}

.tool-btn-active {
	background: var(--q-primary) !important;
	color: white !important;
	box-shadow: 0 2px 8px rgba(80, 100, 247, 0.3);
}

.tool-btn-inner {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 1px;
}

.tool-btn-label {
	font-size: 9px;
	font-weight: 500;
	line-height: 1;
	opacity: 0.8;
}

.tool-btn-active .tool-btn-label {
	opacity: 1;
}

.tool-dock__substeps-btn {
	flex-shrink: 0;
}

.hotkey-chip {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 4px 8px;
	border-radius: 999px;
	background: rgba(255, 255, 255, 0.85);
	border: 1px solid rgba(80, 100, 247, 0.15);
}

.hotkey-chip__label {
	font-size: 12px;
	font-weight: 500;
	color: #374151;
	max-width: 120px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.tool-dock__nav {
	flex-shrink: 0;
}

.panel-slide-enter-active,
.panel-slide-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.panel-slide-enter-from,
.panel-slide-leave-to {
	opacity: 0;
	transform: translateY(6px);
}
</style>

<style>
.substeps-menu__body {
	padding: 12px 14px;
	min-width: 260px;
}
</style>
