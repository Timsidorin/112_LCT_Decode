<template>
	<q-chip
		v-if="selectedStep"
		dense
		:color="chipColor"
		text-color="white"
		class="step-readiness-badge"
		clickable
		@click="showDetails = !showDetails"
	>
		<q-icon :name="chipIcon" size="14px" class="q-mr-xs" />
		{{ chipLabel }}
		<q-tooltip v-if="issues.length" anchor="bottom middle" :offset="[0, 8]">
			<div v-for="(issue, i) in issues" :key="i">{{ issue.message }}</div>
		</q-tooltip>
	</q-chip>
</template>

<script setup>
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import { useTrainingData } from "@store/editTraining.js";
import {
	getStepIssues,
	getStepReadiness,
	readinessColor,
	readinessLabel,
} from "@utils/stepValidation.js";

const store = useTrainingData();
const { selectedStep } = storeToRefs(store);
const showDetails = ref(false);

const readiness = computed(() => getStepReadiness(selectedStep.value));
const issues = computed(() => getStepIssues(selectedStep.value));
const chipLabel = computed(() => readinessLabel(readiness.value));
const chipColor = computed(() => readinessColor(readiness.value));
const chipIcon = computed(() => {
	if (readiness.value === "ready") return "check_circle";
	if (readiness.value === "warning") return "warning";
	return "error_outline";
});
</script>

<style scoped>
.step-readiness-badge {
	font-size: 11px;
	font-weight: 600;
	border-radius: 999px;
	box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
}
</style>
