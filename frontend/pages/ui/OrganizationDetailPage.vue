<template>
	<div class="org-detail-page">
		<div v-if="loading" class="loading-state q-pa-xl column items-center">
			<q-spinner-dots size="48px" color="primary" />
		</div>

		<template v-else-if="org">
			<div class="page-header animate-fade-in-up">
				<q-btn
					outline
					no-caps
					rounded
					color="grey-7"
					icon="arrow_back"
					label="Назад"
					class="wizard-btn wizard-btn--outline page-header__back"
					to="/personal/organizations"
				/>
				<div class="page-header__title min-width-0">
					<q-input
						v-if="editingName"
						v-model="editName"
						outlined
						dense
						rounded
						class="name-input"
						@keyup.enter="saveName"
						@blur="saveName"
					/>
					<h1 v-else class="page-title row items-center no-wrap">
						{{ org.name }}
						<q-btn
							flat
							round
							dense
							icon="edit"
							color="grey-6"
							class="wizard-btn wizard-btn--icon q-ml-xs"
							@click="startEditName"
						/>
					</h1>
				</div>
				<p class="page-subtitle">Управление тренингами и доступом сотрудников</p>
			</div>

			<div class="panels animate-stagger-children">
				<section class="panel">
					<div class="panel__head">
						<h2 class="panel__title">
							<q-icon name="school" size="20px" class="panel__icon" />
							Тренинги
						</h2>
						<div class="panel__actions">
							<q-btn
								unelevated
								no-caps
								rounded
								color="primary"
								icon="add"
								label="Добавить тренинг"
								class="wizard-btn wizard-btn--primary panel__action-btn"
								:disable="!availableTrainings.length"
								@click="trainingPicker = true"
							/>
						</div>
					</div>

					<div v-if="!org.trainings?.length" class="panel-empty column items-center">
						<q-icon name="school" size="40px" color="grey-4" class="q-mb-sm" />
						<p class="text-grey-6 q-mb-md q-ma-none">Добавьте тренинг из ваших существующих</p>
						<q-btn
							outline
							no-caps
							rounded
							color="primary"
							icon="add"
							label="Выбрать тренинг"
							class="wizard-btn wizard-btn--outline"
							:disable="!availableTrainings.length"
							@click="trainingPicker = true"
						/>
					</div>

					<div v-else class="training-list">
						<div
							v-for="t in org.trainings"
							:key="t.uuid"
							class="training-row"
						>
							<div class="training-row__info">
								<div class="text-weight-bold">{{ t.title }}</div>
								<div class="text-caption text-grey-6">
									{{ t.publish ? "Опубликован" : "Черновик" }}
								</div>
							</div>
							<div class="panel__actions panel__actions--row">
								<q-btn
									unelevated
									no-caps
									rounded
									color="primary"
									icon="groups"
									label="Сотрудники"
									class="wizard-btn wizard-btn--primary panel__action-btn"
									@click="openEmployeeWizard(t)"
								/>
								<q-btn
									flat
									round
									color="negative"
									icon="delete"
									class="wizard-btn wizard-btn--icon wizard-btn--icon-danger panel__icon-btn"
									@click="confirmRemoveTraining(t)"
								/>
							</div>
						</div>
					</div>
				</section>

				<section class="panel">
					<div class="panel__head">
						<h2 class="panel__title">
							<q-icon name="groups" size="20px" class="panel__icon" />
							Сотрудники
							<q-badge color="primary" :label="org.employees?.length || 0" class="q-ml-sm" />
						</h2>
						<div class="panel__actions panel__actions--employees">
							<q-btn
								unelevated
								no-caps
								rounded
								color="primary"
								icon="upload_file"
								label="Импорт / учётные записи"
								class="wizard-btn wizard-btn--primary panel__action-btn panel__action-btn--import"
								@click="openEmployeeWizard()"
							/>
							<q-btn
								v-if="org.employees?.length"
								outline
								no-caps
								rounded
								color="negative"
								icon="delete_sweep"
								label="Удалить всех"
								class="wizard-btn wizard-btn--outline panel__action-btn"
								:loading="deletingAllEmployees"
								@click="confirmDeleteAllEmployees"
							/>
						</div>
					</div>

					<div v-if="!org.employees?.length" class="panel-empty column items-center">
						<q-icon name="groups" size="40px" color="grey-4" class="q-mb-sm" />
						<p class="text-grey-6 q-mb-md q-ma-none">Импортируйте сотрудников или добавьте вручную</p>
						<q-btn
							unelevated
							no-caps
							rounded
							color="primary"
							icon="upload_file"
							label="Открыть импорт"
							class="wizard-btn wizard-btn--primary"
							@click="openEmployeeWizard()"
						/>
					</div>

					<div v-else class="employee-list">
						<div
							v-for="emp in org.employees"
							:key="emp.id"
							class="employee-row"
						>
							<div class="employee-row__info">
								<div class="employee-row__name">{{ emp.full_name }}</div>
								<div class="employee-row__meta">
									<span class="employee-row__email">{{ emp.email }}</span>
									<span v-if="emp.position" class="employee-row__dot">·</span>
									<span v-if="emp.position" class="employee-row__position">{{ emp.position }}</span>
								</div>
								<div class="employee-row__status row items-center q-gutter-xs q-mt-xs">
									<q-badge
										:color="emp.account_generated ? 'positive' : 'grey-5'"
										:label="emp.account_generated ? 'Аккаунт создан' : 'Ожидает выдачи'"
									/>
									<span
										v-if="emp.account_generated && emp.account_expires_at"
										class="employee-row__expires"
									>
										до {{ formatExpires(emp.account_expires_at) }}
									</span>
								</div>
							</div>
							<div class="employee-row__actions">
								<q-btn
									flat
									round
									color="negative"
									icon="delete"
									class="wizard-btn wizard-btn--icon wizard-btn--icon-danger panel__icon-btn"
									@click="confirmDeleteEmployee(emp)"
								/>
							</div>
						</div>
					</div>
				</section>
			</div>
		</template>

		<q-dialog v-model="trainingPicker" persistent>
			<q-card class="org-subdialog org-subdialog--wide">
				<q-card-section class="org-subdialog__header">
					<div class="text-h6 text-weight-bold">Добавить тренинг</div>
					<div class="text-body2 text-grey-7 q-mt-xs">Выберите тренинг из ваших существующих</div>
				</q-card-section>
				<q-card-section class="q-pt-none">
					<q-select
						v-model="selectedTrainingUuid"
						:options="availableTrainings"
						option-value="uuid"
						option-label="title"
						emit-value
						map-options
						outlined
						dense
						rounded
						label="Тренинг"
					/>
				</q-card-section>
				<q-card-actions class="org-subdialog__actions row items-center q-gutter-sm">
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
						icon="add"
						label="Добавить"
						class="wizard-btn wizard-btn--primary"
						:disable="!selectedTrainingUuid"
						:loading="addingTraining"
						@click="addTraining"
					/>
				</q-card-actions>
			</q-card>
		</q-dialog>

		<EmployeeImportWizard
			v-model="wizardOpen"
			:org-id="orgId"
			:organization-name="org?.name || ''"
			:training-title="wizardTrainingTitle"
			:existing-employees="org?.employees || []"
			@saved="loadOrg"
		/>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useQuasar } from "quasar";
