<template>
	<q-dialog
		:model-value="modelValue"
		persistent
		no-backdrop-dismiss
		class="employee-import-dialog"
		transition-show="scale"
		transition-hide="scale"
		@update:model-value="emit('update:modelValue', $event)"
	>
		<q-card class="employee-wizard">
			<q-card-section class="employee-wizard__header row items-center">
				<div>
					<div class="text-h6 text-weight-bold">Сотрудники организации</div>
					<div class="text-body2 text-grey-7 q-mt-xs">
						{{ trainingTitle || "Импорт из Excel и выдача доступа" }}
					</div>
				</div>
				<q-space />
				<q-btn
					flat
					round
					dense
					icon="close"
					class="wizard-btn wizard-btn--icon"
					v-close-popup
				/>
			</q-card-section>

			<q-separator />

			<q-card-section class="employee-wizard__body">
				<q-stepper
					v-model="step"
					flat
					:animated="false"
					color="primary"
					class="employee-wizard__stepper"
					header-nav
				>
					<q-step :name="1" title="Импорт" icon="upload_file" :done="step > 1">
						<div class="step-body step-body--import column items-center">
							<p class="text-body1 text-grey-7 text-center q-mb-lg">
								Загрузите Excel-файл со списком сотрудников
							</p>
							<label
								v-if="!isDesktopShell"
								class="excel-dropzone cursor-pointer"
							>
								<input
									ref="fileInput"
									type="file"
									accept=".xlsx,.xls,.csv"
									class="hidden"
									@change="onFileSelected"
								/>
								<div class="excel-dropzone__icon">
									<svg viewBox="0 0 48 48" width="56" height="56" aria-hidden="true">
										<rect x="4" y="4" width="40" height="40" rx="6" fill="#217346" />
										<path d="M14 32V16h12l8 8v8H14z" fill="#fff" opacity="0.9" />
										<text x="24" y="28" text-anchor="middle" fill="#217346" font-size="11" font-weight="700">X</text>
									</svg>
								</div>
								<div class="text-h6 text-weight-bold q-mt-md">Импорт из Excel</div>
								<div class="text-body2 text-grey-6 q-mt-xs">Первая строка с заголовками · .xlsx, .xls, .csv</div>
							</label>
							<div v-else class="column items-center">
								<q-btn
									unelevated
									no-caps
									rounded
									color="primary"
									icon="upload_file"
									label="Выбрать файл Excel"
									class="wizard-btn wizard-btn--primary"
									@click="pickExcelNative"
								/>
								<div class="text-body2 text-grey-6 q-mt-sm">Файл остаётся на вашем компьютере</div>
							</div>
							<q-btn
								outline
								no-caps
								rounded
								color="primary"
								icon="edit_note"
								label="Добавить сотрудников вручную"
								class="wizard-btn wizard-btn--outline q-mt-xl"
								@click="goToReview"
							/>
						</div>
					</q-step>

					<q-step :name="2" title="Сопоставление" icon="account_tree" :done="step > 2">
						<div class="step-body step-body--map column">
							<div v-if="excelColumns.length" class="map-layout">
								<div class="map-wrap">
									<ExcelColumnMappingCanvas
										v-if="mapReady"
										:key="mapFlowKey"
										ref="mapCanvasRef"
										:flow-id="mapFlowKey"
										:columns="excelColumns"
										:mapping="fieldMapping"
										@update:mapping="fieldMapping = $event"
									/>
									<div v-else class="map-wrap__loading column flex-center">
										<q-spinner-dots size="40px" color="primary" />
									</div>
								</div>

								<aside class="map-sidebar">
									<div class="map-sidebar__title">Сопоставление полей</div>
									<div
										v-for="field in mappingFields"
										:key="field.fieldKey"
										class="map-sidebar__field q-mb-md"
									>
										<div class="map-sidebar__label">
											<q-icon :name="field.icon" size="18px" class="q-mr-xs" />
											{{ field.label }}
											<span v-if="field.required" class="text-negative">*</span>
										</div>
										<q-select
											:model-value="selectValue(field.fieldKey)"
											:options="columnOptions"
											outlined
											dense
											clearable
											emit-value
											map-options
											placeholder="Выберите колонку"
											class="map-sidebar__select"
											@update:model-value="setMappingField(field.fieldKey, $event)"
										/>
									</div>
								</aside>
							</div>

							<div v-else class="map-empty column items-center q-pa-xl">
								<q-icon name="warning" size="48px" color="warning" />
								<p class="text-body1 text-grey-7 q-mt-md text-center">
									Не удалось определить колонки. Проверьте, что в файле есть строка с заголовками.
								</p>
							</div>
						</div>
					</q-step>

					<q-step :name="3" title="Список" icon="groups" :done="step > 3">
						<div class="step-body column">
							<div class="step-toolbar row items-center justify-between q-mb-md">
								<p class="step-toolbar__hint text-body2 text-grey-7 q-ma-none">
									{{ localEmployees.length ? `В списке: ${localEmployees.length}` : "Список пуст" }}
								</p>
								<q-btn
									unelevated
									no-caps
									rounded
									color="primary"
									icon="person_add"
									label="Добавить вручную"
									class="wizard-btn wizard-btn--primary"
									@click="manualDialog = true"
								/>
							</div>

							<div v-if="localEmployees.length" class="employee-table-wrap">
								<q-markup-table flat bordered class="employee-table">
									<thead>
										<tr>
											<th>ФИО</th>
											<th>Email</th>
											<th class="employee-table__position-col">Должность</th>
											<th class="employee-table__actions-col"></th>
										</tr>
									</thead>
									<tbody>
										<tr v-for="(emp, idx) in localEmployees" :key="`${emp.email}-${idx}`">
											<td class="employee-table__cell employee-table__cell--name">{{ emp.full_name }}</td>
											<td class="employee-table__cell employee-table__cell--email">{{ emp.email }}</td>
											<td class="employee-table__cell employee-table__cell--position">{{ emp.position || "—" }}</td>
											<td class="employee-table__actions">
												<q-btn
													flat
													round
													dense
													color="negative"
													icon="delete"
													class="wizard-btn wizard-btn--icon wizard-btn--icon-danger"
													@click="removeLocal(idx)"
												/>
											</td>
										</tr>
									</tbody>
								</q-markup-table>
							</div>

							<div v-else class="empty-list column items-center q-pa-xl">
								<q-icon name="groups" size="56px" color="grey-4" />
								<p class="text-body1 text-grey-6 q-mt-md">Добавьте хотя бы одного сотрудника</p>
							</div>
						</div>
					</q-step>

					<q-step :name="4" title="Учётные записи" icon="vpn_key">
						<div class="step-body step-body--accounts column items-center">
							<q-icon
								:name="accountsGenerated ? 'check_circle' : 'vpn_key'"
								size="48px"
								:color="accountsGenerated ? 'positive' : 'primary'"
								class="q-mb-md"
							/>
							<p class="text-body2 text-center q-mb-md accounts-hint">
								<template v-if="accountsGenerated">
									Учётные записи созданы. Скачайте PDF для рассылки сотрудникам.
								</template>
								<template v-else-if="hasPendingAccounts">
									Укажите срок действия и сгенерируйте временные пароли для сотрудников.
								</template>
								<template v-else>
									У всех сотрудников уже есть учётные записи. Задайте новый срок и перегенерируйте пароли.
								</template>
							</p>

							<div
								v-if="hasPendingAccounts || savedEmployees.length"
								class="accounts-ttl-card full-width q-mb-lg"
							>
								<div class="accounts-ttl-card__title">Срок действия доступа</div>
								<div class="row q-gutter-sm q-mb-md accounts-ttl-card__presets">
									<q-btn
										v-for="days in ttlPresets"
										:key="days"
										unelevated
										no-caps
										rounded
										size="sm"
										:color="accountsTtlDays === days ? 'primary' : 'grey-3'"
										:text-color="accountsTtlDays === days ? 'white' : 'grey-8'"
										:label="`${days} дн.`"
										class="wizard-btn"
										@click="accountsTtlDays = days"
									/>
								</div>
								<q-input
									v-model.number="accountsTtlDays"
									type="number"
									outlined
									dense
									rounded
									min="1"
									max="365"
									label="Срок в днях"
									suffix="дн."
									class="accounts-ttl-card__input"
									:rules="[ttlDaysRule]"
								/>
								<div class="text-caption text-grey-7 q-mt-sm">
									Учётные записи действуют до {{ expiresPreviewLabel }}, затем удаляются автоматически.
								</div>
							</div>

							<div class="wizard-actions row items-center justify-center q-gutter-sm q-mt-md q-mb-lg">
								<q-btn
									v-if="!accountsGenerated && hasPendingAccounts"
									unelevated
									no-caps
									rounded
									color="primary"
									icon="auto_fix_high"
									label="Сгенерировать учётные записи"
									class="wizard-btn wizard-btn--primary"
									:loading="generating"
									@click="generateAccounts(false)"
								/>
								<q-btn
									v-if="!accountsGenerated && !hasPendingAccounts && savedEmployees.length"
									unelevated
									no-caps
									rounded
									color="primary"
									icon="refresh"
									label="Перегенерировать пароли"
									class="wizard-btn wizard-btn--primary"
									:loading="generating"
									@click="generateAccounts(true)"
								/>
								<template v-if="accountsGenerated">
									<q-btn
										unelevated
										no-caps
										rounded
										color="primary"
										icon="picture_as_pdf"
										label="Скачать PDF"
										class="wizard-btn wizard-btn--primary"
										@click="downloadPdf"
									/>
									<q-btn
										outline
										no-caps
										rounded
										color="primary"
										icon="refresh"
										label="Перегенерировать"
										class="wizard-btn wizard-btn--outline"
										:loading="generating"
										@click="generateAccounts(true)"
									/>
								</template>
							</div>

							<div
								v-if="accountsGenerated"
								class="employee-table-wrap employee-table-wrap--compact full-width"
							>
									<q-markup-table flat bordered dense class="employee-table">
										<thead>
											<tr>
												<th>ФИО</th>
												<th>Email</th>
												<th>Пароль</th>
												<th class="employee-table__expires-col">Срок</th>
											</tr>
										</thead>
										<tbody>
											<tr v-for="acc in generatedAccounts" :key="acc.employee_id">
												<td class="employee-table__cell employee-table__cell--name">{{ acc.full_name }}</td>
												<td class="employee-table__cell employee-table__cell--email">{{ acc.email }}</td>
												<td class="employee-table__cell employee-table__cell--password">
													<div class="employee-table__password row items-center no-wrap">
														<code class="temp-pass">{{ acc.temp_password }}</code>
														<q-btn
															flat
															round
															dense
															size="sm"
															icon="content_copy"
															class="wizard-btn wizard-btn--icon"
															@click="copyPassword(acc.temp_password)"
														/>
													</div>
												</td>
												<td class="employee-table__cell employee-table__expires-col text-grey-7">
													{{ formatExpires(acc.account_expires_at) }}
												</td>
											</tr>
										</tbody>
									</q-markup-table>
								</div>
						</div>
					</q-step>

					<template #navigation>
						<q-stepper-navigation class="employee-wizard__nav">
							<div class="employee-wizard__nav-inner row items-center no-wrap">
								<div class="employee-wizard__nav-left row items-center q-gutter-sm">
									<q-btn
										v-if="step > 1 && step < 4"
										outline
										no-caps
										rounded
										color="grey-7"
										label="Назад"
										class="wizard-btn wizard-btn--outline"
										@click="step -= 1"
									/>
									<q-btn
										v-if="step === 1"
										outline
										no-caps
										rounded
										color="primary"
										label="Вручную"
										class="wizard-btn wizard-btn--outline"
										@click="goToReview"
									/>
								</div>

								<q-space />

								<div class="employee-wizard__nav-right row items-center q-gutter-sm">
									<q-btn
										v-if="step === 2"
										unelevated
										no-caps
										rounded
										color="primary"
										label="Импортировать"
										class="wizard-btn wizard-btn--primary"
										:disable="!mappingComplete || !mappedPreview.valid.length"
										@click="applyMapping"
									/>
									<q-btn
										v-if="step === 3"
										unelevated
										no-caps
										rounded
										color="primary"
										label="Сохранить"
										class="wizard-btn wizard-btn--primary"
										:loading="saving"
										:disable="!localEmployees.length"
										@click="saveEmployees"
									/>
									<q-btn
										v-if="step === 4 && accountsGenerated"
										unelevated
										no-caps
										rounded
										color="primary"
										label="Готово"
										class="wizard-btn wizard-btn--primary"
										@click="finish"
									/>
									<q-btn
										outline
										no-caps
										rounded
										color="grey-7"
										label="Закрыть"
										class="wizard-btn wizard-btn--outline"
										v-close-popup
									/>
								</div>
							</div>
						</q-stepper-navigation>
					</template>
				</q-stepper>
			</q-card-section>

			<q-dialog v-model="manualDialog" persistent>
				<q-card class="wizard-subdialog">
					<q-card-section class="wizard-subdialog__header">
						<div class="text-h6 text-weight-bold">Новый сотрудник</div>
					</q-card-section>
					<q-card-section class="q-gutter-md q-pt-none">
						<q-input v-model="manualForm.full_name" outlined dense rounded label="ФИО" />
						<q-input v-model="manualForm.email" outlined dense rounded label="Email" type="email" />
						<q-input v-model="manualForm.position" outlined dense rounded label="Должность" />
					</q-card-section>
					<q-card-actions class="wizard-subdialog__actions row items-center q-gutter-sm">
						<q-space />
						<q-btn
							outline
							no-caps
							rounded
							color="grey-7"
							label="Отмена"
							class="wizard-btn wizard-btn--outline"
							v-close-popup
						/>
						<q-btn
							unelevated
							no-caps
							rounded
							color="primary"
							icon="person_add"
							label="Добавить"
							class="wizard-btn wizard-btn--primary"
							@click="addManual"
						/>
					</q-card-actions>
				</q-card>
			</q-dialog>

			<q-dialog v-model="skippedDialog">
				<q-card class="wizard-subdialog wizard-subdialog--wide">
					<q-card-section class="wizard-subdialog__header">
						<div class="text-h6 text-weight-bold">Пропущенные строки</div>
						<div class="text-body2 text-grey-7 q-mt-xs">
							{{ lastSkipped.length }} строк не импортировано
						</div>
					</q-card-section>
					<q-card-section class="q-pt-none skipped-list">
						<div v-for="item in lastSkipped.slice(0, 20)" :key="item.rowIndex" class="skipped-item q-mb-sm">
							<span class="text-weight-medium">Строка {{ item.rowIndex }}:</span>
							{{ item.reason }}
							<span v-if="item.full_name" class="text-grey-7"> · {{ item.full_name }}</span>
						</div>
						<div v-if="lastSkipped.length > 20" class="text-caption text-grey-6 q-mt-sm">
							…и ещё {{ lastSkipped.length - 20 }}
						</div>
					</q-card-section>
					<q-card-actions class="wizard-subdialog__actions row items-center">
						<q-space />
						<q-btn
							unelevated
							no-caps
							rounded
							color="primary"
							label="Понятно"
							class="wizard-btn wizard-btn--primary"
							v-close-popup
						/>
					</q-card-actions>
				</q-card>
			</q-dialog>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { useQuasar } from "quasar";
