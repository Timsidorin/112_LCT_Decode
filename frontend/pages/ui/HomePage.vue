<template>
	<div class="home-page">
		<div class="home-inner">
			<div class="home-hero-wrapper animate-fade-in-down">
				<header class="home-hero">
					<div class="home-hero__row">
						<q-avatar
							v-if="userStore.isYandexUser"
							size="80px"
							class="home-hero__avatar"
						>
							<img
								v-if="userStore.photo"
								:src="userStore.photo"
								alt=""
							/>
							<img
								v-else
								src="/icons/yandex.svg"
								alt=""
								class="home-hero__yandex-fallback"
							/>
						</q-avatar>
						<div class="home-hero__text">
							<h1 class="home-hero__title">
								Добро пожаловать, {{ userStore.fullName }}
							</h1>
							<p class="home-hero__subtitle">
								Управляйте тренингами и следите за прогрессом
							</p>
						</div>
					</div>
				</header>
			</div>

			<div v-if="loading" class="home-loading">
				<q-spinner-dots size="48px" color="primary" class="home-loading__spinner" />
				<p class="home-loading__text">Загрузка...</p>
			</div>

			<div v-else class="home-stack animate-stagger-children">
				<!-- Сводка -->
				<section class="home-panel" aria-labelledby="home-summary-heading">
					<div class="home-panel__head">
						<h2 id="home-summary-heading" class="home-panel__title">
							<q-icon name="insights" size="20px" class="home-panel__title-icon" />
							Сводка
						</h2>
					</div>
					<div class="stats-grid">
						<div class="stat-card">
							<div class="stat-icon">
								<q-icon name="school" size="24px" />
							</div>
							<div class="stat-content">
								<div class="stat-value">{{ stats.totalTrainings }}</div>
								<div class="stat-label">Всего тренингов</div>
							</div>
						</div>
						<div class="stat-card stat-card--success">
							<div class="stat-icon">
								<q-icon name="check_circle" size="24px" />
							</div>
							<div class="stat-content">
								<div class="stat-value">{{ stats.publishedTrainings }}</div>
								<div class="stat-label">Опубликовано</div>
							</div>
						</div>
						<div class="stat-card stat-card--draft">
							<div class="stat-icon">
								<q-icon name="edit_note" size="24px" />
							</div>
							<div class="stat-content">
								<div class="stat-value">{{ stats.draftTrainings }}</div>
								<div class="stat-label">Черновиков</div>
							</div>
						</div>
					</div>
				</section>

				<!-- Быстрые действия -->
				<section class="home-panel" aria-labelledby="home-actions-heading">
					<div class="home-panel__head">
						<h2 id="home-actions-heading" class="home-panel__title">
							<q-icon name="bolt" size="20px" class="home-panel__title-icon" />
							Быстрые действия
						</h2>
					</div>
					<div class="quick-actions">
						<div
							class="action-item"
							role="button"
							tabindex="0"
							@click="$router.push('/personal/training')"
							@keydown.enter="$router.push('/personal/training')"
						>
							<div class="action-icon">
								<q-icon name="add_circle_outline" />
							</div>
							<div class="action-content">
								<div class="action-title">Создать тренинг</div>
								<div class="action-desc">Добавить новый интерактивный тренинг</div>
							</div>
							<q-icon name="arrow_forward" size="20px" class="action-arrow" />
						</div>
						<div
							class="action-item"
							role="button"
							tabindex="0"
							@click="$router.push('/personal/library')"
							@keydown.enter="$router.push('/personal/library')"
						>
							<div class="action-icon">
								<q-icon name="library_books" />
							</div>
							<div class="action-content">
								<div class="action-title">Библиотека</div>
								<div class="action-desc">Каталог всех тренингов</div>
							</div>
							<q-icon name="arrow_forward" size="20px" class="action-arrow" />
						</div>
						<div
							class="action-item"
							role="button"
							tabindex="0"
							@click="$router.push('/personal/courses')"
							@keydown.enter="$router.push('/personal/courses')"
						>
							<div class="action-icon">
								<q-icon name="school" />
							</div>
							<div class="action-content">
								<div class="action-title">Мои курсы</div>
								<div class="action-desc">Собрать и управлять курсами</div>
							</div>
							<q-icon name="arrow_forward" size="20px" class="action-arrow" />
						</div>
					</div>
				</section>

				<!-- Недавние или пустое состояние -->
				<section
					v-if="recentTrainings.length > 0"
					class="home-panel home-panel--grow"
					aria-labelledby="home-recent-heading"
				>
					<div class="home-panel__head">
						<h2 id="home-recent-heading" class="home-panel__title">
							<q-icon name="history" size="20px" class="home-panel__title-icon" />
							Недавние тренинги
						</h2>
						<q-btn
							flat
							dense
							no-caps
							color="primary"
							label="Все тренинги"
							to="/personal/training"
							class="home-panel__link"
						/>
					</div>
					<div class="trainings-grid">
						<div
							v-for="training in recentTrainings"
							:key="training.uuid"
							class="training-card"
							@click="openEdit(training.uuid)"
						>
							<div class="training-header">
								<div class="training-title">{{ training.title }}</div>
								<div
									class="training-status"
									:class="training.publish ? 'training-status--published' : 'training-status--draft'"
								>
									{{ training.publish ? "Опубликован" : "Черновик" }}
								</div>
							</div>
							<div class="training-meta">
								<div class="training-meta-item">
									<q-icon name="layers" size="16px" />
									<span>{{ training.steps?.length || 0 }} шагов</span>
								</div>
							</div>
						</div>
					</div>
				</section>

				<section
					v-else
					class="home-panel home-panel--empty animate-scale-in"
					aria-labelledby="home-empty-heading"
				>
					<div class="empty-inner">
						<div class="empty-icon" aria-hidden="true">
							<q-icon name="school" size="48px" />
						</div>
						<h2 id="home-empty-heading" class="empty-title">У вас пока нет тренингов</h2>
						<p class="empty-desc">Создайте первый тренинг, чтобы начать работу</p>
						<q-btn
							unelevated
							no-caps
							color="primary"
							icon="add"
							label="Создать тренинг"
							class="empty-btn"
							@click="$router.push('/personal/training')"
						/>
					</div>
				</section>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@store/userData.js";
