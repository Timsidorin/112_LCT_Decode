<template>
	<div class="schema-table-node">
		<div class="schema-table-node__head">
			<q-icon name="account_tree" size="18px" color="primary" />
			<span>Поля импорта</span>
		</div>
		<table class="schema-table-node__table">
			<tbody>
				<tr
					v-for="field in fields"
					:key="field.fieldKey"
					class="schema-table-node__row"
					:class="{ 'schema-table-node__row--mapped': mappedLabel(field.fieldKey) }"
				>
					<td class="schema-table-node__field">
						<Handle
							:id="field.fieldKey"
							type="target"
							:position="Position.Left"
							class="schema-table-node__handle"
						/>
						<q-icon :name="field.icon" size="16px" class="q-mr-xs" />
						<span>{{ field.label }}</span>
						<span v-if="field.required" class="text-negative q-ml-xs">*</span>
					</td>
					<td class="schema-table-node__mapped">
						{{ mappedLabel(field.fieldKey) || "не сопоставлено" }}
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { Handle, Position } from "@vue-flow/core";

const props = defineProps({
	data: { type: Object, default: () => ({}) },
});

const fields = [
	{ fieldKey: "full_name", label: "ФИО", icon: "person", required: true },
	{ fieldKey: "email", label: "Email", icon: "mail", required: true },
	{ fieldKey: "position", label: "Должность", icon: "work", required: false },
];

function mappedLabel(fieldKey) {
	const mapping = props.data.mapping || {};
	if (fieldKey === "full_name" && mapping.full_name_parts?.length) {
		return mapping.full_name_parts.join(" + ");
	}
	return mapping[fieldKey] || "";
}
</script>

<style scoped>
.schema-table-node {
	min-width: 300px;
	background: #fff;
	border: 1px solid rgba(80, 100, 247, 0.25);
	border-radius: 14px;
	box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
	overflow: hidden;
}

.schema-table-node__head {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 12px 14px;
	background: rgba(80, 100, 247, 0.08);
	font-size: 13px;
	font-weight: 700;
	color: #3730a3;
	border-bottom: 1px solid rgba(80, 100, 247, 0.15);
}

.schema-table-node__table {
	width: 100%;
	border-collapse: collapse;
	font-size: 13px;
}

.schema-table-node__row {
	border-bottom: 1px solid #f1f5f9;
}

.schema-table-node__row--mapped {
	background: rgba(80, 100, 247, 0.04);
}

.schema-table-node__field {
	position: relative;
	padding: 14px 12px 14px 24px;
	font-weight: 600;
	color: #1e293b;
	white-space: nowrap;
}

.schema-table-node__mapped {
	padding: 14px 16px;
	color: #64748b;
	font-size: 12px;
	max-width: 180px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.schema-table-node__row--mapped .schema-table-node__mapped {
	color: #5064f7;
	font-weight: 600;
}

.schema-table-node__handle {
	left: -6px !important;
	top: 50% !important;
	transform: translateY(-50%);
	width: 12px !important;
	height: 12px !important;
	background: #5064f7 !important;
	border: 2px solid #fff !important;
	box-shadow: 0 2px 6px rgba(80, 100, 247, 0.4);
}
</style>
