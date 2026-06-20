import { computed, ref } from "vue";

const status = ref("saved");
const lastError = ref(null);

export function useEditorSaveStatus() {
	const label = computed(() => {
		switch (status.value) {
			case "saving":
				return "Сохраняем…";
			case "dirty":
				return "Есть изменения";
			case "error":
				return "Ошибка сохранения";
			default:
				return "Сохранено";
		}
	});

	const icon = computed(() => {
		switch (status.value) {
			case "saving":
				return "sync";
			case "dirty":
				return "edit_note";
			case "error":
				return "error_outline";
			default:
				return "cloud_done";
		}
	});

	const color = computed(() => {
		switch (status.value) {
			case "saving":
				return "primary";
			case "dirty":
				return "grey-7";
			case "error":
				return "negative";
			default:
				return "positive";
		}
	});

	const isDirty = computed(
		() => status.value === "dirty" || status.value === "saving",
	);

	function markDirty() {
		if (status.value !== "saving") status.value = "dirty";
	}

	function markSaving() {
		status.value = "saving";
		lastError.value = null;
	}

	function markSaved() {
		status.value = "saved";
		lastError.value = null;
	}

	function markError(message) {
		status.value = "error";
		lastError.value = message || null;
	}

	return {
		status,
		label,
		icon,
		color,
		isDirty,
		lastError,
		markDirty,
		markSaving,
		markSaved,
		markError,
	};
}
