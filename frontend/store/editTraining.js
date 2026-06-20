import { defineStore } from "pinia";
import { ref } from "vue";
import { createComparator } from "@utils/mixed.js";
import { cloneJson } from "@utils/stepActionSequence.js";

export const useTrainingData = defineStore("training", () => {
	const trainingData = ref(null);
	const steps = ref(null);
	const selectedStep = ref(null);
	const selectedEvent = ref(null);
	/** Индекс редактируемого поддействия (area.actions[i]) */
	const stepActionEditIndex = ref(0);
	const previewOpen = ref(false);

	const selectEvent = (val) => {
		selectedEvent.value = val;
	};

	function setTrainingData(newTrainingData, options = {}) {
		const data = cloneJson(newTrainingData);
		trainingData.value = data;
		const sorted = [...(data.steps || [])].sort(createComparator("step_number"));
		steps.value = sorted;
		const preserveId = options.preserveStepId ?? null;
		if (preserveId) {
			const found = sorted.find((s) => s.id === preserveId);
			if (found) {
				selectStep(found);
				return;
			}
		}
		if (sorted.length > 0) {
			selectStep(sorted[0]);
		} else {
			selectedStep.value = null;
		}
	}

	function setSteps(newSteps) {
		steps.value = newSteps;
		if (steps.value.length > 0) {
			selectStep(steps.value[0]);
		}
	}

	function addStep(newStep) {
		steps.value.push(newStep);
	}

	function selectStep(newStep) {
		selectedStep.value = newStep;
		stepActionEditIndex.value = 0;
	}

	function sortedSteps() {
		return [...(steps.value || [])].sort(createComparator("step_number"));
	}

	function goToAdjacentStep(delta) {
		const list = sortedSteps();
		if (!list.length || !selectedStep.value) return false;
		const idx = list.findIndex((s) => s.id === selectedStep.value.id);
		if (idx < 0) return false;
		const nextIdx = idx + delta;
		if (nextIdx < 0 || nextIdx >= list.length) return false;
		selectStep(list[nextIdx]);
		return true;
	}

	function goToPreviousStep() {
		return goToAdjacentStep(-1);
	}

	function goToNextStep() {
		return goToAdjacentStep(1);
	}

	return {
		trainingData,
		setTrainingData,
		setSteps,
		steps,
		addStep,
		selectStep,
		selectedStep,
		selectEvent,
		selectedEvent,
		stepActionEditIndex,
		previewOpen,
		sortedSteps,
		goToPreviousStep,
		goToNextStep,
	};
});
