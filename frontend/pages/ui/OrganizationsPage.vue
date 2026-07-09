<template>
	<div class="orgs-page">
		<div class="page-header page-header--with-actions animate-fade-in-up">
			<div>
				<h1 class="page-title">Мои организации</h1>
				<p class="page-subtitle">
					Создавайте организации, назначайте тренинги и выдавайте доступ сотрудникам
				</p>
			</div>
			<q-btn
				unelevated
				no-caps
				rounded
				color="primary"
				icon="add"
				label="Создать"
				class="wizard-btn wizard-btn--primary"
				@click="createDialog = true"
			/>
		</div>

		<div v-if="loading" class="loading-state q-pa-xl column items-center">
			<q-spinner-dots size="48px" color="primary" />
			<p class="text-grey-7 q-mt-md">Загрузка...</p>
		</div>

		<div
			v-else-if="!organizations.length"
			class="empty-state q-pa-xl column items-center animate-scale-in"
		>
			<div class="empty-icon-wrap q-mb-lg">
				<q-icon name="business" size="64px" color="primary" />
			</div>
			<h3 class="text-h5 text-weight-bold text-dark q-mb-sm">Пока нет организаций</h3>
			<p class="text-body1 text-grey-6 text-center q-mb-lg empty-state__text">
				Создайте организацию и добавьте в неё тренинги для сотрудников
			</p>
			<q-btn
				unelevated
				no-caps
				rounded
				color="primary"
				icon="add"
				label="Создать организацию"
				class="wizard-btn wizard-btn--primary q-px-xl"
				@click="createDialog = true"
			/>
		</div>

		<div v-else class="orgs-grid q-pb-xl animate-stagger-children">
			<q-card
				v-for="org in organizations"
				:key="org.id"
				class="org-card relative-position"
				flat
				bordered
				v-ripple
				@click="$router.push(`/personal/organizations/${org.id}`)"
			>
				<q-card-section>
					<div class="org-card__top row items-center justify-between q-mb-sm">
						<div class="org-card__icon-wrap">
							<q-icon name="business" size="24px" color="primary" />
						</div>
						<q-btn
							flat
							round
							dense
							color="negative"
							icon="delete"
							class="wizard-btn wizard-btn--icon wizard-btn--icon-danger"
							@click.stop="confirmDelete(org)"
						/>
					</div>
					<div class="text-h6 text-weight-bold text-dark ellipsis q-mb-md">{{ org.name }}</div>
					<div class="row q-gutter-md text-caption text-grey-6">
						<span class="row items-center">
							<q-icon name="groups" size="16px" class="q-mr-xs" />
							{{ org.employees_count }} сотрудников
						</span>
						<span class="row items-center">
							<q-icon name="school" size="16px" class="q-mr-xs" />
							{{ org.trainings_count }} тренингов
						</span>
					</div>
				</q-card-section>
			</q-card>

			<q-card class="org-card create-card" flat bordered v-ripple @click="createDialog = true">
				<q-card-section class="column items-center justify-center full-height text-center">
					<div class="create-card__icon">
						<q-icon name="add" size="32px" color="primary" />
					</div>
					<div class="text-weight-bold text-primary q-mt-sm">Новая организация</div>
				</q-card-section>
			</q-card>
		</div>

		<q-dialog v-model="createDialog" persistent>
			<q-card class="org-subdialog">
				<q-card-section class="org-subdialog__header">
					<div class="text-h6 text-weight-bold">Новая организация</div>
					<div class="text-body2 text-grey-7 q-mt-xs">Укажите название для вашей организации</div>
				</q-card-section>
				<q-card-section class="q-pt-none">
					<q-input
						v-model="newOrgName"
						outlined
						dense
						rounded
						label="Название"
						autofocus
						@keyup.enter="createOrganization"
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
						label="Создать"
						class="wizard-btn wizard-btn--primary"
						:loading="creating"
						:disable="!newOrgName.trim()"
						@click="createOrganization"
					/>
				</q-card-actions>
			</q-card>
		</q-dialog>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useQuasar } from "quasar";
