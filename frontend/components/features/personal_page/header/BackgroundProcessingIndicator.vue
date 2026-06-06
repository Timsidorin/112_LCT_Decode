<template>
	<div v-if="notificationsStore.isProcessing" class="processing-indicator">
		<q-btn
			flat
			no-caps
			class="processing-indicator__btn"
			:aria-label="ariaLabel"
			@click.stop
		>
			<div class="processing-indicator__inner row items-center no-wrap">
				<div class="hourglass-wrap">
					<q-icon name="hourglass_top" size="20px" class="hourglass hourglass--top" />
					<q-icon name="hourglass_bottom" size="20px" class="hourglass hourglass--bottom" />
					<span class="hourglass-ring" aria-hidden="true" />
				</div>
				<span v-if="$q.screen.gt.xs" class="processing-indicator__label">
					{{ headerProgress }}%
				</span>
			</div>

			<q-badge
				v-if="notificationsStore.activeTaskCount > 1"
				floating
				color="primary"
				:label="notificationsStore.activeTaskCount"
			/>

			<q-tooltip anchor="bottom middle" self="top middle" :offset="[0, 8]">
				{{ tooltipText }}
			</q-tooltip>

			<q-menu
				anchor="bottom right"
				self="top right"
				:offset="[0, 10]"
				class="processing-menu"
				transition-show="jump-down"
				transition-hide="jump-up"
			>
				<div class="processing-panel">
					<div class="processing-panel__header">
						<div class="processing-panel__icon">
							<q-icon name="auto_awesome" size="20px" color="white" />
						</div>
						<div class="processing-panel__titles">
							<div class="processing-panel__title">Создание тренинга</div>
							<div class="processing-panel__subtitle">
								{{ notificationsStore.activeTaskCount === 1
									? "Обработка видео в фоне"
									: `Задач в работе: ${notificationsStore.activeTaskCount}` }}
							</div>
						</div>
					</div>

					<div class="processing-panel__body">
						<div
							v-for="task in notificationsStore.activeTasks"
							:key="task.task_id"
							class="processing-task"
						>
							<div class="processing-task__row">
								<div class="processing-task__info">
									<div class="processing-task__name" :title="taskLabel(task)">
										{{ taskLabel(task) }}
									</div>
									<div class="processing-task__status">
										{{ task.message || statusText(task.status) }}
									</div>
								</div>
								<div class="processing-task__ring">
									<q-circular-progress
										:value="task.progress || 0"
										size="44px"
										:thickness="0.18"
										color="primary"
										track-color="grey-3"
										show-value
										font-size="11px"
										class="processing-task__progress"
									>
										<span class="processing-task__percent">{{ task.progress || 0 }}%</span>
									</q-circular-progress>
								</div>
							</div>
							<q-linear-progress
								:value="(task.progress || 0) / 100"
								color="primary"
								track-color="grey-3"
								size="6px"
								rounded
								class="processing-task__bar"
							/>
						</div>
					</div>

					<div class="processing-panel__footer column q-gutter-y-xs">
						<div class="row items-center no-wrap">
							<q-icon name="check_circle_outline" size="16px" class="processing-panel__footer-icon" />
							<span>Можно продолжать работу — обработка идёт в фоне</span>
						</div>
						<q-btn
							flat
							dense
							no-caps
							color="grey-7"
							label="Сбросить зависшие задачи"
							class="processing-panel__dismiss"
							:loading="dismissing"
							@click="dismissStuckTasks"
						/>
					</div>
				</div>
			</q-menu>
		</q-btn>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useQuasar } from "quasar";
import { tasksApi } from "@api";
import { useNotificationsStore } from "@store/notifications.js";

const $q = useQuasar();
const notificationsStore = useNotificationsStore();
const dismissing = ref(false);

const headerProgress = computed(() => {
	const tasks = notificationsStore.activeTasks;
	if (!tasks.length) return 0;
	if (tasks.length === 1) return tasks[0].progress || 0;
	const sum = tasks.reduce((acc, t) => acc + (t.progress || 0), 0);
	return Math.round(sum / tasks.length);
});

const tooltipText = computed(() => {
	const n = notificationsStore.activeTaskCount;
	if (n === 1) {
		const task = notificationsStore.activeTasks[0];
		const progress = task?.progress ? ` (${task.progress}%)` : "";
		return `Создаётся тренинг из видео${progress}`;
	}
	return `Создаётся тренингов: ${n} (≈${headerProgress.value}%)`;
});

const ariaLabel = computed(() => tooltipText.value);

function taskLabel(task) {
	if (task.original_filename) {
		return task.original_filename;
	}
	if (task.training_uuid) {
		return `Тренинг ${task.training_uuid.slice(0, 8)}…`;
	}
	return "Обработка видео";
}

function statusText(status) {
	const map = {
		pending: "В очереди на обработку",
		processing: "AI анализирует видео и создаёт шаги",
	};
	return map[status] || "Обработка";
}

async function dismissStuckTasks() {
	if (dismissing.value) return;
	dismissing.value = true;
	try {
		const { data } = await tasksApi.dismissActiveTasks();
		notificationsStore.pruneStaleTasks();
		await notificationsStore.syncActiveTasks();
		$q.notify({
			type: "info",
			message: data?.dismissed
				? `Сброшено задач: ${data.dismissed}`
				: "Активных задач не было",
			position: "top-right",
		});
	} catch {
		$q.notify({
			type: "negative",
			message: "Не удалось сбросить задачи",
			position: "top-right",
		});
	} finally {
		dismissing.value = false;
	}
}
</script>

<style scoped>
.processing-indicator {
	flex-shrink: 0;
	margin-right: 6px;
}

