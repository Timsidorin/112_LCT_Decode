<template>
	<NodeResizer min-width="15" min-height="15" @resize-end="onResizeEnd" />

	<template v-if="isInputTextMode">
		<input-text
			v-model="metaText"
			:font-size-px="metaFontSize"
			:match-mode="metaMatchMode"
			:pattern="metaPattern"
			:pattern-preset="metaPatternPreset"
			@update:font-size-px="onFontSizeChange"
			@update:match-mode="onMatchModeChange"
			@update:pattern="onPatternChange"
			@update:pattern-preset="onPatternPresetChange"
			@save="saveAll"
		/>
	</template>
	<template v-if="selectedMode === 'keyPress'">
		<watch-key
			v-model="metaKeywords"
			v-model:open="isHotkeyDialogOpen"
		/>
	</template>
</template>

<script setup>
import { NodeResizer } from '@vue-flow/node-resizer';
import { computed, inject, ref, watch, nextTick } from "vue";
import { useQuasar } from "quasar";
import { trainingStepApi } from "@api";
import { useTrainingData } from "@store/editTraining.js";
import { eventRequiresAreaCoordinates } from "@utils/actionTypes.js";
import InputText from "@components/features/edit_page/InputText.vue";
import WatchKey from "@components/features/edit_page/WatchKey.vue";

const DEFAULT_FONT_SIZE = 16;

const props = defineProps(['node']);
const $q = useQuasar();
const store = useTrainingData();
const getAreaForSave = inject("getAreaForSave", () => null);
const isHotkeyDialogOpen = ref(false);

// ── metaText ──────────────────────────────────────────────────────────────
const metaText = computed({
	get() { return store.selectedStep?.area?.metaText || ''; },
	set(value) {
		ensureArea();
		store.selectedStep.area.metaText = value;
	},
});

// ── metaFontSize (прямые пиксели, 10–72) ──────────────────────────────────
const metaFontSize = computed({
	get() {
		const raw = Number(store.selectedStep?.area?.metaFontSize);
		if (Number.isFinite(raw) && raw >= 8) return Math.round(raw);
		// Обратная совместимость: если есть старый metaTextScale — конвертируем
		const oldScale = Number(store.selectedStep?.area?.metaTextScale);
		if (Number.isFinite(oldScale) && oldScale > 0) return Math.round(14 * oldScale);
		return DEFAULT_FONT_SIZE;
	},
	set(value) {
		ensureArea();
		store.selectedStep.area.metaFontSize = Math.max(8, Math.min(72, Math.round(value)));
	},
});

// ── metaKeywords ───────────────────────────────────────────────────────────
const metaKeywords = computed({
	get() { return store.selectedStep?.area?.metaKeywords || []; },
	set(value) {
		ensureArea();
		store.selectedStep.area.metaKeywords = value;
	},
});

// ── metaMatchMode ('exact' | 'regex') ─────────────────────────────────────
const metaMatchMode = computed({
	get() { return store.selectedStep?.area?.metaMatchMode || 'exact'; },
	set(v) { ensureArea(); store.selectedStep.area.metaMatchMode = v; },
});

// ── metaPattern (regex string) ────────────────────────────────────────────
const metaPattern = computed({
	get() { return store.selectedStep?.area?.metaPattern || ''; },
	set(v) { ensureArea(); store.selectedStep.area.metaPattern = v; },
});

// ── metaPatternPreset ('any'|'email'|'phone'|'number'|'date'|'custom') ────
const metaPatternPreset = computed({
	get() { return store.selectedStep?.area?.metaPatternPreset || 'any'; },
	set(v) { ensureArea(); store.selectedStep.area.metaPatternPreset = v; },
});

const selectedMode = computed(() => props.node?.data?.type);
const isInputTextMode = computed(() => selectedMode.value === "inputText");

function ensureArea() {
	if (!store.selectedStep.area) store.selectedStep.area = {};
}

// ── Font size change ──────────────────────────────────────────────────────
let saveTimer = null;

function onFontSizeChange(px) {
	metaFontSize.value = px;
	clearTimeout(saveTimer);
	saveTimer = setTimeout(() => saveAll(), 600);
}

