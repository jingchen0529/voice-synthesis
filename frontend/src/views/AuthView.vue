<template>
  <div class="auth-page">
    <!-- 左侧：系统介绍 -->
    <div class="left-panel">
      <div class="left-content">
        <div class="logo">
          <div class="logo-icon">
            <Zap :size="32" />
          </div>
          <span class="logo-text">Integration Platform</span>
        </div>

        <h1 class="welcome-title">欢迎使用</h1>
        <p class="welcome-subtitle">一站式 AI 内容创作平台</p>

        <div class="features">
          <div class="feature-item">
            <Mic :size="28" />
            <span>语音克隆 - 多语言语音合成</span>
          </div>
          <div class="feature-item">
            <Video :size="28" />
            <span>视频混剪 - AI 智能剪辑</span>
          </div>
          <div class="feature-item">
            <TrendingUp :size="28" />
            <span>TikTok 分析 - 数据采集</span>
          </div>
        </div>
      </div>

      <div class="left-footer">© {{ new Date().getFullYear() }} Integration Platform</div>
    </div>

    <!-- 右侧：登录/注册表单 -->
    <div class="right-panel">
      <div class="form-container">
        <h2 class="form-title">{{ isLogin ? '登录' : '注册' }}</h2>

        <!-- 登录表单 -->
        <a-form v-if="isLogin" :model="loginForm" :rules="loginRules" @finish="handleLogin" layout="vertical">
          <a-form-item name="username">
            <a-input v-model:value="loginForm.username" placeholder="用户名" size="large">
              <template #prefix><User :size="16" class="input-icon" /></template>
            </a-input>
          </a-form-item>

          <a-form-item name="password">
            <a-input-password v-model:value="loginForm.password" placeholder="密码" size="large">
              <template #prefix><Lock :size="16" class="input-icon" /></template>
            </a-input-password>
          </a-form-item>

          <div class="form-options">
            <a-checkbox v-model:checked="rememberMe">记住我</a-checkbox>
            <router-link to="/forgot-password" class="forgot-link">忘记密码?</router-link>
          </div>

          <a-button type="primary" html-type="submit" block :loading="loading" class="submit-btn">登录</a-button>
        </a-form>

        <!-- 注册表单 -->
        <a-form v-else :model="registerForm" :rules="registerRules" @finish="handleRegister" layout="vertical">
          <a-form-item name="username">
            <a-input v-model:value="registerForm.username" placeholder="用户名" size="large">
              <template #prefix><User :size="16" class="input-icon" /></template>
            </a-input>
          </a-form-item>

          <a-form-item name="email">
            <a-input v-model:value="registerForm.email" placeholder="邮箱" size="large">
              <template #prefix><Mail :size="16" class="input-icon" /></template>
            </a-input>
          </a-form-item>

          <a-form-item name="password">
            <a-input-password v-model:value="registerForm.password" placeholder="密码" size="large">
              <template #prefix><Lock :size="16" class="input-icon" /></template>
            </a-input-password>
          </a-form-item>

          <a-button type="primary" html-type="submit" block :loading="loading" class="submit-btn">注册</a-button>
        </a-form>

        <div class="switch-mode">
          <span>{{ isLogin ? '没有账号?' : '已有账号?' }}</span>
          <a @click="toggleMode">{{ isLogin ? '立即注册' : '立即登录' }}</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { Zap, Mic, Video, TrendingUp, User, Lock, Mail } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import type { Rule } from 'ant-design-vue/es/form'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const mode = ref<'login' | 'register'>((route.query.mode as 'login' | 'register') || 'login')
const isLogin = computed(() => mode.value === 'login')
const rememberMe = ref(false)
const loading = ref(false)

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', password: '' })

const loginRules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules: Record<string, Rule[]> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }],
}

const toggleMode = () => {
  mode.value = isLogin.value ? 'register' : 'login'
  router.replace({ query: { ...route.query, mode: mode.value } })
}

const handleLogin = async () => {
  loading.value = true
  try {
    await userStore.login(loginForm)
    message.success('登录成功')
    router.push((route.query.redirect as string) || '/tts')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '登录失败')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value = true
  try {
    await userStore.register(registerForm)
    message.success('注册成功')
    router.push('/tts')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  height: 100vh;
  display: flex;
  overflow: hidden;
}

.left-panel {
  flex: 1;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: white;
  position: relative;
}

.left-content {
  max-width: 400px;
  text-align: center;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
}

.welcome-title {
  font-size: 36px;
  font-weight: 800;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0 0 32px 0;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  font-size: 14px;
}

.left-footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
  opacity: 0.7;
}

.right-panel {
  width: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.form-container {
  width: 100%;
  max-width: 320px;
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 24px 0;
}

.input-icon {
  color: #94a3b8;
}

.form-options {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  font-size: 13px;
}

.forgot-link {
  color: #10b981;
}

.submit-btn {
  height: 44px;
  font-weight: 600;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
}

.switch-mode {
  text-align: center;
  margin-top: 20px;
  font-size: 13px;
  color: #64748b;
}

.switch-mode a {
  color: #10b981;
  margin-left: 4px;
  cursor: pointer;
}

:deep(.ant-input-affix-wrapper) {
  padding: 10px 12px;
  border-radius: 8px;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .left-panel { display: none; }
  .right-panel { width: 100%; }
}
</style>
