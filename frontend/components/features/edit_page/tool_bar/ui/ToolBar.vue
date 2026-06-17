<template>
	<div class="tool-bar-container animate-fade-in-up">
		<!-- Предыдущий шаг -->
		<q-btn
			v-if="hasPreviousStep"
			class="nav-btn"
			round
			dense
			icon="chevron_left"
			color="white"
			text-color="grey-9"
			@click="goToPreviousStep"
		>
			<q-tooltip>Предыдущий шаг</q-tooltip>
		</q-btn>

		<!-- Тулбар -->
		<div class="tool-bar glass-panel">
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

		<div v-if="store.selectedStep" class="multi-action-strip glass-panel">
			<div class="multi-action-header row items-center justify-between">
				<div class="multi-action-title row items-center no-wrap">
					<q-icon name="account_tree" size="16px" class="q-mr-xs" color="primary" />
					<span>Подшаги</span>
					<q-badge
						v-if="chainLength > 1"
						color="primary"
						class="q-ml-xs"
						:label="chainLength"
					/>
				</div>
				<q-btn
					dense
					no-caps
					unelevated
					color="primary"
					size="sm"
					icon="playlist_add"
					label="Добавить"
					class="multi-action-btn"
					@click="addChainAction"
				>
					<q-tooltip>Добавить подшаг</q-tooltip>
				</q-btn>
			</div>

			<div v-if="chainLength > 1" class="multi-action-tabs row items-center q-gutter-xs">
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
					class="multi-action-toggle"
				/>
			</div>

			<div v-if="chainLength > 1" class="multi-action-actions row items-center q-gutter-xs">
				<q-btn
					dense
					round
					flat
					color="negative"
					size="sm"
					icon="remove_circle_outline"
					class="multi-action-btn multi-action-btn--danger"
					@click="removeCurrentChainAction"
				>
					<q-tooltip>Удалить текущий подшаг</q-tooltip>
				</q-btn>
				<q-btn
					dense
					round
					flat
					color="grey-8"
					size="sm"
					icon="playlist_remove"
					class="multi-action-btn"
					@click="collapseChain"
				>
					<q-tooltip>Оставить только один подшаг</q-tooltip>
				</q-btn>
			</div>
		</div>

		<!-- Панель хоткея -->
		<transition name="panel-slide">
			<div v-if="isKeyPressSelected" class="hotkey-panel">
				<div class="hotkey-panel-label">{{ hotkeyLabel }}</div>
				<q-btn
					dense
					no-caps
					unelevated
					color="primary"
					size="sm"
					label="Выбрать"
					@click="openHotkeyDialog"
				/>
			</div>
		</transition>

		<!-- Следующий шаг -->
		<q-btn
			v-if="hasNextStep"
			class="nav-btn"
			round
			dense
			icon="chevron_right"
			color="white"
			text-color="grey-9"
			@click="goToNextStep"
		>
			<q-tooltip>Следующий шаг</q-tooltip>
		</q-btn>

		<watch-key
			v-if="isKeyPressSelected"
			v-model="metaKeywords"
			v-model:open="isHotkeyDialogOpen"
		/>
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
} from "@utils/stepActionSequence.js";
import { trainingStepApi } from "@api";
import { useTrainingData } from "@store/editTraining.js";
import { computed, ref, watch } from "vue";
import { useQuasar } from "quasar";

const $q = useQuasar();

const store = useTrainingData();
const isHotkeyDialogOpen = ref(false);

const hasPreviousStep = computed(() => {
	if (!store.trainingData?.steps) return false;
	const idx = store.trainingData.steps.findIndex(s => s.id === store.selectedStep?.id);
	return idx > 0;
});

const hasNextStep = computed(() => {
	if (!store.trainingData?.steps) return false;
	const idx = store.trainingData.steps.findIndex(s => s.id === store.selectedStep?.id);
	return idx >= 0 && idx < store.trainingData.steps.length - 1;
});

const goToPreviousStep = () => {
	if (!store.trainingData?.steps) return;
	const idx = store.trainingData.steps.findIndex(s => s.id === store.selectedStep?.id);
	if (idx > 0) store.selectStep(store.trainingData.steps[idx - 1]);
};

const goToNextStep = () => {
	if (!store.trainingData?.steps) return;
	const idx = store.trainingData.steps.findIndex(s => s.id === store.selectedStep?.id);
	if (idx < store.trainingData.steps.length - 1) store.selectStep(store.trainingData.steps[idx + 1]);
};

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
	metaKeywords.value?.length ? metaKeywords.value.join(' + ') : "Не назначено"
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
				seq.length - 1
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

