<template>
	<VueFlow
		:id="flowId"
		v-model:nodes="nodes"
		v-model:edges="edges"
		:node-types="nodeTypes"
		:edge-types="edgeTypes"
		:default-viewport="{ zoom: 0.85 }"
		:min-zoom="0.25"
		:max-zoom="1.5"
		:nodes-connectable="false"
		:edges-updatable="false"
		:delete-key-code="null"
		class="scenario-map-flow"
		@node-drag-stop="emit('node-drag-stop')"
	>
	</VueFlow>
</template>

<script setup>
import { markRaw, onMounted, watch } from "vue";
import { VueFlow, useVueFlow } from "@vue-flow/core";
import StepNode from "./StepNode.vue";
import AddEdge from "./AddEdge.vue";

const props = defineProps({
	flowId: { type: String, required: true },
	nodes: { type: Array, required: true },
	edges: { type: Array, required: true },
});

const emit = defineEmits(["node-drag-stop", "update:nodes", "update:edges"]);

const nodes = defineModel("nodes", { type: Array, required: true });
const edges = defineModel("edges", { type: Array, required: true });

const nodeTypes = { step: markRaw(StepNode) };
const edgeTypes = { add: markRaw(AddEdge) };

const { fitView } = useVueFlow({ id: props.flowId });

function doFitView() {
	void fitView({ padding: 0.2, duration: 250 });
}

onMounted(() => {
	doFitView();
});

watch(
	() => [props.nodes.length, props.edges.length],
	() => {
		doFitView();
	},
);

defineExpose({ fitView: doFitView });
</script>

<style scoped>
.scenario-map-flow {
	width: 100%;
	height: 100%;
}
</style>

<style>
@import "@vue-flow/core/dist/style.css";
@import "@vue-flow/core/dist/theme-default.css";

.scenario-map-flow .vue-flow__pane {
	background:
		radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.35) 1px, transparent 0)
		0 0 / 20px 20px !important;
}
</style>
