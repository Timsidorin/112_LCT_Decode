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

	const selectEvent = (val) => {
		selectedEvent.value = val;
	};

	function setTrainingData(newTrainingData) {
		const data = cloneJson(newTrainingData);
		trainingData.value = data;
		setSteps([...(data.steps || [])].sort(createComparator("step_number")));
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
	};
});