import { organizationApi } from "@api/api/OrganizationApi.js";
import { TrainingApi } from "@api";
import EmployeeImportWizard from "@components/features/organizations/EmployeeImportWizard.vue";
import { formatAccountExpiresAt } from "@utils/formatAccountExpiresAt.js";

const route = useRoute();
const $q = useQuasar();
const trainingApi = new TrainingApi();

const orgId = computed(() => Number(route.params.id));
const loading = ref(true);
const org = ref(null);
const myTrainings = ref([]);
const editingName = ref(false);
const editName = ref("");
const trainingPicker = ref(false);
const selectedTrainingUuid = ref(null);
const addingTraining = ref(false);
const wizardOpen = ref(false);
const wizardTrainingTitle = ref("");
const deletingAllEmployees = ref(false);

const dialogOkBtn = {
	rounded: true,
	noCaps: true,
	unelevated: true,
	color: "negative",
	label: "Удалить",
	class: "wizard-btn wizard-btn--danger",
};

const dialogCancelBtn = {
	rounded: true,
	noCaps: true,
	outline: true,
	color: "grey-7",
	label: "Отмена",
	class: "wizard-btn wizard-btn--outline",
	flat: false,
};

const availableTrainings = computed(() => {
	const linked = new Set((org.value?.trainings || []).map((t) => t.uuid));
	return myTrainings.value.filter((t) => !linked.has(t.uuid));
});

async function loadOrg() {
	try {
		const { data } = await organizationApi.get(orgId.value);
		org.value = data;
	} catch {
		org.value = null;
		$q.notify({ type: "negative", message: "Организация не найдена" });
	}
}

