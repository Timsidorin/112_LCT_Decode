import { createEventHook } from '@vueuse/core';

export const trainingEvents = {
	created: createEventHook(),
	improveText: createEventHook(),
	generateTTS: createEventHook(),
	forceSave: createEventHook(),
	selectActionById: createEventHook(),
	clearCurrentArea: createEventHook(),
	togglePreview: createEventHook(),
	duplicateStep: createEventHook(),
};