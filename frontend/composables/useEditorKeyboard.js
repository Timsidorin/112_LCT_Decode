import { onMounted, onUnmounted } from "vue";

function isEditableTarget(target) {
	if (!target || typeof target !== "object") return false;
	const el = target;
	const tag = el.tagName?.toUpperCase?.() ?? "";
	if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
	if (el.isContentEditable) return true;
	return !!el.closest?.(
		".ProseMirror, .q-dialog, .q-menu, .q-select__dialog, [contenteditable='true']",
	);
}

/**
 * Горячие клавиши редактора тренинга.
 */
export function useEditorKeyboard(handlers = {}) {
	function onKeydown(event) {
		if (isEditableTarget(event.target)) return;

		const key = event.key;
		const ctrl = event.ctrlKey || event.metaKey;

		if (ctrl && key.toLowerCase() === "s") {
			event.preventDefault();
			handlers.onForceSave?.();
			return;
		}

		if (ctrl && key.toLowerCase() === "d") {
			event.preventDefault();
			handlers.onDuplicateStep?.();
			return;
		}

		if (key === "Escape") {
			handlers.onEscape?.();
			return;
		}

		if (key === " " && !ctrl && !event.altKey) {
			event.preventDefault();
			handlers.onTogglePreview?.();
			return;
		}

		if (key === "ArrowLeft" && !ctrl) {
			event.preventDefault();
			handlers.onPreviousStep?.();
			return;
		}

		if (key === "ArrowRight" && !ctrl) {
			event.preventDefault();
			handlers.onNextStep?.();
			return;
		}

		if (/^[1-6]$/.test(key) && !ctrl && !event.altKey) {
			event.preventDefault();
			handlers.onSelectAction?.(Number(key));
			return;
		}

		if ((key === "Delete" || key === "Backspace") && !ctrl) {
			event.preventDefault();
			handlers.onClearArea?.();
		}
	}

	onMounted(() => {
		window.addEventListener("keydown", onKeydown, { capture: true });
	});

	onUnmounted(() => {
		window.removeEventListener("keydown", onKeydown, { capture: true });
	});
}
