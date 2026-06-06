<template>
	<div class="course-page">
		<div class="page-header page-header--with-actions animate-fade-in-up">
			<div>
				<h1 class="page-title">Мои курсы</h1>
				<p class="page-subtitle">Собирайте курсы из существующих тренингов и запускайте прохождение</p>
			</div>
			<div class="header-actions row items-center q-gutter-sm">
				<q-input
					outlined
					dense
					v-model="searchQuery"
					placeholder="Поиск курса..."
					class="search-input bg-white"
					color="primary"
					clearable
				>
					<template #prepend><q-icon name="search" /></template>
				</q-input>
				<q-btn
					unelevated
					color="primary"
					icon="add"
					label="Создать"
					class="create-btn btn-rounded text-weight-bold shadow-4 q-px-md"
					@click="openCreateModal"
				/>
			</div>
		</div>

		<q-tabs
			v-model="filterTab"
			dense
			class="text-grey-7 q-mb-lg animate-fade-in-up"
			active-color="primary"
			indicator-color="primary"
			align="left"
			narrow-indicator
		>
			<q-tab name="all" label="Все" />
			<q-tab name="published" label="С опубликованными" />
			<q-tab name="draft" label="Черновые" />
		</q-tabs>

		<div v-if="loading" class="loading-state q-pa-xl column items-center justify-center">
			<q-spinner-dots size="48px" color="primary" class="loading-spinner" />
			<p class="text-grey-7 q-mt-md loading-text">Загрузка курсов...</p>
		</div>

		<div
			v-else-if="courses.length === 0"
			class="empty-state q-pa-xl column items-center justify-center animate-scale-in"
		>
			<div class="empty-icon-wrap q-mb-lg">
				<q-icon name="school" size="64px" color="primary" />
			</div>
			<h3 class="text-h5 text-weight-bold text-dark q-mb-sm">Пока нет курсов</h3>
			<p class="text-body1 text-grey-6 text-center q-mb-lg max-w-md">
				Создайте курс и добавьте в него нужные тренинги.
			</p>
			<q-btn
				unelevated
				no-caps
				color="primary"
				size="lg"
				icon="add"
				label="Создать курс"
				class="shadow-4 text-weight-bold q-px-xl"
				style="border-radius: 12px;"
				@click="openCreateModal"
			/>
		</div>

		<div
			v-else-if="filteredCourses.length === 0"
			class="empty-state q-pa-xl column items-center justify-center animate-scale-in"
		>
			<q-icon name="search_off" size="64px" color="grey-4" class="q-mb-md" />
			<h3 class="text-h6 text-weight-bold text-dark q-mb-sm">Ничего не найдено</h3>
			<p class="text-body2 text-grey-6 text-center">
				По вашему запросу курсы не найдены.
			</p>
			<q-btn flat color="primary" label="Сбросить фильтры" class="q-mt-sm" @click="resetFilters" />
		</div>

		<div v-else class="courses-grid q-pb-xl animate-stagger-children">
			<q-card class="course-card create-card" flat bordered v-ripple @click="openCreateModal">
				<q-card-section class="create-card-section column items-center justify-center full-height text-center">
					<div class="create-icon-wrap">
						<q-icon name="add" size="36px" color="primary" />
					</div>
					<div class="text-h6 text-weight-bold text-primary q-mb-xs">Новый курс</div>
					<div class="text-body2 text-grey-6">Нажмите, чтобы создать</div>
				</q-card-section>
			</q-card>

			<q-card
				v-for="course in filteredCourses"
				:key="course.id"
				class="course-card relative-position"
				flat
				bordered
				v-ripple
				@click="openDetails(course)"
			>
				<q-card-section class="card-content">
					<div class="row items-center justify-between q-mb-sm">
						<div class="status-pill" :class="courseStatusClass(course)">
							<div class="status-dot"></div>
							{{ courseStatusLabel(course) }}
						</div>
						<q-btn
							flat
							round
							dense
							color="negative"
							icon="delete"
							@click.stop="confirmDelete(course)"
						/>
					</div>

					<div class="text-h6 text-weight-bold text-dark ellipsis q-mb-xs" :title="course.title">
						{{ course.title }}
					</div>

					<div class="row items-center text-caption text-grey-6 q-mb-md q-gutter-x-md">
						<span class="row items-center">
							<q-icon name="menu_book" size="18px" class="q-mr-xs" />
							{{ course.trainings?.length || 0 }} тренингов
						</span>
						<span class="row items-center">
							<q-icon name="public" size="18px" class="q-mr-xs" />
							{{ publishedCount(course) }} опублик.
						</span>
					</div>

					<p class="card-description text-body2 text-grey-7 ellipsis-2 q-mb-md">
						{{ course.description || "Описание отсутствует." }}
					</p>

					<div class="row q-gutter-sm q-mt-auto">
						<q-badge
							v-for="training in (course.trainings || []).slice(0, 3)"
							:key="training.uuid"
							class="badge-tag"
							:label="training.title"
						/>
						<q-badge
							v-if="(course.trainings?.length || 0) > 3"
							class="badge-tag badge-tag--more"
							:label="`+${course.trainings.length - 3}`"
						/>
					</div>
				</q-card-section>
				<q-separator />
				<q-card-actions class="justify-between q-px-md q-py-sm">
					<span class="text-caption text-grey-6">Создан: {{ formatDate(course.created_at) }}</span>
					<span class="row items-center text-caption text-primary text-weight-medium">
						<q-icon name="visibility" size="16px" class="q-mr-xs" />
						Открыть
					</span>
				</q-card-actions>
			</q-card>
		</div>
	</div>

	<q-dialog v-model="createModal">
		<q-card class="course-modal" flat bordered>
			<q-card-section class="row items-center no-wrap">
				<div class="text-h6">Новый курс</div>
				<q-space />
				<q-btn icon="close" flat round dense v-close-popup />
			</q-card-section>
			<q-separator />
			<q-card-section>
				<q-input v-model.trim="form.title" outlined label="Название курса" class="q-mb-md" />
				<q-input
					v-model.trim="form.description"
					outlined
					label="Описание (необязательно)"
					type="textarea"
					autogrow
					class="q-mb-md"
				/>
				<q-input v-model.trim="searchTrainings" outlined dense label="Поиск тренинга" class="q-mb-md" />
				<div class="text-caption text-grey-7 q-mb-sm">
					Выбрано тренингов: {{ form.training_uuids.length }}
				</div>
				<q-list bordered separator class="trainings-select-list">
					<q-item v-if="filteredTrainingsForCreate.length === 0">
						<q-item-section class="text-grey-6">Тренинги не найдены</q-item-section>
					</q-item>
					<q-item
						v-for="training in filteredTrainingsForCreate"
						:key="training.uuid"
						clickable
						v-ripple
						@click="toggleTraining(training.uuid)"
					>
						<q-item-section avatar>
							<q-checkbox
								:model-value="selectedSet.has(training.uuid)"
								@update:model-value="toggleTraining(training.uuid)"
								@click.stop
							/>
						</q-item-section>
						<q-item-section>
							<q-item-label>{{ training.title }}</q-item-label>
							<q-item-label caption>{{ training.level?.label ?? "Без уровня" }}</q-item-label>
						</q-item-section>
					</q-item>
				</q-list>
			</q-card-section>
			<q-card-actions align="right">
				<q-btn flat no-caps label="Отмена" class="btn-rounded" v-close-popup />
				<q-btn
					unelevated
					no-caps
					color="primary"
					label="Создать курс"
					class="btn-rounded"
					:disable="!canCreate"
					@click="createCourse"
				/>
			</q-card-actions>
		</q-card>
	</q-dialog>

	<q-dialog v-model="detailsModal">
		<q-card class="details-modal" flat bordered>
			<q-card-section class="details-header row items-center no-wrap">
				<div class="details-header-icon q-mr-md">
					<q-icon name="school" size="28px" color="primary" />
				</div>
				<div class="col">
					<div class="text-h5 text-weight-bold text-dark">{{ selectedCourse?.title || "Курс" }}</div>
					<div class="text-caption text-grey-7 q-mt-xs">
						Тренингов в курсе: {{ selectedCourse?.trainings?.length || 0 }}
					</div>
				</div>
				<q-btn icon="close" flat round dense v-close-popup color="grey-7" />
			</q-card-section>
			<q-separator />
			<q-card-section class="details-body bg-grey-1">
				<div v-if="!(selectedCourse?.trainings?.length)" class="empty-trainings-list column flex-center q-py-xl">
					<q-icon name="auto_stories" size="48px" color="grey-4" class="q-mb-md" />
					<div class="text-subtitle1 text-grey-7">В этом курсе пока нет тренингов</div>
				</div>

				<div v-else class="trainings-list q-gutter-y-sm">
					<div
						v-for="(training, index) in selectedCourse?.trainings || []"
						:key="training.uuid"
						class="training-list-item row items-center no-wrap bg-white"
					>
						<div class="training-list-item__number text-grey-5 text-weight-bold q-mr-md">
							{{ index + 1 }}
						</div>
						<div class="training-list-item__icon q-mr-md">
							<q-icon name="play_lesson" size="24px" color="primary" />
						</div>
						<div class="col overflow-hidden q-pr-md">
							<div class="text-subtitle1 text-weight-bold text-dark ellipsis q-mb-xs" :title="training.title">
								{{ training.title }}
							</div>
							<div class="row items-center text-caption text-grey-6 q-gutter-x-md">
								<span class="row items-center"><q-icon name="trending_up" size="16px" class="q-mr-xs"/> {{ training.level?.label ?? "Без уровня" }}</span>
								<span class="row items-center"><q-icon name="schedule" size="16px" class="q-mr-xs"/> {{ training.duration_minutes || "—" }} мин</span>
								<span class="status-pill-small" :class="training.publish ? 'status-published' : 'status-draft'">
									<span class="status-dot"></span>
									{{ training.publish ? "Опубликован" : "Черновик" }}
								</span>
							</div>
						</div>
						<div class="training-list-item__actions row items-center q-gutter-x-sm no-wrap">
							<q-btn
								flat
								dense
								no-caps
								color="primary"
								icon="edit"
								class="btn-rounded q-px-sm"
								label="Открыть"
								@click="openTrainingEditor(training.uuid)"
							/>
							<q-btn
								unelevated
								dense
								no-caps
								color="primary"
								icon="play_arrow"
								class="btn-rounded q-px-sm"
								label="Пройти"
								@click="startTrainingPassage(training)"
							/>
						</div>
					</div>
				</div>
			</q-card-section>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useQuasar } from "quasar";
