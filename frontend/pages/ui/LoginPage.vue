<template>
  <div class="auth-page">
    <div class="auth-split">
      <div class="auth-left">
        <div class="auth-left-content">
          <div class="auth-logo">
            <q-icon name="school" size="32px" color="white" />
            <span class="auth-logo-text">SkillSnap</span>
          </div>
          <div class="auth-left-text">
            <h1 class="auth-left-title">Обучайте команду<br/>быстрее и эффективнее</h1>
            <p class="auth-left-subtitle">
              Интерактивные симуляторы для корпоративного обучения. Превращаем инструкции в реальный опыт.
            </p>
          </div>
          <div class="auth-left-footer">
            <div class="auth-quote">
              "SkillSnap помог нам сократить время онбординга новых сотрудников на 40%."
            </div>
          </div>
        </div>
        <div class="auth-left-bg"></div>
      </div>
      <div class="auth-right">
        <div class="auth-right-inner">
          <LoginForm class="auth-form-component" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  background: #ffffff;
}

.auth-split {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

/* LEFT SIDE (Branding) */
.auth-left {
  flex: 1;
  position: relative;
  display: none;
  background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 100%);
  color: white;
  overflow: hidden;
}

@media (min-width: 900px) {
  .auth-left {
    display: flex;
    flex-direction: column;
  }
}

.auth-left-bg {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(124, 58, 237, 0.4) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(56, 189, 248, 0.3) 0%, transparent 50%);
  z-index: 1;
}

.auth-left-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 60px;
}

.auth-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: auto;
}

.auth-logo-text {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.auth-left-text {
  margin-bottom: 60px;
}

.auth-left-title {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -1px;
  margin: 0 0 24px 0;
}

.auth-left-subtitle {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  max-width: 480px;
  margin: 0;
}

.auth-left-footer {
  margin-top: auto;
}

.auth-quote {
  font-size: 1.1rem;
  font-style: italic;
  color: rgba(255, 255, 255, 0.9);
  border-left: 4px solid rgba(255, 255, 255, 0.3);
  padding-left: 20px;
  max-width: 500px;
}

/* RIGHT SIDE (Form) */
.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #f8fafc;
}

.auth-right-inner {
  width: 100%;
  max-width: 440px;
  animation: scaleIn 0.4s var(--anim-ease-spring) backwards;
}

.auth-form-component {
  width: 100%;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  border-radius: 24px !important;
}

@media (max-width: 899px) {
  .auth-right {
    background: #e8ecf4;
    background-image:
      radial-gradient(ellipse 80% 80% at 0% -10%, rgba(80, 100, 247, 0.12), transparent 60%),
      radial-gradient(ellipse 80% 80% at 100% 110%, rgba(124, 108, 240, 0.1), transparent 60%);
  }
}
</style>

<script>
import LoginForm from '@components/features/login_page/LoginForm.vue';
export default {
  name: "LoginPage",
  components: { LoginForm },
  mounted() {
    if (this.$route.query.yandex_error) {
      this.$q.notify({
        type: "negative",
        message: "Не удалось войти через Яндекс. Проверьте Redirect URI и ключи в .env.",
        position: "top",
        timeout: 5000,
      });
      this.$router.replace({ path: "/login", query: {} });
    }
  },
}
</script>