import { organizationApi } from "@api/api/OrganizationApi.js";
import { parseExcelFile, mapRowsWithFields, guessColumnMapping } from "@utils/parseExcelFile.js";
import { downloadAccountsPdf } from "@utils/generateAccountsPdf.js";
import { formatAccountExpiresAt } from "@utils/formatAccountExpiresAt.js";
import ExcelColumnMappingCanvas from "./ExcelColumnMappingCanvas.vue";

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	orgId: { type: Number, default: null },
	organizationName: { type: String, default: "" },
	trainingTitle: { type: String, default: "" },
	existingEmployees: { type: Array, default: () => [] },
	desktopMode: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue", "saved", "local-save", "local-provision"]);

const $q = useQuasar();

const step = ref(1);
const fileInput = ref(null);
const mapCanvasRef = ref(null);
const excelColumns = ref([]);
const excelRows = ref([]);
const parsedFileName = ref("");
const fieldMapping = ref({});
const mapFlowKey = ref("excel-map-0");
const mapReady = ref(false);
const localEmployees = ref([]);
const savedEmployees = ref([]);
const saving = ref(false);
const generating = ref(false);
const accountsGenerated = ref(false);
const generatedAccounts = ref([]);
const manualDialog = ref(false);
const skippedDialog = ref(false);
const lastSkipped = ref([]);
const manualForm = ref({ full_name: "", email: "", position: "" });
const accountsTtlDays = ref(14);
const ttlPresets = [7, 14, 30, 90];

