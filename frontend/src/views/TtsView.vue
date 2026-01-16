<template>
  <div class="container mx-auto max-w-7xl px-4 py-6 lg:py-10">
    <div class="flex flex-col gap-6 rounded-xl border border-slate-200 py-6 shadow-sm mb-18 bg-white/30">
      <div class="px-6">
        <div class="space-y-6 lg:space-y-8 w-full">
          <div class="flex justify-center">
            <div class="flex bg-slate-200 rounded-full p-1">
              <button @click="activeTab = 'clone'" :class="[
                'px-6 py-2 rounded-full text-sm font-medium transition-all duration-200',
                activeTab === 'clone'
                  ? 'bg-white text-slate-800 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              ]">
                语音克隆
              </button>
              <button @click="activeTab = 'tts'" :class="[
                'px-6 py-2 rounded-full text-sm font-medium transition-all duration-200',
                activeTab === 'tts'
                  ? 'bg-white text-slate-800 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              ]">
                文本转语音
              </button>
            </div>
          </div>

          <!-- 输入区域 - idle 状态显示 -->
          <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 lg:gap-8">
            <!-- 左侧：文本输入 -->
            <div
              class="flex flex-col gap-6 border border-slate-200 py-6 shadow-lg bg-foreground/3 rounded-2xl overflow-hidden lg:col-span-3">
              <div class="p-4 lg:p-6 space-y-4">
                <div class="space-y-3">
                  <label class="block text-sm font-semibold text-slate-800 flex items-center gap-2">
                    <FileAudio class="h-4 w-4 text-emerald-500" />
                    要朗读的文本
                  </label>
                  <textarea v-model="textInput" :disabled="currentState === 'generating'"
                    class="w-full min-h-[200px] lg:min-h-[300px] p-3 lg:p-4 text-base border-2 border-slate-200 focus:border-emerald-500 rounded-xl transition-all duration-200 resize-none focus:outline-none bg-white text-slate-800"
                    placeholder="请输入要朗读的文本..."></textarea>
                  <div class="flex justify-between items-center">
                    <p class="text-xs text-gray-500 flex items-center gap-1">
                      <Zap class="h-3 w-3" />
                      请输入文本
                    </p>
                    <div class="text-xs text-gray-500">
                      {{ textInput.length }} / 500
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <!-- 右侧：音频上传和生成 (Clone Mode) / 设置 (TTS Mode) -->
            <div
              class="flex flex-col gap-6 border border-slate-200 py-6 shadow-lg bg-foreground/3 rounded-2xl overflow-hidden lg:col-span-2">
              <div class="p-4 lg:p-6 space-y-4 lg:space-y-6">
                <!-- Clone Mode UI -->
                <div v-if="activeTab === 'clone'" class="space-y-4">
                  <div class="flex items-center gap-3">
                    <input ref="audioInputRef" accept=".mp3,.wav,.wma,.ogg,.flac,.amr,.m4a,.aiff,.aac,audio/*"
                      class="hidden" type="file" @change="handleFileChange" />
                    <a-button @click="handleUploadClick"
                      class="flex items-center justify-center gap-2 h-10 lg:h-12 px-4 lg:px-6 border-2 border-slate-200 hover:border-emerald-500 rounded-full transition-all duration-200 w-full text-sm lg:text-base bg-white hover:bg-slate-50">
                      <Upload class="h-4 w-4 text-emerald-500" />
                      选择音频
                    </a-button>
                  </div>
                  <div class="space-y-3">
                    <div v-if="selectedFile" class="flex items-center gap-2 p-3 border border-green-200 rounded-full">
                      <CircleCheckBig class="h-4 w-4 text-green-600 flex-shrink-0" />
                      <span class="text-sm font-medium text-green-800 truncate">{{ selectedFile.name }}</span>
                    </div>
                    <div v-else class="flex items-center gap-2 p-3 bg-slate-100 border border-slate-200 rounded-full">
                      <Info class="h-4 w-4 text-gray-500" />
                      <span class="text-sm text-gray-500">
                        请选择音频文件
                      </span>
                    </div>
                    <p class="text-xs text-gray-500 flex items-center gap-1">
                      <Music class="h-4 w-4" />
                      支持格式：MP3、WAV、WMA、OGG、FLAC、AMR、M4A、AIFF、AAC
                    </p>
                     <p class="text-xs text-gray-500 flex items-center gap-1">
                      <Upload class="h-4 w-4" />
                      上传音频文件小于10M，时长10-60S
                    </p>
                  </div>
                </div>

                <!-- TTS Mode UI -->
                <div v-else class="space-y-6">
                  <!-- 语言选择 -->
                  <div class="space-y-2">
                    <label class="block text-sm font-semibold text-slate-800">语言</label>
                    <a-select v-model:value="selectedLanguage" class="w-full" size="large" @change="handleLanguageChange">
                       <a-select-option v-for="(name, code) in supportedLanguages" :key="code" :value="code">
                        {{ name }}
                      </a-select-option>
                    </a-select>
                  </div>

                  <!-- 说话者选择 -->
                  <div class="space-y-2">
                    <label class="block text-sm font-semibold text-slate-800">说话者</label>
                    <a-select v-model:value="selectedSpeakerId" class="w-full" size="large" :loading="loadingSpeakers" placeholder="请选择说话者">
                      <a-select-option v-for="speaker in speakers" :key="speaker.short_name" :value="speaker.short_name">
                        {{ speaker.label }}
                      </a-select-option>
                    </a-select>
                  </div>
                </div>

                <a-divider style="margin: 15px 0;background-color:#e5e7eb" />

                <a-button @click="handleGenerate" type="primary"
                  :disabled="!canGenerate || currentState === 'generating'" :loading="currentState === 'generating'"
                  class="flex items-center justify-center gap-2 w-full h-12 lg:h-14 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white text-base lg:text-lg font-semibold rounded-full shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed border-none">
                  <Sparkles v-if="currentState !== 'generating'" class="h-4 w-4" />
                  {{ currentState === 'generating' ? '生成中...' : '生成' }}
                </a-button>
              </div>
            </div>
          </div>

          <!-- 进度条 - generating 状态显示 -->
          <div v-if="currentState === 'generating'" class="bg-white border border-slate-200 shadow-2xl rounded-2xl">
            <div class="p-8 lg:p-10">
              <div class="space-y-6">
                <div class="relative">
                  <a-progress :percent="progress" :show-info="true" strokeColor="#10b981" />
                </div>
                <div class="flex items-center justify-center px-1">
                  <div class="space-y-1">
                    <div class="text-xs text-slate-400">不要刷新页面</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 成功 - complete 状态显示 -->
          <div v-if="currentState === 'complete'" class="w-full">
            <div
              class="flex flex-col rounded-xl py-6 shadow-lg overflow-hidden bg-white/50 border border-slate-200 pt-12 gap-2">
              <div class="grid auto-rows-min items-start gap-1.5 px-6 text-green-500 pb-0 -mt-1 -mx-1">
                <div class="flex items-center justify-center gap-3 text-2xl lg:text-3xl font-bold">
                  语音生成完成！
                </div>
              </div>
              <div class="px-6">
                <div class="text-center mb-6">
                  <div class="w-16 h-16 lg:w-20 lg:h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CircleCheckBig class="h-12 w-12 text-green-500 flex-shrink-0" />
                  </div>
                  <h3 class="text-xl lg:text-lg text-gray-500 mb-2 pt-10">
                    您的语音克隆已成功创建。
                  </h3>
                </div>
                <div class="bg-white rounded-xl p-4 lg:p-6 mb-6 border border-slate-200">
                  <div class="flex items-center gap-3 mb-4">
                    <div class="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
                      <Music class="h-4 w-4 text-emerald-600" />
                    </div>
                    <div class="font-semibold text-slate-800 text-base lg:text-lg">
                      生成的音频
                    </div>
                  </div>
                  <audio controls class="w-full h-12 rounded-lg" :src="generatedAudioUrl!">
                    Your browser does not support the audio element.
                  </audio>
                </div>
                <div class="flex flex-col sm:flex-row gap-3 justify-center">
                  <a-button type="primary" @click="handleDownload"
                    class="min-w-[140px] flex items-center justify-center rounded-full bg-green-600">
                    <Download class="h-4 w-4 mr-2" />
                    下载
                  </a-button>
                  <a-button @click="handleReset" class="min-w-[140px] flex items-center justify-center rounded-full">
                    <Sparkles class="h-4 w-4 mr-2" />
                    重新生成
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  Upload,
  Sparkles,
  FileAudio,
  Zap,
  Info,
  Music,
  CircleCheckBig,
  Download,
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { ttsApi } from '@/api'
import type { Speaker, SupportedLanguages } from '@/api/tts'

