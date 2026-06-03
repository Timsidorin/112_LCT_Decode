<template>
	<q-btn
		flat
		no-caps
		class="user-trigger"
		:loading="loading"
		:disable="loading"
	>
		<q-tooltip v-if="!$q.screen.gt.xs">{{ userStore.fullName }}</q-tooltip>
		<div class="user-trigger__inner row items-center no-wrap">
			<q-avatar
				size="36px"
				font-size="14px"
				class="user-avatar"
				:class="{ 'user-avatar--initials': !avatarIsImage }"
			>
				<img
					v-if="userStore.photo"
					:src="userStore.photo"
					class="user-avatar-img"
					alt=""
				/>
				<YandexMark
					v-else-if="userStore.isYandexUser"
					:size="36"
					class="user-avatar-yandex"
				/>
				<template v-else>{{ userInitials }}</template>
			</q-avatar>
			<span v-if="$q.screen.gt.xs" class="user-name q-ml-sm">{{ userStore.fullName }}</span>
			<q-icon
				v-if="$q.screen.gt.xs"
				name="expand_more"
				size="20px"
				class="user-chevron q-ml-xs"
			/>
		</div>
		<q-menu fit anchor="bottom right" self="top right" :offset="[0, 8]">
			<q-list class="user-menu-list">
				<q-item>
					<q-item-section>
						<q-item-label class="text-weight-medium">{{ userStore.fullName }}</q-item-label>
						<q-item-label caption>{{ userStore.email }}</q-item-label>
					</q-item-section>
				</q-item>
				<q-separator />
				<q-item clickable v-ripple v-close-popup @click="openProfile">
					<q-item-section avatar>
						<q-icon name="person" size="sm" color="grey-7" />
					</q-item-section>
					<q-item-section>Профиль</q-item-section>
				</q-item>
				<q-separator />
				<q-item clickable v-ripple v-close-popup @click="logout">
					<q-item-section avatar>
						<q-icon name="logout" size="sm" color="negative" />
					</q-item-section>
					<q-item-section class="text-negative">Выйти</q-item-section>
				</q-item>
			</q-list>
		</q-menu>
	</q-btn>

	<q-dialog v-model="profileDialog" persistent transition-show="scale" transition-hide="scale">
		<q-card class="profile-card">
			<!-- Banner & Avatar -->
			<div class="profile-banner relative-position" style="height: 140px">
				<div class="absolute-bottom bg-transparent profile-avatar-container">
					<q-avatar size="84px" class="profile-avatar shadow-4">
						<img v-if="userStore.photo" :src="userStore.photo" />
						<YandexMark v-else-if="userStore.isYandexUser" :size="84" class="bg-white q-pa-xs" />
						<span v-else class="bg-primary text-white">{{ userInitials }}</span>
					</q-avatar>
					<q-btn round dense color="primary" icon="edit" class="profile-avatar-edit" size="sm" />
				</div>
			</div>

			<q-card-section class="q-pt-xl q-pb-sm">
				<div class="row justify-between items-start">
					<div>
						<div class="text-h5 text-weight-bold text-blue-grey-9">{{ userStore.fullName }}</div>
						<div class="text-blue-grey-5">{{ userStore.email }}</div>
					</div>
					<q-chip v-if="userStore.isYandexUser" color="red-1" text-color="red-7" class="text-weight-medium">
						<template #avatar>
							<YandexMark :size="20" />
						</template>
						Yandex ID
					</q-chip>
					<q-chip v-else color="blue-1" text-color="blue-7" icon="verified_user" class="text-weight-medium">
						Базовый аккаунт
					</q-chip>
				</div>
			</q-card-section>

			<q-tabs 
				v-model="profileTab" 
				dense 
				class="text-grey-7" 
				active-color="primary" 
				indicator-color="primary" 
				align="justify" 
				narrow-indicator
			>
				<q-tab name="overview" icon="person" label="Обзор" />
				<q-tab name="settings" icon="settings" label="Настройки" />
				<q-tab name="security" icon="security" label="Безопасность" />
			</q-tabs>

			<q-separator />

			<q-tab-panels v-model="profileTab" animated class="profile-panels">
				<!-- Вкладка: Обзор -->
				<q-tab-panel name="overview">
					<div class="text-subtitle2 text-blue-grey-8 q-mb-md text-weight-bold">Ваша статистика</div>
					<div class="row q-col-gutter-md q-mb-lg">
						<div class="col-4">
							<div class="stat-box bg-blue-50 text-blue-9">
								<q-icon name="school" size="28px" class="q-mb-sm opacity-80" />
								<div class="stat-value">12</div>
								<div class="stat-label">Пройдено</div>
							</div>
						</div>
						<div class="col-4">
							<div class="stat-box bg-emerald-50 text-emerald-9">
								<q-icon name="edit_note" size="28px" class="q-mb-sm opacity-80" />
								<div class="stat-value">4</div>
								<div class="stat-label">Создано</div>
							</div>
						</div>
						<div class="col-4">
							<div class="stat-box bg-orange-50 text-orange-9">
								<q-icon name="local_fire_department" size="28px" class="q-mb-sm opacity-80" />
								<div class="stat-value">3</div>
								<div class="stat-label">Дня подряд</div>
							</div>
						</div>
					</div>
					
					<div class="text-subtitle2 text-blue-grey-8 q-mb-sm text-weight-bold">Достижения</div>
					<div class="row gap-2 q-mb-md">
						<q-chip color="amber-1" text-color="amber-9" icon="emoji_events">Первый тренинг</q-chip>
						<q-chip color="purple-1" text-color="purple-9" icon="psychology">Знаток</q-chip>
						<q-chip outline color="grey-5" icon="lock">Скрыто</q-chip>
					</div>

					<div class="text-subtitle2 text-blue-grey-8 q-mb-sm text-weight-bold">О себе</div>
					<div class="bio-box">
						Увлеченный создатель обучающих материалов. Стремлюсь сделать процесс обучения интерактивным и увлекательным. 🚀
					</div>
				</q-tab-panel>

				<!-- Вкладка: Настройки -->
				<q-tab-panel name="settings">
					<q-list padding class="settings-list">
						<q-item tag="label" v-ripple class="q-mb-sm rounded-borders bg-grey-1">
							<q-item-section>
								<q-item-label class="text-weight-medium">Уведомления на email</q-item-label>
								<q-item-label caption>Получать новости, обновления и отчеты</q-item-label>
							</q-item-section>
							<q-item-section side>
								<q-toggle v-model="settings.emailNotif" color="primary" />
							</q-item-section>
						</q-item>
						
						<q-item tag="label" v-ripple class="q-mb-sm rounded-borders bg-grey-1">
							<q-item-section>
								<q-item-label class="text-weight-medium">Публичный профиль</q-item-label>
								<q-item-label caption>Другие пользователи могут видеть вашу статистику и достижения</q-item-label>
							</q-item-section>
							<q-item-section side>
								<q-toggle v-model="settings.publicProfile" color="primary" />
							</q-item-section>
						</q-item>

						<q-item tag="label" v-ripple class="rounded-borders bg-grey-1">
							<q-item-section>
								<q-item-label class="text-weight-medium">Темная тема</q-item-label>
								<q-item-label caption>Включить ночной режим интерфейса</q-item-label>
							</q-item-section>
							<q-item-section side>
								<q-toggle v-model="settings.darkMode" color="primary" @update:model-value="$q.dark.set" />
							</q-item-section>
						</q-item>
					</q-list>
				</q-tab-panel>

				<!-- Вкладка: Безопасность -->
				<q-tab-panel name="security">
					<q-list bordered separator class="rounded-borders">
						<q-item class="q-py-md">
							<q-item-section avatar>
								<q-avatar color="blue-50" text-color="blue-7" icon="mail" />
							</q-item-section>
							<q-item-section>
								<q-item-label caption>Основной Email</q-item-label>
								<q-item-label class="text-weight-medium">{{ userStore.email }}</q-item-label>
							</q-item-section>
							<q-item-section side>
								<q-icon name="verified" color="positive" size="24px">
									<q-tooltip>Подтвержден</q-tooltip>
								</q-icon>
							</q-item-section>
						</q-item>
						
						<q-item class="q-py-md">
							<q-item-section avatar>
								<q-avatar color="grey-2" text-color="grey-7" icon="phone" />
							</q-item-section>
							<q-item-section>
								<q-item-label caption>Телефон</q-item-label>
								<q-item-label class="text-weight-medium">{{ userStore.phone_number || "Не указан" }}</q-item-label>
							</q-item-section>
							<q-item-section side>
								<q-btn flat round dense icon="edit" color="grey-6" />
							</q-item-section>
						</q-item>

						<q-item clickable v-ripple class="q-py-md text-primary">
							<q-item-section avatar>
								<q-avatar color="blue-50" text-color="primary" icon="lock_reset" />
							</q-item-section>
							<q-item-section class="text-weight-medium">Изменить пароль</q-item-section>
							<q-item-section side>
								<q-icon name="chevron_right" color="primary" />
							</q-item-section>
						</q-item>
					</q-list>
				</q-tab-panel>
			</q-tab-panels>

			<q-card-actions align="right" class="bg-grey-1 q-pa-md">
				<q-btn flat label="Отмена" color="grey-7" v-close-popup class="text-weight-medium" />
				<q-btn unelevated label="Сохранить изменения" color="primary" v-close-popup class="text-weight-medium q-px-md" />
			</q-card-actions>
		</q-card>
	</q-dialog>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useQuasar } from "quasar";