import { useRouter } from "vue-router";
import { CourseApi, TrainingApi } from "@api";

const $q = useQuasar();
const router = useRouter();
const courseApi = new CourseApi();
const trainingApi = new TrainingApi();

const loading = ref(true);
const courses = ref([]);
const trainings = ref([]);

const searchQuery = ref("");
const filterTab = ref("all");

const createModal = ref(false);
const detailsModal = ref(false);
const selectedCourse = ref(null);

const searchTrainings = ref("");
const form = ref({
	title: "",
	description: "",
	training_uuids: [],
});

const selectedSet = computed(() => new Set(form.value.training_uuids));
const canCreate = computed(() => !!form.value.title && form.value.training_uuids.length > 0);

const filteredTrainingsForCreate = computed(() => {
	const query = searchTrainings.value.trim().toLowerCase();
	if (!query) return trainings.value;
	return trainings.value.filter((item) => item.title?.toLowerCase().includes(query));
});

const filteredCourses = computed(() => {
	const q = searchQuery.value.trim().toLowerCase();
	let result = courses.value;
	if (filterTab.value === "published") {
		result = result.filter((course) => publishedCount(course) > 0);
	}
	if (filterTab.value === "draft") {
		result = result.filter((course) => publishedCount(course) === 0);
	}
	if (q) {
		result = result.filter((course) => {
			const inTitle = course.title?.toLowerCase().includes(q);
			const inDesc = course.description?.toLowerCase().includes(q);
			const inTrainings = (course.trainings || []).some((t) => t.title?.toLowerCase().includes(q));
			return inTitle || inDesc || inTrainings;
		});
	}
	return result;
});

