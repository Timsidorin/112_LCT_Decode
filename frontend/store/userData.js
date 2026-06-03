import { defineStore } from "pinia";
import { authApi } from "@api";

export const useUserStore = defineStore("user", {
	state: () => ({
		id: null,
		email: "",
		phone_number: "",
		first_name: "",
		last_name: "",
		photo: "",
		yandex_id: null,
		isLoaded: false,
	}),
	getters: {
		getName: (state) => state.first_name || "Пользователь",
		/** Имя для шапки: имя из профиля или логин из почты Яндекса / метка для синтетического email */
		fullName: (state) => {
			const parts = [state.first_name, state.last_name].filter(Boolean).join(" ").trim();
			if (parts) return parts;
			const em = (state.email || "").trim();
			if (em && em.includes("@")) {
				const [local, domain] = em.split("@");
				if (domain === "yandex.ru" || domain === "ya.ru" || domain === "narod.ru") {
					return local || "Пользователь";
				}
				if (domain === "yandex.oauth.local" && local.startsWith("yandex_")) {
					return "Пользователь Яндекс";
				}
				if (local) return local;
			}
			return "Пользователь";
		},
		isYandexUser: (state) => !!state.yandex_id,
		isLoggedIn: (state) => !!state.id,
	},
	actions: {
		setUser(user) {
			if (!user) return;
			this.id = user.id;
			this.email = user.email || "";
			this.phone_number = user.phone_number ?? "";
			this.first_name = user.first_name ?? "";
			this.last_name = user.last_name ?? "";
			this.photo = user.photo ?? "";
			this.yandex_id = user.yandex_id ?? user.yandexId ?? null;
			this.isLoaded = true;
		},
		clearUser() {
			this.id = null;
			this.email = "";
			this.phone_number = "";
			this.first_name = "";
			this.last_name = "";
			this.photo = "";
			this.yandex_id = null;
			this.isLoaded = false;
		},
		async fetchUser() {
			try {
				const { data } = await authApi.getMe();
				this.setUser(data);
				return data;
			} catch {
				this.clearUser();
				return null;
			}
		},
	},
});