const isDesktopShell = computed(
	() => props.desktopMode || Boolean(typeof window !== "undefined" && window.hrDesktop),
);

const mappingFields = [
	{ fieldKey: "full_name", label: "ФИО", icon: "person", required: true },
	{ fieldKey: "email", label: "Email", icon: "mail", required: true },
	{ fieldKey: "position", label: "Должность", icon: "work", required: false },
];

const columnOptions = computed(() =>
	excelColumns.value.map((col) => ({ label: col, value: col })),
);

const mappingComplete = computed(() => {
	const m = fieldMapping.value;
	return Boolean(
		m.email && (m.full_name || (m.full_name_parts && m.full_name_parts.length)),
	);
});

const mappedPreview = computed(() => {
	if (!mappingComplete.value) {
		return { valid: [], skipped: [] };
	}
	return mapRowsWithFields(excelRows.value, fieldMapping.value);
});

const hasPendingAccounts = computed(() =>
	savedEmployees.value.some((e) => !e.account_generated),
);

const expiresPreviewLabel = computed(() => {
	const days = Number(accountsTtlDays.value);
	if (!Number.isFinite(days) || days < 1) return "—";
	const d = new Date();
	d.setDate(d.getDate() + Math.floor(days));
	return formatAccountExpiresAt(d.toISOString());
});