function formatDate(value) {
	if (!value) return "—";
	try {
		return new Date(value).toLocaleString("ru-RU", {
			day: "2-digit",
			month: "2-digit",
			year: "numeric",
		});
	} catch {
		return "—";
	}
}

function publishedCount(course) {
	return (course.trainings || []).filter((t) => t.publish).length;
}

function courseStatusLabel(course) {
	const total = (course.trainings || []).length;
	const pub = publishedCount(course);
	if (total === 0) return "Пустой курс";
	if (pub === 0) return "Черновик";
	if (pub === total) return "Готов к прохождению";
	return "Частично опубликован";
}

function courseStatusClass(course) {
	const total = (course.trainings || []).length;
	const pub = publishedCount(course);
	if (total === 0 || pub === 0) return "status-draft";
	if (pub === total) return "status-published";
	return "status-mixed";
}

function resetCreateForm() {
	form.value = { title: "", description: "", training_uuids: [] };
	searchTrainings.value = "";
}

function resetFilters() {
	searchQuery.value = "";
	filterTab.value = "all";
}

function openCreateModal() {
	resetCreateForm();
	createModal.value = true;
}

function openDetails(course) {
	selectedCourse.value = course;
	detailsModal.value = true;
}

function toggleTraining(uuid) {
	const set = new Set(form.value.training_uuids);
	if (set.has(uuid)) set.delete(uuid);
	else set.add(uuid);
	form.value.training_uuids = [...set];
}

