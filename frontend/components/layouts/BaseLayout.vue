<template>
	<q-layout view="lHh lpR fFf" class="base-layout">
		<q-header class="header text-grey-9" bordered>
			<q-toolbar class="toolbar">
				<div class="toolbar-inner row items-center no-wrap">
					<q-btn
						v-if="$q.screen.lt.md"
						flat
						dense
						round
						icon="menu"
						class="header-menu-btn"
						@click="drawerLeft = !drawerLeft"
					/>
					<router-link
						to="/personal/home"
						class="layout-brand row items-center no-wrap"
						:class="{ 'layout-brand--icon-only': !$q.screen.gt.xs }"
						:title="!$q.screen.gt.xs ? 'Конструктор тренингов' : undefined"
					>
						<div class="brand-mark flex flex-center">
							<q-icon name="school" size="22px" color="primary" />
						</div>
						<div v-if="$q.screen.gt.xs" class="brand-copy column justify-center q-ml-sm">
							<span class="brand-title">Конструктор тренингов</span>
							<span v-if="$q.screen.gt.sm" class="brand-tagline">Личный кабинет</span>
						</div>
					</router-link>
					<q-space />
					<div
						v-if="$q.screen.gt.sm"
						class="header-divider"
						aria-hidden="true"
					/>
					<UserCard />
				</div>
			</q-toolbar>
		</q-header>

		<q-drawer
			v-model="drawerLeft"
			show-if-above
			:breakpoint="768"
			side="left"
			bordered
			class="drawer"
			:width="260"
		>
			<q-list class="drawer-nav-list" padding>
				<q-item-label header class="drawer-nav-header">
					Разделы
				</q-item-label>
				<q-item
					v-for="(nav, idx) in navigationButtons"
					:key="nav.url"
					:to="nav.url"
					exact
					clickable
					v-ripple
					class="drawer-nav-item"
					active-class="drawer-nav-item--active"
					:style="{ '--stagger': idx }"
				>
					<q-item-section avatar>
						<q-icon :name="nav.icon" color="grey-7" class="drawer-nav-icon" />
					</q-item-section>
					<q-item-section>
						<q-item-label>{{ nav.name }}</q-item-label>
					</q-item-section>
				</q-item>
			</q-list>
		</q-drawer>

		<q-page-container class="page-container">
			<router-view v-slot="{ Component }">
				<transition name="fade-page" mode="out-in">
					<component :is="Component" />
				</transition>
			</router-view>
		</q-page-container>
	</q-layout>
</template>

<script>
import { ref } from "vue";
import UserCard from "@components/features/personal_page/header/UserCard.vue";
import { useUserStore } from "@store/userData.js";
import { useNotificationsStore } from "@store/notifications.js";

export default {
	name: "BaseLayout",
	components: { UserCard },
	async mounted() {
		const token = localStorage.getItem("tokenAuth");
		if (token && !useUserStore().isLoaded) {
			await useUserStore().fetchUser();
		}
		if (token) {
			useNotificationsStore().connect();
		}
	},
	beforeUnmount() {
		useNotificationsStore().disconnect();
	},
	setup() {
		const drawerLeft = ref(false);
		return {
			drawerLeft,
			navigationButtons: [
				{ name: "Главная", icon: "home", url: "/personal/home" },
				{ name: "Библиотека", icon: "menu_book", url: "/personal/library" },
				{ name: "Мои тренинги", icon: "list_alt", url: "/personal/training" },
				{ name: "Мои курсы", icon: "school", url: "/personal/courses" },
				{ name: "Поддержка", icon: "help", url: "/personal/help" },
			],
		};
	},
};
</script>

<style scoped>
/*
 * Фон личного кабинета: современный мягкий градиент
 */
.base-layout {
	background-color: #eef2f6;
	background-image: 
		radial-gradient(circle at 15% 50%, rgba(80, 100, 247, 0.12) 0, transparent 50%), 
		radial-gradient(circle at 85% 30%, rgba(168, 85, 247, 0.08) 0, transparent 50%), 
		radial-gradient(circle at 50% 100%, rgba(80, 100, 247, 0.1) 0, transparent 50%);
	min-height: 100vh;
	position: relative;
}

.base-layout::before {
	content: "";
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-image: radial-gradient(rgba(15, 23, 42, 0.05) 1px, transparent 1px);
	background-size: 24px 24px;
	pointer-events: none;
	z-index: 0;
}

.base-layout::after {
	content: "";
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	height: 400px;
	background: linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 100%);
	pointer-events: none;
	z-index: 0;
}

