<template>
	<div class="upload-container column items-center relative-position">
		<video-processing-loader v-if="loading && uploadMode === 'video'" />
		<q-inner-loading :showing="loading && uploadMode === 'photos'">
			<q-spinner-gears size="48px" color="primary" />
		</q-inner-loading>

		<div class="upload-card column items-center">
			<div class="upload-icon-wrap q-mb-lg">
				<q-icon
					:name="uploadMode === 'photos' ? 'add_photo_alternate' : uploadMode === 'video' ? 'videocam' : uploadMode === 'pdf' ? 'picture_as_pdf' : 'screenshot_monitor'"
					size="48px"
					color="primary"
				/>
			</div>
			<h5 class="text-weight-bold text-grey-9 q-mb-xs q-mt-none">
				{{ uploadMode === 'photos' ? 'Начните с добавления скриншотов' : uploadMode === 'video' ? 'Загрузите видео' : uploadMode === 'pdf' ? 'Загрузите PDF инструкцию' : 'Захват экрана' }}
			</h5>
			<p class="text-body2 text-grey-6 text-center q-mb-lg" style="max-width: 420px">
				{{ uploadMode === 'photos'
					? 'Загрузите изображения интерфейса, чтобы создать шаги тренинга'
					: uploadMode === 'video'
					? 'AI автоматически создаст шаги с описаниями и определит области действий'
					: uploadMode === 'pdf'
					? 'AI разберет инструкцию, извлечет скрины и определит области для клика'
					: 'Транслируйте нужный экран или окно и делайте снимки на лету'
				}}
			</p>

			<!-- Переключатель режима — карточки -->
			<div class="mode-toggle q-mb-lg">
				<div
					class="mode-card"
					:class="{ 'mode-card--active': uploadMode === 'photos' }"
					@click="uploadMode = 'photos'"
				>
					<q-icon name="photo_library" size="28px" />
					<span class="mode-label">Скриншоты</span>
					<span class="mode-desc">Пачка изображений</span>
				</div>
				<div
					class="mode-card"
					:class="{ 'mode-card--active': uploadMode === 'video' }"
					@click="uploadMode = 'video'"
				>
					<q-icon name="smart_display" size="28px" />
					<span class="mode-label">Видео</span>
					<span class="mode-desc">AI-анализ</span>
				</div>
				<div
					class="mode-card"
					:class="{ 'mode-card--active': uploadMode === 'pdf' }"
					@click="uploadMode = 'pdf'"
				>
					<q-icon name="picture_as_pdf" size="28px" />
					<span class="mode-label">PDF</span>
					<span class="mode-desc">Из инструкции</span>
				</div>
				<div
					class="mode-card"
					:class="{ 'mode-card--active': uploadMode === 'capture' }"
					@click="uploadMode = 'capture'"
				>
					<q-icon name="screenshot_monitor" size="28px" />
					<span class="mode-label">Захват</span>
					<span class="mode-desc">Live-снимки</span>
				</div>
			</div>

			<!-- Режим скриншотов -->
			<template v-if="uploadMode === 'photos'">
				<div v-if="images.length === 0" class="dropzone-wrap">
					<form-upload-photo
						@add-image="addImage"
						@download-photos="downloadPhotos"
					/>
				</div>
				<template v-else>
					<div class="photos-preview-area">
						<photo-list @delete-image="deleteImage" :images="images" :title="true" />
						<div class="photos-actions q-mt-md row justify-center q-gutter-sm">
							<q-btn
								outline
								no-caps
								rounded
								color="primary"
								icon="add_photo_alternate"
								label="Ещё фото"
								class="btn-create-steps"
								@click="addMorePhotos"
							/>
							<q-btn
								unelevated
								no-caps
								rounded
								color="primary"
								icon="check"
								label="Создать шаги"
								:loading="loading"
								:disable="loading"
								class="btn-create-steps btn-create-steps--primary"
								@click="uploadImages"
							/>
						</div>
					</div>
				</template>
			</template>

			<!-- Режим захвата экрана -->
			<template v-else-if="uploadMode === 'capture'">
				<div v-if="!videoStream" class="capture-start-card" @click="startCapture">
					<q-icon name="screen_share" size="64px" color="primary" class="q-mb-sm" />
					<span class="text-body1 text-grey-8 text-weight-medium">Предоставить доступ</span>
					<span class="text-caption text-grey-5 q-mt-xs">Разрешите браузеру показ нужного окна, чтобы делать скриншоты в один клик</span>
				</div>
				
				<div v-else class="capture-container column items-center">
					<div class="video-wrapper relative-position">
						<video ref="videoPlayerRef" autoplay playsinline muted class="capture-video"></video>
					</div>
					<div class="capture-actions q-mt-md row q-gutter-md justify-center">
						<q-btn
							unelevated
							no-caps
							rounded
							color="negative"
							icon="stop_screen_share"
							label="Завершить"
							class="btn-create-steps"
							@click="stopCapture"
						/>
						<q-btn
							unelevated
							no-caps
							rounded
							color="primary"
							icon="camera"
							label="Сделать снимок (Пробел)"
							class="btn-create-steps btn-create-steps--primary"
							@click="takeSnapshot"
						/>
					</div>
				</div>
			</template>

			<!-- Режим видео -->
			<template v-else-if="uploadMode === 'video'">
				<!-- Информация об ограничениях -->
				<div class="video-requirements q-mb-lg">
					<div class="requirements-header">
						<q-icon name="info" size="18px" color="primary" />
						<span class="requirements-title">Требования к видео</span>
					</div>
					<div class="requirements-list">
						<div class="requirement-item">
							<q-icon name="timer" size="16px" color="grey-7" />
							<span>Длительность: <strong>до 5 минут</strong></span>
						</div>
						<div class="requirement-item">
							<q-icon name="storage" size="16px" color="grey-7" />
							<span>Размер: <strong>до 100 МБ</strong></span>
						</div>
						<div class="requirement-item">
							<q-icon name="slow_motion_video" size="16px" color="grey-7" />
							<span>Интервал между действиями: <strong>2-3 сек</strong></span>
						</div>
						<div class="requirement-item">
							<q-icon name="videocam" size="16px" color="grey-7" />
							<span>Формат: <strong>mp4, webm, avi</strong></span>
						</div>
					</div>
				</div>
				
				<div
					v-if="!videoFile"
					class="dropzone-video"
					@click="triggerVideoInput"
					@dragover.prevent
					@drop.prevent="onVideoDrop"
					@dragenter.prevent
					@dragleave.prevent
				>
					<q-icon name="smart_display" size="64px" color="primary" class="q-mb-sm" />
					<span class="text-body1 text-grey-8 text-weight-medium">Выберите видео</span>
					<span class="text-caption text-grey-5 q-mt-xs">mp4, webm, avi — или перетащите сюда</span>
					<input
						ref="videoInputRef"
						type="file"
						accept="video/*"
						class="hidden"
						@change="onVideoSelected"
					/>
				</div>
				<template v-else>
					<div class="video-preview-card q-mb-md">
						<div class="video-preview-icon">
							<q-icon name="smart_display" size="32px" color="primary" />
						</div>
						<div class="video-preview-info">
							<span class="video-preview-name">{{ videoFile.name }}</span>
							<span class="video-preview-size">{{ formatFileSize(videoFile.size) }}</span>
						</div>
						<q-btn flat round dense icon="close" size="sm" color="grey-6" @click="clearVideo">
							<q-tooltip>Удалить</q-tooltip>
						</q-btn>
					</div>
					<q-btn
						unelevated
						no-caps
						rounded
						color="primary"
						icon="check"
						label="Создать шаги из видео"
						size="lg"
						:loading="loading"
						:disable="loading"
						class="btn-create-steps btn-create-steps--primary btn-create-steps--lg"
						@click="uploadVideo"
					/>
				</template>
			</template>

			<!-- Режим PDF -->
			<template v-else-if="uploadMode === 'pdf'">
				<div class="video-requirements q-mb-lg">
					<div class="requirements-header">
						<q-icon name="picture_as_pdf" size="18px" color="primary" />
						<span class="requirements-title">Разбор инструкции</span>
					</div>
					<p class="text-caption text-grey-7 q-mb-none">
						Загрузите PDF-файл. AI проанализирует каждую страницу, найдет скриншоты и автоматически создаст шаги с описанием и областями для нажатия.
					</p>
				</div>
				
				<div
					v-if="!pdfFile"
					class="dropzone-video"
					@click="triggerPdfInput"
					@dragover.prevent
					@drop.prevent="onPdfDrop"
					@dragenter.prevent
					@dragleave.prevent
				>
					<q-icon name="picture_as_pdf" size="64px" color="primary" class="q-mb-sm" />
					<span class="text-body1 text-grey-8 text-weight-medium">Выберите PDF</span>
					<span class="text-caption text-grey-5 q-mt-xs">Перетащите файл инструкции сюда</span>
					<input
						ref="pdfInputRef"
						type="file"
						accept=".pdf"
						class="hidden"
						@change="onPdfSelected"
					/>
				</div>
				<template v-else>
					<div class="video-preview-card q-mb-md">
						<div class="video-preview-icon">
							<q-icon name="picture_as_pdf" size="32px" color="primary" />
						</div>
						<div class="video-preview-info">
							<span class="video-preview-name">{{ pdfFile.name }}</span>
							<span class="video-preview-size">{{ formatFileSize(pdfFile.size) }}</span>
						</div>
						<q-btn flat round dense icon="close" size="sm" color="grey-6" @click="clearPdf">
							<q-tooltip>Удалить</q-tooltip>
						</q-btn>
					</div>
					<q-btn
						unelevated
						no-caps
						rounded
						color="primary"
						icon="auto_awesome"
						label="Создать шаги из PDF"
						size="lg"
						:loading="loading"
						:disable="loading"
						class="btn-create-steps btn-create-steps--primary btn-create-steps--lg"
						@click="uploadPdf"
					/>
				</template>
			</template>
		</div>
	</div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import useDnd from "@composables/useDnd.js";
