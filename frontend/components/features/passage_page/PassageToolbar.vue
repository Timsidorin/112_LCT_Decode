<template>
	<div class="passage-toolbar">
		<q-btn
			v-if="hasPreviousStep"
			round
			unelevated
			dense
			icon="chevron_left"
			color="primary"
			class="nav-btn nav-btn--round"
			@click="$emit('prev')"
		>
			<q-tooltip>Предыдущий шаг</q-tooltip>
		</q-btn>

		<!-- Кнопка "Далее" для шагов без действия или при skip_steps -->
		<q-btn
			v-if="showNextButton"
			unelevated
			no-caps
			rounded
			color="primary"
			icon="arrow_forward"
			:label="hasNextStep ? 'Далее' : 'Завершить'"
			class="next-btn"
			@click="$emit('next')"
		/>

		<q-btn
			v-if="hasNextStep && !showNextButton"
			round
			unelevated
			dense
			icon="chevron_right"
			color="primary"
			class="nav-btn nav-btn--round"
			@click="$emit('next')"
		>
			<q-tooltip>Следующий шаг</q-tooltip>
		</q-btn>

	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	hasPreviousStep: { type: Boolean, default: false },
	hasNextStep: { type: Boolean, default: false },
	selectedStep: { type: Object, default: null },
	skipSteps: { type: Boolean, default: false },
	hintsEnabled: { type: Boolean, default: false },
	hintsAvailable: { type: Boolean, default: true },
});

defineEmits(["prev", "next", "toggle-hints"]);

// Показывать кнопку "Далее" если: нет action_type, или skip_steps (свободная навигация)
const showNextButton = computed(() => {
	if (props.skipSteps) return true;
	return !props.selectedStep?.action_type;
});
</script>

<style scoped>
.passage-toolbar {
	position: absolute;
	bottom: 32px;
	left: 50%;
	transform: translateX(-50%);
	z-index: 1000;
	padding: 10px 24px;
	border-radius: 100px;
	background: rgba(255, 255, 255, 0.4);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border: 1px solid rgba(255, 255, 255, 0.5);
	box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
	display: flex;
	align-items: center;
	gap: 16px;
}

.nav-btn--hints {
	box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
}

.passage-toolbar > * {
	pointer-events: auto;
}

.nav-btn--round {
	width: 48px;
	height: 48px;
	box-shadow: 0 8px 16px rgba(80, 100, 247, 0.25);
}

.nav-btn--round :deep(.q-btn__wrapper) {
	padding: 0;
	min-height: 44px;
	min-width: 44px;
}

.next-btn {
	padding: 10px 20px;
	font-weight: 600;
	box-shadow: 0 4px 16px rgba(80, 100, 247, 0.3);
}
</style>