.processing-indicator__btn {
	min-height: 40px;
	padding: 4px 10px 4px 8px;
	border-radius: 12px;
	border: 1px solid rgba(80, 100, 247, 0.18);
	background: rgba(255, 255, 255, 0.92);
	color: #5064f7;
	position: relative;
	transition:
		background 0.2s ease,
		border-color 0.2s ease,
		box-shadow 0.2s ease,
		transform 0.2s ease;
}

.processing-indicator__btn:hover {
	background: #fff;
	border-color: rgba(80, 100, 247, 0.32);
	box-shadow: 0 4px 16px rgba(80, 100, 247, 0.12);
}

.processing-indicator__inner {
	gap: 8px;
}

.processing-indicator__label {
	font-size: 13px;
	font-weight: 700;
	letter-spacing: -0.02em;
	color: #5064f7;
	min-width: 2.5ch;
}

.hourglass-wrap {
	position: relative;
	width: 20px;
	height: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.hourglass {
	position: absolute;
	color: #5064f7;
}

.hourglass--top {
	animation: hourglass-flip-top 2.4s ease-in-out infinite;
}

.hourglass--bottom {
	opacity: 0;
	animation: hourglass-flip-bottom 2.4s ease-in-out infinite;
}

.hourglass-ring {
	position: absolute;
	inset: -5px;
	border-radius: 50%;
	border: 2px solid rgba(80, 100, 247, 0.22);
	animation: hourglass-pulse 2.4s ease-in-out infinite;
	pointer-events: none;
}

@keyframes hourglass-flip-top {
	0%,
	45% {
		opacity: 1;
		transform: rotate(0deg);
	}
	50%,
	95% {
		opacity: 0;
		transform: rotate(180deg);
	}
	100% {
		opacity: 1;
		transform: rotate(360deg);
	}
}

@keyframes hourglass-flip-bottom {
	0%,
	45% {
		opacity: 0;
		transform: rotate(180deg);
	}
	50%,
	95% {
		opacity: 1;
		transform: rotate(0deg);
	}
	100% {
		opacity: 0;
		transform: rotate(180deg);
	}
}

@keyframes hourglass-pulse {
	0%,
	100% {
		transform: scale(1);
		opacity: 0.5;
	}
	50% {
		transform: scale(1.15);
		opacity: 0.15;
	}
}

.processing-menu {
	min-width: 320px;
	max-width: 380px;
	border-radius: 16px !important;
	overflow: hidden;
	box-shadow: 0 16px 48px rgba(15, 23, 42, 0.14) !important;
	border: 1px solid rgba(255, 255, 255, 0.5);
	background: transparent !important;
}

.processing-panel {
	background: rgba(255, 255, 255, 0.88);
	backdrop-filter: blur(24px);
	-webkit-backdrop-filter: blur(24px);
	border-radius: 16px;
	overflow: hidden;
}

.processing-panel__header {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 16px 18px 14px;
	background: linear-gradient(
		135deg,
		rgba(80, 100, 247, 0.08) 0%,
		rgba(168, 85, 247, 0.06) 100%
	);
	border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.processing-panel__icon {
	width: 40px;
	height: 40px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	background: linear-gradient(135deg, #5064f7 0%, #8b5cf6 100%);
	box-shadow: 0 4px 12px rgba(80, 100, 247, 0.35);
}

.processing-panel__titles {
	min-width: 0;
}

.processing-panel__title {
	font-size: 15px;
	font-weight: 700;
	color: #1a1a2e;
	letter-spacing: -0.02em;
	line-height: 1.25;
}

.processing-panel__subtitle {
	font-size: 12px;
	font-weight: 500;
	color: #64748b;
	margin-top: 2px;
}

.processing-panel__body {
	padding: 12px 14px 14px;
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.processing-task {
	padding: 12px 14px;
	border-radius: 14px;
	background: #fff;
	border: 1px solid rgba(0, 0, 0, 0.06);
	box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.processing-task:hover {
	border-color: rgba(80, 100, 247, 0.15);
	box-shadow: 0 4px 14px rgba(80, 100, 247, 0.08);
}

.processing-task__row {
	display: flex;
	align-items: flex-start;
	gap: 12px;
	margin-bottom: 10px;
}

.processing-task__info {
	flex: 1;
	min-width: 0;
}

.processing-task__name {
	font-size: 13px;
	font-weight: 600;
	color: #1a1a2e;
	line-height: 1.35;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.processing-task__status {
	font-size: 12px;
	color: #64748b;
	margin-top: 4px;
	line-height: 1.4;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.processing-task__ring {
	flex-shrink: 0;
}

.processing-task__percent {
	font-size: 11px;
	font-weight: 700;
	color: #5064f7;
}

.processing-task__bar {
	border-radius: 999px;
	overflow: hidden;
}

.processing-panel__footer {
	display: flex;
	align-items: flex-start;
	gap: 8px;
	padding: 12px 16px 14px;
	font-size: 12px;
	line-height: 1.45;
	font-weight: 500;
	color: #64748b;
	background: rgba(248, 250, 252, 0.9);
	border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.processing-panel__footer-icon {
	flex-shrink: 0;
	margin-top: 1px;
	color: #5064f7;
	opacity: 0.85;
}

@media (max-width: 599px) {
	.processing-menu {
		min-width: min(320px, calc(100vw - 24px));
	}
}

@media (prefers-reduced-motion: reduce) {
	.hourglass--top,
	.hourglass--bottom,
	.hourglass-ring {
		animation: none;
	}

	.hourglass--bottom {
		display: none;
	}
}
</style>