const router = useRouter()
const userStore = useUserStore()

// 状态
type State = 'idle' | 'generating' | 'complete'
const currentState = ref<State>('idle')
const activeTab = ref<'clone' | 'tts'>('clone')

// 语音克隆表单数据
const textInput = ref('')
const audioInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const generatedAudioUrl = ref<string | null>(null)

// TTS 表单数据
const supportedLanguages = ref<SupportedLanguages>({})
const selectedLanguage = ref('')
const speakers = ref<Speaker[]>([])
const selectedSpeakerId = ref<string | undefined>(undefined)
const loadingSpeakers = ref(false)

// 进度
const progress = ref(0)
const progressMessage = ref('')

// 轮询控制
let pollController: { stop: () => void } | null = null

// 计算是否可以生成
const canGenerate = computed(() => {
  const hasText = textInput.value.trim().length > 0
  if (activeTab.value === 'clone') {
    return hasText && selectedFile.value !== null
  } else {
    return hasText && !!selectedSpeakerId.value
  }
})

// 加载语言和说话人
onMounted(async () => {
  try {
    // 获取支持的语言
    const langs = await ttsApi.getLanguages()
    if (langs && Object.keys(langs).length > 0) {
      supportedLanguages.value = langs
      // 设置默认语言：优先选择 zh-CN，否则选第一个
      const keys = Object.keys(langs)
      const defaultLang = keys.find(k => k === 'zh-CN') || keys[0]
      if (defaultLang) {
        selectedLanguage.value = defaultLang
        // 加载默认语言的说话人
        await loadSpeakers(defaultLang)
      }
    }
  } catch (error) {
    console.error('Failed to load initial data:', error)
  }
})

