<template>
	<div ref="flowContainerRef" class="fullscreen-flow">
		<VueFlow
			v-model="nodes"
			:default-viewport="{ zoom: 0.7 }"
			:node-types="nodeTypes"
			@node-drag-start="onNodeDragStart"
			@node-drag-stop="onNodeDragStop"
		>
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
import {
	getExplicitActions,
	findToolbarEventById,
	buildAreaWithActions,
	sanitizeAreaForActionType,
	patchStepInStore,
	cloneJson,
} from "@utils/stepActionSequence.js";
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

function normalizeAreaForCanvas(rawArea, photoDimensions) {
	if (!rawArea || !photoDimensions?.width || !photoDimensions?.height) return rawArea;
	const W = Number(photoDimensions.width) || 1;
	const H = Number(photoDimensions.height) || 1;
	let x = Number(rawArea.x);
	let y = Number(rawArea.y);
	let w = Number(rawArea.width);
	let h = Number(rawArea.height);
	if (![x, y, w, h].every(Number.isFinite)) return rawArea;

	// 0..1 -> px
	if (
		x >= 0 && y >= 0 && w > 0 && h > 0 &&
		x <= 1 && y <= 1 && w <= 1 && h <= 1
	) {
		x *= W;
		y *= H;
		w *= W;
		h *= H;
	}
	// x1,y1,x2,y2 -> x,y,w,h
	else if (w > x && h > y && (x + w > W * 1.02 || y + h > H * 1.02)) {
		w = w - x;
		h = h - y;
	}

	return {
		...rawArea,
		x: Math.max(0, Math.round(x)),
		y: Math.max(0, Math.round(y)),
		width: Math.max(1, Math.round(w)),
		height: Math.max(1, Math.round(h)),
	};
}

const drawingEnabled = computed(() => {
	return !!store.selectedEvent && eventRequiresAreaOpt(store.selectedEvent);
});

// Флаг, указывающий, происходит ли сейчас рисование новой области
const isCurrentlyDrawing = ref(false);
const lastDrawnArea = ref(null);
/** Контекст перетаскивания: фиксируем шаг, чтобы async-save не попал в другой кадр */
const dragEditContext = ref(null);

onPaneClick(() => {
	if (isCurrentlyDrawing.value) isCurrentlyDrawing.value = false;
});

const onAreaDrawn = async (area) => {
	isCurrentlyDrawing.value = false;
	const event = store.selectedEvent;
	if (!event) return;
	lastDrawnArea.value = { x: area.x, y: area.y, width: area.width, height: area.height };
	createNode(event, area.width, area.height, area.x, area.y);
	const drawStepId = store.selectedStep?.id;
	const drawTrainingUuid = store.trainingData?.uuid;
	// Автосохранение после рисования
	if (eventRequiresAreaCoordinates(event) && drawTrainingUuid && drawStepId) {
		try {
			const step = store.steps?.find((s) => s.id === drawStepId) || store.selectedStep;
			const seq = getExplicitActions(step);
			const idx = Math.min(
				Math.max(0, store.stepActionEditIndex ?? 0),
				Math.max(0, (seq?.length || 1) - 1)
			);
			let payload;
			if (seq?.length) {
				const actions = seq.map((x) => ({ ...x }));
				while (actions.length <= idx) {
					actions.push({
						action_type_id: event.id,
						x: 0,
						y: 0,
						width: 0,
						height: 0,
					});
				}
				const prev = actions[idx] || {};
				actions[idx] = {
					...prev,
					action_type_id: event.id,
					x: area.x,
					y: area.y,
					width: area.width,
					height: area.height,
				};
				const newArea = buildAreaWithActions(actions, step.area);
				payload = {
					action_type_id: actions[0].action_type_id,
					area: newArea,
				};
			} else {
				payload = {
					action_type_id: event.id,
					area: sanitizeAreaForActionType(step.area, event.id, {
						x: area.x,
						y: area.y,
						width: area.width,
						height: area.height,
					}),
				};
			}
			await trainingStepApi.editStep(drawTrainingUuid, drawStepId, payload);
			patchStepInStore(store.steps, drawStepId, payload);
			$q.notify({ color: 'positive', message: 'Область сохранена', position: 'bottom-right', icon: 'check_circle', timeout: 1500 });
		} catch {
			$q.notify({ color: 'negative', message: 'Не удалось сохранить область', position: 'top' });
		}
	}
};

