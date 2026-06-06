import { createWebHistory, createRouter } from "vue-router";
import { routes } from "./routes.js";
import { checkAuth } from "@utils/checkAuth.js";
import { useUserStore } from "@store/userData.js";

const router = createRouter({
	history: createWebHistory(),
	routes,
});

router.beforeEach(async (to, from, next) => {
	if (!to.path.startsWith("/personal")) {
		next();
		return;
	}

	const tokenAuth = localStorage.getItem("tokenAuth");
	if (!tokenAuth) {
		next({ path: "/login", query: { redirect: to.fullPath } });
		return;
	}

	const userStore = useUserStore();
	const withinPersonal =
		from.path.startsWith("/personal") && to.path.startsWith("/personal");

	// Между разделами ЛК не дергаем /auth/me — иначе при нагрузке на backend навигация зависает.
	if (withinPersonal && userStore.isLoaded) {
		next();
		return;
	}

	const auth = await checkAuth(tokenAuth);
	if (!auth.status) {
		next({ path: "/login", query: { redirect: to.fullPath } });
		return;
	}
	next();
});

export default router;