import { organizationApi } from "@api/api/OrganizationApi.js";

const $q = useQuasar();
const router = useRouter();

const loading = ref(true);
const creating = ref(false);
const organizations = ref([]);
const createDialog = ref(false);
const newOrgName = ref("");

async function load() {
	loading.value = true;
	try {
		const { data } = await organizationApi.list();
		organizations.value = data || [];
	} catch {
		organizations.value = [];
	} finally {
		loading.value = false;
	}
}

async function createOrganization() {
	const name = newOrgName.value.trim();
	if (!name) return;
	creating.value = true;
	try {
		const { data } = await organizationApi.create({ name });
		createDialog.value = false;
		newOrgName.value = "";
		await router.push(`/personal/organizations/${data.id}`);
	} catch (err) {
		$q.notify({
			type: "negative",
			message: err?.response?.data?.detail || "Не удалось создать организацию",
		});
	} finally {
		creating.value = false;
	}
}

function confirmDelete(org) {
	$q.dialog({
		title: "Удалить организацию?",
		message: `«${org.name}» и все связанные данные будут удалены.`,
		persistent: true,
		ok: {
			rounded: true,
			noCaps: true,
			unelevated: true,
			color: "negative",
			label: "Удалить",
			class: "wizard-btn wizard-btn--danger",
		},
		cancel: {
			rounded: true,
			noCaps: true,
			outline: true,
			color: "grey-7",
			label: "Отмена",
			class: "wizard-btn wizard-btn--outline",
			flat: false,
		},
	}).onOk(async () => {
		try {
			await organizationApi.delete(org.id);
			organizations.value = organizations.value.filter((o) => o.id !== org.id);
			$q.notify({ type: "positive", message: "Организация удалена" });
		} catch {
			$q.notify({ type: "negative", message: "Ошибка удаления" });
		}
	});
}

onMounted(load);
</script>

<style scoped>
.orgs-page {
	padding: 32px;
	max-width: 1400px;
	margin: 0 auto;
}

.page-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 24px;
	margin-bottom: 32px;
	flex-wrap: wrap;
}

.page-title {
	font-size: 32px;
	font-weight: 800;
	color: #0f172a;
	margin: 0 0 8px;
	letter-spacing: -0.02em;
}

.page-subtitle {
	font-size: 16px;
	color: #64748b;
	margin: 0;
	max-width: 520px;
}

.loading-state,
.empty-state {
	min-height: 320px;
	justify-content: center;
}

.empty-state__text {
	max-width: 360px;
}

.orgs-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 20px;
}

.org-card {
	border-radius: 20px;
	background: rgba(255, 255, 255, 0.9);
	backdrop-filter: blur(24px);
	border: 1px solid rgba(0, 0, 0, 0.06);
	cursor: pointer;
	transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
	min-height: 168px;
}

.org-card:hover {
	transform: translateY(-3px);
	box-shadow: 0 14px 36px rgba(80, 100, 247, 0.1);
	border-color: rgba(80, 100, 247, 0.28);
}

.org-card__icon-wrap {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
}

.create-card {
	border-style: dashed;
	border-color: rgba(80, 100, 247, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
	min-height: 168px;
}

.create-card:hover {
	border-color: rgba(80, 100, 247, 0.55);
	background: rgba(80, 100, 247, 0.03);
}

.create-card__icon {
	width: 56px;
	height: 56px;
	border-radius: 16px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
}

.empty-icon-wrap {
	width: 96px;
	height: 96px;
	border-radius: 24px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
}

@media (max-width: 640px) {
	.orgs-page {
		padding: 16px;
	}

	.page-header {
		flex-direction: column;
		align-items: stretch;
	}

	.page-header .wizard-btn {
		width: 100%;
	}
}
</style>
