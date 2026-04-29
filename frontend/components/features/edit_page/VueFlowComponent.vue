<template>
	<div ref="flowContainerRef" class="fullscreen-flow">
		<VueFlow v-model="nodes" :default-viewport="{ zoom: 0.7 }" :node-types="nodeTypes" @node-drag-stop="onNodeDragStop">
			<template #node-screenshot>
				<ScreenshotNode />
			</template>
			<template #node-resizable="resizableNodeProps">
				<ResizableNode :node="resizableNodeProps" />
			</template>
		</VueFlow>
	</div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed, provide, nextTick } from "vue";
import { VueFlow, Position } from "@vue-flow/core";
import { eventRequiresArea, eventRequiresAreaCoordinates } from "@utils/actionTypes.js";
import { useTrainingData } from "@store/editTraining.js";
import { trainingStepApi } from "@api";
import { useQuasar } from "quasar";
import ResizableNode from "./ResizableNode.vue";
import ScreenshotNode from "./ScreenshotNode.vue";
import { useVueFlow } from "@vue-flow/core";

const store = useTrainingData();
const $q = useQuasar();
const nodes = ref([]);
const flowContainerRef = ref(null);
const nodeTypes = { screenshot: ScreenshotNode };
const DEFAULT_ZOOM = 0.7;

const { onPaneClick } = useVueFlow();

const eventRequiresAreaOpt = (event) => eventRequiresArea(event);

const drawingEnabled = computed(() => {
	return !!store.selectedEvent && eventRequiresAreaOpt(store.selectedEvent);
});

// Флаг, указывающий, происходит ли сейчас рисование новой области
const isCurrentlyDrawing = ref(false);
const lastDrawnArea = ref(null);

onPaneClick(() => {
	if (isCurrentlyDrawing.value) isCurrentlyDrawing.value = false;
});

const onAreaDrawn = async (area) => {
	isCurrentlyDrawing.value = false;
	const event = store.selectedEvent;
	if (!event) return;
	lastDrawnArea.value = { x: area.x, y: area.y, width: area.width, height: area.height };
	createNode(event, area.width, area.height, area.x, area.y);
	// Автосохранение после рисования
	if (eventRequiresAreaCoordinates(event) && store.trainingData?.uuid && store.selectedStep?.id) {
		try {
			await trainingStepApi.editStep(store.trainingData.uuid, store.selectedStep.id, {
				action_type_id: event.id,
				area: {
					x: area.x,
					y: area.y,
					width: area.width,
					height: area.height,
					metaText: store.selectedStep.area?.metaText ?? '',
					metaKeywords: store.selectedStep.area?.metaKeywords ?? [],
					metaTextScale: store.selectedStep.area?.metaTextScale ?? 1,
				}
			});
			// Обновляем стор — чтобы при возврате на шаг область восстановилась
			if (!store.selectedStep.area) store.selectedStep.area = {};
			Object.assign(store.selectedStep.area, area);
			store.selectedStep.action_type = { ...event };
			// Синхронизируем объект в массиве шагов
			const stepInList = store.steps?.find(s => s.id === store.selectedStep.id);
			if (stepInList) {
				if (!stepInList.area) stepInList.area = {};
				Object.assign(stepInList.area, area);
				stepInList.action_type = { ...event };
			}
			$q.notify({ color: 'positive', message: 'Область сохранена', position: 'bottom-right', icon: 'check_circle', timeout: 1500 });
		} catch {
			$q.notify({ color: 'negative', message: 'Не удалось сохранить область', position: 'top' });
		}
	}
};