import { MetaTrainingApi, TrainingApi } from "@api";
import { useRoute } from "vue-router";
import { useQuasar } from "quasar";
import { useTrainingData } from "@store/editTraining.js";
import {
	FormUploadPhoto,
	PhotoList
} from "@components/features/edit_page/uploader_photo";
import VideoProcessingLoader from "@components/features/edit_page/VideoProcessingLoader.vue";

const metaApi = new MetaTrainingApi();
const trainingApi = new TrainingApi();
const $q = useQuasar();
const store = useTrainingData();
const [images, addImage] = useDnd();
const route = useRoute();
const loading = ref(false);
const uploadMode = ref("photos");
const videoFile = ref(null);
const videoInputRef = ref(null);
const pdfFile = ref(null);
const pdfInputRef = ref(null);

const videoStream = ref(null);
const videoPlayerRef = ref(null);

const handleGlobalKeydown = (e) => {
	if (uploadMode.value === "capture" && videoStream.value) {
		// Проверяем все возможные варианты кода клавиши пробел
		if (e.code === "Space" || e.key === " " || e.keyCode === 32) {
			// Игнорируем нажатия, если пользователь печатает в инпут
			const targetTag = e.target?.tagName?.toLowerCase();
			if (targetTag === "input" || targetTag === "textarea") return;
			
			e.preventDefault();
			takeSnapshot();
		}
	}
};

