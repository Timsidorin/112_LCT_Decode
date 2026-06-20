<template>
	<q-dialog
		:model-value="modelValue"
		maximized
		transition-show="slide-up"
		transition-hide="slide-down"
		@update:model-value="emit('update:modelValue', $event)"
	>
		<q-card class="scenario-map-dialog column">
			<q-card-section class="scenario-map-dialog__header row items-center q-pb-sm">
				<div>
					<div class="text-h6">Карта сценария</div>
					<div class="text-caption text-grey-7">
						Перетаскивайте карточки для изменения порядка · клик — перейти к шагу
					</div>
				</div>
				<q-space />
				<q-btn
					flat
					no-caps
					rounded
					color="primary"
					icon="add_photo_alternate"
					label="В начало"
					class="q-mr-sm"
					:disable="busy"
					@click="insertAtStart"
				/>
				<q-btn
					flat
					round
					dense
					icon="fit_screen"
					color="grey-7"
					@click="canvasRef?.fitView?.()"
				>
					<q-tooltip>Подогнать масштаб</q-tooltip>
				</q-btn>
				<q-btn flat round dense icon="close" v-close-popup />
			</q-card-section>

			<q-separator />

			<q-card-section class="scenario-map-dialog__canvas col q-pa-none">
				<q-inner-loading :showing="busy">
					<q-spinner-dots size="42px" color="primary" />
				</q-inner-loading>

				<div v-if="!stepsArray.length" class="scenario-map-dialog__empty">
					<q-icon name="account_tree" size="56px" color="grey-5" />
					<p class="text-body2 text-grey-7 q-mt-md q-mb-none">
						Шагов пока нет — добавьте скриншоты в редакторе
					</p>
				</div>

				<ScenarioMapCanvas
					v-else
					ref="canvasRef"
					:flow-id="flowId"
					v-model:nodes="nodes"
					v-model:edges="edges"
					@node-drag-stop="onNodeDragStop"
				/>
			</q-card-section>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useQuasar } from "quasar";
import { useTrainingData } from "@store/editTraining.js";
import { TrainingApi, TrainingStepApi, MetaTrainingApi } from "@api";
import ScenarioMapCanvas from "./ScenarioMapCanvas.vue";
import {
	buildOrderWithInsert,
	buildOrderWithInsertAtStart,
	buildScenarioGraph,
	computeOrderFromNodes,
	layoutNodesInOrder,
	sortStepsByNumber,
	stepLabel,
} from "@utils/scenarioMapLayout.js";

