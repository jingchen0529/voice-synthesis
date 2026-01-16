import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type QuotaInfo } from '@/api'

export interface User {
  id: number
  username: string
  email: string
  nickname: string
  avatar?: string
  quotas: QuotaInfo[]
  remainingUses: number
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const initialized = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  // 获取 TTS 剩余次数
  const ttsQuota = computed(() => {
    if (!user.value?.quotas) return 0
    const quota = user.value.quotas.find((q) => q.service_code === 'tts')
    return quota ? quota.total : 0
  })

  // 获取视频混剪剩余次数
  const videoQuota = computed(() => {
    if (!user.value?.quotas) return 0
    const quota = user.value.quotas.find((q) => q.service_code === 'video')
    return quota ? quota.total : 0
  })

  // Actions
  const login = async (credentials: LoginCredentials) => {
    const response = await authApi.login(credentials)

    token.value = response.access_token
    localStorage.setItem('token', response.access_token)

    // 获取完整用户信息（包含配额）
    await fetchUserInfo()
  }

  const register = async (data: RegisterData) => {
    await authApi.register({
      username: data.username,
      email: data.email,
      password: data.password,
    })

    // 注册成功后自动登录
    await login({
      username: data.username,
      password: data.password,
    })
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    if (!token.value) return

    try {
      const userInfo = await authApi.getMe()
      user.value = {
        id: userInfo.id,
        username: userInfo.username,
        email: userInfo.email,
        nickname: userInfo.nickname,
        avatar: userInfo.avatar,
        quotas: userInfo.quotas,
        remainingUses: userInfo.remaining_uses,
      }
      localStorage.setItem('user', JSON.stringify(user.value))
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      logout()
    }
  }

  // 刷新配额信息
  const refreshQuotas = async () => {
    if (isLoggedIn.value) {
      await fetchUserInfo()
    }
  }

  // 初始化 - 只从 localStorage 恢复，不调用接口
  const initializeUser = () => {
    if (initialized.value) return

    const storedUser = localStorage.getItem('user')
    const storedToken = localStorage.getItem('token')

    if (storedUser && storedToken) {
      try {
        user.value = JSON.parse(storedUser)
        token.value = storedToken
      } catch (error) {
        console.error('Failed to parse user data:', error)
        logout()
      }
    }

    initialized.value = true
  }

  // 验证 token 有效性（需要时调用）
  const validateToken = async () => {
    if (!token.value) return false

    try {
      await fetchUserInfo()
      return true
    } catch {
      logout()
      return false
    }
  }

  // 初始化
  initializeUser()

  return {
    user,
    token,
    isLoggedIn,
    ttsQuota,
    videoQuota,
    initialized,
    login,
    register,
    logout,
    fetchUserInfo,
    refreshQuotas,
    validateToken,
  }
})