async function loadTrainings() {
	try {
		const { data } = await trainingApi.getTrainings();
		myTrainings.value = data || [];
	} catch {
		myTrainings.value = [];
	}
}

async function load() {
	loading.value = true;
	await Promise.all([loadOrg(), loadTrainings()]);
	loading.value = false;
}

function startEditName() {
	editName.value = org.value.name;
	editingName.value = true;
}

async function saveName() {
	if (!editingName.value) return;
	editingName.value = false;
	const name = editName.value.trim();
	if (!name || name === org.value.name) return;
	try {
		const { data } = await organizationApi.update(orgId.value, { name });
		org.value = data;
	} catch {
		$q.notify({ type: "negative", message: "Не удалось сохранить название" });
	}
}

async function addTraining() {
	if (!selectedTrainingUuid.value) return;
	const uuid = selectedTrainingUuid.value;
	addingTraining.value = true;
	try {
		const { data } = await organizationApi.addTraining(orgId.value, uuid);
		org.value = data;
		trainingPicker.value = false;
		selectedTrainingUuid.value = null;
		$q.notify({ type: "positive", message: "Тренинг добавлен" });
		const added = data.trainings.find((t) => t.uuid === uuid);
		if (added) openEmployeeWizard(added);
	} catch (err) {
		$q.notify({
			type: "negative",
			message: err?.response?.data?.detail || "Ошибка добавления",
		});
	} finally {
		addingTraining.value = false;
	}
}

function confirmRemoveTraining(training) {
	$q.dialog({
		title: "Удалить тренинг?",
		message: `«${training.title}» будет отвязан от организации.`,
		persistent: true,
		ok: dialogOkBtn,
		cancel: dialogCancelBtn,
	}).onOk(() => removeTraining(training.uuid));
}

async function removeTraining(uuid) {
	try {
		const { data } = await organizationApi.removeTraining(orgId.value, uuid);
		org.value = data;
		$q.notify({ type: "positive", message: "Тренинг удалён" });
	} catch {
		$q.notify({ type: "negative", message: "Ошибка удаления тренинга" });
	}
}

function openEmployeeWizard(training) {
	wizardTrainingTitle.value = training?.title || "";
	wizardOpen.value = true;
}

function formatExpires(value) {
	return formatAccountExpiresAt(value);
}

function confirmDeleteEmployee(emp) {
	$q.dialog({
		title: "Удалить сотрудника?",
		message: `${emp.full_name} будет удалён из организации.`,
		persistent: true,
		ok: dialogOkBtn,
		cancel: dialogCancelBtn,
	}).onOk(() => deleteEmployee(emp.id));
}

async function deleteEmployee(employeeId) {
	try {
		await organizationApi.deleteEmployee(orgId.value, employeeId);
		await loadOrg();
		$q.notify({ type: "positive", message: "Сотрудник удалён" });
	} catch {
		$q.notify({ type: "negative", message: "Ошибка удаления" });
	}
}

function confirmDeleteAllEmployees() {
	const count = org.value?.employees?.length || 0;
	$q.dialog({
		title: "Удалить всех сотрудников?",
		message: `Будут удалены все ${count} сотрудников организации и их временные учётные записи. Это действие нельзя отменить.`,
		persistent: true,
		ok: dialogOkBtn,
		cancel: dialogCancelBtn,
	}).onOk(deleteAllEmployees);
}

async function deleteAllEmployees() {
	deletingAllEmployees.value = true;
	try {
		await organizationApi.deleteAllEmployees(orgId.value);
		await loadOrg();
		$q.notify({ type: "positive", message: "Все сотрудники удалены" });
	} catch {
		$q.notify({ type: "negative", message: "Ошибка удаления сотрудников" });
	} finally {
		deletingAllEmployees.value = false;
	}
}

onMounted(load);
</script>

<style scoped>
.org-detail-page {
	padding: 32px;
	max-width: 1000px;
	margin: 0 auto;
	--panel-actions-width: 272px;
}

.page-header {
	display: grid;
	grid-template-columns: auto minmax(0, 1fr);
	grid-template-rows: auto auto;
	column-gap: 16px;
	row-gap: 8px;
	align-items: center;
	margin-bottom: 32px;
}

.page-header__back {
	grid-row: 1;
	grid-column: 1;
	flex-shrink: 0;
	align-self: center;
}

.page-header__title {
	grid-row: 1;
	grid-column: 2;
	min-width: 0;
}