function ttlDaysRule(value) {
	const days = Number(value);
	if (!Number.isFinite(days) || days < 1 || days > 365) {
		return "Укажите срок от 1 до 365 дней";
	}
	return true;
}

function formatExpires(value) {
	return formatAccountExpiresAt(value);
}

watch(
	() => props.modelValue,
	(open) => {
		if (!open) return;
		resetWizard();
		savedEmployees.value = [...(props.existingEmployees || [])];
		localEmployees.value = savedEmployees.value.map((e) => ({
			email: e.email,
			full_name: e.full_name,
			position: e.position,
		}));
	},
);

watch(step, async (value) => {
	if (value === 2 && excelColumns.value.length) {
		await activateMapCanvas();
	} else {
		mapReady.value = false;
	}
});

async function activateMapCanvas() {
	mapReady.value = false;
	mapFlowKey.value = `excel-map-${Date.now()}`;
	await nextTick();
	requestAnimationFrame(() => {
		mapReady.value = true;
		nextTick(() => {
			setTimeout(() => mapCanvasRef.value?.refreshView?.(), 150);
		});
	});
}

function resetWizard() {
	step.value = 1;
	mapReady.value = false;
	excelColumns.value = [];
	excelRows.value = [];
	parsedFileName.value = "";
	fieldMapping.value = {};
	localEmployees.value = [];
	accountsGenerated.value = false;
	generatedAccounts.value = [];
	lastSkipped.value = [];
	accountsTtlDays.value = 14;
}

