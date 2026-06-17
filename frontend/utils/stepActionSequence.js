/**
 * Несколько действий на одном скриншоте: area.actions[]
 * Совместимо с «плоским» area + step.action_type (одно действие).
 */

import { isInputTextType, isKeyPressType } from "./actionTypes.js";

export const KNOWN_ACTION_EVENTS = [
	{ id: 1, type: "leftClick", name: "Левый клик" },
	{ id: 2, type: "rightClick", name: "Правый клик" },
	{ id: 3, type: "doubleClick", name: "Двойной клик" },
	{ id: 4, type: "hover", name: "Наведение курсора" },
	{ id: 5, type: "inputText", name: "Ввод текста" },
	{ id: 6, type: "keyPress", name: "Нажатие клавиши" },
];

export function findToolbarEventById(id) {
	return KNOWN_ACTION_EVENTS.find((e) => e.id === id) || KNOWN_ACTION_EVENTS[0];
}

function _hasRect(a) {
	return !!(a && Number(a.width) > 0 && Number(a.height) > 0);
}

function _pickMetaFromArea(a) {
	if (!a || typeof a !== "object") return {};
	const keys = [
		"metaText",
		"metaKeywords",
		"metaFontSize",
		"metaTextScale",
		"metaMatchMode",
		"metaPattern",
		"metaPatternPreset",
	];
	const o = {};
	for (const k of keys) if (k in a && a[k] != null) o[k] = a[k];
	return o;
}

/**
 * Явная цепочка из area.actions (несколько действий на одном скрине).
 * Без поля actions — null (обычный одиночный шаг).
 */
export function getExplicitActions(step) {
	if (!step) return null;
	const raw = step.area?.actions;
	if (!Array.isArray(raw) || raw.length === 0) return null;
	return raw.filter((x) => x && typeof x.action_type_id === "number");
}

export function isMultiActionStep(step) {
	const s = getExplicitActions(step);
	return !!(s && s.length > 1);
}

/** Плоские координаты + мета текущего поддействия для оверлея */
export function areaViewFromEntry(entry) {
	if (!entry) return null;
	const { action_type_id: _a, ...rest } = entry;
	return rest;
}

/** Сохранить цепочку: зеркалируем первое действие в корень area для совместимости */
export function buildAreaWithActions(actions, baseArea = {}) {
	const first = actions[0] || {};
	const rect = {
		x: Number(first.x) || 0,
		y: Number(first.y) || 0,
		width: Number(first.width) || 0,
		height: Number(first.height) || 0,
	};
	const meta = _pickMetaFromArea(first);
	return {
		...rect,
		...meta,
		actions: actions.map((x) => ({ ...x })),
	};
}

const TEXT_META_KEYS = [
	"metaText",
	"metaFontSize",
	"metaMatchMode",
	"metaPattern",
	"metaPatternPreset",
	"metaTextScale",
];

/** Клонирует JSON-совместимые данные (area, шаг). */
export function cloneJson(value) {
	if (value == null) return value;
	return JSON.parse(JSON.stringify(value));
}

/**
 * Оставляет в area только поля, релевантные типу действия.
 * Иначе metaText от «ввода текста» остаётся на шагах-кликах и ломает прохождение.
 */
export function sanitizeAreaForActionType(area, actionTypeId, rectOverride = {}) {
	const source = { ...(area || {}), ...rectOverride };
	const event = findToolbarEventById(actionTypeId);
	const out = {};
	for (const k of ["x", "y", "width", "height"]) {
		if (source[k] != null) out[k] = source[k];
	}
	if (Array.isArray(source.actions) && source.actions.length) {
		out.actions = cloneJson(source.actions);
	}
	if (isInputTextType(event)) {
		for (const k of TEXT_META_KEYS) {
			if (source[k] != null) out[k] = source[k];
		}
	} else if (isKeyPressType(event)) {
		if (Array.isArray(source.metaKeywords)) {
			out.metaKeywords = [...source.metaKeywords];
		}
	}
	return out;
}

/** Обновляет шаг в store по id (не зависит от текущего selectedStep). */
export function patchStepInStore(steps, stepId, { action_type_id, area }) {
	const step = steps?.find((s) => s.id === stepId);
	if (!step) return;
	if (area !== undefined) {
		step.area = cloneJson(area);
	}
	if (action_type_id != null) {
		step.action_type_id = action_type_id;
		step.action_type = { ...findToolbarEventById(action_type_id) };
	}
}