.page-title {
	font-size: 28px;
	font-weight: 800;
	color: #0f172a;
	margin: 0;
	line-height: 1.2;
}

.page-subtitle {
	grid-row: 2;
	grid-column: 2;
	font-size: 15px;
	color: #64748b;
	margin: 0;
}

.name-input {
	max-width: 400px;
	font-size: 24px;
	font-weight: 700;
}

.panels {
	display: flex;
	flex-direction: column;
	gap: 24px;
}

.panel {
	background: rgba(255, 255, 255, 0.9);
	backdrop-filter: blur(24px);
	border: 1px solid rgba(0, 0, 0, 0.06);
	border-radius: 20px;
	padding: 24px 28px;
	box-shadow: 0 8px 32px rgba(15, 23, 42, 0.04);
}

.panel__head,
.training-row {
	display: grid;
	grid-template-columns: minmax(0, 1fr) var(--panel-actions-width);
	align-items: center;
	column-gap: 20px;
}

.panel__head {
	margin-bottom: 20px;
	min-height: 42px;
}

.panel__title {
	display: flex;
	align-items: center;
	margin: 0;
	font-size: 16px;
	font-weight: 700;
	color: #1e293b;
	min-width: 0;
}

.panel__actions {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 8px;
	width: var(--panel-actions-width);
	justify-self: end;
}

.panel__actions--employees {
	flex-direction: column;
	align-items: stretch;
}

.panel__actions--row .panel__action-btn {
	flex: 1 1 auto;
	min-width: 0;
}

.panel__action-btn {
	width: 100%;
}

.panel__icon-btn {
	flex-shrink: 0;
	width: 42px !important;
	height: 42px !important;
	min-height: 42px !important;
}

.panel__icon {
	color: #5064f7;
	background: rgba(80, 100, 247, 0.1);
	padding: 6px;
	border-radius: 10px;
	margin-right: 10px;
}

.panel-empty {
	padding: 32px 24px;
	text-align: center;
	border: 2px dashed rgba(0, 0, 0, 0.08);
	border-radius: 16px;
}

.training-list {
	display: flex;
	flex-direction: column;
	gap: 0;
	padding: 4px 0;
}

.training-row {
	padding: 14px 0;
	border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.training-row:last-child {
	border-bottom: none;
	padding-bottom: 0;
}

.training-row:first-child {
	padding-top: 0;
}

.training-row__info {
	min-width: 0;
	padding-right: 8px;
}

.employee-list {
	display: flex;
	flex-direction: column;
}

.employee-row {
	display: grid;
	grid-template-columns: minmax(0, 1fr) auto;
	align-items: center;
	gap: 12px 16px;
	padding: 14px 0;
	border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.employee-row:last-child {
	border-bottom: none;
	padding-bottom: 0;
}

.employee-row:first-child {
	padding-top: 0;
}

.employee-row__info {
	min-width: 0;
}

.employee-row__name {
	font-weight: 700;
	color: #1e293b;
	word-break: break-word;
}

.employee-row__meta {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 4px;
	margin-top: 4px;
	font-size: 13px;
	color: #64748b;
}

.employee-row__email {
	word-break: break-all;
}

.employee-row__dot {
	color: #cbd5e1;
}

.employee-row__status {
	flex-wrap: wrap;
	align-items: center;
	overflow: visible;
}

.employee-row__status .q-badge {
	flex-shrink: 0;
}

.employee-row__expires {
	font-size: 12px;
	color: #64748b;
}

.employee-row__actions {
	flex-shrink: 0;
}

.panel__action-btn--import {
	white-space: nowrap;
}

.loading-state {
	min-height: 320px;
	justify-content: center;
}

@media (max-width: 720px) {
	.org-detail-page {
		padding: 16px;
		--panel-actions-width: 100%;
	}

	.page-header {
		grid-template-columns: 1fr;
	}

	.page-header__back {
		grid-row: 1;
		grid-column: 1;
		justify-self: start;
		margin-bottom: 4px;
	}

	.page-header__title {
		grid-row: 2;
		grid-column: 1;
	}

	.page-subtitle {
		grid-row: 3;
		grid-column: 1;
	}

	.panel__head,
	.training-row {
		grid-template-columns: 1fr;
		row-gap: 12px;
	}

	.panel__actions {
		width: 100%;
		justify-self: stretch;
	}

	.panel__actions--row {
		justify-content: flex-end;
	}

	.panel__action-btn--import {
		font-size: 13px;
		padding-left: 14px;
		padding-right: 14px;
	}
}
</style>