import { TrainingApi } from "@api";

const router = useRouter();
const userStore = useUserStore();
const trainingApi = new TrainingApi();
const loading = ref(true);
const trainings = ref([]);

const stats = computed(() => ({
	totalTrainings: trainings.value.length,
	publishedTrainings: trainings.value.filter((t) => t.publish).length,
	draftTrainings: trainings.value.filter((t) => !t.publish).length,
}));

const recentTrainings = computed(() => trainings.value.slice(0, 6));

function openEdit(uuid) {
	const route = router.resolve(`/edit/${uuid}`);
	window.open(route.href, "_blank");
}

onMounted(async () => {
	try {
		const { data } = await trainingApi.getTrainings();
		trainings.value = data || [];
	} catch {
		trainings.value = [];
	} finally {
		loading.value = false;
	}
});
</script>

<style scoped>
.home-page {
	padding: 0;
	min-height: 100%;
	box-sizing: border-box;
	background: transparent;
}

.home-inner {
	width: 100%;
	max-width: 1400px;
	margin: 0 auto;
	padding: 32px 32px 48px;
}

/* ——— Hero ——— */
.home-hero-wrapper {
	background: rgba(255, 255, 255, 0.55);
	backdrop-filter: blur(24px);
	-webkit-backdrop-filter: blur(24px);
	border: 1px solid rgba(255, 255, 255, 0.8);
	border-radius: 24px;
	padding: 40px 32px;
	margin-bottom: 32px;
	box-shadow: 0 8px 32px rgba(31, 38, 135, 0.05);
	color: #1a1a2e;
}

.home-hero {
	width: 100%;
}

.home-hero__row {
	display: flex;
	align-items: center;
	gap: 24px;
	flex-wrap: wrap;
}

.home-hero__avatar {
	flex-shrink: 0;
	border: 4px solid rgba(255, 255, 255, 0.8);
	box-shadow: 0 8px 24px rgba(80, 100, 247, 0.15);
	background: white;
}

.home-hero__avatar img {
	object-fit: cover;
	width: 100%;
	height: 100%;
}

.home-hero__yandex-fallback {
	padding: 12px;
	object-fit: contain !important;
	background: #fff;
}

.home-hero__text {
	min-width: 0;
	flex: 1;
}

