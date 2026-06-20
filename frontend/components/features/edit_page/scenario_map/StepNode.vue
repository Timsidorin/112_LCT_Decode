<template>
	<div
		class="scenario-step-node"
		:class="{ 'scenario-step-node--selected': data.selected }"
		@click="onCardClick"
	>
		<Handle type="target" :position="Position.Left" class="scenario-step-node__handle" />
		<Handle type="source" :position="Position.Right" class="scenario-step-node__handle" />

		<div class="scenario-step-node__header">
			<span class="scenario-step-node__badge">{{ data.step?.step_number }}</span>
			<span class="scenario-step-node__title">{{ label }}</span>
			<q-btn
				flat
				dense
				round
				size="xs"
				icon="delete_outline"
				color="grey-7"
				class="scenario-step-node__delete"
				@click.stop="onDeleteClick"
			>
				<q-tooltip>Удалить шаг</q-tooltip>
			</q-btn>
		</div>

		<div class="scenario-step-node__thumb">
			<img
				v-if="data.step?.image_url"
				:src="data.step.image_url"
				:alt="label"
				loading="lazy"
			/>
			<div v-else class="scenario-step-node__thumb-placeholder">
				<q-icon name="image_not_supported" size="28px" color="grey-5" />
			</div>
		</div>

		<div class="scenario-step-node__footer">
			<q-icon name="touch_app" size="14px" color="primary" />
			<span>{{ actionLabel }}</span>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { Handle, Position } from "@vue-flow/core";
import { stepActionLabel, stepLabel } from "@utils/scenarioMapLayout.js";

const props = defineProps({
	id: { type: String, required: true },
	data: { type: Object, required: true },
});

const label = computed(() => stepLabel(props.data?.step));
const actionLabel = computed(() => stepActionLabel(props.data?.step));

function onCardClick() {
	props.data?.onSelect?.(props.data.step);
}

function onDeleteClick() {
	props.data?.onDelete?.(props.data.step);
}
</script>

<style scoped>
.scenario-step-node {
	width: 200px;
	border-radius: 14px;
	background: rgba(255, 255, 255, 0.96);
	border: 1px solid rgba(15, 23, 42, 0.1);
	box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
	overflow: hidden;
	cursor: grab;
	transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.scenario-step-node:active {
	cursor: grabbing;
}

.scenario-step-node:hover {
	box-shadow: 0 12px 28px rgba(80, 100, 247, 0.16);
	border-color: rgba(80, 100, 247, 0.35);
}

.scenario-step-node--selected {
	border-color: rgba(80, 100, 247, 0.65);
	box-shadow: 0 0 0 3px rgba(80, 100, 247, 0.18);
}

.scenario-step-node__handle {
	width: 8px;
	height: 8px;
	background: var(--q-primary);
	border: 2px solid #fff;
	opacity: 0;
}

.scenario-step-node:hover .scenario-step-node__handle,
.scenario-step-node--selected .scenario-step-node__handle {
	opacity: 1;
}

.scenario-step-node__header {
	display: flex;
	align-items: center;
	gap: 6px;
	padding: 8px 8px 6px;
}

.scenario-step-node__badge {
	flex-shrink: 0;
	min-width: 22px;
	height: 22px;
	border-radius: 999px;
	background: rgba(80, 100, 247, 0.12);
	color: var(--q-primary);
	font-size: 11px;
	font-weight: 700;
	display: inline-flex;
	align-items: center;
	justify-content: center;
}

.scenario-step-node__title {
	flex: 1;
	min-width: 0;
	font-size: 12px;
	font-weight: 600;
	color: #1e293b;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.scenario-step-node__delete {
	opacity: 0;
	transition: opacity 0.15s ease;
}

.scenario-step-node:hover .scenario-step-node__delete,
.scenario-step-node--selected .scenario-step-node__delete {
	opacity: 0.75;
}

.scenario-step-node__thumb {
	height: 108px;
	margin: 0 8px;
	border-radius: 10px;
	overflow: hidden;
	background: #f1f5f9;
	border: 1px solid rgba(15, 23, 42, 0.06);
}

.scenario-step-node__thumb img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	display: block;
}

.scenario-step-node__thumb-placeholder {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.scenario-step-node__footer {
	display: flex;
	align-items: center;
	gap: 4px;
	padding: 8px;
	font-size: 11px;
	color: #64748b;
}
</style>