function selectValue(fieldKey) {
	if (fieldKey === "full_name") {
		return fieldMapping.value.full_name || null;
	}
	return fieldMapping.value[fieldKey] || null;
}

function setMappingField(fieldName, value) {
	const next = { ...fieldMapping.value };

	if (fieldName === "full_name") {
		delete next.full_name_parts;
		if (!value) {
			delete next.full_name;
		} else {
			next.full_name = value;
			for (const key of ["email", "position"]) {
				if (next[key] === value) delete next[key];
			}
		}
	} else if (!value) {
		delete next[fieldName];
	} else {
		for (const key of Object.keys(next)) {
			if (key === "full_name_parts" && Array.isArray(next[key])) {
				next[key] = next[key].filter((c) => c !== value);
				if (!next[key].length) delete next[key];
			} else if (next[key] === value && key !== fieldName) {
				delete next[key];
			}
		}
		next[fieldName] = value;
	}

	fieldMapping.value = next;
}

async function onFileSelected(event) {
	const file = event.target.files?.[0];
	if (!file) return;
	await loadExcelFromFile(file);
}

async function pickExcelNative() {
	const picked = await window.hrDesktop?.openExcelFile?.();
	if (!picked) return;
	const binary = atob(picked.base64);
	const bytes = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
	await loadExcelFromFile(new File([bytes], picked.fileName));
}

async function loadExcelFromFile(file) {
	try {
		const parsed = await parseExcelFile(file);
		if (!parsed.columns.length) {
			$q.notify({
				type: "warning",
				message: "Не найдены заголовки. Убедитесь, что первая строка с данными содержит названия колонок.",
			});
			return;
		}
		excelColumns.value = parsed.columns;
		excelRows.value = parsed.rows;
		parsedFileName.value = file.name;
		fieldMapping.value = guessColumnMapping(parsed.columns);
		step.value = 2;
		$q.notify({
			type: "positive",
			message: `Загружено: ${parsed.columns.length} колонок, ${parsed.rows.length} строк`,
			timeout: 3000,
		});
	} catch {
		$q.notify({ type: "negative", message: "Не удалось прочитать файл" });
	} finally {
		if (fileInput.value) fileInput.value.value = "";
	}
}