.home-hero__title {
	font-size: 32px;
	font-weight: 800;
	color: #1a1a2e;
	margin: 0 0 8px 0;
	letter-spacing: -0.02em;
	line-height: 1.2;
}

.home-hero__subtitle {
	font-size: 16px;
	color: #64748b;
	margin: 0;
	font-weight: 500;
	line-height: 1.5;
	max-width: 40em;
}

/* ——— Loading ——— */
.home-loading {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 80px 0;
	gap: 20px;
}

.home-loading__spinner {
	animation: pulse-soft 1.2s var(--anim-ease-in-out) infinite;
}

.home-loading__text {
	font-size: 16px;
	color: #64748b;
	margin: 0;
	font-weight: 500;
}

/* ——— Stack & panels ——— */
.home-stack {
	display: flex;
	flex-direction: column;
	gap: 32px;
}

.home-panel {
	background: #ffffff;
	border: 1px solid rgba(226, 232, 240, 0.8);
	border-radius: 20px;
	padding: 28px 32px;
	box-shadow: 0 4px 20px rgba(15, 23, 42, 0.03);
	transition: box-shadow 0.3s ease;
}

.home-panel:hover {
	box-shadow: 0 8px 30px rgba(15, 23, 42, 0.06);
}

.home-panel--grow {
	flex: 1;
	min-height: 0;
}

.home-panel__head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16px;
	margin-bottom: 24px;
	flex-wrap: wrap;
}

.home-panel__title {
	display: flex;
	align-items: center;
	gap: 10px;
	margin: 0;
	font-size: 16px;
	font-weight: 700;
	color: #1e293b;
	letter-spacing: 0.02em;
}

.home-panel__title-icon {
	color: #5064f7;
	background: rgba(80, 100, 247, 0.1);
	padding: 6px;
	border-radius: 8px;
}

.home-panel__link {
	font-size: 14px;
	font-weight: 600;
	margin: -4px -8px -4px 0;
	border-radius: 8px;
}

/* ——— Stats ——— */
.stats-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 20px;
}

.stat-card {
	background: #ffffff;
	border: 1px solid #e2e8f0;
	border-radius: 16px;
	padding: 20px;
	display: flex;
	align-items: center;
	gap: 16px;
	transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
	position: relative;
	overflow: hidden;
}

.stat-card::before {
	content: '';
	position: absolute;
	top: 0;
	left: 0;
	width: 4px;
	height: 100%;
	background: #5064f7;
	opacity: 0;
	transition: opacity 0.25s ease;
}

.stat-card:hover {
	border-color: #cbd5e1;
	transform: translateY(-2px);
	box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
}

.stat-card:hover::before {
	opacity: 1;
}

