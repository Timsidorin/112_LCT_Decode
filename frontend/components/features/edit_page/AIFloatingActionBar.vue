<template>
	<transition name="pill-fade">
		<div
			v-if="visible"
			class="ai-floating-bar glass-panel-dark"
			:style="positionStyle"
		>
			<div class="ai-floating-bar__content">
				<q-icon name="auto_awesome" size="14px" class="ai-floating-bar__magic" />
				<span class="ai-floating-bar__label">AI Помощник</span>
				
				<div class="ai-floating-bar__divider" />
				
				<q-btn
					flat
					dense
					round
					size="sm"
					icon="edit_note"
					color="white"
					@click="$emit('improve')"
				>
					<q-tooltip>Улучшить описание</q-tooltip>
				</q-btn>
				
				<q-btn
					flat
					dense
					round
					size="sm"
					icon="record_voice_over"
					color="white"
					@click="$emit('tts')"
				>
					<q-tooltip>Озвучить</q-tooltip>
				</q-btn>
				
				<q-btn
					flat
					dense
					round
					size="sm"
					icon="delete"
					color="red-4"
					class="q-ml-xs"
					@click="$emit('delete')"
				>
					<q-tooltip>Удалить область</q-tooltip>
				</q-btn>
			</div>
		</div>
	</transition>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	visible: Boolean,
	x: Number,
	y: Number,
});

defineEmits(["improve", "tts", "delete"]);

const positionStyle = computed(() => {
	return {
		left: `${props.x}px`,
		top: `${props.y - 12}px`, // Панель будет "центрована" по X, и чуть выше по Y
		transform: 'translate(-50%, -100%)', // Центрируем по горизонтали относительно X
	};
});
</script>

<style scoped>
.ai-floating-bar {
	position: absolute;
	z-index: 1000;
	padding: 6px 14px;
	border-radius: 100px;
	display: flex;
	align-items: center;
	pointer-events: auto;
	box-shadow: 
		0 20px 25px -5px rgba(0, 0, 0, 0.2), 
		0 10px 10px -5px rgba(0, 0, 0, 0.1),
		0 0 0 1px rgba(168, 85, 247, 0.4);
	animation: ai-bar-pulse 4s infinite;
}

@keyframes ai-bar-pulse {
	0%, 100% { box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(168, 85, 247, 0.4); }
	50% { box-shadow: 0 10px 35px -5px rgba(0, 0, 0, 0.3), 0 0 0 2px rgba(168, 85, 247, 0.6); }
}

.ai-floating-bar__content {
	display: flex;
	align-items: center;
	gap: 6px;
}

.ai-floating-bar__magic {
	color: #a855f7;
	filter: drop-shadow(0 0 4px rgba(168, 85, 247, 0.6));
}

.ai-floating-bar__label {
	font-size: 11px;
	font-weight: 600;
	color: white;
	opacity: 0.9;
	margin-right: 4px;
}

.ai-floating-bar__divider {
	width: 1px;
	height: 16px;
	background: rgba(255, 255, 255, 0.2);
	margin: 0 4px;
}

.pill-fade-enter-active,
.pill-fade-leave-active {
	transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pill-fade-enter-from {
	opacity: 0;
	transform: translateY(10px) scale(0.9);
}

.pill-fade-leave-to {
	opacity: 0;
	transform: translateY(5px) scale(0.95);
}
</style>
