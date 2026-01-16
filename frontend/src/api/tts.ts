/**
 * TTS 语音合成 API
 */
import { get, post } from '../utils/request'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// 类型定义
export interface CreateTaskResponse {
  task_id: string
  status: string
}

export interface TaskStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  download_url?: string
}

export type SupportedLanguages = Record<string, string>

export interface Speaker {
  id: number
  short_name: string
  display_name: string
  locale: string
  gender: string
  label: string
}


// 语言列表响应
export interface LocaleItem {
  value: string
  label: string
}

export interface LocalesResponse {
  locales: LocaleItem[]
  speeds: { value: string; label: string }[]
}

// 音色列表响应
export interface VoicesResponse {
  voices: Speaker[]
  total: number
}

// 直接生成音频响应
export interface GenerateAudioResponse {
  audio_url: string
  file_path: string
}

// API 方法
export const ttsApi = {
  // 获取支持的语言列表（使用 video API）
  getLanguages: async (): Promise<SupportedLanguages> => {
    const res = await get<LocalesResponse>('/video/tts/locales')
    // 转换为 SupportedLanguages 格式
    const languages: SupportedLanguages = {}
    for (const locale of res.locales) {
      languages[locale.value] = locale.label
    }
    return languages
  },

  // 获取支持的音色列表（使用 video API）
  getSpeakers: async (language?: string): Promise<Speaker[]> => {
    const query = language ? `?locale=${language}` : ''
    const res = await get<VoicesResponse>(`/video/tts/voices${query}`)
    return res.voices
  },

  // 直接生成音频（TTS 模式，不走 Celery）
  generateAudio: async (
    text: string,
    voice: string,
    rate: string = '+0%'
  ): Promise<GenerateAudioResponse> => {
    return post<GenerateAudioResponse>('/video/tts/generate-audio', {
      text,
      voice,
      rate,
      volume: '+0%',
      pitch: '+0Hz'
    })
  },

  // 创建 TTS 任务（Clone 模式，走 Celery）
  createTask: async (
    text: string,
    speakerAudio: File | null,
    language: string = 'zh',
    type: 'clone' | 'tts' = 'clone',
    voice?: string
  ): Promise<CreateTaskResponse> => {
    const formData = new FormData()
    formData.append('text', text)
    formData.append('type', type)
    formData.append('language', language)

    if (type === 'clone' && speakerAudio) {
      formData.append('speaker_audio', speakerAudio)
    } else if (type === 'tts' && voice) {
      formData.append('voice', voice)
    }

    return post<CreateTaskResponse>('/tts/create', formData)
  },

  // 查询任务状态
  getTaskStatus: async (taskId: string): Promise<TaskStatus> => {
    const token = localStorage.getItem('token')
    const response = await fetch(`${BASE_URL}/tts/${taskId}/status`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error('查询状态失败')
    }

    return response.json()
  },

  // 轮询任务进度（每秒调一次）
  pollProgress: (
    taskId: string,
    onProgress: (progress: number, message: string) => void,
    onComplete: (downloadUrl: string) => void,
    onError: (error: string) => void
  ): { stop: () => void } => {
    let stopped = false
    let lastProgress = 0

    const poll = async () => {
      if (stopped) return

      try {
        const status = await ttsApi.getTaskStatus(taskId)

        if (status.status === 'completed') {
          onProgress(100, status.message)
          onComplete(status.download_url || ttsApi.getDownloadUrl(taskId))
          return
        }

        if (status.status === 'failed') {
          onError(status.message || '合成失败')
          return
        }

        // 使用后端返回的进度，但确保进度只增不减
        const newProgress = Math.max(status.progress, lastProgress)
        lastProgress = newProgress

        onProgress(newProgress, status.message)

        // 继续轮询
        if (!stopped) {
          setTimeout(poll, 1000)
        }
      } catch (error) {
        if (!stopped) {
          onError(error instanceof Error ? error.message : '查询失败')
        }
      }
    }

    // 立即开始轮询
    poll()

    return {
      stop: () => {
        stopped = true
      }
    }
  },

  // 获取下载链接（完整 URL）
  getDownloadUrl: (taskId: string): string => {
    return `${BASE_URL}/tts/${taskId}/download`
  },
}