onMounted(() => {
	document.addEventListener("keydown", handleGlobalKeydown, { capture: true });
});

onUnmounted(() => {
	document.removeEventListener("keydown", handleGlobalKeydown, { capture: true });
});

watch(uploadMode, (newVal) => {
	if (newVal !== "video") videoFile.value = null;
	if (newVal !== "pdf") pdfFile.value = null;
	if (newVal !== "photos" && images.value.length > 0 && newVal !== "capture") images.value = [];
	if (newVal !== "capture") stopCapture();
});

const startCapture = async () => {
	try {
		const stream = await navigator.mediaDevices.getDisplayMedia({
			video: { displaySurface: "window" },
			audio: false
		});
		videoStream.value = stream;
		
		stream.getVideoTracks()[0].onended = () => {
			stopCapture();
		};

		setTimeout(() => {
			if (videoPlayerRef.value) {
				videoPlayerRef.value.srcObject = stream;
			}
		}, 100);
	} catch (error) {
		console.error("Ошибка при захвате экрана:", error);
		$q.notify({
			message: "Не удалось запустить захват экрана",
			caption: "Возможно, вы отменили выбор или у приложения нет прав",
			type: "negative",
			position: "top"
		});
	}
};

const stopCapture = () => {
	if (videoStream.value) {
		videoStream.value.getTracks().forEach((track) => track.stop());
		videoStream.value = null;
	}
	if (uploadMode.value === "capture") {
		uploadMode.value = "photos";
	}
};