const onNodeDragStop = async () => {
	// Пересохраняем позицию ноды после перетаскивания
	const event = store.selectedEvent;
	if (!event || !eventRequiresAreaCoordinates(event)) return;
	if (!store.trainingData?.uuid || !store.selectedStep?.id) return;
	if (nodes.value.length < 2) return;
	const imageNode = nodes.value[0];
	const eventNode = nodes.value[1];
	const imgPos = imageNode.computedPosition ?? imageNode.position ?? { x: 0, y: 0 };
	const evtPos = eventNode.computedPosition ?? eventNode.position ?? { x: 0, y: 0 };
	const relX = Math.max(0, Math.round(evtPos.x - imgPos.x));
	const relY = Math.max(0, Math.round(evtPos.y - imgPos.y));
	const dims = eventNode.dimensions ?? {};
	const w = Math.round(dims.width || parseInt(eventNode.style?.width, 10) || 0);
	const h = Math.round(dims.height || parseInt(eventNode.style?.height, 10) || 0);
	if (!w || !h) return;
	const updatedArea = { x: relX, y: relY, width: w, height: h };
	try {
		await trainingStepApi.editStep(store.trainingData.uuid, store.selectedStep.id, {
			action_type_id: event.id,
			area: {
				...updatedArea,
				metaText: store.selectedStep.area?.metaText ?? '',
				metaKeywords: store.selectedStep.area?.metaKeywords ?? [],
				metaTextScale: store.selectedStep.area?.metaTextScale ?? 1,
			}
		});
		if (!store.selectedStep.area) store.selectedStep.area = {};
		Object.assign(store.selectedStep.area, updatedArea);
		store.selectedStep.action_type = { ...event };
		const stepInList = store.steps?.find(s => s.id === store.selectedStep.id);
		if (stepInList) {
			if (!stepInList.area) stepInList.area = {};
			Object.assign(stepInList.area, updatedArea);
			stepInList.action_type = { ...event };
		}
		$q.notify({ color: 'positive', message: 'Позиция обновлена', position: 'bottom-right', icon: 'check_circle', timeout: 1200 });
	} catch {
		// тихо игнорируем
	}
	lastDrawnArea.value = null;
};

provide("onAreaDrawn", onAreaDrawn);
provide("drawingEnabled", drawingEnabled);
provide("setIsCurrentlyDrawing", (val) => { isCurrentlyDrawing.value = val; });
provide("getAreaForSave", () => {
	if (nodes.value.length < 2) return null;
	const imageNode = nodes.value[0];
	const eventNode = nodes.value[1];
	const imgPos = imageNode.computedPosition ?? imageNode.position ?? { x: 0, y: 0 };
	const evtPos = eventNode.computedPosition ?? eventNode.position ?? { x: 0, y: 0 };
	const relX = evtPos.x - imgPos.x;
	const relY = evtPos.y - imgPos.y;
	const dims = eventNode.dimensions ?? {};
	let w = dims.width ?? 0;
	let h = dims.height ?? 0;
	if (!w || !h) {
		const style = eventNode.style || {};
		if (typeof style.width === "string") w = parseInt(style.width, 10) || w;
		if (typeof style.height === "string") h = parseInt(style.height, 10) || h;
	}
	let width = Math.round(w) || 0;
	let height = Math.round(h) || 0;

	if (lastDrawnArea.value) {
		const drawn = lastDrawnArea.value;
		const dimsMatch = Math.abs((dims.width || 0) - drawn.width) < 2 && Math.abs((dims.height || 0) - drawn.height) < 2;
		if (dimsMatch) {
			return {
				x: drawn.x,
				y: drawn.y,
				width: drawn.width,
				height: drawn.height,
			};
		}
	}

	if (!width || !height) return null;
	return {
		x: Math.max(0, Math.round(relX)),
		y: Math.max(0, Math.round(relY)),
		width,
		height,
	};
});

const clearEventNode = () => {
	if (nodes.value.length > 0) {
		nodes.value = [nodes.value[0]];
	}
	lastDrawnArea.value = null;
};

