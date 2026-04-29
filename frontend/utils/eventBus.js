import { createEventHook } from '@vueuse/core';

export const trainingEvents = {
	created: createEventHook(),
	improveText: createEventHook(),
	generateTTS: createEventHook(),
};