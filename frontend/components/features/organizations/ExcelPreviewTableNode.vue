<template>
	<div class="excel-columns-node">
		<div class="excel-columns-node__head">
			<q-icon name="view_column" size="18px" color="positive" />
			<span>Колонки из файла</span>
			<q-badge color="grey-4" text-color="grey-9">{{ data.columns?.length || 0 }}</q-badge>
		</div>
		<ul class="excel-columns-node__list">
			<li
				v-for="(col, index) in data.columns"
				:key="`${col}-${index}`"
				class="excel-columns-node__item"
				:class="{ 'excel-columns-node__item--mapped': isMapped(col) }"
			>
				<Handle
					:id="`col-${index}`"
					type="source"
					:position="Position.Right"
					class="excel-columns-node__handle"
				/>
				<q-icon name="table_chart" size="16px" class="excel-columns-node__icon" />
				<span class="excel-columns-node__label">{{ col }}</span>
			</li>
		</ul>
		<div class="excel-columns-node__hint">
			Потяните связь от колонки → к полю справа
		</div>
	</div>
</template>

<script setup>
import { Handle, Position } from "@vue-flow/core";

const props = defineProps({
	data: { type: Object, default: () => ({}) },
});

function isMapped(col) {
	return Object.values(props.data.mapping || {}).includes(col)
		|| (props.data.mapping?.full_name_parts || []).includes(col);
}
</script>

<style scoped>
.excel-columns-node {
	min-width: 240px;
	max-width: 320px;
	background: #fff;
	border: 1px solid rgba(33, 115, 70, 0.25);
	border-radius: 14px;
	box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
	overflow: hidden;
}

.excel-columns-node__head {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 12px 14px;
	background: rgba(33, 115, 70, 0.08);
	font-size: 13px;
	font-weight: 700;
	color: #166534;
	border-bottom: 1px solid rgba(33, 115, 70, 0.15);
}

.excel-columns-node__list {
	list-style: none;
	margin: 0;
	padding: 8px;
	max-height: 360px;
	overflow-y: auto;
}

.excel-columns-node__item {
	position: relative;
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 10px 28px 10px 12px;
	margin-bottom: 4px;
	border-radius: 10px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	font-size: 13px;
	font-weight: 600;
	color: #334155;
	transition: background 0.15s ease, border-color 0.15s ease;
}

.excel-columns-node__item:last-child {
	margin-bottom: 0;
}

.excel-columns-node__item--mapped {
	background: rgba(80, 100, 247, 0.1);
	border-color: rgba(80, 100, 247, 0.35);
	color: #3730a3;
}

.excel-columns-node__icon {
	flex-shrink: 0;
	color: #217346;
}

.excel-columns-node__item--mapped .excel-columns-node__icon {
	color: #5064f7;
}

.excel-columns-node__label {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.excel-columns-node__handle {
	right: -6px !important;
	top: 50% !important;
	transform: translateY(-50%);
	width: 12px !important;
	height: 12px !important;
	background: #217346 !important;
	border: 2px solid #fff !important;
	box-shadow: 0 2px 6px rgba(33, 115, 70, 0.4);
}

.excel-columns-node__item--mapped .excel-columns-node__handle {
	background: #5064f7 !important;
	box-shadow: 0 2px 6px rgba(80, 100, 247, 0.4);
}

.excel-columns-node__hint {
	padding: 8px 12px;
	font-size: 11px;
	color: #64748b;
	background: #fafafa;
	border-top: 1px solid #f1f5f9;
}
</style>