const createFullscreenNode = async () => {
	const { width: imgWidth, height: imgHeight } = store.selectedStep.photo_dimensions;
	const el = flowContainerRef.value;
	const canvasWidth = el ? el.clientWidth : window.innerWidth;
	const canvasHeight = el ? el.clientHeight : window.innerHeight;
	const viewFlowW = canvasWidth / DEFAULT_ZOOM;
	const viewFlowH = canvasHeight / DEFAULT_ZOOM;
	const x = (viewFlowW - imgWidth) / 2;
	const y = (viewFlowH - imgHeight) / 2;

	nodes.value[0] = {
		id: "fullscreen-image",
		type: "screenshot",
		position: { x, y },
		style: {
			backgroundImage: `url(${store.selectedStep.image_url})`,
			backgroundSize: "contain",
			backgroundRepeat: "no-repeat",
			width: `${imgWidth}px`,
			height: `${imgHeight}px`,
		},
		dimensions: {
			width: imgWidth,
			height: imgHeight,
		},
		connectable: false,
		data: { label: "" },
		class: "fullscreen-node",
		draggable: false,
		selectable: false,
	};

	/* Не трогаем selectedEvent здесь: иначе при смене действия в тулбаре watch пересобирает сцену
	   и снова подставляет action_type с сервера, сбрасывая выбор пользователя. */
};

const createNode = (
	event,
	width = 200,
	height = 200,
	relativeX = 0,
	relativeY = 0,
) => {
	const imageNode = nodes.value[0];

	if (!imageNode) {
		return;
	}

	const maxX = imageNode.dimensions.width - width;
	const maxY = imageNode.dimensions.height - height;

	const clampedX = Math.max(0, Math.min(relativeX, maxX));
	const clampedY = Math.max(0, Math.min(relativeY, maxY));

	const finalAbsoluteX = imageNode.position.x + clampedX;
	const finalAbsoluteY = imageNode.position.y + clampedY;

	const nodeData = {
		id: `event-${event.id}`,
		type: "resizable",
		draggable: true,
		data: {
			label: event.name,
			type: event.type,
			toolbarPosition: Position.Top,
			toolbarVisible: true,
		},
		dimensions: {
			width: Math.round(width),
			height: Math.round(height),
		},
		position: {
			x: finalAbsoluteX,
			y: finalAbsoluteY
		},
		style: {
			border: "2px solid var(--q-primary)",
			borderRadius: "4px",
			background: "rgba(80, 100, 247, 0.06)",
			width: `${Math.round(width)}px`,
			height: `${Math.round(height)}px`,
		},
		class: "event-node",
	};

	if (nodes.value.length > 1) {
		nodes.value[1] = nodeData;
	} else {
		nodes.value.push(nodeData);
	}

	nodes.value = [...nodes.value];
};

/** Пересборка сцены при смене шага, картинки или выбранного действия в тулбаре */
async function syncFlowFromStep() {
	const step = store.selectedStep;
	if (!step?.image_url || !step.photo_dimensions) {
		nodes.value = [];
		return;
	}
	lastDrawnArea.value = null;
	clearEventNode();
	await createFullscreenNode();
	await nextTick();
	await nextTick();
	const ev = store.selectedEvent;
	if (!ev || !eventRequiresAreaOpt(ev)) return;
	const a = step.area;
	// Показываем сохранённую область если она есть И соответствует текущему типу события
	const areaMatchesEvent = step.action_type?.id === ev.id;
	if (areaMatchesEvent && a?.width > 0 && a?.height > 0) {
		createNode(ev, a.width, a.height, a.x ?? 0, a.y ?? 0);
	} else if (!areaMatchesEvent && a?.width > 0 && a?.height > 0 && !step.action_type) {
		// Нет action_type на шаге, но area есть — показываем (данные после автосохранения)
		createNode(ev, a.width, a.height, a.x ?? 0, a.y ?? 0);
	} else {
		createNode(ev);
	}
}

