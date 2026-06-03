import axios from "axios";

export class AuthApi {
	getMe() {
		const token = localStorage.getItem("tokenAuth");
		return axios.get(`${__BASE__URL__}/auth/me/`, {
			headers: { Authorization: `Bearer ${token}` },
		});
	}

	getYandexConfig() {
		return axios.get(`${__BASE__URL__}/auth/yandex/config`);
	}

	sendYandexToken(access_token) {
		return axios.post(`${__BASE__URL__}/auth/yandex/token`, { access_token });
	}
}

export const authApi = new AuthApi();