async function fetchData() {
	try {
		loading.value = true;
		const [coursesResponse, trainingsResponse] = await Promise.all([
			courseApi.getCourses(),
			trainingApi.getTrainings(),
		]);
		courses.value = Array.isArray(coursesResponse.data) ? coursesResponse.data : [];
		trainings.value = Array.isArray(trainingsResponse.data) ? trainingsResponse.data : [];
	} catch (error) {
		console.error(error);
		$q.notify({
			message: "Не удалось загрузить данные курсов",
			type: "negative",
			position: "top",
		});
	} finally {
		loading.value = false;
	}
}

async function createCourse() {
	if (!canCreate.value) return;
	try {
		await courseApi.createCourse(form.value);
		$q.notify({ message: "Курс создан", type: "positive", position: "top-right" });
		createModal.value = false;
		await fetchData();
	} catch (error) {
		console.error(error);
		$q.notify({
			message: error?.response?.data?.detail || "Не удалось создать курс",
			type: "negative",
			position: "top",
		});
	}
}

function openTrainingEditor(uuid) {
	const route = router.resolve(`/edit/${uuid}`);
	window.open(route.href, "_blank");
}

function extractTokenFromPublishResponse(data) {
	if (!data) return null;
	if (data.access_token) return data.access_token;
	const link = data.public_link || "";
	if (!link) return null;
	const chunks = String(link).split("/").filter(Boolean);
	return chunks[chunks.length - 1] || null;
}

async function startTrainingPassage(training) {
	try {
		const { data } = await trainingApi.publishTraining(training.uuid);
		const token = extractTokenFromPublishResponse(data);
		if (!token) throw new Error("No passage token");
		const route = router.resolve(`/training/passage/${token}/welcome`);
		window.open(route.href, "_blank");
	} catch (error) {
		console.error(error);
		$q.notify({
			message: "Не удалось запустить прохождение",
			type: "negative",
			position: "top",
		});
	}
}