// 加载说话人列表
const loadSpeakers = async (lang: string) => {
  loadingSpeakers.value = true
  try {
    const list = await ttsApi.getSpeakers(lang)
    speakers.value = list
    // 如果当前选中的说话人不在新列表中，重置选择
    if (selectedSpeakerId.value && !list.find(s => s.short_name === selectedSpeakerId.value)) {
      selectedSpeakerId.value = undefined
    }
    // 如果没有选中且列表不为空，默认选中第一个
    if (!selectedSpeakerId.value && list.length > 0) {
      selectedSpeakerId.value = list[0]?.short_name
    }
  } catch (error) {
    message.error('加载语音列表失败')
  } finally {
    loadingSpeakers.value = false
  }
}

// 监听语言变化
const handleLanguageChange = async (value: string) => {
  await loadSpeakers(value)
}

// 处理上传按钮点击
const handleUploadClick = () => {
  audioInputRef.value?.click()
}

// 文件选择处理
const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) {
    selectedFile.value = null
    return
  }

  // 验证文件大小 (10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    message.error('文件大小不能超过 10MB')
    return
  }

  // 验证文件类型
  const validTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/mp4', 'audio/aac']
  const isValidType =
    validTypes.includes(file.type) || /\.(mp3|wav|wma|ogg|flac|amr|m4a|aiff|aac)$/i.test(file.name)

  if (!isValidType) {
    message.error('不支持的音频格式')
    return
  }

  selectedFile.value = file
}

