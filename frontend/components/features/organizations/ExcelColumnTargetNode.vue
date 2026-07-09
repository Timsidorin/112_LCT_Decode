<template>
	<div class="map-node map-node--target" :class="{ 'map-node--mapped': data.mapped }">
		<Handle type="target" :position="Position.Left" />
		<q-icon :name="data.icon" size="16px" class="map-node__icon" />
		<div class="map-node__body">
			<span class="map-node__label">{{ data.label }}</span>
			<span v-if="data.mappedFrom" class="map-node__hint">{{ data.mappedFrom }}</span>
		</div>
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
	min-width: 160px;
	background: rgba(255, 255, 255, 0.95);
	border: 1px solid rgba(0, 0, 0, 0.08);
	border-radius: 12px;
	box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
	font-size: 13px;
	font-weight: 600;
	color: #334155;
}

.map-node--target {
	border-left: 3px solid #5064f7;
}

.map-node--mapped {
	border-color: rgba(80, 100, 247, 0.35);
	background: rgba(80, 100, 247, 0.04);
}

.map-node__icon {
	color: #5064f7;
}

.map-node__body {
	display: flex;
	flex-direction: column;
	min-width: 0;
}

.map-node__hint {
	font-size: 11px;
	font-weight: 500;
	color: #64748b;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	max-width: 120px;
}
</style>