/* Шапка чуть светлее и с лёгким размытием */
.header {
	background: rgba(255, 255, 255, 0.85) !important;
	backdrop-filter: blur(24px);
	-webkit-backdrop-filter: blur(24px);
	border-bottom: 1px solid rgba(0, 0, 0, 0.06) !important;
	box-shadow: 0 4px 20px rgba(15, 23, 42, 0.02);
}

.toolbar {
	min-height: 60px;
	padding: 8px 16px;
}

@media (min-width: 1024px) {
	.toolbar {
		padding-left: 24px;
		padding-right: 24px;
	}
}

/* Без max-width и auto-margin: бренд остается у левого края рабочей области (рядом с drawer) */
.toolbar-inner {
	flex: 1 1 auto;
	min-width: 0;
	width: 100%;
	align-items: center;
}

.header-menu-btn {
	color: #475569;
	transition: background 0.2s ease, color 0.2s ease;
	margin-right: 4px;
}

.header-menu-btn:hover {
	background: rgba(0, 0, 0, 0.05);
	color: #1a1a2e;
}

.layout-brand {
	text-decoration: none;
	color: inherit;
	border-radius: 12px;
	padding: 6px 10px 6px 4px;
	margin: 0 8px 0 0;
	transition: background 0.2s ease;
	outline: none;
}

.layout-brand:focus-visible {
	box-shadow: 0 0 0 2px rgba(80, 100, 247, 0.35);
}

.layout-brand--icon-only {
	padding: 4px;
	margin-left: 0;
}

.layout-brand:hover {
	background: rgba(0, 0, 0, 0.03);
}

.layout-brand:active {
	background: rgba(0, 0, 0, 0.045);
}

.brand-mark {
	width: 40px;
	height: 40px;
	border-radius: 11px;
	background: rgba(80, 100, 247, 0.1);
	flex-shrink: 0;
	transition: background 0.2s ease, transform 0.25s var(--anim-ease-spring, ease-out);
}

.layout-brand:hover .brand-mark {
	background: rgba(80, 100, 247, 0.14);
	transform: scale(1.02);
}

.brand-copy {
	min-width: 0;
	line-height: 1.25;
}

.brand-title {
	font-size: 15px;
	font-weight: 700;
	color: #1a1a2e;
	letter-spacing: -0.02em;
}

.brand-tagline {
	font-size: 11px;
	font-weight: 500;
	color: #94a3b8;
	letter-spacing: 0.01em;
	margin-top: 1px;
}

.header-divider {
	width: 1px;
	height: 28px;
	background: rgba(0, 0, 0, 0.08);
	margin-right: 12px;
	margin-left: 4px;
	flex-shrink: 0;
}

.drawer {
	background: rgba(255, 255, 255, 0.85) !important;
	backdrop-filter: blur(24px);
	-webkit-backdrop-filter: blur(24px);
	border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
}

:deep(.q-drawer) {
	background: rgba(255, 255, 255, 0.85) !important;
	backdrop-filter: blur(24px);
	-webkit-backdrop-filter: blur(24px);
}

:deep(.q-drawer__content) {
	background: transparent !important;
}

.drawer-nav-header {
	font-size: 11px;
	font-weight: 600;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: #64748b;
	padding: 16px 16px 8px;
	line-height: 1.2;
}

.drawer-nav-list {
	padding-top: 4px;
	padding-bottom: 12px;
}

.drawer-nav-item {
	margin: 4px 12px;
	border-radius: 10px;
	transition: all 0.25s ease;
	animation: fadeInUp 0.35s var(--anim-ease-out) backwards;
	animation-delay: calc(0.04s * (var(--stagger, 0) + 1));
	background: transparent;
	border: 1px solid transparent;
	color: #64748b;
}

.drawer-nav-item:hover {
	background: rgba(80, 100, 247, 0.04);
	color: #0f172a;
}

.drawer-nav-item:active {
	transform: scale(0.98);
}

.drawer-nav-item--active {
	background: #ffffff !important;
	color: #5064f7;
	border-color: rgba(0, 0, 0, 0.04);
	box-shadow: 0 4px 12px rgba(80, 100, 247, 0.06);
}

.drawer-nav-item--active :deep(.drawer-nav-icon) {
	color: var(--q-primary) !important;
}

.drawer-nav-item--active :deep(.q-item__label) {
	font-weight: 600;
	color: #5064f7;
}

.page-container {
	background: transparent;
	position: relative;
	z-index: 1;
}

/* Анимация переходов между страницами */
.fade-page-enter-active,
.fade-page-leave-active {
	transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-page-enter-from {
	opacity: 0;
	transform: translateY(8px);
}

.fade-page-leave-to {
	opacity: 0;
	transform: translateY(-8px);
}

@media (prefers-reduced-motion: reduce) {
	.header {
		backdrop-filter: none;
		-webkit-backdrop-filter: none;
		background: #eef0f6 !important;
	}
}
</style>
