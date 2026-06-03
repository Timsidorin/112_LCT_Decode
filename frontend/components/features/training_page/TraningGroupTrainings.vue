<template>
	<div class="training-page">
		<!-- Заголовок страницы -->
		<div class="page-header page-header--with-actions animate-fade-in-up">
			<div>
				<h1 class="page-title">Мои тренинги</h1>
				<p class="page-subtitle">Создавайте и управляйте обучающими материалами</p>
			</div>
			<div class="header-actions row items-center q-gutter-sm">
				<q-input outlined dense v-model="searchQuery" placeholder="Поиск..." class="search-input bg-white" color="primary" clearable>
					<template v-slot:prepend>
						<q-icon name="search" />
					</template>
				</q-input>
				<q-btn unelevated color="primary" icon="add" label="Создать" class="create-btn text-weight-bold shadow-4 q-px-md" @click="openCreateModal" />
			</div>
		</div>

		<!-- Фильтры -->
		<q-tabs v-model="filterTab" dense class="text-grey-7 q-mb-lg animate-fade-in-up" active-color="primary" indicator-color="primary" align="left" narrow-indicator>
			<q-tab name="all" label="Все" />
			<q-tab name="published" label="Опубликованные" />
			<q-tab name="drafts" label="Черновики" />
		</q-tabs>

		<!-- Состояние загрузки -->
		<div v-if="status" class="loading-state q-pa-xl column items-center justify-center">
			<q-spinner-dots size="48px" color="primary" class="loading-spinner" />
			<p class="text-grey-7 q-mt-md loading-text">Загрузка тренингов...</p>
		</div>

		<!-- Пустое состояние -->
		<div
			v-else-if="filteredTrainings.length === 0 && trainings.length === 0"
			class="empty-state q-pa-xl column items-center justify-center animate-scale-in"
		>
			<div class="empty-icon-wrap q-mb-lg">
				<q-icon name="school" size="64px" color="primary" />
			</div>
			<h3 class="text-h5 text-weight-bold text-dark q-mb-sm">Пока нет тренингов</h3>
			<p class="text-body1 text-grey-6 text-center q-mb-lg max-w-md">
				Создайте первый тренинг и начните обучать с помощью интерактивных скриншотов.
			</p>
			<q-btn
				unelevated
				no-caps
				color="primary"
				size="lg"
				icon="add"
				label="Создать тренинг"
				class="shadow-4 text-weight-bold q-px-xl"
				style="border-radius: 12px;"
				@click="openCreateModal"
			/>
		</div>

		<!-- Пустое состояние при поиске -->
		<div
			v-else-if="filteredTrainings.length === 0"
			class="empty-state q-pa-xl column items-center justify-center animate-scale-in"
		>
			<q-icon name="search_off" size="64px" color="grey-4" class="q-mb-md" />
			<h3 class="text-h6 text-weight-bold text-dark q-mb-sm">Ничего не найдено</h3>
			<p class="text-body2 text-grey-6 text-center">
				По вашему запросу не найдено ни одного тренинга.
			</p>
			<q-btn flat color="primary" label="Сбросить фильтры" class="q-mt-sm" @click="searchQuery = ''; filterTab = 'all'" />
		</div>

		<!-- Сетка карточек -->
		<div v-else class="trainings-grid q-pb-xl animate-stagger-children">
			<!-- Карточка создания -->
			<q-card v-if="filterTab === 'all' && !searchQuery" class="training-card create-card" flat bordered v-ripple @click="openCreateModal">
				<q-card-section class="create-card-section column items-center justify-center full-height text-center">
					<div class="create-icon-wrap">
						<q-icon name="add" size="36px" color="primary" />
					</div>
					<div class="text-h6 text-weight-bold text-primary q-mb-xs">Новый тренинг</div>
					<div class="text-body2 text-grey-6">Нажмите, чтобы создать</div>
				</q-card-section>
			</q-card>

			<!-- Карточки тренингов -->
			<q-card
				v-for="training in filteredTrainings"
				:key="training.uuid"
				class="training-card relative-position"
				flat
				bordered
				v-ripple
				@click="editTraining(training.uuid)"
			>
				<q-card-section class="card-content">
					<div class="row items-center justify-between q-mb-sm">
						<div class="status-pill" :class="training.publish ? 'status-published' : 'status-draft'">
							<div class="status-dot"></div>
							{{ training.publish ? 'Опубликован' : 'Черновик' }}
						</div>
						<q-btn-dropdown
							flat
							round
							dense
							color="grey-6"
							dropdown-icon="more_vert"
							class="training-card-menu-trigger"
							content-class="training-card-actions-menu"
							:menu-offset="[0, 8]"
							@click.stop
						>
							<q-list dense class="training-card-actions-list">
								<q-item clickable v-close-popup @click="editTraining(training.uuid)">
									<q-item-section avatar>
										<q-icon name="edit" size="sm" />
									</q-item-section>
									<q-item-section>Редактировать шаги</q-item-section>
								</q-item>
								<q-item clickable v-close-popup @click="openSettingsData(training)">
									<q-item-section avatar>
										<q-icon name="settings" size="sm" />
									</q-item-section>
									<q-item-section>Настройки</q-item-section>
								</q-item>
								<q-item clickable v-close-popup @click="openPublishModal(training)">
									<q-item-section avatar>
										<q-icon :name="training.publish ? 'share' : 'publish'" size="sm" color="primary" />
									</q-item-section>
									<q-item-section>{{ training.publish ? 'Поделиться' : 'Опубликовать' }}</q-item-section>
								</q-item>
								<q-item
									v-if="training.publish"
									clickable
									v-close-popup
									@click="openPassageStats(training)"
								>
									<q-item-section avatar>
										<q-icon name="bar_chart" size="sm" color="primary" />
									</q-item-section>
									<q-item-section>Статистика</q-item-section>
								</q-item>
								<q-item v-if="training.publish" clickable v-close-popup @click="confirmUnpublish(training)">
									<q-item-section avatar>
										<q-icon name="link_off" size="sm" color="grey-7" />
									</q-item-section>
									<q-item-section>Снять с публикации</q-item-section>
								</q-item>
								<q-separator class="q-my-xs" />
								<q-item clickable v-close-popup @click="confirmDelete(training)">
									<q-item-section avatar>
										<q-icon name="delete" size="sm" color="negative" />
									</q-item-section>
									<q-item-section class="text-negative">Удалить</q-item-section>
								</q-item>
							</q-list>
						</q-btn-dropdown>
					</div>

					<div class="text-h6 text-weight-bold text-dark ellipsis q-mb-xs" :title="training.title">{{ training.title }}</div>
					
					<div class="row items-center text-caption text-grey-6 q-mb-md q-gutter-x-md">
						<span class="row items-center"><q-icon name="layers" size="18px" class="q-mr-xs"/> {{ training.steps_count ?? training.steps?.length ?? 0 }} шагов</span>
						<span v-if="training.duration_minutes" class="row items-center"><q-icon name="schedule" size="18px" class="q-mr-xs"/> {{ training.duration_minutes }} мин</span>
						<span v-if="training.level" class="row items-center"><q-icon name="trending_up" size="18px" class="q-mr-xs"/> {{ training.level.label }}</span>
					</div>

					<p class="card-description text-body2 text-grey-7 ellipsis-2 q-mb-md">
						{{ training.description || 'Описание отсутствует. Добавьте его в настройках тренинга.' }}
					</p>

					<div class="row q-gutter-sm q-mt-auto">
						<q-badge
							v-for="tag in training.tags"
							:key="tag.value"
							class="badge-tag"
							:label="tag.label"
						/>
					</div>
				</q-card-section>
			</q-card>
		</div>
	</div>

	<training-modal v-model="modal" :mode="modalMode" :editData="editingTraining"/>
	<publish-modal-training
		v-model="publishModal"
		:data="publishTrainingData"
		@published="onPublished"
	/>

	<q-dialog v-model="passageStatsOpen">
		<q-card class="passage-stats-card" flat bordered>
			<q-card-section class="passage-stats-header row items-center no-wrap">
				<q-icon name="bar_chart" size="28px" color="primary" class="q-mr-sm passage-stats-header__icon" />
				<div class="col passage-stats-header__titles">
					<div class="text-h6">Статистика прохождений</div>
					<div
						v-if="passageStatsTraining"
						class="text-body2 text-grey-7 ellipsis q-mt-xs"
					>
						{{ passageStatsTraining.title }}
					</div>
				</div>
				<q-btn flat round dense icon="close" v-close-popup />
			</q-card-section>

			<q-separator />

			<q-card-section v-if="passageStatsLoading" class="passage-stats-loading column flex-center q-py-xl">
				<q-spinner-dots color="primary" size="40px" />
				<div class="text-body2 text-grey-7 q-mt-md">Загрузка…</div>
			</q-card-section>

			<template v-else>
				<q-card-section v-if="passageAnalytics" class="passage-stats-body">
					<div class="row q-col-gutter-sm">
						<div class="col-6 col-sm-3">
							<q-card flat bordered class="passage-stats-metric">
								<q-card-section class="q-pa-md">
									<div class="passage-stats-metric__label text-caption text-grey-7">Старты</div>
									<div class="passage-stats-metric__value text-h6 text-weight-bold text-grey-10">
										{{ passageAnalytics.total_starts }}
									</div>
								</q-card-section>
							</q-card>
						</div>
						<div class="col-6 col-sm-3">
							<q-card flat bordered class="passage-stats-metric">
								<q-card-section class="q-pa-md">
									<div class="passage-stats-metric__label text-caption text-grey-7">Завершения</div>
									<div class="passage-stats-metric__value text-h6 text-weight-bold text-grey-10">
										{{ passageAnalytics.total_completions }}
									</div>
								</q-card-section>
							</q-card>
						</div>
						<div class="col-6 col-sm-3">
							<q-card flat bordered class="passage-stats-metric">
								<q-card-section class="q-pa-md">
									<div class="passage-stats-metric__label text-caption text-grey-7">До конца</div>
									<div class="passage-stats-metric__value text-h6 text-weight-bold text-grey-10">
										{{ formatPercent(passageAnalytics.completion_rate) }}
									</div>
								</q-card-section>
							</q-card>
						</div>
						<div class="col-6 col-sm-3">
							<q-card flat bordered class="passage-stats-metric">
								<q-card-section class="q-pa-md">
									<div class="passage-stats-metric__label text-caption text-grey-7">Среднее время</div>
									<div class="passage-stats-metric__value text-h6 text-weight-bold text-grey-10">
										{{ formatDurationHuman(passageAnalytics.avg_duration_seconds) }}
									</div>
								</q-card-section>
							</q-card>
						</div>
					</div>
					<div class="q-mt-md">
						<div class="text-caption text-grey-7 q-mb-xs">Доля завершивших</div>
						<q-linear-progress
							:model-value="completionRateForRing / 100"
							color="primary"
							track-color="grey-3"
							size="4px"
							rounded
						/>
					</div>
				</q-card-section>

				<q-separator />

				<q-card-section class="passage-stats-history q-pb-lg">
					<div class="passage-stats-section-label q-mb-md">
						<q-icon name="history" size="18px" />
						<span>Последние попытки</span>
						<span
							v-if="passageHistory.length"
							class="text-caption text-grey-6 q-ml-sm"
						>
							({{ passageHistory.length }})
						</span>
					</div>

					<q-scroll-area
						v-if="passageHistory.length"
						class="passage-stats-table-wrap"
						:thumb-style="{ borderRadius: '4px', background: 'rgba(0,0,0,0.2)' }"
						:bar-style="{ borderRadius: '4px' }"
					>
						<q-markup-table flat bordered class="passage-stats-table" wrap-cells>
							<thead>
								<tr>
									<th class="text-left">Начало</th>
									<th class="text-left">Конец</th>
									<th class="text-center">Статус</th>
									<th class="text-right">Время</th>
									<th class="text-right">Ошибок</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="(row, idx) in passageHistory" :key="idx">
									<td class="text-body2 text-grey-9">{{ formatDt(row.started_at) }}</td>
									<td class="text-body2 text-grey-9">{{ formatDt(row.finished_at) }}</td>
									<td class="text-center text-body2">
										<span v-if="row.is_completed" class="text-positive">Завершено</span>
										<span v-else class="text-grey-7">Не завершено</span>
									</td>
									<td class="text-right text-body2 text-grey-9">
										{{ formatDurationHuman(row.duration_seconds) }}
									</td>
									<td class="text-right text-body2 text-grey-9">
										{{ row.wrong_attempts_total != null ? row.wrong_attempts_total : "—" }}
									</td>
								</tr>
							</tbody>
						</q-markup-table>
					</q-scroll-area>

					<q-card
						v-else
						flat
						class="passage-stats-empty bg-grey-3 q-pa-lg"
					>
						<div class="row items-start no-wrap">
							<q-icon name="info_outline" color="grey-7" size="22px" class="q-mr-md passage-stats-empty__lead-icon" />
							<div>
								<div class="text-subtitle2 text-grey-8 q-mb-xs">Пока нет записей</div>
								<div class="text-body2 text-grey-7">
									После прохождения тренинга по публичной ссылке здесь появится история попыток.
								</div>
							</div>
						</div>
					</q-card>
				</q-card-section>
			</template>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { TrainingApi } from "@api/api/TrainingApi.js";