.stat-card--success::before { background: #10b981; }
.stat-card--draft::before { background: #64748b; }

.stat-icon {
	width: 48px;
	height: 48px;
	border-radius: 12px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	color: #5064f7;
	flex-shrink: 0;
}

.stat-card--success .stat-icon {
	background: rgba(16, 185, 129, 0.12);
	color: #059669;
}

.stat-card--draft .stat-icon {
	background: rgba(148, 163, 184, 0.15);
	color: #64748b;
}

.stat-content {
	flex: 1;
	min-width: 0;
}

.stat-value {
	font-size: 28px;
	font-weight: 800;
	color: #0f172a;
	line-height: 1.1;
	margin-bottom: 4px;
}

.stat-label {
	font-size: 13px;
	color: #64748b;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

/* ——— Quick actions ——— */
.quick-actions {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 20px;
}

.action-item {
	background: #ffffff;
	border: 1px solid #e2e8f0;
	border-radius: 16px;
	padding: 20px;
	display: flex;
	align-items: center;
	gap: 16px;
	cursor: pointer;
	transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
	outline: none;
}

.action-item:hover,
.action-item:focus-visible {
	border-color: #5064f7;
	background: #f8fafc;
	transform: translateY(-2px);
	box-shadow: 0 10px 25px rgba(80, 100, 247, 0.1);
}

.action-item:focus-visible {
	box-shadow: 0 0 0 3px rgba(80, 100, 247, 0.3);
}

.action-item:hover .action-arrow,
.action-item:focus-visible .action-arrow {
	transform: translateX(4px);
	color: #5064f7;
}

.action-icon {
	width: 52px;
	height: 52px;
	border-radius: 14px;
	background: rgba(80, 100, 247, 0.08);
	display: flex;
	align-items: center;
	justify-content: center;
	color: #5064f7;
	flex-shrink: 0;
	transition: background 0.25s ease, color 0.25s ease;
}

.action-item:hover .action-icon {
	background: #5064f7;
	color: white;
}

.action-icon .q-icon {
	font-size: 24px;
}

.action-content {
	flex: 1;
	min-width: 0;
}

.action-title {
	font-size: 15px;
	font-weight: 700;
	color: #0f172a;
	margin-bottom: 4px;
}

.action-desc {
	font-size: 13px;
	color: #64748b;
	line-height: 1.4;
}

.action-arrow {
	color: #cbd5e1;
	transition: transform 0.25s ease, color 0.25s ease;
	flex-shrink: 0;
}

/* ——— Recent trainings ——— */
.trainings-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
	gap: 20px;
}

.training-card {
	background: #ffffff;
	border: 1px solid #e2e8f0;
	border-radius: 16px;
	padding: 20px;
	cursor: pointer;
	transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
	display: flex;
	flex-direction: column;
	height: 100%;
}

.training-card:hover {
	border-color: #5064f7;
	box-shadow: 0 12px 30px rgba(80, 100, 247, 0.08);
	transform: translateY(-3px);
}

.training-header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 12px;
	margin-bottom: 16px;
	flex: 1;
}

.training-title {
	flex: 1;
	font-size: 15px;
	font-weight: 700;
	color: #0f172a;
	line-height: 1.4;
	overflow: hidden;
	text-overflow: ellipsis;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
}

.training-status {
	font-size: 11px;
	font-weight: 700;
	padding: 4px 10px;
	border-radius: 20px;
	white-space: nowrap;
	flex-shrink: 0;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

.training-status--published {
	background: rgba(16, 185, 129, 0.1);
	color: #059669;
}

.training-status--draft {
	background: rgba(100, 116, 139, 0.1);
	color: #475569;
}

.training-meta {
	display: flex;
	align-items: center;
	gap: 16px;
	padding-top: 16px;
	border-top: 1px solid #f1f5f9;
	margin-top: auto;
}

.training-meta-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 13px;
	font-weight: 500;
	color: #64748b;
}

/* ——— Empty ——— */
.home-panel--empty {
	padding: 60px 32px;
	background: #f8fafc;
	border: 2px dashed #e2e8f0;
}

.empty-inner {
	max-width: 420px;
	margin: 0 auto;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-icon {
	width: 88px;
	height: 88px;
	border-radius: 24px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	color: #5064f7;
	margin-bottom: 24px;
	box-shadow: 0 8px 24px rgba(80, 100, 247, 0.15);
}

.empty-title {
	font-size: 20px;
	font-weight: 700;
	color: #0f172a;
	margin: 0 0 12px 0;
}

.empty-desc {
	font-size: 15px;
	color: #64748b;
	margin: 0 0 28px 0;
	line-height: 1.5;
}

.empty-btn {
	border-radius: 12px;
	padding: 12px 28px;
	font-weight: 600;
	font-size: 15px;
	box-shadow: 0 4px 12px rgba(80, 100, 247, 0.25);
}

/* ——— Responsive ——— */
@media (max-width: 1024px) {
	.stats-grid, .quick-actions {
		grid-template-columns: repeat(2, 1fr);
	}
}

@media (max-width: 768px) {
	.home-inner {
		padding: 24px 24px 32px;
	}
	
	.home-hero-wrapper {
		padding: 32px 24px;
	}
	
	.home-hero__title {
		font-size: 26px;
	}
}

@media (max-width: 640px) {
	.home-inner {
		padding: 16px 16px 24px;
	}

	.home-hero-wrapper {
		padding: 24px 16px;
	}
	
	.home-hero__row {
		flex-direction: column;
		text-align: center;
		gap: 16px;
	}

	.home-hero__title {
		font-size: 22px;
	}

	.stats-grid, .quick-actions {
		grid-template-columns: 1fr;
	}

	.trainings-grid {
		grid-template-columns: 1fr;
	}
	
	.home-panel {
		padding: 20px;
	}
}
</style>