import { useUserStore } from "@store/userData.js";
import { YandexMark } from "@components/base_components";

const $q = useQuasar();
const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const profileDialog = ref(false);

const profileTab = ref('overview');
const settings = ref({
	emailNotif: true,
	publicProfile: false,
	darkMode: $q.dark.isActive
});

const userInitials = computed(() => {
	const fn = (userStore.first_name || "").trim();
	const ln = (userStore.last_name || "").trim();
	if (fn || ln) {
		const a = fn.charAt(0).toUpperCase();
		const b = ln.charAt(0).toUpperCase();
		return (a + b) || a || "?";
	}
	const name = userStore.fullName;
	if (name && name !== "Пользователь") {
		const parts = name.split(/\s+/).filter(Boolean);
		if (parts.length >= 2) {
			return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
		}
		return parts[0]?.slice(0, 2).toUpperCase() || "?";
	}
	return "?";
});

const avatarIsImage = computed(
	() => !!(userStore.photo || userStore.isYandexUser)
);

async function loadUser() {
	loading.value = true;
	try {
		await userStore.fetchUser();
	} finally {
		loading.value = false;
	}
}

function openProfile() {
	profileDialog.value = true;
}

function logout() {
	localStorage.removeItem("tokenAuth");
	userStore.clearUser();
	router.push("/login");
}