import { computed, onMounted, ref, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useQuasar } from "quasar";
import { trainingEvents } from "@utils/eventBus.js";
import TrainingModal from "@components/features/training_page/TrainingModal.vue";
import PublishModalTraining from "@components/features/training_page/PublishModalTraining.vue";

const router = useRouter();
const $q = useQuasar();
const trainings = ref([]);
const api = new TrainingApi();
const status = ref(true);
const modal = ref(false);
const modalMode = ref("create");
const editingTraining = ref(null);
const publishModal = ref(false);
const publishTrainingData = ref(null);

const searchQuery = ref("");
const filterTab = ref("all");

const filteredTrainings = computed(() => {
	let result = trainings.value;
	
	if (filterTab.value === 'published') {
		result = result.filter(t => t.publish);
	} else if (filterTab.value === 'drafts') {
		result = result.filter(t => !t.publish);
	}
	
	if (searchQuery.value) {
		const q = searchQuery.value.toLowerCase();
		result = result.filter(t => 
			t.title.toLowerCase().includes(q) || 
			(t.description && t.description.toLowerCase().includes(q))
		);
	}
	
	return result;
});

function openCreateModal() {
	modalMode.value = "create";
	editingTraining.value = null;
	modal.value = true;
}

function openSettingsData(training) {
	modalMode.value = "edit";
	editingTraining.value = training;
	modal.value = true;
}