const openHotkeyDialog = () => { isHotkeyDialogOpen.value = true; };

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
			seq.length - 1
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
	}))
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
				...(["metaText", "metaKeywords", "metaFontSize", "metaMatchMode", "metaPattern", "metaPatternPreset"].reduce(
					(o, k) => {
						if (a[k] != null) o[k] = a[k];
						return o;
					},
					{}
				)),
			},
		];
	}
	const w = step.photo_dimensions?.width || 800;
	const h = step.photo_dimensions?.height || 600;
	actions = [...actions, {
		action_type_id: ev.id,
		x: Math.min(32, w - 180),
		y: Math.min(120, h - 80),
		width: 168,
		height: 44,
	}];
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
	for (const k of ["metaText", "metaKeywords", "metaFontSize", "metaMatchMode", "metaPattern", "metaPatternPreset", "metaTextScale"]) {
		if (f[k] != null) flat[k] = f[k];
	}
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, step.id, {
			action_type_id: f.action_type_id,
			area: {
				...flat,
				actions: [],
			},
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
		seq.length - 1
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
			for (const k of ["metaText", "metaKeywords", "metaFontSize", "metaMatchMode", "metaPattern", "metaPatternPreset", "metaTextScale"]) {
				if (f[k] != null) flat[k] = f[k];
			}
			await trainingStepApi.editStep(store.trainingData.uuid, step.id, {
				action_type_id: f.action_type_id,
				area: {
					...flat,
					actions: [],
				},
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
	}
);

const events = [
	{ type: "leftClick",  name: "Левый клик",       shortName: "ЛКМ",     icon: LeftClick,   id: 1 },
	{ type: "rightClick", name: "Правый клик",      shortName: "ПКМ",     icon: RightClick,  id: 2 },
	{ type: "doubleClick",name: "Двойной клик",     shortName: "2x клик", icon: DoubleClick, id: 3 },
	{ type: "hover",      name: "Наведение курсора",shortName: "Hover",   icon: Mouseover,   id: 4 },
	{ type: "inputText",  name: "Ввод текста",      shortName: "Текст",   icon: Text,        id: 5 },
	{ type: "keyPress",   name: "Нажатие клавиши",  shortName: "Клавиша", icon: Keyboard,    id: 6 },
];
</script>

<style scoped>
.tool-bar-container {
	position: absolute;
	z-index: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12px;
	width: 100%;
	left: 0;
	bottom: 24px;
	pointer-events: none;
}

.tool-bar-container > * {
	pointer-events: auto;
}

.tool-bar {
	display: flex;
	gap: 4px;
	padding: 8px;
	border-radius: 20px;
}

.tool-btn {
	border-radius: 12px;
	padding: 6px 10px;
	transition: all 0.2s ease;
	min-width: 56px;
}

.tool-btn:hover {
	background: rgba(80, 100, 247, 0.08);
}

.tool-btn-active {
	background: var(--q-primary) !important;
	color: white !important;
	box-shadow: 0 2px 8px rgba(80, 100, 247, 0.3);
}

.tool-btn-active:hover {
	background: var(--q-primary) !important;
}

.tool-btn-inner {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 2px;
}

.tool-btn-label {
	font-size: 10px;
	font-weight: 500;
	line-height: 1;
	opacity: 0.8;
}

.tool-btn-active .tool-btn-label {
	opacity: 1;
}

.hotkey-panel {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 10px 16px;
	border-radius: 14px;
}

.hotkey-panel-label {
	font-size: 13px;
	font-weight: 500;
	color: #374151;
}

.nav-btn {
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
	border: 1px solid rgba(0, 0, 0, 0.06);
}

.panel-slide-enter-active,
.panel-slide-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.panel-slide-enter-from,
.panel-slide-leave-to {
	opacity: 0;
	transform: translateY(8px);
}

.multi-action-strip {
	display: flex;
	flex-direction: column;
	align-items: stretch;
	gap: 6px;
	pointer-events: auto;
	max-width: min(340px, 90vw);
	padding: 8px 10px;
	border-radius: 14px;
	border: 1px solid rgba(80, 100, 247, 0.14);
	box-shadow: 0 6px 14px rgba(15, 23, 42, 0.07);
}

.multi-action-header {
	gap: 8px;
}

.multi-action-title {
	font-size: 12px;
	font-weight: 600;
	color: #334155;
}

.multi-action-btn {
	border-radius: 999px;
	padding: 4px 8px;
}

.multi-action-btn--danger {
	background: rgba(239, 68, 68, 0.08);
}

.multi-action-tabs {
	flex-wrap: wrap;
	justify-content: flex-start;
}

.multi-action-tabs .text-caption {
	font-size: 11px;
}

.multi-action-toggle :deep(.q-btn) {
	min-width: 30px;
	min-height: 28px;
	border-radius: 999px;
}

.multi-action-actions {
	flex-wrap: nowrap;
	justify-content: flex-end;
}
</style>