const takeSnapshot = () => {
	const video = videoPlayerRef.value;
	if (!video || !video.videoWidth) return;

	const canvas = document.createElement("canvas");
	canvas.width = video.videoWidth;
	canvas.height = video.videoHeight;
	const ctx = canvas.getContext("2d");
	ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

	canvas.toBlob((blob) => {
		if (!blob) return;
		const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
		const file = new File([blob], `screenshot_${timestamp}.png`, { type: "image/png" });
		const newImage = {
			id: Date.now(),
			name: file.name,
			url: URL.createObjectURL(file),
			size: file.size,
			originalFile: file,
		};
		images.value = [...images.value, newImage];
		
		$q.notify({
			message: "Снимок сохранен",
			type: "positive",
			position: "bottom-right",
			icon: "camera",
			timeout: 1000
		});
	}, "image/png", 1.0);
};

const formatFileSize = (bytes) => {
	if (!bytes) return "";
	if (bytes < 1024) return bytes + " Б";
	if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " КБ";
	return (bytes / (1024 * 1024)).toFixed(1) + " МБ";
};

const triggerVideoInput = () => videoInputRef.value?.click();

const onVideoSelected = (event) => {
	const file = event.target.files?.[0];
	if (file) videoFile.value = file;
	event.target.value = "";
};

const onVideoDrop = (event) => {
	const file = event.dataTransfer?.files?.[0];
	if (file && file.type.startsWith("video/")) {
		videoFile.value = file;
	}
};

const clearVideo = () => {
	videoFile.value = null;
	if (videoInputRef.value) videoInputRef.value.value = "";
};

const triggerPdfInput = () => pdfInputRef.value?.click();

const onPdfSelected = (event) => {
	const file = event.target.files?.[0];
	if (file) pdfFile.value = file;
	event.target.value = "";
};

const onPdfDrop = (event) => {
	const file = event.dataTransfer?.files?.[0];
	if (file && file.type === "application/pdf") {
		pdfFile.value = file;
	}
};

const clearPdf = () => {
	pdfFile.value = null;
	if (pdfInputRef.value) pdfInputRef.value.value = "";
};

const downloadPhotos = (event) => {
	let files = [...event.target.files];
	images.value = files.map((item, index) => ({
		id: index,
		name: item.name,
		url: URL.createObjectURL(item),
		size: item.size,
		originalFile: item,
	}));
};

const addMorePhotos = () => {
	const input = document.createElement("input");
	input.type = "file";
	input.multiple = true;
	input.accept = "image/*";
	input.onchange = (event) => {
		const files = event.target.files;
		if (!files || files.length === 0) return;
		const newImages = Array.from(files).map((file, i) => ({
			id: Date.now() + i,
			name: file.name,
			url: URL.createObjectURL(file),
			size: file.size,
			originalFile: file,
		}));
		images.value = [...images.value, ...newImages];
	};
	input.click();
};

