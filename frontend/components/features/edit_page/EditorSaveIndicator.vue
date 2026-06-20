<template>
	<div class="editor-save-indicator" :class="`editor-save-indicator--${status}`">
		<q-icon
			:name="icon"
			size="16px"
			:color="color"
			:class="{ 'editor-save-indicator__spin': status === 'saving' }"
		/>
		<span>{{ label }}</span>
	</div>
</template>

<script setup>
import { useEditorSaveStatus } from "@composables/useEditorSaveStatus.js";

const { status, label, icon, color } = useEditorSaveStatus();
</script>

<style scoped>
.editor-save-indicator {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 10px;
	border-radius: 999px;
	background: rgba(255, 255, 255, 0.92);
	border: 1px solid rgba(15, 23, 42, 0.08);
	font-size: 12px;
	color: #475569;
	box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
}

.editor-save-indicator__spin {
	animation: editor-save-spin 1s linear infinite;
}

@keyframes editor-save-spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}
</style>