const onNodeDragStart = () => {
	const step = store.selectedStep;
	if (!step?.id || !store.trainingData?.uuid) return;
	dragEditContext.value = {
		stepId: step.id,
		trainingUuid: store.trainingData.uuid,
		eventId: store.selectedEvent?.id,
		area: cloneJson(step.area),
	};
};

const onNodeDragStop = async () => {
	const ctx = dragEditContext.value;
	dragEditContext.value = null;
	const eventId = ctx?.eventId ?? store.selectedEvent?.id;
	const event = eventId ? findToolbarEventById(eventId) : store.selectedEvent;
	if (!event || !eventRequiresAreaCoordinates(event)) return;
	const stepId = ctx?.stepId;
	const trainingUuid = ctx?.trainingUuid;
	if (!trainingUuid || !stepId) return;
	if (nodes.value.length < 2) return;
	const step = store.steps?.find((s) => s.id === stepId);
	if (!step) return;
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
		const baseArea = ctx?.area ?? step.area;
		const seq = getExplicitActions(step);
		let body;
		if (seq?.length) {
			const idx = Math.min(
				Math.max(0, store.stepActionEditIndex ?? 0),
				seq.length - 1
			);
			const actions = seq.map((x) => ({ ...x }));
			const prev = actions[idx] || {};
			actions[idx] = {
				...prev,
				action_type_id: event.id,
				...updatedArea,
			};
			const newArea = buildAreaWithActions(actions, baseArea);
			body = {
				action_type_id: actions[0].action_type_id,
				area: newArea,
			};
		} else {
			body = {
				action_type_id: event.id,
				area: sanitizeAreaForActionType(baseArea, event.id, updatedArea),
			};
		}
		await trainingStepApi.editStep(trainingUuid, stepId, body);
		patchStepInStore(store.steps, stepId, body);
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
	const seq = getExplicitActions(step);
	if (seq?.length) {
		const idx = Math.min(
			Math.max(0, store.stepActionEditIndex ?? 0),
			seq.length - 1
		);
		const entry = seq[idx];
		const ev =
			store.selectedEvent ??
			findToolbarEventById(entry.action_type_id);
		const w = Number(entry.width) || 0;
		const h = Number(entry.height) || 0;
		const x = Number(entry.x) || 0;
		const y = Number(entry.y) || 0;
		if (eventRequiresAreaOpt(ev) && w > 0 && h > 0) {
			createNode(ev, w, h, x, y);
		} else {
			createNode(ev);
		}
		return;
	}

	let ev = store.selectedEvent;
	if (!ev || !eventRequiresAreaOpt(ev)) return;
	const a = normalizeAreaForCanvas(step.area, step.photo_dimensions);
	const areaMatchesEvent = step.action_type?.id === ev.id;
	if (areaMatchesEvent && a?.width > 0 && a?.height > 0) {
		createNode(ev, a.width, a.height, a.x ?? 0, a.y ?? 0);
	} else if (!areaMatchesEvent && a?.width > 0 && a?.height > 0 && !step.action_type) {
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


/**
 * При смене шага, картинки, подшага или цепочки — выставить тулбар из данных шага.
 * Не вызывается при смене только selectedEvent (клик по иконке), чтобы не откатывать выбор пользователя.
 */
watch(
	() => [
		store.selectedStep?.id,
		store.selectedStep?.image_url,
		store.stepActionEditIndex,
		store.selectedStep?.area?.actions,
	],
	() => {
		const st = store.selectedStep;
		if (!st) {
			store.selectEvent(null);
			return;
		}
		const seq = getExplicitActions(st);
		if (seq?.length) {
			const idx = Math.min(
				Math.max(0, store.stepActionEditIndex ?? 0),
				seq.length - 1
			);
			const entry = seq[idx];
			store.selectEvent({ ...findToolbarEventById(entry.action_type_id) });
			return;
		}
		if (st.action_type) {
			store.selectEvent({ ...st.action_type });
		} else {
			store.selectEvent(null);
		}
	},
	{ flush: "pre", immediate: true },
);

watch(
	() => [
		store.selectedStep?.id,
		store.selectedStep?.image_url,
		store.selectedEvent?.id,
		store.stepActionEditIndex,
		store.selectedStep?.area?.actions,
	],
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