function confirmDelete(course) {
	$q.dialog({
		title: "Удалить курс?",
		message: `Курс «${course.title}» будет удалён без возможности восстановления.`,
		cancel: { label: "Отмена", flat: true },
		ok: { label: "Удалить", color: "negative", flat: true },
		persistent: true,
	}).onOk(async () => {
		try {
			await courseApi.deleteCourse(course.id);
			$q.notify({ message: "Курс удален", type: "positive", position: "top-right" });
			if (selectedCourse.value?.id === course.id) detailsModal.value = false;
			await fetchData();
		} catch (error) {
			console.error(error);
			$q.notify({ message: "Не удалось удалить курс", type: "negative", position: "top" });
		}
	});
}

onMounted(fetchData);
</script>

<style scoped>
.course-page {
	min-height: 60vh;
	max-width: 1400px;
	margin: 0 auto;
	padding: 32px 40px 24px;
}

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
	width: 280px;
}

.search-input :deep(.q-field__control) {
	border-radius: 12px;
}

.create-btn {
	border-radius: 12px;
	height: 40px;
}

.btn-rounded {
	border-radius: 12px;
}

.loading-state,
.empty-state {
	min-height: 300px;
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

.max-w-md {
	max-width: 400px;
}

.courses-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
	gap: 24px;
	position: relative;
	z-index: 2;
}

.course-card {
	border-radius: 20px;
	transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
	border: 1px solid rgba(0, 0, 0, 0.06);
	background: rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	display: flex;
	flex-direction: column;
	height: 275px;
	box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
	cursor: pointer;
}

.course-card:hover {
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

.status-mixed {
	background: #eff6ff;
	color: #1d4ed8;
	border: 1px solid #bfdbfe;
}

.status-mixed .status-dot {
	background: #3b82f6;
}

.card-description {
	line-height: 1.5;
	flex: 1;
}

.ellipsis {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.ellipsis-2 {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
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

.badge-tag--more {
	color: #5064f7;
	background: rgba(80, 100, 247, 0.08);
	border-color: rgba(80, 100, 247, 0.2);
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

.create-card-section {
	min-height: 100%;
}

.create-icon-wrap {
	width: 64px;
	height: 64px;
	border-radius: 20px;
	background: #ffffff;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16px;
	transition: transform 0.3s var(--anim-ease-spring);
}

.create-card:hover .create-icon-wrap {
	transform: scale(1.1);
	background: #5064f7;
}

.create-card:hover .create-icon-wrap .q-icon {
	color: #fff !important;
}

.course-modal,
.details-modal {
	width: min(820px, 95vw);
	max-width: 95vw;
}

.trainings-select-list {
	max-height: 320px;
	overflow: auto;
	border-radius: 10px;
}

.details-header {
	padding: 24px 32px;
	background: linear-gradient(135deg, rgba(80, 100, 247, 0.04) 0%, rgba(80, 100, 247, 0.01) 100%);
}

.details-header-icon {
	width: 56px;
	height: 56px;
	border-radius: 16px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
}

.details-body {
	padding: 24px 32px;
	max-height: 65vh;
	overflow-y: auto;
}

.trainings-list {
	display: flex;
	flex-direction: column;
}

.training-list-item {
	padding: 16px 20px;
	border-radius: 16px;
	border: 1px solid rgba(0, 0, 0, 0.06);
	transition: all 0.25s ease;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.training-list-item:hover {
	border-color: rgba(80, 100, 247, 0.3);
	box-shadow: 0 4px 16px rgba(80, 100, 247, 0.08);
	transform: translateY(-2px);
}

.training-list-item__number {
	font-size: 18px;
	min-width: 24px;
	text-align: center;
}

.training-list-item__icon {
	width: 48px;
	height: 48px;
	border-radius: 12px;
	background: rgba(80, 100, 247, 0.06);
	display: flex;
	align-items: center;
	justify-content: center;
}

.status-pill-small {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	padding: 2px 8px;
	border-radius: 6px;
	font-size: 11px;
	font-weight: 600;
}

@media (max-width: 768px) {
	.course-page {
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
