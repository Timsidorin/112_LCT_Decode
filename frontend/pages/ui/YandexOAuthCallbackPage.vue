<template>
	<div class="ya-oauth column items-center justify-center q-pa-xl">
		<q-spinner color="primary" size="3em" />
		<div class="q-mt-md text-body1 text-grey-8">Завершение входа через Яндекс…</div>
	</div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useQuasar } from "quasar";
import { useUserStore } from "@store/userData.js";
import { authApi } from "@api";

const route = useRoute();
const router = useRouter();
const $q = useQuasar();
const userStore = useUserStore();

onMounted(async () => {
	// 1. Режим фоллбэка (обычный редирект через бэкенд)
	// Бэкенд возвращает наш готовый JWT-токен в query-параметре ?token=...
	if (route.query.token) {
		localStorage.setItem("tokenAuth", route.query.token);
		const data = await userStore.fetchUser();
		if (!data) {
			localStorage.removeItem("tokenAuth");
			$q.notify({
				type: "negative",
				message: "Ошибка загрузки профиля.",
				position: "top",
			});
			await router.replace("/login");
			return;
		}
		$q.notify({
			type: "positive",
			message: "Вы вошли через Яндекс",
			position: "bottom-right",
			timeout: 2000,
		});
		const redirect = route.query.redirect || "/personal";
		await router.replace(redirect);
		return;
	}

	// 2. Режим официального виджета (всплывающее окно)
	// В этом случае токен от Яндекса приходит в hash URL, и нам нужно передать его родительскому окну
	const script = document.createElement("script");
	script.src = "https://yastatic.net/s3/passport-sdk/autofill/v1/sdk-suggest-token-with-polyfills-latest.js";
	script.onload = () => {
		if (window.YaSendSuggestToken) {
			window.YaSendSuggestToken(window.location.origin);
		}
	};
	script.onerror = () => {
		console.error("Yandex SDK token script blocked");
		// Если скрипт заблокирован даже в попапе, закрываем его, чтобы не висел
		window.close();
	};
	document.head.appendChild(script);
});
</script>

<style scoped>
.ya-oauth {
	min-height: 50vh;
}
</style>
