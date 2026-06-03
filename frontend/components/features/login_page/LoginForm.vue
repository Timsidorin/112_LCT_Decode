<template>
	<BaseCard class="login-card" width="500px">
		<template v-slot:title>
			<div class="column content-center items-center auth-title">
				<h5 class="q-mb-xs auth-heading">Добро пожаловать</h5>
				<div class="auth-sub">Вход</div>
				<div class="auth-switch">
					Нет аккаунта?
					<router-link class="auth-link" to="/registration">Регистрация</router-link>
				</div>
			</div>
		</template>
		<template v-slot:body>
			<div class="column justify-center items-center content-center auth-body">
				<q-input
					filled
					v-model="email"
					label="Логин *"
					lazy-rules
					class="full-width auth-input"
					color="primary"
				/>
				<q-input
					filled
					:type="isPwd ? 'password' : 'text'"
					v-model="password"
					label="Пароль *"
					lazy-rules
					class="full-width q-mt-lg auth-input"
					color="primary"
				>
					<template v-slot:append>
						<q-icon
							:name="isPwd ? 'visibility_off' : 'visibility'"
							class="cursor-pointer"
							@click="isPwd = !isPwd"
						/>
					</template>
				</q-input>
				<q-btn
					unelevated
					rounded
					class="q-mt-lg size-button-70 auth-btn"
					color="primary"
					@click="login()"
				>
					<q-spinner-bars v-if="loader === true" color="white" size="2em" />
					<span v-else>Войти</span>
				</q-btn>

				<div class="row items-center no-wrap full-width q-my-lg auth-or-row">
					<q-separator class="col" />
					<span class="auth-or-label">или</span>
					<q-separator class="col" />
				</div>

				<div class="column items-center yandex-oauth-block">
					<div class="text-caption text-grey-7 q-mb-sm text-center auth-yandex-hint">
						Войти с помощью
					</div>

					<!-- Если виджет заблокирован или не загрузился, показываем фоллбэк-кнопку -->
					<q-btn
						v-if="yandexWidgetError"
						round
						flat
						dense
						type="button"
						class="yandex-id-round"
						aria-label="Войти с Яндексом"
						@click.prevent="startYandexFallback()"
					>
						<YandexMark class="yandex-id-round__mark" :size="32" />
					</q-btn>

					<!-- Контейнер для официального виджета -->
					<div v-show="!yandexWidgetError" id="yandex-auth-container" class="yandex-widget-container"></div>
					
					<div class="text-caption text-grey-6 q-mt-xs text-center">
						Яндекс ID
					</div>
				</div>
			</div>
		</template>
	</BaseCard>
</template>

<script>
import axios from "axios";
import { BaseCard, YandexMark } from "@components/base_components";
import { authApi } from "@api";
import { useUserStore } from "@store/userData.js";
export default {
	name: "LoginForm",
	components: { BaseCard, YandexMark },
	data() {
		return {
			email: "",
			password: "",

			loader: false,
			isPwd: true,
			yandexWidgetError: false,
		};
	},
	async mounted() {
		try {
			const { data } = await authApi.getYandexConfig();
			if (data.client_id) {
				this.initYandexWidget(data.client_id, data.redirect_uri);
			}
		} catch (e) {
			console.error("Failed to load Yandex config", e);
		}
	},
	methods: {
		startYandexFallback() {
			const next =
				(typeof this.$route.query.redirect === "string" && this.$route.query.redirect) ||
				"/personal";
			const url = `${__BASE__URL__}/auth/yandex/start?next=${encodeURIComponent(next)}`;
			window.location.href = url;
		},
		initYandexWidget(clientId, redirectUri) {
			const init = () => {
				if (!window.YaAuthSuggest) {
					this.yandexWidgetError = true;
					return;
				}
				window.YaAuthSuggest.init(
					{
						client_id: clientId,
						response_type: "token",
						redirect_uri: redirectUri,
					},
					window.location.origin,
					{
						view: "button",
						parentId: "yandex-auth-container",
						buttonView: "icon",
						buttonTheme: "light",
						buttonSize: "m",
						buttonBorderRadius: 22,
					}
				)
					.then(({ handler }) => handler())
					.then(async (data) => {
						if (data.access_token) {
							this.loader = true;
							try {
								const res = await authApi.sendYandexToken(data.access_token);
								localStorage.setItem("tokenAuth", res.data.access_token);
								await useUserStore().fetchUser();
								const redirect = this.$route.query.redirect || "/personal";
								this.$router.push(redirect);
							} catch (err) {
								this.$q.notify({
									type: "negative",
									message: "Ошибка авторизации через Яндекс",
									position: "top",
								});
							} finally {
								this.loader = false;
							}
						}
					})
					.catch((error) => {
						console.log("Yandex widget closed or error", error);
						if (error && error.code === "not_available") {
							this.yandexWidgetError = true;
						} else {
							this.$q.notify({
								type: "warning",
								message: "Окно входа закрыто или неверно настроен Redirect URI в консоли Яндекса",
								position: "top",
							});
						}
					});
			};

			if (window.YaAuthSuggest) {
				init();
			} else {
				const script = document.createElement("script");
				script.src = "https://yastatic.net/s3/passport-sdk/autofill/v1/sdk-suggest-with-polyfills-latest.js";
				script.onload = init;
				script.onerror = () => {
					this.yandexWidgetError = true;
				};
				document.head.appendChild(script);
			}
		},
		async login() {
			this.loader = true;
			let form = new FormData();
			form.set("username", this.email);
			form.set("password", this.password);
			axios
				.post(`${__BASE__URL__}/auth/login`, form)
				.then(async (response) => {
					localStorage.setItem("tokenAuth", response.data.access_token);
					await useUserStore().fetchUser();
					const redirect = this.$route.query.redirect || "/personal";
					this.$router.push(redirect);
				})
				.catch(() => {
					this.$q.notify({
						position: "top",
						type: "negative",
						message: "Произошла ошибка!",
					});
				})
				.finally(() => {
					this.loader = false;
				});
		},
	},
};
</script>