onMounted(() => {
	if (!userStore.isLoaded) {
		loadUser();
	}
});
</script>

<style scoped>
.user-trigger {
	min-height: 44px;
	padding: 4px 10px 4px 6px;
	border-radius: 12px;
	border: 1px solid rgba(0, 0, 0, 0.08);
	background: #fff;
	transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.user-trigger:hover {
	background: #f9fafb;
	border-color: rgba(0, 0, 0, 0.1);
	box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.user-trigger__inner {
	min-width: 0;
}

.user-avatar {
	font-weight: 700;
	flex-shrink: 0;
}

.user-avatar--initials {
	background: #e5e7eb;
	color: #1a1a2e;
}

.user-avatar-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	border-radius: inherit;
}

.user-avatar-yandex {
	display: block;
	margin: auto;
	padding: 5px;
	background: #fff;
	border-radius: inherit;
}

.user-name {
	max-width: 140px;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	font-size: 14px;
	font-weight: 600;
	color: #1a1a2e;
}

.user-chevron {
	color: #64748b;
	opacity: 0.85;
}

.user-menu-list {
	min-width: 220px;
	border-radius: 12px;
	overflow: hidden;
	box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.user-menu-list .q-item {
	transition: background 0.2s ease;
}

.profile-card {
	width: 100%;
	max-width: 540px;
	border-radius: 20px;
	overflow: hidden;
	box-shadow: 0 24px 56px rgba(15, 23, 42, 0.2);
}

.profile-banner {
	background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
}

.profile-avatar-container {
	padding: 0 24px;
	transform: translateY(30%);
	display: flex;
	align-items: flex-end;
}

.profile-avatar {
	border: 4px solid #ffffff;
	background: #ffffff;
}

.profile-avatar-edit {
	margin-left: -20px;
	margin-bottom: 4px;
	border: 2px solid #ffffff;
	box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.profile-panels {
	min-height: 320px;
}

.stat-box {
	border-radius: 12px;
	padding: 16px;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: transform 0.2s ease;
}

.stat-box:hover {
	transform: translateY(-2px);
}

.stat-value {
	font-size: 24px;
	font-weight: 800;
	line-height: 1.2;
	margin-bottom: 4px;
}

.stat-label {
	font-size: 12px;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	opacity: 0.9;
}

.bio-box {
	background: #f8fafc;
	border-radius: 12px;
	padding: 16px;
	font-size: 14px;
	color: #475569;
	line-height: 1.5;
	border: 1px solid #e2e8f0;
}

.opacity-80 {
	opacity: 0.8;
}
</style>
