<template>
	<div class="media-upload-panel">
		<div class="panel-header">
			<h2 class="panel-title">Обработка файлов</h2>
			<p class="panel-subtitle">
				Загрузите видео или PDF — обработка пойдёт в фоне, уведомление придёт автоматически
			</p>
		</div>

		<div
			class="drop-zone"
			:class="{ 'drop-zone--active': isDragging }"
			@dragover.prevent="isDragging = true"
			@dragleave.prevent="isDragging = false"
			@drop.prevent="onDrop"
		>
			<q-icon name="cloud_upload" size="48px" color="primary" class="q-mb-md" />
			<div class="text-body1 text-weight-medium text-dark q-mb-xs">
				Перетащите файл сюда или выберите на диске
			</div>
			<div class="text-caption text-grey-7 q-mb-md">Видео (mp4, webm, mov) или PDF</div>
			<q-btn
				unelevated
				color="primary"
				label="Выбрать файл"
				icon="attach_file"
				:loading="uploading"
				:disable="uploading"
				@click="triggerFileInput"
			/>
			<input
				ref="fileInput"
				type="file"
				class="hidden-input"
				accept=".pdf,.mp4,.webm,.mov,.avi,.mkv,video/*,application/pdf"
				@change="onFileSelected"
			/>
		</div>

		<q-linear-progress
			v-if="uploading"
			:value="uploadProgress / 100"
			color="primary"
			class="q-mt-md"
			rounded
		/>

		<div v-if="recentTasks.length" class="tasks-list q-mt-lg">
			<div class="text-subtitle2 text-weight-bold text-dark q-mb-sm">Недавние задачи</div>
			<div
				v-for="task in recentTasks"
				:key="task.task_id || task.id"
				class="task-row"
			>
				<div class="row items-center justify-between">
					<span class="text-body2 ellipsis">{{ task.original_filename || task.task_id }}</span>
					<q-badge :color="statusColor(task.status)" :label="statusLabel(task.status)" />
				</div>
				<q-linear-progress
					v-if="task.status === 'processing' || task.status === 'pending'"
					:value="(task.progress || 0) / 100"
					color="primary"
					class="q-mt-xs"
					size="4px"
					rounded
				/>
				<div v-if="task.result_url && task.status === 'completed'" class="q-mt-xs">
					<a :href="task.result_url" target="_blank" rel="noopener" class="result-link">
						Открыть результат
					</a>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useQuasar } from "quasar";
import { tasksApi } from "@api";
import { useNotificationsStore } from "@store/notifications.js";

const $q = useQuasar();
const notificationsStore = useNotificationsStore();

const fileInput = ref(null);
const uploading = ref(false);
const uploadProgress = ref(0);
const isDragging = ref(false);
const localTasks = ref([]);

const recentTasks = computed(() => {
	const fromWs = Object.values(notificationsStore.taskUpdates);
	const merged = [...fromWs, ...localTasks.value];
	const byId = new Map();
	for (const t of merged) {
		const id = t.task_id || t.id;
		if (id) byId.set(String(id), { ...byId.get(String(id)), ...t, task_id: id });
	}
	return Array.from(byId.values()).slice(0, 8);
});

function statusColor(status) {
	const map = {
		pending: "grey-6",
		processing: "primary",
		completed: "positive",
		failed: "negative",
	};
	return map[status] || "grey";
}

function statusLabel(status) {
	const map = {
		pending: "В очереди",
		processing: "Обработка",
		completed: "Готово",
		failed: "Ошибка",
	};
	return map[status] || status;
}

function triggerFileInput() {
	fileInput.value?.click();
}

async function uploadFile(file) {
	if (!file) return;
	uploading.value = true;
	uploadProgress.value = 0;
	try {
		const { data } = await tasksApi.upload(file, (e) => {
			if (e.total) {
				uploadProgress.value = Math.round((e.loaded * 100) / e.total);
			}
		});
		localTasks.value.unshift({
			task_id: data.task_id,
			status: data.status,
			progress: 0,
			original_filename: file.name,
		});
		$q.notify({
			type: "positive",
			message: data.message || "Файл принят в обработку",
		});
	} catch (err) {
		const detail = err.response?.data?.detail;
		$q.notify({
			type: "negative",
			message: typeof detail === "string" ? detail : "Не удалось загрузить файл",
		});
	} finally {
		uploading.value = false;
		uploadProgress.value = 0;
	}
}

function onFileSelected(ev) {
	const file = ev.target.files?.[0];
	ev.target.value = "";
	uploadFile(file);
}

function onDrop(ev) {
	isDragging.value = false;
	const file = ev.dataTransfer?.files?.[0];
	uploadFile(file);
}

onMounted(async () => {
	try {
		const { data } = await tasksApi.listTasks();
		localTasks.value = (data || []).map((t) => ({
			...t,
			task_id: t.id,
		}));
	} catch {
		/* ignore if not auth */
	}
});
</script>

<style scoped>
.media-upload-panel {
	background: rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(24px);
	border: 1px solid rgba(0, 0, 0, 0.06);
	border-radius: 20px;
	padding: 28px 32px;
	box-shadow: 0 8px 32px rgba(15, 23, 42, 0.04);
}

.panel-title {
	font-size: 20px;
	font-weight: 700;
	color: #0f172a;
	margin: 0 0 8px;
}

.panel-subtitle {
	font-size: 14px;
	color: #64748b;
	margin: 0 0 20px;
}

.drop-zone {
	border: 2px dashed rgba(80, 100, 247, 0.35);
	border-radius: 16px;
	padding: 32px 24px;
	text-align: center;
	background: rgba(239, 246, 255, 0.4);
	transition: border-color 0.2s ease, background 0.2s ease;
}

.drop-zone--active {
	border-color: #5064f7;
	background: rgba(239, 246, 255, 0.8);
}

.hidden-input {
	display: none;
}

.tasks-list {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.task-row {
	padding: 12px 14px;
	border-radius: 12px;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
}

.result-link {
	font-size: 13px;
	color: #5064f7;
	text-decoration: none;
}

.result-link:hover {
	text-decoration: underline;
}
</style>