const deleteImage = (id) => {
	images.value = images.value.filter((el) => el.id !== id);
};

const uploadImages = async () => {
	loading.value = true;
	try {
		const formData = new FormData();
		images.value.forEach((el) => {
			formData.append("files", el.originalFile);
		});
		await metaApi.uploadImages(route.params.uuid, formData);

		const { data } = await trainingApi.getTrainingByUuid(route.params.uuid);
		store.setTrainingData(data);

		images.value = [];

		$q.notify({
			message: "Шаги успешно созданы",
			type: "positive",
			position: "bottom-right",
			icon: "check_circle",
		});
	} catch {
		$q.notify({
			message: "Ошибка загрузки изображений",
			type: "negative",
			position: "top",
		});
	} finally {
		loading.value = false;
	}
};

const uploadVideo = async () => {
	if (!videoFile.value) return;
	loading.value = true;
	try {
		const formData = new FormData();
		formData.append("file", videoFile.value);
		await metaApi.uploadVideo(route.params.uuid, formData);

		const { data } = await trainingApi.getTrainingByUuid(route.params.uuid);
		store.setTrainingData(data);

		clearVideo();

		$q.notify({
			message: "Шаги из видео успешно созданы!",
			caption: "AI распознал действия автоматически. Вы можете отредактировать описания и уточнить области действий.",
			type: "positive",
			position: "bottom-right",
			icon: "smart_display",
			timeout: 5000,
			actions: [
				{
					label: "Понятно",
					color: "white",
					handler: () => {}
				}
			]
		});
	} catch {
		$q.notify({
			message: "Ошибка обработки видео",
			type: "negative",
			position: "top",
		});
	} finally {
		loading.value = false;
	}
};

const uploadPdf = async () => {
	if (!pdfFile.value) return;
	loading.value = true;
	try {
		const response = await trainingApi.uploadPdf(route.params.uuid, pdfFile.value);
		const createdStepsCount = response.data?.created_steps?.length || 0;

		const { data } = await trainingApi.getTrainingByUuid(route.params.uuid);
		store.setTrainingData(data);

		clearPdf();

		if (createdStepsCount > 0) {
			$q.notify({
				message: `Успешно создано шагов: ${createdStepsCount}`,
				caption: "AI проанализировал инструкцию и определил области действий.",
				type: "positive",
				position: "bottom-right",
				icon: "picture_as_pdf",
				timeout: 5000,
			});
		} else {
			$q.notify({
				message: "Шаги не были созданы",
				caption: "AI не смог найти подходящие действия в инструкции. Попробуйте другой файл.",
				type: "warning",
				position: "bottom-right",
				icon: "warning",
				timeout: 7000,
			});
		}
	} catch (err) {
		console.error("PDF Processing Error:", err);
		$q.notify({
			message: "Ошибка обработки PDF",
			caption: err.response?.data?.detail || "Проверьте формат файла и настройки AI",
			type: "negative",
			position: "top",
		});
	} finally {
		loading.value = false;
	}
};
</script>

<style scoped>
.upload-container {
	padding: 48px 20px;
	min-height: 100%;
}

.upload-card {
	text-align: center;
	max-width: 600px;
	width: 100%;
}

.upload-icon-wrap {
	width: 88px;
	height: 88px;
	border-radius: 50%;
	background: rgba(80, 100, 247, 0.08);
	display: flex;
	align-items: center;
	justify-content: center;
}

/* ——— Переключатель режима ——— */
.mode-toggle {
	display: flex;
	gap: 12px;
}

.mode-card {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4px;
	padding: 16px 28px;
	border-radius: 14px;
	border: 2px solid rgba(0, 0, 0, 0.08);
	background: #fff;
	cursor: pointer;
	transition: all 0.25s ease;
	min-width: 150px;
	color: #9e9e9e;
}

.mode-card:hover {
	border-color: rgba(80, 100, 247, 0.3);
	background: rgba(80, 100, 247, 0.03);
}

