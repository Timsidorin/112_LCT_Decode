<template>
	<q-dialog
		:model-value="modelValue"
		maximized
		transition-show="fade"
		transition-hide="fade"
		@update:model-value="emit('update:modelValue', $event)"
	>
		<q-card class="editor-passage-preview column">
			<q-card-section class="editor-passage-preview__header row items-center">
				<div>
					<div class="text-h6">Превью прохождения</div>
					<div class="text-caption text-grey-7">
						Пробел — открыть/закрыть · ← → — шаги · Esc — закрыть
					</div>
				</div>
				<q-space />
				<q-toggle
					v-model="showHints"
					dense
					color="amber-8"
					label="Показать подсказки (области)"
					class="q-mr-md"
				/>
				<q-btn flat round dense icon="close" v-close-popup />
			</q-card-section>

			<q-separator />

			<div class="editor-passage-preview__body row no-wrap">
				<div class="editor-passage-preview__canvas col">
					<PassageFlowComponent
						v-if="selectedStep"
						:selected-step="selectedStep"
						mode="passage"
						:show-hint-highlight="showHints"
					/>
				</div>
				<aside class="editor-passage-preview__aside">
					<PassageTaskPanel :selected-step="selectedStep" />
				</aside>
			</div>

			<div class="editor-passage-preview__footer row items-center justify-center q-gutter-sm">
				<q-btn
					flat
					round
					icon="chevron_left"
					color="primary"
					:disable="!hasPrevious"
					@click="store.goToPreviousStep()"
				/>
				<span class="text-body2 text-grey-8">
					Шаг {{ selectedStep?.step_number ?? "—" }} / {{ stepsCount }}
				</span>
				<q-btn
					flat
					round
					icon="chevron_right"
					color="primary"
					:disable="!hasNext"
					@click="store.goToNextStep()"
				/>
			</div>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useTrainingData } from "@store/editTraining.js";
import { PassageFlowComponent } from "@components/features/passage_page";
import PassageTaskPanel from "@components/features/passage_page/PassageTaskPanel.vue";

defineProps({
	modelValue: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue"]);

const store = useTrainingData();
const { selectedStep, steps } = storeToRefs(store);
const showHints = ref(false);

const stepsList = computed(() => store.sortedSteps());
const stepsCount = computed(() => stepsList.value.length);

const currentIndex = computed(() => {
	if (!selectedStep.value) return -1;
	return stepsList.value.findIndex((s) => s.id === selectedStep.value.id);
});

const hasPrevious = computed(() => currentIndex.value > 0);
const hasNext = computed(
	() => currentIndex.value >= 0 && currentIndex.value < stepsList.value.length - 1,
);

watch(
	() => selectedStep.value?.id,
	() => {
		showHints.value = false;
	},
);
</script>

<style scoped>
.editor-passage-preview {
	width: 100%;
	height: 100%;
	background: #f8fafc;
}

.editor-passage-preview__header {
	flex-shrink: 0;
	padding: 12px 16px;
	background: rgba(255, 255, 255, 0.94);
}

.editor-passage-preview__body {
	flex: 1;
	min-height: 0;
	overflow: hidden;
}

.editor-passage-preview__canvas {
	min-width: 0;
	min-height: 0;
	display: flex;
	flex-direction: column;
}

.editor-passage-preview__aside {
	width: min(380px, 34vw);
	flex-shrink: 0;
	padding: 12px;
	border-left: 1px solid rgba(15, 23, 42, 0.08);
	overflow: auto;
}

.editor-passage-preview__footer {
	flex-shrink: 0;
	padding: 10px;
	background: rgba(255, 255, 255, 0.94);
	border-top: 1px solid rgba(15, 23, 42, 0.08);
}

@media (max-width: 900px) {
	.editor-passage-preview__body {
		flex-direction: column;
	}

	.editor-passage-preview__aside {
		width: 100%;
		max-height: 38vh;
		border-left: none;
		border-top: 1px solid rgba(15, 23, 42, 0.08);
	}
}
</style>