// 处理生成
const handleGenerate = async () => {
  if (!canGenerate.value) {
    if (activeTab.value === 'clone') {
       message.warning('请输入文本并上传音频文件')
    } else {
       message.warning('请输入文本并选择说话者')
    }
    return
  }

  // 检查是否登录
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再使用')
    router.push({ path: '/auth', query: { redirect: '/tts' } })
    return
  }

  // 检查剩余次数
  if (userStore.ttsQuota <= 0) {
    message.error('您的配额已用完，请联系管理员充值')
    return
  }

  currentState.value = 'generating'
  progress.value = 0

  try {
    if (activeTab.value === 'tts') {
      // TTS 模式：直接调用生成接口
      progress.value = 30
      progressMessage.value = '正在生成语音...'

      const result = await ttsApi.generateAudio(
        textInput.value,
        selectedSpeakerId.value!
      )

      progress.value = 100
      progressMessage.value = '合成完成'
      generatedAudioUrl.value = result.audio_url
      currentState.value = 'complete'
      userStore.refreshQuotas()
      message.success('生成成功！')
    } else {
      // Clone 模式：创建任务并轮询
      const task = await ttsApi.createTask(
        textInput.value,
        selectedFile.value!,
        'zh',
        'clone'
      )

      // 轮询进度
      pollController = ttsApi.pollProgress(
        task.task_id,
        // onProgress
        (prog, msg) => {
          progress.value = prog
          progressMessage.value = msg
        },
        // onComplete
        (downloadUrl) => {
          progress.value = 100
          progressMessage.value = '合成完成'
          generatedAudioUrl.value = downloadUrl
          currentState.value = 'complete'
          userStore.refreshQuotas()
          message.success('生成成功！')
        },
        // onError
        (error) => {
          message.error(error)
          currentState.value = 'idle'
        },
      )
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '创建任务失败'
    message.error(errorMessage)
    currentState.value = 'idle'
  }
}

// 下载音频
const handleDownload = () => {
  if (generatedAudioUrl.value) {
    const link = document.createElement('a')
    link.href = generatedAudioUrl.value
    link.download = 'generated_audio.wav'
    link.click()
  }
}

// 重新生成
const handleReset = () => {
  currentState.value = 'idle'
  progress.value = 0
  progressMessage.value = ''
  generatedAudioUrl.value = null
}

// 清理
onUnmounted(() => {
  if (pollController) {
    pollController.stop()
  }
})
</script>

<style scoped>
/* 所有按钮 hover 绿色 */
:deep(.ant-btn):hover {
  border-color: #10b981 !important;
  color: #10b981 !important;
}

:deep(.ant-btn-primary):hover {
  background-color: #059669 !important;
  border-color: #059669 !important;
  color: #fff !important;
}

/* 进度区域 */
.progress-section {
  margin-top: 32px;
}

.progress-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-radius: 16px;
  overflow: hidden;
}

.progress-content {
  padding: 32px 40px;
}

.progress-bar-wrapper {
  width: 100%;
  height: 16px;
  background: #f1f5f9;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.5);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.06);
  margin-bottom: 24px;
}

.progress-bar {
  position: relative;
  height: 100%;
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
  border-radius: 8px;
  transition: width 0.5s ease-out;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}

.progress-shimmer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.3) 50%,
      transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}

.progress-info {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 0 4px;
}

.progress-text {
  font-size: 12px;
  color: #6b7280;
}

.progress-percent {
  font-size: 32px;
  font-weight: 900;
  font-style: italic;
  letter-spacing: -1px;
  color: #10b981;
}

/* 结果区域 */
.result-section {
  margin-top: 40px;
}

.result-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  text-align: center;
}

.result-header {
  margin-bottom: 24px;
}

.result-title {
  font-size: 24px;
  font-weight: 700;
  color: #10b981;
  margin: 0 0 16px 0;
}

.success-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 16px 0;
}

.success-icon {
  color: #10b981;
}

.result-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 8px 0 0 0;
}

.audio-card {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
}

.audio-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.audio-icon-wrapper {
  width: 32px;
  height: 32px;
  background: rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.audio-icon {
  color: #10b981;
}

.audio-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.audio-player {
  width: 100%;
  height: 48px;
  border-radius: 8px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 16px;
  justify-content: center;
}

@media (min-width: 640px) {
  .action-buttons {
    flex-direction: row;
  }
}
</style>