function applyMapping() {
	const { valid, skipped } = mapRowsWithFields(excelRows.value, fieldMapping.value);
	if (!valid.length) {
		$q.notify({
			type: "warning",
			message: "Нет строк с заполненными email и ФИО по выбранному сопоставлению",
		});
		return;
	}

	const existing = new Set(localEmployees.value.map((e) => e.email.toLowerCase()));
	let added = 0;
	let duplicates = 0;

	for (const row of valid) {
		if (existing.has(row.email.toLowerCase())) {
			duplicates += 1;
			continue;
		}
		localEmployees.value.push(row);
		existing.add(row.email.toLowerCase());
		added += 1;
	}

	lastSkipped.value = skipped;
	step.value = 3;

	const parts = [`Импортировано: ${added}`];
	if (duplicates) parts.push(`дубликатов: ${duplicates}`);
	if (skipped.length) parts.push(`пропущено: ${skipped.length}`);

	$q.notify({
		type: skipped.length ? "warning" : "positive",
		message: parts.join(" · "),
		timeout: 4000,
		actions: skipped.length
			? [{ label: "Подробнее", color: "white", handler: () => { skippedDialog.value = true; } }]
			: undefined,
	});
}

function goToReview() {
	step.value = 3;
}

function removeLocal(idx) {
	localEmployees.value.splice(idx, 1);
}

function addManual() {
	const full_name = manualForm.value.full_name.trim();
	const email = manualForm.value.email.trim().toLowerCase();
	if (!full_name || !email) {
		$q.notify({ type: "warning", message: "Укажите ФИО и email" });
		return;
	}
	if (localEmployees.value.some((e) => e.email.toLowerCase() === email)) {
		$q.notify({ type: "warning", message: "Такой email уже в списке" });
		return;
	}
	localEmployees.value.push({
		full_name,
		email,
		position: manualForm.value.position.trim() || null,
	});
	manualForm.value = { full_name: "", email: "", position: "" };
	manualDialog.value = false;
}

async function saveEmployees() {
	saving.value = true;
	try {
		const existingEmails = new Set(
			(props.existingEmployees || []).map((e) => (e.email || e.provisionRef || "").toLowerCase()),
		);
		const toSave = localEmployees.value.filter(
			(e) => !existingEmails.has((e.email || e.provision_ref || "").toLowerCase()),
		);

		if (props.desktopMode) {
			savedEmployees.value = [...(props.existingEmployees || []), ...toSave];
			emit("local-save", { employees: toSave, allEmployees: savedEmployees.value });
			$q.notify({
				type: "positive",
				message: toSave.length
					? `Сохранено локально: ${toSave.length} сотрудников`
					: "Список актуален",
			});
			emit("saved");
			step.value = 4;
			return;
		}

		if (!props.orgId) {
			throw new Error("Не указана организация");
		}
		if (toSave.length) {
			await organizationApi.addEmployeesBulk(props.orgId, toSave);
		}
		const { data: orgData } = await organizationApi.get(props.orgId);
		savedEmployees.value = orgData?.employees || [];
		$q.notify({
			type: "positive",
			message: toSave.length
				? `Сохранено ${toSave.length} новых сотрудников`
				: "Список актуален",
		});
		emit("saved", savedEmployees.value);
		step.value = 4;
	} catch (err) {
		$q.notify({
			type: "negative",
			message: err?.response?.data?.detail || "Ошибка сохранения",
		});
	} finally {
		saving.value = false;
	}
}

async function generateAccounts(regenerate = false) {
	const ttlDays = Math.floor(Number(accountsTtlDays.value));
	if (!Number.isFinite(ttlDays) || ttlDays < 1 || ttlDays > 365) {
		$q.notify({ type: "warning", message: "Укажите срок доступа от 1 до 365 дней" });
		return;
	}
	generating.value = true;
	try {
		if (props.desktopMode) {
			const pending = regenerate
				? savedEmployees.value
				: savedEmployees.value.filter((e) => !e.account_generated);
			if (!pending.length) {
				$q.notify({ type: "warning", message: "Нет сотрудников для генерации" });
				generating.value = false;
				return;
			}
			emit("local-provision", {
				ttlDays,
				regenerate,
				employees: pending,
			});
			return;
		}

		if (!props.orgId) {
			throw new Error("Не указана организация");
		}
		const { data } = await organizationApi.generateAccounts(props.orgId, regenerate, {
			ttl_days: ttlDays,
		});
		generatedAccounts.value = data || [];
		accountsGenerated.value = true;
		emit("saved");
		$q.notify({
			type: "positive",
			message: regenerate ? "Пароли перегенерированы" : "Учётные записи созданы",
		});
	} catch (err) {
		$q.notify({
			type: "negative",
			message: err?.response?.data?.detail || "Ошибка генерации",
		});
	} finally {
		generating.value = false;
	}
}