<style scoped>
.login-card {
	background: #ffffff;
	box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
	border: 1px solid #e2e8f0;
	border-radius: 20px;
	overflow: hidden;
	animation: scaleIn 0.4s var(--anim-ease-spring) forwards;
}
.login-card :deep(.q-card__section) {
	transition: background 0.2s ease;
}
.auth-title {
	padding: 28px 24px 24px;
	color: #1a1a2e;
}
.auth-heading {
	font-size: 1.5rem;
	font-weight: 700;
	letter-spacing: -0.02em;
	color: #1a1a2e;
}
.auth-sub {
	font-size: 0.95rem;
	color: #64748b;
	margin-top: 4px;
}
.auth-switch {
	font-size: 0.9rem;
	margin-top: 12px;
	color: #64748b;
}
.auth-link {
	color: #5064f7;
	text-decoration: none;
	font-weight: 600;
	transition: opacity 0.2s ease;
}
.auth-link:hover {
	opacity: 0.85;
	text-decoration: underline;
}
.auth-body {
	padding: 8px 24px 28px;
}
.auth-input :deep(.q-field__control) {
	border-radius: 12px;
	transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.auth-input :deep(.q-field--focused .q-field__control) {
	box-shadow: 0 0 0 2px rgba(80, 100, 247, 0.25);
}
/* Стили автозаполнения — как у обычных filled-полей Quasar */
.auth-input :deep(input:-webkit-autofill),
.auth-input :deep(input:-webkit-autofill:hover),
.auth-input :deep(input:-webkit-autofill:focus),
.auth-input :deep(input:-webkit-autofill:active) {
	-webkit-box-shadow: 0 0 0 100px rgba(0, 0, 0, 0.05) inset !important;
	box-shadow: 0 0 0 100px rgba(0, 0, 0, 0.05) inset !important;
	-webkit-text-fill-color: #1a1a2e !important;
	caret-color: #1a1a2e;
	transition: background-color 5000s ease-in-out 0s;
}
.auth-input :deep(.q-field__control::before) {
	border-color: rgba(0, 0, 0, 0.24);
}
.auth-btn {
	transition: transform 0.25s var(--anim-ease-spring), box-shadow 0.25s ease;
}
.auth-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 16px rgba(80, 100, 247, 0.3);
}
.auth-btn:active {
	transform: translateY(0);
}

.auth-or-row {
	gap: 12px;
}

.auth-or-label {
	flex-shrink: 0;
	font-size: 12px;
	font-weight: 600;
	letter-spacing: 0.06em;
	text-transform: uppercase;
	color: #94a3b8;
}

.yandex-oauth-block {
	max-width: 100%;
}

.auth-yandex-hint {
	line-height: 1.35;
	max-width: 280px;
}

.yandex-widget-container {
	width: 44px;
	height: 44px;
	display: flex;
	justify-content: center;
	align-items: center;
}

.yandex-id-round {
	width: 44px !important;
	height: 44px !important;
	min-width: 44px !important;
	min-height: 44px !important;
	padding: 0 !important;
	border-radius: 50% !important;
	background: #f8fafc !important;
	border: 1px solid #e2e8f0 !important;
	box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
	transition: transform 0.25s var(--anim-ease-spring), box-shadow 0.25s ease,
		border-color 0.2s ease;
}

.yandex-id-round:hover {
	transform: translateY(-2px);
	border-color: rgba(80, 100, 247, 0.35);
	box-shadow: 0 4px 14px rgba(80, 100, 247, 0.12);
}

.yandex-id-round:active {
	transform: translateY(0);
}

.yandex-id-round__mark {
	display: block;
	width: 32px;
	height: 32px;
	object-fit: contain;
	pointer-events: none;
}
</style>