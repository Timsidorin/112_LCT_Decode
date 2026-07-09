<template>
	<div class="map-node map-node--source">
		<Handle type="source" :position="Position.Right" />
		<q-icon name="table_chart" size="16px" class="map-node__icon" />
		<span class="map-node__label">{{ data.label }}</span>
	</div>
</template>

<script setup>
import { Handle, Position } from "@vue-flow/core";

defineProps({
	data: { type: Object, default: () => ({}) },
});
</script>

<style scoped>
.map-node {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 10px 14px;
	min-width: 140px;
	background: rgba(255, 255, 255, 0.95);
	border: 1px solid rgba(0, 0, 0, 0.08);
	border-radius: 12px;
	box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
	font-size: 13px;
	font-weight: 600;
	color: #334155;
}

.map-node--source {
	border-left: 3px solid #217346;
}

.map-node__icon {
	color: #217346;
}
</style>