.mode-card--active {
	border-color: #5064f7;
	background: rgba(80, 100, 247, 0.06);
	color: #5064f7;
	box-shadow: 0 2px 12px rgba(80, 100, 247, 0.15);
}

.mode-label {
	font-size: 14px;
	font-weight: 600;
	line-height: 1.3;
}

.mode-desc {
	font-size: 11px;
	opacity: 0.7;
}

/* ——— Drop-зоны ——— */
.dropzone-wrap {
	border-radius: 16px;
	overflow: hidden;
}

.dropzone-video {
	width: 340px;
	max-width: 100%;
	height: 200px;
	border-radius: 16px;
	border: 2px dashed rgba(89, 106, 246, 0.28);
	background: rgba(191, 197, 244, 0.12);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: background-color 0.3s, border-color 0.3s;
}

.dropzone-video:hover {
	background: rgba(191, 197, 244, 0.22);
	border-color: rgba(89, 106, 246, 0.45);
}

/* ——— Требования к видео ——— */
.video-requirements {
	background: linear-gradient(135deg, rgba(80, 100, 247, 0.04) 0%, rgba(80, 100, 247, 0.01) 100%);
	border: 1px solid rgba(80, 100, 247, 0.12);
	border-radius: 14px;
	padding: 16px 20px;
	max-width: 480px;
	width: 100%;
}

.requirements-header {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 12px;
}

.requirements-title {
	font-size: 14px;
	font-weight: 600;
	color: #374151;
}

.requirements-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.requirement-item {
	display: flex;
	align-items: center;
	gap: 10px;
	font-size: 13px;
	color: #6b7280;
}

.requirement-item strong {
	color: #1f2937;
	font-weight: 600;
}

/* ——— Режим захвата экрана ——— */
.capture-start-card {
	width: 340px;
	max-width: 100%;
	height: 200px;
	border-radius: 16px;
	border: 2px dashed rgba(89, 106, 246, 0.28);
	background: rgba(191, 197, 244, 0.12);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: background-color 0.3s, border-color 0.3s;
	text-align: center;
	padding: 0 20px;
}
.capture-start-card:hover {
	background: rgba(191, 197, 244, 0.22);
	border-color: rgba(89, 106, 246, 0.45);
}

.capture-container {
	width: 100%;
	max-width: 520px;
}

.video-wrapper {
	width: 100%;
	aspect-ratio: 16/9;
	border-radius: 14px;
	overflow: hidden;
	background: #111;
	box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
	border: 2px solid rgba(80, 100, 247, 0.1);
}

.capture-video {
	width: 100%;
	height: 100%;
	object-fit: contain;
}

.capture-actions {
	width: 100%;
}

/* ——— Превью фото ——— */
.photos-preview-area {
	width: 100%;
	max-width: 520px;
}

/* ——— Превью видео ——— */
.video-preview-card {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 14px 18px;
	background: rgba(80, 100, 247, 0.06);
	border: 1px solid rgba(80, 100, 247, 0.15);
	border-radius: 12px;
	min-width: 300px;
	max-width: 420px;
}

.video-preview-icon {
	width: 48px;
	height: 48px;
	border-radius: 10px;
	background: rgba(80, 100, 247, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.video-preview-info {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	text-align: left;
}

.video-preview-name {
	font-size: 13px;
	font-weight: 500;
	color: #333;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.video-preview-size {
	font-size: 11px;
	color: #999;
	margin-top: 2px;
}

/* ——— Кнопки создания шагов ——— */
.btn-create-steps {
	border-radius: 24px;
	padding: 10px 20px;
	font-weight: 500;
	box-shadow: 0 2px 8px rgba(80, 100, 247, 0.2);
	transition: box-shadow 0.2s, transform 0.2s;
}
.btn-create-steps:hover:not(:disabled) {
	box-shadow: 0 4px 16px rgba(80, 100, 247, 0.35);
	transform: translateY(-1px);
}
.btn-create-steps--primary {
	padding: 12px 24px;
}
.btn-create-steps--lg {
	padding: 14px 28px;
	font-size: 15px;
}
</style>