const passageStatsOpen = ref(false);
const passageStatsLoading = ref(false);
const passageStatsTraining = ref(null);
const passageAnalytics = ref(null);
const passageHistory = ref([]);

const completionRateForRing = computed(() => {
	const a = passageAnalytics.value;
	if (!a || a.completion_rate == null || Number.isNaN(a.completion_rate)) return 0;
	return Math.min(100, Math.max(0, a.completion_rate * 100));
});

function formatPercent(rate) {
	if (rate == null || Number.isNaN(rate)) return "—";
	return `${Math.round(rate * 1000) / 10}%`;
}

function formatDurationHuman(sec) {
	if (sec == null || Number.isNaN(Number(sec))) return "—";
	const s = Math.floor(Number(sec));
	if (s < 60) return `${s} с`;
	const m = Math.floor(s / 60);
	const r = s % 60;
	if (m < 60) return `${m} мин ${r > 0 ? `${r} с` : ""}`.trim();
	const h = Math.floor(m / 60);
	const mm = m % 60;
	return `${h} ч ${mm} мин`;
}

function formatDt(iso) {
	if (!iso) return "—";
	try {
		return new Date(iso).toLocaleString("ru-RU", {
			day: "2-digit",
			month: "2-digit",
			year: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	} catch {
		return "—";
	}
}

async function openPassageStats(training) {
	passageStatsTraining.value = training;
	passageAnalytics.value = null;
	passageHistory.value = [];
	passageStatsOpen.value = true;
	passageStatsLoading.value = true;
	try {
		const [anRes, histRes] = await Promise.all([
			api.getPassageAnalytics(training.uuid),
			api.getPassageHistory(training.uuid, { skip: 0, limit: 20 }),
		]);
		passageAnalytics.value = anRes.data;
		passageHistory.value = Array.isArray(histRes.data) ? histRes.data : [];
	} catch (e) {
		console.error(e);
		$q.notify({
			message: "Не удалось загрузить статистику",
			type: "negative",
			position: "top",
		});
		passageStatsOpen.value = false;
	} finally {
		passageStatsLoading.value = false;
	}
}

async function getTrainings() {
	try {
		status.value = true;
		trainings.value = [];
		const response = await api.getTrainings();
		trainings.value = response.data;
	} catch (e) {
		console.error(e);
		$q.notify({
			message: "Ошибка получения списка тренингов",
			position: "top",
			type: "negative",
		});
	} finally {
		status.value = false;
	}
}

function openPublishModal(training) {
	publishModal.value = true;
	publishTrainingData.value = training;
}

async function onPublished() {
	await getTrainings();
}

function confirmUnpublish(training) {
	$q.dialog({
		title: "Снять с публикации?",
		message: `Ссылка на тренинг «${training.title}» перестанет работать. Вы сможете опубликовать его снова и получить новую ссылку.`,
		cancel: { label: "Отмена", flat: true },
		ok: { label: "Снять", color: "primary", flat: true },
		persistent: true,
	}).onOk(async () => {
		await unpublishTraining(training.uuid);
	});
}

async function unpublishTraining(uuid) {
	try {
		await api.unpublishTraining(uuid);
		$q.notify({
			message: "Тренинг снят с публикации",
			type: "positive",
			position: "top-right",
		});
		await getTrainings();
	} catch (e) {
		console.error(e);
		$q.notify({
			message: "Не удалось снять с публикации",
			type: "negative",
			position: "top",
		});
	}
}

function confirmDelete(training) {
	$q.dialog({
		title: "Удалить тренинг?",
		message: `Тренинг «${training.title}» будет удалён без возможности восстановления.`,
		cancel: { label: "Отмена", flat: true },
		ok: { label: "Удалить", color: "negative", flat: true },
		persistent: true,
	}).onOk(async () => {
		await deleteTraining(training.uuid);
	});
}

async function deleteTraining(uuid) {
	try {
		await api.deleteTraining(uuid);
		$q.notify({
			message: "Тренинг успешно удалён",
			type: "positive",
			position: "top-right",
		});
		await getTrainings();
	} catch (e) {
		console.error(e);
		$q.notify({
			message: "Не удалось удалить тренинг",
			type: "negative",
			position: "top",
		});
	}
}

function editTraining(uuid) {
	const route = router.resolve(`/edit/${uuid}`);
	window.open(route.href, "_blank");
}

const unsubscribe = trainingEvents.created.on(() => {
	getTrainings();
});

onMounted(() => {
	getTrainings();
});

onUnmounted(() => {
	unsubscribe.off();
});
</script>

<style scoped>
.training-page {
	min-height: 60vh;
	max-width: 1400px;
	margin: 0 auto;
	padding: 32px 40px 24px;
}

/* ——— Header ——— */
.page-header {
	margin-bottom: 32px;
	position: relative;
	z-index: 2;
}

.page-header--with-actions {
	display: flex;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 16px;
}

.page-title {
	font-size: 32px;
	font-weight: 800;
	color: #0f172a;
	margin: 0 0 8px 0;
	letter-spacing: -0.02em;
	line-height: 1.2;
}

.page-subtitle {
	font-size: 16px;
	color: #64748b;
	margin: 0;
	font-weight: 500;
	line-height: 1.5;
}

.search-input {
	width: 260px;
}
.search-input :deep(.q-field__control) {
	border-radius: 12px;
}

.create-btn {
	border-radius: 12px;
	height: 40px;
}

.loading-state {
	position: relative;
	z-index: 2;
}

.empty-icon-wrap {
	width: 120px;
	height: 120px;
	border-radius: 32px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
}

.empty-state {
	position: relative;
	z-index: 2;
}

.max-w-md {
	max-width: 400px;
}

.trainings-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
	gap: 24px;
	position: relative;
	z-index: 2;
}

.training-card {
	border-radius: 20px;
	cursor: pointer;
	transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
	border: 1px solid rgba(0, 0, 0, 0.06);
	background: rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	display: flex;
	flex-direction: column;
	height: 250px;
	box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.training-card:hover {
	transform: translateY(-6px);
	box-shadow: 0 20px 40px rgba(15, 23, 42, 0.06);
	border-color: rgba(255, 255, 255, 1);
	background: rgba(255, 255, 255, 0.9);
}

.card-content {
	padding: 24px;
	flex: 1;
	display: flex;
	flex-direction: column;
}

.status-pill {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 12px;
	border-radius: 10px;
	font-size: 13px;
	font-weight: 600;
	letter-spacing: 0.02em;
}

.status-dot {
	width: 6px;
	height: 6px;
	border-radius: 50%;
}

.status-published {
	background: #ecfdf5;
	color: #059669;
	border: 1px solid #d1fae5;
}
.status-published .status-dot {
	background: #10b981;
	box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.status-draft {
	background: #f8fafc;
	color: #475569;
	border: 1px solid #e2e8f0;
}
.status-draft .status-dot {
	background: #94a3b8;
}

.training-card-menu-trigger {
	margin-right: -8px;
	margin-top: -4px;
	opacity: 0.88;
	transition: opacity 0.2s ease, background 0.2s ease;
}

.card-description {
	line-height: 1.5;
	flex: 1;
}

.badge-tag {
	background: #f1f5f9;
	color: #475569;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	padding: 6px 12px;
	font-size: 13px;
	font-weight: 500;
}

.create-card {
	background: rgba(255, 255, 255, 0.5);
	border: 2px dashed rgba(15, 23, 42, 0.15);
	box-shadow: none;
	backdrop-filter: none;
	-webkit-backdrop-filter: none;
}

.create-card:hover {
	border-color: rgba(80, 100, 247, 0.6);
	background: rgba(239, 246, 255, 0.6);
	box-shadow: none;
}

.create-icon-wrap {
	width: 64px;
	height: 64px;
	border-radius: 20px;
	background: #ffffff;
	box-shadow: 0 4px 12px rgba(0,0,0,0.05);
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16px;
	transition: transform 0.3s var(--anim-ease-spring);
}

.create-card:hover .create-icon-wrap {
	transform: scale(1.1);
	background: #5064f7;
	color: #ffffff !important;
}
.create-card:hover .create-icon-wrap .q-icon {
	color: #ffffff !important;
}

/* В духе TrainingModal / PublishModal: спокойно, без ярких градиентов */
.passage-stats-card {
	min-width: min(480px, 94vw);
	max-width: 700px;
	width: 100%;
	border-radius: 18px;
	overflow: hidden;
	box-shadow: 0 24px 56px rgba(0, 0, 0, 0.14);
	border-color: rgba(0, 0, 0, 0.08) !important;
}

.passage-stats-header {
	padding: 20px 24px;
	background: linear-gradient(135deg, rgba(80, 100, 247, 0.04) 0%, rgba(80, 100, 247, 0.01) 100%);
}

.passage-stats-header__icon {
	flex-shrink: 0;
}

.passage-stats-header__titles {
	min-width: 0;
}

.passage-stats-header .text-h6 {
	color: #1a1a2e;
	font-weight: 700;
	letter-spacing: -0.01em;
}

.passage-stats-loading {
	min-height: 200px;
}

.passage-stats-body {
	padding: 20px 24px 16px;
}

.passage-stats-metric {
	border-radius: 12px;
	border-color: rgba(0, 0, 0, 0.08) !important;
	background: #fff;
}

.passage-stats-metric__label {
	letter-spacing: 0.02em;
}

.passage-stats-metric__value {
	margin-top: 6px;
	line-height: 1.25;
	word-break: break-word;
}

.passage-stats-section-label {
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 13px;
	font-weight: 600;
	color: #374151;
}

.passage-stats-section-label .q-icon {
	opacity: 0.85;
	color: #5064f7;
}

.passage-stats-history {
	padding: 20px 24px 24px;
}

.passage-stats-table-wrap {
	height: min(260px, 40vh);
	border-radius: 12px;
	overflow: hidden;
	border: 1px solid rgba(0, 0, 0, 0.08);
}

.passage-stats-table {
	background: #fff;
}

.passage-stats-table thead tr {
	background: #f3f4f6;
}

.passage-stats-table thead th {
	font-size: 12px;
	font-weight: 600;
	color: #6b7280;
	padding: 10px 12px;
	border-color: rgba(0, 0, 0, 0.06);
}

.passage-stats-table tbody td {
	padding: 10px 12px;
	border-color: rgba(0, 0, 0, 0.06);
	vertical-align: middle;
}

.passage-stats-table tbody tr:nth-child(even) {
	background: rgba(249, 250, 251, 0.9);
}

.passage-stats-empty {
	border-radius: 12px;
	border: 1px solid rgba(0, 0, 0, 0.06);
}

.passage-stats-empty__lead-icon {
	flex-shrink: 0;
}

.training-card-menu-trigger:hover {
	opacity: 1;
	background: rgba(0, 0, 0, 0.05) !important;
}

@media (max-width: 768px) {
	.training-page {
		padding: 24px 16px 20px;
	}
	.page-header {
		margin-bottom: 24px;
	}
	.page-title {
		font-size: 26px;
	}
	.page-subtitle {
		font-size: 14px;
	}
}
</style>

/* Меню рендерится в портале — стили без scoped */
<style>
.training-card-actions-menu {
	border-radius: 14px !important;
	padding: 8px 0 !important;
	background: #fff !important;
	border: 1px solid rgba(26, 26, 46, 0.1) !important;
	box-shadow: 0 16px 48px rgba(26, 26, 46, 0.12), 0 4px 12px rgba(0, 0, 0, 0.06) !important;
	overflow: hidden;
}

.training-card-actions-menu .training-card-actions-list {
	min-width: 208px;
	padding: 0;
}

.training-card-actions-menu .q-item {
	min-height: 42px;
	padding: 8px 14px;
	margin: 2px 10px;
	border-radius: 10px;
	font-size: 14px;
	font-weight: 500;
	color: #1a1a2e;
	transition: background 0.15s ease, color 0.15s ease;
}

.training-card-actions-menu .q-item:hover {
	background: rgba(80, 100, 247, 0.08) !important;
}

.training-card-actions-menu .q-item__section--avatar {
	min-width: 40px;
}

.training-card-actions-menu .q-item__section--avatar .q-icon {
	opacity: 0.9;
}

.training-card-actions-menu .q-separator {
	margin: 6px 14px;
	background: rgba(26, 26, 46, 0.08) !important;
}
</style>