import {
	eventRequiresAreaCoordinates,
	isInputTextType,
	isKeyPressType,
} from "./actionTypes.js";
import { findToolbarEventById, getExplicitActions } from "./stepActionSequence.js";

function hasValidRect(area) {
	return !!(area && Number(area.width) > 0 && Number(area.height) > 0);
}

/**
 * Список проблем с шагом для индикатора готовности.
 */
export function getStepIssues(step) {
	if (!step) return [];

	const issues = [];
	const annotation = (step.annotation ?? "").trim();

	if (!step.image_url) {
		issues.push({ type: "no_image", message: "Нет скриншота" });
	}
	if (!annotation) {
		issues.push({ type: "empty_task", message: "Нет задания" });
	}

	const actions = getExplicitActions(step);
	const actionTypeId =
		actions?.[0]?.action_type_id ??
		step.action_type_id ??
		step.action_type?.id ??
		null;

	if (!actionTypeId) {
		issues.push({ type: "no_action", message: "Не выбран тип действия" });
		return issues;
	}

	const event = findToolbarEventById(actionTypeId);

	if (isKeyPressType(event)) {
		const keywords =
			actions?.[0]?.metaKeywords ?? step.area?.metaKeywords ?? [];
		if (!Array.isArray(keywords) || keywords.length === 0) {
			issues.push({ type: "no_hotkey", message: "Не назначена клавиша" });
		}
		return issues;
	}

	if (eventRequiresAreaCoordinates(event)) {
		if (actions?.length) {
			actions.forEach((entry, index) => {
				if (!hasValidRect(entry)) {
					issues.push({
						type: "no_area",
						message:
							actions.length > 1
								? `Подшаг ${index + 1}: нет области`
								: "Не выделена область",
					});
				}
			});
		} else if (!hasValidRect(step.area)) {
			issues.push({ type: "no_area", message: "Не выделена область" });
		}
	}

	if (isInputTextType(event)) {
		const text = actions?.[0]?.metaText ?? step.area?.metaText ?? "";
		if (!String(text).trim()) {
			issues.push({
				type: "no_expected_text",
				message: "Не задан ожидаемый текст",
				severity: "info",
			});
		}
	}

	return issues;
}

/** ready | warning | incomplete */
export function getStepReadiness(step) {
	const issues = getStepIssues(step);
	if (!issues.length) return "ready";
	if (issues.some((i) => i.type === "no_image" || i.type === "empty_task")) {
		return "incomplete";
	}
	return "warning";
}

export function readinessLabel(readiness) {
	switch (readiness) {
		case "ready":
			return "Готов";
		case "warning":
			return "Нужна проверка";
		default:
			return "Не готов";
	}
}

export function readinessColor(readiness) {
	switch (readiness) {
		case "ready":
			return "positive";
		case "warning":
			return "warning";
		default:
			return "negative";
	}
}