const props = defineProps({
	modelValue: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const $q = useQuasar();
const store = useTrainingData();
const { steps, selectedStep, trainingData } = storeToRefs(store);
const stepApi = new TrainingStepApi();
const trainingApi = new TrainingApi();
const metaApi = new MetaTrainingApi();

const flowId = "scenario-map-flow";
const canvasRef = ref(null);
const nodes = ref([]);
const edges = ref([]);
const busy = ref(false);
const skipGraphRebuild = ref(false);

const stepsArray = computed(() =>
	Array.isArray(steps.value) ? sortStepsByNumber(steps.value) : [],
);

const trainingUuid = computed(() => trainingData.value?.uuid ?? "");

function closeDialog() {
	emit("update:modelValue", false);
}

function rebuildGraph() {
	if (skipGraphRebuild.value) return;
	const graph = buildScenarioGraph(stepsArray.value, {
		selectedStepId: selectedStep.value?.id,
		onSelect: handleSelectStep,
		onDelete: confirmDeleteStep,
		onAdd: insertAfterStep,
	});
	nodes.value = graph.nodes;
	edges.value = graph.edges;
}

watch(
	() => [props.modelValue, stepsArray.value, selectedStep.value?.id],
	([open]) => {
		if (!open) return;
		rebuildGraph();
		void nextTick(() => canvasRef.value?.fitView?.());
	},
	{ deep: true },
);

function handleSelectStep(step) {
	if (!step) return;
	store.selectStep(step);
	closeDialog();
}

function confirmDeleteStep(step) {
	const name = stepLabel(step);
	$q.dialog({
		title: "Удалить шаг?",
		message: `Шаг «${name}» будет удалён без возможности восстановления.`,
		cancel: { label: "Отмена", flat: true },
		ok: { label: "Удалить", color: "negative", flat: true },
		persistent: true,
	}).onOk(() => {
		void deleteStep(step.id);
	});
}

async function deleteStep(stepId) {
	if (!trainingUuid.value) return;
	busy.value = true;
	try {
		skipGraphRebuild.value = true;
		await stepApi.deleteStep(trainingUuid.value, stepId);
		const { data } = await trainingApi.getTrainingByUuid(trainingUuid.value);
		store.setTrainingData(data, { preserveStepId: selectedStep.value?.id });
		rebuildGraph();
		$q.notify({
			color: "positive",
			message: "Шаг удалён",
			position: "bottom-right",
		});
	} catch {
		$q.notify({
			color: "negative",
			message: "Не удалось удалить шаг",
			position: "top",
		});
	} finally {
		skipGraphRebuild.value = false;
		busy.value = false;
	}
}

async function persistOrder(orderPayload) {
	if (!trainingUuid.value || !orderPayload.length) return;
	await stepApi.reorderSteps(trainingUuid.value, { steps: orderPayload });
	const sortedLocal = [...stepsArray.value].sort((a, b) => {
		const aOrder = orderPayload.find((x) => x.id === a.id)?.step_number ?? a.step_number;
		const bOrder = orderPayload.find((x) => x.id === b.id)?.step_number ?? b.step_number;
		return aOrder - bOrder;
	});
	store.steps = sortedLocal.map((step) => {
		const nextNumber = orderPayload.find((x) => x.id === step.id)?.step_number;
		return nextNumber ? { ...step, step_number: nextNumber } : step;
	});
	const currentId = selectedStep.value?.id;
	if (currentId) {
		const refreshed = store.steps.find((s) => s.id === currentId);
		if (refreshed) store.selectStep(refreshed);
	}
}

async function onNodeDragStop() {
	const orderPayload = computeOrderFromNodes(nodes.value);
	const currentOrder = stepsArray.value.map((s, i) => ({
		id: s.id,
		step_number: i + 1,
	}));
	const changed = orderPayload.some(
		(item, index) => item.id !== currentOrder[index]?.id,
	);
	if (!changed) {
		nodes.value = layoutNodesInOrder(nodes.value);
		return;
	}

	busy.value = true;
	try {
		skipGraphRebuild.value = true;
		await persistOrder(orderPayload);
		nodes.value = layoutNodesInOrder(nodes.value);
		rebuildGraph();
		$q.notify({
			color: "positive",
			message: "Порядок шагов обновлён",
			position: "bottom-right",
			timeout: 1500,
		});
	} catch {
		rebuildGraph();
		$q.notify({
			color: "negative",
			message: "Не удалось сохранить порядок",
			position: "top",
		});
	} finally {
		skipGraphRebuild.value = false;
		busy.value = false;
	}
}

function pickImages() {
	return new Promise((resolve) => {
		const input = document.createElement("input");
		input.type = "file";
		input.accept = "image/*";
		input.multiple = true;
		input.onchange = () => resolve(Array.from(input.files || []));
		input.click();
	});
}

async function uploadAndInsert(files, buildOrderFn) {
	if (!files.length || !trainingUuid.value) return;
	busy.value = true;
	try {
		skipGraphRebuild.value = true;
		const prevIds = new Set(stepsArray.value.map((s) => s.id));
		const formData = new FormData();
		for (const file of files) formData.append("files", file);
		await metaApi.uploadImages(trainingUuid.value, formData);

		const { data } = await trainingApi.getTrainingByUuid(trainingUuid.value);
		const allSteps = data.steps || [];
		const added = allSteps.filter((s) => !prevIds.has(s.id));
		const orderPayload = buildOrderFn(stepsArray.value, added);
		await stepApi.reorderSteps(trainingUuid.value, { steps: orderPayload });

		const { data: refreshed } = await trainingApi.getTrainingByUuid(trainingUuid.value);
		const firstAddedId = added[0]?.id;
		store.setTrainingData(refreshed, {
			preserveStepId: firstAddedId ?? selectedStep.value?.id,
		});
		rebuildGraph();
		void nextTick(() => canvasRef.value?.fitView?.());

		$q.notify({
			color: "positive",
			message: `Добавлено шагов: ${added.length}`,
			position: "bottom-right",
		});
	} catch {
		$q.notify({
			color: "negative",
			message: "Не удалось добавить шаг",
			position: "top",
		});
	} finally {
		skipGraphRebuild.value = false;
		busy.value = false;
	}
}

async function insertAfterStep(afterStepId) {
	const files = await pickImages();
	if (!files.length) return;
	await uploadAndInsert(files, (current, added) =>
		buildOrderWithInsert(current, added, afterStepId),
	);
}

async function insertAtStart() {
	const files = await pickImages();
	if (!files.length) return;
	await uploadAndInsert(files, buildOrderWithInsertAtStart);
}
</script>

<style scoped>
.scenario-map-dialog {
	width: 100%;
	height: 100%;
	background: #f8fafc;
}

.scenario-map-dialog__header {
	flex-shrink: 0;
	padding: 14px 18px;
	background: rgba(255, 255, 255, 0.92);
	backdrop-filter: blur(10px);
}

.scenario-map-dialog__canvas {
	position: relative;
	min-height: 0;
	overflow: hidden;
}

.scenario-map-dialog__empty {
	height: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}
</style>
