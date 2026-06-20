<template>
	<g>
		<BaseEdge :path="path" :marker-end="markerEnd" class="scenario-add-edge__line" />
		<EdgeLabelRenderer>
			<div
				class="scenario-add-edge__label nodrag nopan"
				:style="labelStyle"
			>
				<q-btn
					round
					dense
					unelevated
					color="primary"
					icon="add"
					size="sm"
					class="scenario-add-edge__btn"
					@click.stop="onAddClick"
				>
					<q-tooltip>Добавить шаг после этого</q-tooltip>
				</q-btn>
			</div>
		</EdgeLabelRenderer>
	</g>
</template>

<script setup>
import { computed } from "vue";
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "@vue-flow/core";

const props = defineProps({
	id: { type: String, required: true },
	sourceX: { type: Number, required: true },
	sourceY: { type: Number, required: true },
	targetX: { type: Number, required: true },
	targetY: { type: Number, required: true },
	sourcePosition: { type: String, required: true },
	targetPosition: { type: String, required: true },
	markerEnd: { type: String, default: undefined },
	data: { type: Object, default: () => ({}) },
});

const pathData = computed(() =>
	getBezierPath({
		sourceX: props.sourceX,
		sourceY: props.sourceY,
		targetX: props.targetX,
		targetY: props.targetY,
		sourcePosition: props.sourcePosition,
		targetPosition: props.targetPosition,
	}),
);

const path = computed(() => pathData.value[0]);
const labelX = computed(() => pathData.value[1]);
const labelY = computed(() => pathData.value[2]);

const labelStyle = computed(() => ({
	position: "absolute",
	transform: `translate(-50%, -50%) translate(${labelX.value}px, ${labelY.value}px)`,
	pointerEvents: "all",
}));

function onAddClick() {
	props.data?.onAdd?.(props.data?.afterStepId);
}
</script>

<style>
.scenario-add-edge__line {
	stroke: rgba(80, 100, 247, 0.45);
	stroke-width: 2;
}

.scenario-add-edge__btn {
	box-shadow: 0 4px 14px rgba(80, 100, 247, 0.35);
}
</style>
