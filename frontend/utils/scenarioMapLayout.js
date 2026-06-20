import { MarkerType } from "@vue-flow/core";

export const SCENARIO_NODE_WIDTH = 200;
export const SCENARIO_NODE_HEIGHT = 168;
export const SCENARIO_NODE_GAP = 72;
export const SCENARIO_ROW_Y = 40;

/**
 * Сортирует шаги по step_number.
 */
export function sortStepsByNumber(steps) {
	return [...(steps || [])].sort(
		(a, b) => (a.step_number ?? 0) - (b.step_number ?? 0),
	);
}

/**
 * Строит nodes/edges для линейной карты сценария.
 */
export function buildScenarioGraph(steps, callbacks = {}) {
	const sorted = sortStepsByNumber(steps);
	const { onDelete, onSelect, selectedStepId } = callbacks;

	const nodes = sorted.map((step, index) => ({
		id: `step-${step.id}`,
		type: "step",
		position: {
			x: index * (SCENARIO_NODE_WIDTH + SCENARIO_NODE_GAP),
			y: SCENARIO_ROW_Y,
		},
		draggable: true,
		selectable: true,
		data: {
			step,
			selected: step.id === selectedStepId,
			onDelete,
			onSelect,
		},
	}));

	const edges = sorted.slice(0, -1).map((step, index) => {
		const next = sorted[index + 1];
		return {
			id: `edge-${step.id}-${next.id}`,
			source: `step-${step.id}`,
			target: `step-${next.id}`,
			type: "add",
			animated: true,
			markerEnd: MarkerType.ArrowClosed,
			data: {
				afterStepId: step.id,
				onAdd: callbacks.onAdd,
			},
		};
	});

	return { nodes, edges };
}

/**
 * Вычисляет новый порядок шагов по горизонтальной позиции узлов.
 */
export function computeOrderFromNodes(nodes) {
	return nodes
		.filter((n) => n.type === "step")
		.sort((a, b) => a.position.x - b.position.x)
		.map((n, index) => ({
			id: Number(String(n.id).replace(/^step-/, "")),
			step_number: index + 1,
		}));
}

/**
 * Раскладывает узлы по сетке после изменения порядка.
 */
export function layoutNodesInOrder(nodes) {
	const stepNodes = nodes
		.filter((n) => n.type === "step")
		.sort((a, b) => a.position.x - b.position.x);

	return nodes.map((node) => {
		if (node.type !== "step") return node;
		const orderIndex = stepNodes.findIndex((n) => n.id === node.id);
		return {
			...node,
			position: {
				x: orderIndex * (SCENARIO_NODE_WIDTH + SCENARIO_NODE_GAP),
				y: SCENARIO_ROW_Y,
			},
		};
	});
}

/**
 * Вставляет новые шаги после указанного id и возвращает payload для reorder API.
 */
export function buildOrderWithInsert(currentSteps, newSteps, afterStepId) {
	const sorted = sortStepsByNumber(currentSteps);
	const result = [];

	for (const step of sorted) {
		result.push(step);
		if (step.id === afterStepId) {
			for (const added of newSteps) result.push(added);
		}
	}

	return result.map((step, index) => ({
		id: step.id,
		step_number: index + 1,
	}));
}

/**
 * Вставляет новые шаги в начало сценария.
 */
export function buildOrderWithInsertAtStart(currentSteps, newSteps) {
	const sorted = sortStepsByNumber(currentSteps);
	const result = [...newSteps, ...sorted];
	return result.map((step, index) => ({
		id: step.id,
		step_number: index + 1,
	}));
}

export function stepLabel(step) {
	const name = (step?.meta?.name ?? "").trim();
	if (name && name !== "Шаг без названия") return name;
	return `Шаг ${step?.step_number ?? ""}`.trim();
}

export function stepActionLabel(step) {
	if (step?.action_type?.name) return step.action_type.name;
	const actions = step?.area?.actions;
	if (Array.isArray(actions) && actions.length > 0) {
		const id = actions[0]?.action_type_id;
		if (id === 5) return "Ввод текста";
		if (id === 6) return "Нажатие клавиши";
		if (id === 1) return "Левый клик";
	}
	return "Не задано";
}
