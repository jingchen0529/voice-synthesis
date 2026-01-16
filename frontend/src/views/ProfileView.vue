<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="py-10 px-4">
    <div class="container mx-auto max-w-6xl">
      <h1 class="text-3xl font-bold text-slate-800 mb-8 text-center">个人中心</h1>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 左侧：用户信息 -->
        <div class="bg-white/80 backdrop-blur border border-slate-200 rounded-3xl p-8">
          <h2 class="text-xl font-bold text-slate-800 mb-6 flex items-center">
            <User class="w-5 h-5 mr-2 text-green-600" />
            基本信息
          </h2>

          <div class="flex items-center gap-6 mb-6">
            <a-avatar :size="72" class="bg-green-500 flex-shrink-0">
              {{ userStore.user?.nickname?.charAt(0) || userStore.user?.username?.charAt(0) || 'U' }}
            </a-avatar>
            <div>
              <p class="text-xl font-semibold text-slate-800">{{ userStore.user?.nickname || userStore.user?.username
              }}</p>
              <p class="text-slate-500">{{ userStore.user?.email }}</p>
            </div>
          </div>

          <div class="space-y-4">
            <div class="flex justify-between py-3 border-b border-slate-100">
              <span class="text-slate-500">用户名</span>
              <span class="text-slate-800 font-medium">{{ userStore.user?.username }}</span>
            </div>
            <div class="flex justify-between py-3 border-b border-slate-100">
              <span class="text-slate-500">昵称</span>
              <span class="text-slate-800 font-medium">{{ userStore.user?.nickname || '-' }}</span>
            </div>
            <div class="flex justify-between py-3">
              <span class="text-slate-500">邮箱</span>
              <span class="text-slate-800 font-medium">{{ userStore.user?.email }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧：API密钥 + 次数 -->
        <div class="space-y-6">
          <!-- API 密钥 -->
          <div class="bg-white/80 backdrop-blur border border-slate-200 rounded-3xl p-8">
            <h2 class="text-xl font-bold text-slate-800 mb-6 flex items-center m-0">
              <Key class="w-5 h-5 mr-2 text-green-600" />
              API 密钥
            </h2>

            <div v-if="keyLoading" class="text-center py-6">
              <a-spin />
            </div>

            <div v-else-if="!apiKey" class="text-center py-6">
              <p class="text-slate-500 mb-4">您还没有生成 API 密钥</p>
              <a-button type="primary" :loading="generating" @click="handleCreate"
                class="!bg-green-600 !border-green-600 hover:!bg-green-500">
                生成密钥
              </a-button>
            </div>

            <div v-else class="space-y-4">
              <div>
                <p class="text-sm text-slate-500 mb-2">Access Key</p>
                <div class="flex gap-2">
                  <a-input :value="apiKey.access_key" readonly class="font-mono text-sm" />
                  <a-button @click="copy(apiKey.access_key)" size="small">复制</a-button>
                </div>
              </div>

              <div>
                <p class="text-sm text-slate-500 mb-2">Secret Key</p>
                <div v-if="newSk" class="flex gap-2">
                  <a-input :value="newSk" readonly :type="showSk ? 'text' : 'password'" class="font-mono text-sm" />
                  <a-button @click="showSk = !showSk" size="small">{{ showSk ? '隐藏' : '显示' }}</a-button>
                  <a-button type="primary" @click="copy(newSk)" size="small"
                    class="!bg-green-600 !border-green-600">复制</a-button>
                </div>
                <div v-else class="flex items-center justify-between">
                  <span class="text-slate-400 text-sm">仅生成时显示一次</span>
                  <a-popconfirm title="重新生成后旧密钥失效" @confirm="handleRegenerate">
                    <a-button type="primary" danger size="small" :loading="regenerating" class="flex items-center">
                      <RefreshCw v-if="!refreshing" class="w-3 h-3 mr-2 flex-shrink-0" />
                      <span class="text-xs">重新生成</span>
                    </a-button>
                  </a-popconfirm>
                </div>
              </div>

              <a-alert v-if="newSk" type="success" show-icon class="mt-4">
                <template #message>请立即保存 Secret Key，刷新后无法再次查看</template>
              </a-alert>
            </div>
          </div>

          <!-- 服务次数 -->
          <div class="bg-white/80 backdrop-blur border border-slate-200 rounded-3xl p-8">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-bold text-slate-800 flex items-center m-0">
                <Zap class="w-5 h-5 mr-2 text-green-600" />
                服务配额
              </h2>
              <a-button @click="refreshQuotas" :loading="refreshing" class="flex items-center">
                <RefreshCw v-if="!refreshing" class="w-3 h-3 mr-2 flex-shrink-0" />
                <span class="text-xs">刷新配额</span>
              </a-button>
            </div>

            <div v-if="userStore.user?.quotas?.length" class="space-y-4">
              <div v-for="quota in userStore.user.quotas" :key="quota.service_code" class="bg-slate-50 rounded-xl p-4">
                <div class="flex items-center justify-between mb-2">
                  <span class="font-medium text-slate-700">{{ quota.service_name }}</span>
                  <span class="text-xl font-bold text-green-600">{{ quota.total }} 次</span>
                </div>
                <div class="text-xs text-slate-400">
                  免费 {{ quota.free_quota }} 次 · 付费 {{ quota.paid_quota }} 次
                </div>
                <a-progress :percent="getQuotaPercent(quota)" :show-info="false" :stroke-color="getQuotaColor(quota)"
                  class="mt-2" />
              </div>
            </div>
            <div v-else class="text-center py-4 text-slate-400">暂无配额</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { User, Key, Zap, RefreshCw } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { authApi, type ApiKeyInfo, type QuotaInfo } from '@/api'

const userStore = useUserStore()

const keyLoading = ref(true)
const generating = ref(false)
const regenerating = ref(false)
const refreshing = ref(false)
const showSk = ref(false)
const apiKey = ref<ApiKeyInfo | null>(null)
const newSk = ref<string | null>(null)

onMounted(async () => {
  try {
    apiKey.value = await authApi.getApiKey()
  } finally {
    keyLoading.value = false
  }
})

const handleCreate = async () => {
  generating.value = true
  try {
    const res = await authApi.createApiKey()
    apiKey.value = { id: 0, access_key: res.access_key, status: 1, created_at: '' }
    newSk.value = res.secret_key
    message.success('生成成功')
  } catch {
    message.error('生成失败')
  } finally {
    generating.value = false
  }
}

const handleRegenerate = async () => {
  regenerating.value = true
  try {
    const res = await authApi.regenerateApiKey()
    newSk.value = res.secret_key
    showSk.value = false
    message.success('重新生成成功')
  } catch {
    message.error('失败')
  } finally {
    regenerating.value = false
  }
}

const refreshQuotas = async () => {
  refreshing.value = true
  try {
    await userStore.refreshQuotas()
    message.success('已刷新')
  } finally {
    refreshing.value = false
  }
}

const copy = (text: string) => {
  navigator.clipboard.writeText(text)
  message.success('已复制')
}

const getQuotaPercent = (quota: QuotaInfo) => {
  const maxQuota = 100
  return Math.min((quota.total / maxQuota) * 100, 100)
}

const getQuotaColor = (quota: QuotaInfo) => {
  if (quota.total <= 0) return '#ff4d4f'
  if (quota.total <= 5) return '#faad14'
  return '#22c55e'
}
</script>