function copyPassword(text) {
	void navigator.clipboard.writeText(text);
	$q.notify({ type: "info", message: "Пароль скопирован", timeout: 1200 });
}

function downloadPdf() {
	downloadAccountsPdf(props.organizationName, generatedAccounts.value);
}

function finish() {
	emit("update:modelValue", false);
}

function completeProvision(accounts) {
	generatedAccounts.value = (accounts || []).map((acc) => ({
		employee_id: acc.slot_id || acc.employee_id,
		email: acc.login_id || acc.email,
		full_name: acc.full_name || "—",
		temp_password: acc.temp_password,
		account_expires_at: acc.account_expires_at,
		ttl_days: acc.ttl_days,
	}));
	accountsGenerated.value = true;
	generating.value = false;
	emit("saved");
	$q.notify({
		type: "positive",
		message: "Учётные записи созданы",
	});
}

function failProvision(message) {
	generating.value = false;
	$q.notify({
		type: "negative",
		message: message || "Ошибка генерации",
	});
}

defineExpose({ completeProvision, failProvision });
</script>

<style scoped>
.employee-wizard {
	display: flex;
	flex-direction: column;
	width: 1400px;
	max-width: 96vw;
	max-height: 94vh;
	border-radius: 20px;
	background: #f1f5f9;
	overflow: hidden;
}

.employee-wizard__header {
	background: #fff;
	padding: 20px 28px 16px;
	flex-shrink: 0;
}

.employee-wizard__body {
	padding: 0;
	flex: 1 1 auto;
	min-height: 0;
}

.employee-wizard__stepper {
	background: transparent;
	box-shadow: none;
	width: 100%;
}

.employee-wizard__stepper :deep(.q-stepper__header) {
	background: #fff;
	border-bottom: 1px solid rgba(0, 0, 0, 0.06);
	padding: 12px 28px 0;
}

.employee-wizard__stepper :deep(.q-stepper__title) {
	font-size: 14px;
	font-weight: 600;
}

.employee-wizard__stepper :deep(.q-stepper__step-content) {
	overflow: visible;
}

.employee-wizard__stepper :deep(.q-stepper__step-inner) {
	padding: 20px 28px 32px;
}

.employee-wizard__stepper :deep(.q-stepper__nav) {
	padding: 0;
}

.employee-wizard__nav {
	padding: 20px 28px;
	margin-top: 24px;
	background: #fff;
	border-top: 1px solid rgba(0, 0, 0, 0.06);
	flex-shrink: 0;
}

.employee-wizard__nav-inner {
	width: 100%;
	gap: 12px;
}

.employee-wizard__nav-left,
.employee-wizard__nav-right {
	flex-wrap: nowrap;
}

.wizard-actions {
	width: 100%;
	flex-wrap: wrap;
}

.step-toolbar__hint {
	line-height: 42px;
}

.wizard-subdialog {
	min-width: 400px;
	border-radius: 20px;
	overflow: hidden;
}

.wizard-subdialog--wide {
	min-width: 480px;
	max-width: 640px;
}

.wizard-subdialog__header {
	padding: 20px 24px 8px;
}

.wizard-subdialog__actions {
	padding: 12px 24px 20px;
}

.step-body {
	width: 100%;
}

.step-body--import {
	padding: 16px 0 24px;
}

.step-body--accounts {
	padding: 24px 0;
}

.accounts-hint {
	max-width: 480px;
	color: #64748b;
}