const updateNodePositionOnResize = () => {
	if (nodes.value.length < 1) return;

	const imageNode = nodes.value[0];
	if (!imageNode) return;

	const el = flowContainerRef.value;
	const canvasWidth = el ? el.clientWidth : window.innerWidth;
	const canvasHeight = el ? el.clientHeight : window.innerHeight;
	if (canvasWidth < 80 || canvasHeight < 80) return;

	const imgWidth = imageNode.dimensions.width;
	const imgHeight = imageNode.dimensions.height;
	const viewFlowW = canvasWidth / DEFAULT_ZOOM;
	const viewFlowH = canvasHeight / DEFAULT_ZOOM;
	const newImageX = (viewFlowW - imgWidth) / 2;
	const newImageY = (viewFlowH - imgHeight) / 2;

	if (nodes.value.length < 2) {
		nodes.value[0].position = { x: newImageX, y: newImageY };
		nodes.value = [...nodes.value];
		return;
	}

	const eventNode = nodes.value[1];
	const relativeX = eventNode.position.x - imageNode.position.x;
	const relativeY = eventNode.position.y - imageNode.position.y;

	nodes.value[0].position = { x: newImageX, y: newImageY };
	nodes.value[1].position = {
		x: newImageX + relativeX,
		y: newImageY + relativeY,
	};

	nodes.value = [...nodes.value];
};


/** При смене шага или картинки — восстановить выбранное действие из сохранённых данных шага */
watch(
	() => [store.selectedStep?.id, store.selectedStep?.image_url],
	() => {
		const st = store.selectedStep;
		if (st?.action_type) {
			store.selectEvent(st.action_type);
		} else {
			store.selectEvent(null);
		}
	},
	{ flush: "pre", immediate: true },
);

watch(
	() => [store.selectedStep?.id, store.selectedStep?.image_url, store.selectedEvent?.id],
	() => {
		syncFlowFromStep();
	},
	{ flush: "post" },
);

let flowResizeObserver = null;

onMounted(() => {
	void syncFlowFromStep();
	window.addEventListener("resize", updateNodePositionOnResize);
	nextTick(() => {
		nextTick(() => {
			updateNodePositionOnResize();
			if (typeof ResizeObserver !== "undefined" && flowContainerRef.value) {
				flowResizeObserver = new ResizeObserver(() => {
					updateNodePositionOnResize();
				});
				flowResizeObserver.observe(flowContainerRef.value);
			}
		});
	});
});

onUnmounted(() => {
	window.removeEventListener("resize", updateNodePositionOnResize);
	flowResizeObserver?.disconnect();
});
</script>

<style>
@import "@vue-flow/core/dist/style.css";
@import "@vue-flow/core/dist/theme-default.css";
.fullscreen-flow {
	flex: 1;
	min-height: 0;
	width: 100%;
	height: 100%;
	margin: 0;
	padding: 0;
	overflow: hidden;
	display: flex;
	flex-direction: column;
	position: relative;
}

.fullscreen-flow .vue-flow,
.fullscreen-flow .vue-flow__pane {
	background: transparent !important;
}

.fullscreen-node {
	border: none !important;
	background-color: transparent !important;
	box-shadow: none !important;
}

.fullscreen-node .vue-flow__handle {
	display: none !important;
}

.event-node .vue-flow__handle {
	display: none !important;
}

.event-node {
	transition: box-shadow 0.2s ease;
}

.event-node:hover {
	box-shadow: 0 0 0 4px rgba(80, 100, 247, 0.2);
}

.event-node.selected {
	border: 2px solid #a855f7 !important;
	box-shadow: 0 0 15px rgba(168, 85, 247, 0.4);
	animation: node-pulse 2s infinite;
}

@keyframes node-pulse {
	0%, 100% { box-shadow: 0 0 12px rgba(168, 85, 247, 0.3); }
	50% { box-shadow: 0 0 20px rgba(168, 85, 247, 0.6); }
}
</style>