function onMatchModeChange(mode) {
	metaMatchMode.value = mode;
}

function onPatternChange(pattern) {
	metaPattern.value = pattern;
}

function onPatternPresetChange(preset) {
	metaPatternPreset.value = preset;
}

// ── Авто-расширение ноды под длинный текст ─────────────────────────────────
watch(() => metaText.value, (v) => {
	nextTick(() => autoExpand(v));
});

function autoExpand(txt) {
	if (!isInputTextMode.value || !props.node || !txt) return;
	const lines = String(txt).split("\n");
	const charW = metaFontSize.value * 0.6;
	const lineH = metaFontSize.value * 1.5;
	const maxLen = lines.reduce((m, l) => Math.max(m, l.length), 0);

	const wantedW = Math.max(30, maxLen * charW + 8);
	const wantedH = Math.max(20, lines.length * lineH + 4);

	const imgW = Number(store.selectedStep?.photo_dimensions?.width || 0);
	const imgH = Number(store.selectedStep?.photo_dimensions?.height || 0);
	const maxW = imgW > 0 ? Math.floor(imgW * 0.95) : 1200;
	const maxH = imgH > 0 ? Math.floor(imgH * 0.95) : 900;

	const curW = Number(props.node.dimensions?.width || 0);
	const curH = Number(props.node.dimensions?.height || 0);
	const newW = Math.max(curW, Math.min(maxW, wantedW));
	const newH = Math.max(curH, Math.min(maxH, wantedH));

	if (newW === curW && newH === curH) return;

	// eslint-disable-next-line vue/no-mutating-props
	props.node.dimensions = { ...(props.node.dimensions || {}), width: newW, height: newH };
	// eslint-disable-next-line vue/no-mutating-props
	props.node.style = { ...(props.node.style || {}), width: `${newW}px`, height: `${newH}px` };
}

// ── Сохранение ────────────────────────────────────────────────────────────
async function saveAll() {
	const eventType = store.selectedEvent;
	if (!eventType || !store.trainingData?.uuid || !store.selectedStep?.id) return;
	const area = getAreaForSave?.() ?? {};
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, store.selectedStep.id, {
			action_type_id: eventType.id,
			area: {
				...area,
				metaText: metaText.value,
				metaKeywords: metaKeywords.value,
				metaFontSize: metaFontSize.value,
				metaMatchMode: metaMatchMode.value,
				metaPattern: metaPattern.value,
				metaPatternPreset: metaPatternPreset.value,
			}
		});
		ensureArea();
		Object.assign(store.selectedStep.area, {
			...area,
			metaText: metaText.value,
			metaKeywords: metaKeywords.value,
			metaFontSize: metaFontSize.value,
			metaMatchMode: metaMatchMode.value,
			metaPattern: metaPattern.value,
			metaPatternPreset: metaPatternPreset.value,
		});
	} catch {
		// тихо игнорируем
	}
}

/** Автосохранение после ресайза */
async function onResizeEnd() {
	const eventType = store.selectedEvent;
	if (!eventType || !eventRequiresAreaCoordinates(eventType)) return;
	if (!store.trainingData?.uuid || !store.selectedStep?.id) return;
	const area = getAreaForSave?.();
	if (!area || !area.width || !area.height) return;
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, store.selectedStep.id, {
			action_type_id: eventType.id,
			area: {
				...area,
				metaText: metaText.value,
				metaKeywords: metaKeywords.value,
				metaFontSize: metaFontSize.value,
				metaMatchMode: metaMatchMode.value,
				metaPattern: metaPattern.value,
				metaPatternPreset: metaPatternPreset.value,
			}
		});
		ensureArea();
		Object.assign(store.selectedStep.area, area, {
			metaText: metaText.value,
			metaFontSize: metaFontSize.value,
			metaMatchMode: metaMatchMode.value,
			metaPattern: metaPattern.value,
			metaPatternPreset: metaPatternPreset.value,
		});
		$q.notify({ color: 'positive', message: 'Размер сохранён', position: 'bottom-right', icon: 'check_circle', timeout: 1000 });
	} catch {
		// тихо игнорируем
	}
}
</script>

<style>
@import "@vue-flow/node-resizer/dist/style.css";
</style>
