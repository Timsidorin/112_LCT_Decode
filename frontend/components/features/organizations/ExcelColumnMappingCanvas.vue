<template>
	<div ref="rootRef" class="excel-map-root">
		<VueFlow
			:id="flowId"
			v-model:nodes="nodes"
			v-model:edges="edges"
			:node-types="nodeTypes"
			:default-viewport="{ zoom: 0.85, x: 0, y: 0 }"
			:min-zoom="0.35"
			:max-zoom="1.3"
			:nodes-connectable="true"
			:elements-selectable="true"
			:connect-on-click="false"
			class="excel-map-flow"
			@connect="onConnect"
			@edges-change="onEdgesChange"
		/>
	</div>
</template>

<script setup>
import { markRaw, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { VueFlow, useVueFlow } from "@vue-flow/core";
import ExcelPreviewTableNode from "./ExcelPreviewTableNode.vue";
import ImportSchemaTableNode from "./ImportSchemaTableNode.vue";

const props = defineProps({
	flowId: { type: String, required: true },
	columns: { type: Array, default: () => [] },
	mapping: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["update:mapping"]);

const nodes = defineModel("nodes", { type: Array, default: () => [] });
const edges = defineModel("edges", { type: Array, default: () => [] });

const rootRef = ref(null);
let resizeObserver = null;

const nodeTypes = {
	excelTable: markRaw(ExcelPreviewTableNode),
	schemaTable: markRaw(ImportSchemaTableNode),
};

const { fitView } = useVueFlow({ id: props.flowId });

function columnIndexFromHandle(handleId) {
	const match = String(handleId || "").match(/^col-(\d+)$/);
	return match ? Number(match[1]) : -1;
}

function doFitView() {
	void fitView({ padding: 0.18, duration: 200 });
}

function buildGraph() {
	if (!props.columns.length) {
		nodes.value = [];
		edges.value = [];
		return;
	}

	nodes.value = [
		{
			id: "excel-source",
			type: "excelTable",
			position: { x: 30, y: 30 },
			data: {
				columns: props.columns,
				mapping: props.mapping,
			},
			draggable: true,
		},
		{
			id: "schema-target",
			type: "schemaTable",
			position: { x: 380, y: 30 },
			data: { mapping: props.mapping },
			draggable: true,
		},
	];

	rebuildEdges();
	void nextTick(doFitView);
}

function rebuildEdges() {
	const next = [];

	const pushEdge = (colIndex, fieldKey) => {
		next.push({
			id: `e-${colIndex}-${fieldKey}`,
			source: "excel-source",
			sourceHandle: `col-${colIndex}`,
			target: "schema-target",
			targetHandle: fieldKey,
			animated: true,
			style: { stroke: "#5064f7", strokeWidth: 2.5 },
		});
	};

	props.columns.forEach((col, index) => {
		for (const fieldKey of ["email", "full_name", "position"]) {
			if (props.mapping[fieldKey] === col) {
				pushEdge(index, fieldKey);
			}
		}
		if (Array.isArray(props.mapping.full_name_parts) && props.mapping.full_name_parts.includes(col)) {
			pushEdge(index, "full_name");
		}
	});

	edges.value = next;

	if (nodes.value.length) {
		nodes.value = nodes.value.map((node) => ({
			...node,
			data: {
				...node.data,
				columns: props.columns,
				mapping: props.mapping,
			},
		}));
	}
}

function onConnect(params) {
	const colIndex = columnIndexFromHandle(params.sourceHandle);
	const fieldKey = params.targetHandle;
	if (colIndex < 0 || !fieldKey || !props.columns[colIndex]) return;

	const column = props.columns[colIndex];
	const next = { ...props.mapping };

	if (fieldKey === "full_name") {
		const parts = Array.isArray(next.full_name_parts) ? [...next.full_name_parts] : [];
		delete next.full_name;
		if (!parts.includes(column)) parts.push(column);
		next.full_name_parts = parts.filter(Boolean);
		for (const fk of ["email", "position"]) {
			if (next[fk] === column) delete next[fk];
		}
	} else {
		for (const fk of Object.keys(next)) {
			if (fk === "full_name_parts" && Array.isArray(next[fk])) {
				next[fk] = next[fk].filter((c) => c !== column);
				if (!next[fk].length) delete next[fk];
			} else if (next[fk] === column && fk !== fieldKey) {
				delete next[fk];
			}
		}
		next[fieldKey] = column;
		delete next.full_name;
	}

	emit("update:mapping", next);
}

function onEdgesChange(changes) {
	for (const change of changes) {
		if (change.type !== "remove") continue;
		const fieldKey = String(change.id).replace(/^e-\d+-/, "");
		if (!fieldKey) continue;
		const next = { ...props.mapping };
		if (fieldKey === "full_name") {
			delete next.full_name;
			delete next.full_name_parts;
		} else {
			delete next[fieldKey];
		}
		emit("update:mapping", next);
	}
}

watch(
	() => props.columns,
	() => buildGraph(),
	{ immediate: true, deep: true },
);

watch(
	() => props.mapping,
	() => rebuildEdges(),
	{ deep: true },
);

onMounted(() => {
	void nextTick(doFitView);
	if (rootRef.value && typeof ResizeObserver !== "undefined") {
		resizeObserver = new ResizeObserver(() => doFitView());
		resizeObserver.observe(rootRef.value);
	}
});

onBeforeUnmount(() => {
	resizeObserver?.disconnect();
});

defineExpose({ refreshView: doFitView });
</script>

<style scoped>
.excel-map-root {
	position: absolute;
	inset: 0;
	width: 100%;
	height: 100%;
}

.excel-map-flow {
	width: 100%;
	height: 100%;
}
</style>

<style>
@import "@vue-flow/core/dist/style.css";
@import "@vue-flow/core/dist/theme-default.css";

.excel-map-flow .vue-flow__pane {
	background: radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.22) 1px, transparent 0)
		0 0 / 20px 20px !important;
}

.excel-map-flow .vue-flow__handle {
	width: 11px;
	height: 11px;
	background: #5064f7;
	border: 2px solid #fff;
}
</style>