.accounts-ttl-card {
	max-width: 420px;
	padding: 20px 22px;
	background: #fff;
	border-radius: 16px;
	border: 1px solid rgba(80, 100, 247, 0.2);
	box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

.accounts-ttl-card__title {
	font-size: 14px;
	font-weight: 700;
	color: #1e293b;
	margin-bottom: 12px;
}

.accounts-ttl-card__presets {
	flex-wrap: wrap;
}

.accounts-ttl-card__input {
	max-width: 200px;
}

.map-layout {
	display: grid;
	grid-template-columns: minmax(800px, 1fr) 280px;
	gap: 20px;
	align-items: start;
	width: 100%;
}

.map-wrap {
	position: relative;
	height: 600px;
	min-height: 600px;
	min-width: 800px;
	width: 100%;
	border-radius: 16px;
	overflow: hidden;
	border: 1px solid rgba(0, 0, 0, 0.08);
	background: #fff;
	box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
}

.map-wrap__loading {
	position: absolute;
	inset: 0;
	background: #fff;
}

.map-sidebar {
	background: #fff;
	border-radius: 16px;
	padding: 18px;
	border: 1px solid rgba(0, 0, 0, 0.08);
}

.map-sidebar__title {
	font-size: 14px;
	font-weight: 700;
	color: #1e293b;
	margin-bottom: 16px;
}

.map-sidebar__label {
	font-size: 14px;
	font-weight: 600;
	color: #334155;
	margin-bottom: 6px;
	display: flex;
	align-items: center;
}

.excel-dropzone {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 40px 64px;
	border: 2px dashed rgba(33, 115, 70, 0.35);
	border-radius: 20px;
	background: #fff;
	transition: all 0.2s ease;
}

.excel-dropzone:hover {
	border-color: #217346;
	box-shadow: 0 12px 32px rgba(33, 115, 70, 0.12);
}

.hidden {
	display: none;
}

.employee-table-wrap {
	max-height: 360px;
	overflow: auto;
	border-radius: 12px;
	-webkit-overflow-scrolling: touch;
}

.employee-table-wrap--compact {
	max-height: 280px;
}

.employee-table {
	background: #fff;
	border-radius: 12px;
	width: 100%;
	min-width: 520px;
}

.employee-table th {
	font-size: 12px;
	text-transform: uppercase;
	color: #64748b;
	background: #f8fafc;
	white-space: nowrap;
}

.employee-table__cell {
	max-width: 220px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.employee-table__cell--name {
	max-width: 180px;
}

.employee-table__cell--email {
	max-width: 200px;
}

.employee-table__cell--position {
	max-width: 140px;
}

.employee-table__cell--password {
	max-width: none;
	overflow: visible;
	white-space: nowrap;
}

.employee-table__password {
	gap: 2px;
}

.employee-table__expires-col {
	width: 96px;
	min-width: 96px;
	white-space: nowrap;
}

.employee-table th.employee-table__actions-col,
.employee-table td.employee-table__actions {
	width: 52px;
	min-width: 52px;
	padding-left: 4px;
	padding-right: 4px;
	text-align: center;
	position: sticky;
	right: 0;
	z-index: 1;
	background: #fff;
	box-shadow: -6px 0 10px rgba(15, 23, 42, 0.06);
}

.employee-table thead th.employee-table__actions-col {
	background: #f8fafc;
}

.employee-table__actions .q-btn {
	margin: 0 auto;
}

.temp-pass {
	background: rgba(80, 100, 247, 0.08);
	padding: 4px 8px;
	border-radius: 6px;
	font-weight: 600;
}

.map-empty {
	background: #fff;
	border-radius: 16px;
	border: 1px dashed rgba(0, 0, 0, 0.12);
}

.skipped-list {
	max-height: 320px;
	overflow-y: auto;
}

.skipped-item {
	font-size: 13px;
	line-height: 1.4;
}

@media (max-width: 900px) {
	.employee-wizard {
		width: 96vw;
	}

	.employee-wizard__nav-inner {
		flex-wrap: wrap;
		justify-content: stretch;
	}

	.employee-wizard__nav-left,
	.employee-wizard__nav-right {
		width: 100%;
		justify-content: space-between;
	}

	.map-layout {
		grid-template-columns: 1fr;
	}

	.map-wrap {
		min-width: 0;
		height: 360px;
		min-height: 360px;
	}

	.employee-table {
		min-width: 360px;
	}

	.employee-table__position-col,
	.employee-table__cell--position {
		display: none;
	}
}
</style>

<style>
.employee-import-dialog .q-dialog__inner > .q-card.employee-wizard {
	width: 1400px !important;
	max-width: 96vw !important;
}
</style>
