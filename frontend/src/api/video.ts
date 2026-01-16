/**
 * 视频混剪 API
 */
import { get, post } from '../utils/request'
import { message } from 'ant-design-vue'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// 处理 401 错误的辅助函数
const handleUnauthorized = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  message.error('登录已过期，请重新登录')
  // 使用 setTimeout 确保 message 显示后再跳转
  setTimeout(() => {
    window.location.href = '/auth?mode=login'
  }, 500)
}

// 带认证的 fetch 封装
const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = localStorage.getItem('token')
  const headers = new Headers(options.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  const response = await fetch(url, { ...options, headers })
  
  if (response.status === 401) {
    handleUnauthorized()
    throw new Error('登录已过期')
  }
  
  return response
}

// 类型定义
export interface VideoConfig {
  resolutions: { value: string; label: string }[]
  layouts: { value: string; label: string }[]
  fps_options: number[]
  platform_presets: { value: string; label: string }[]
  fit_modes: { value: string; label: string }[]
  transitions: { value: string; label: string }[]
  color_filters: { value: string; label: string }[]
  effect_types: { value: string; label: string }[]
  subtitle_positions: { value: string; label: string }[]
  output_qualities: { value: string; label: string }[]
  voice_speeds: { value: string; label: string }[]
  // 旧字段兼容
  sizes?: { value: string; label: string }[]
}

export interface VideoTaskCreate {
  topic?: string
  script: string
  script_language?: string
  voice_language?: string
  voice_name?: string
  voice_speed?: string
  voice_volume?: string
  voice_pitch?: string
  voice_audio_url?: string
  // 背景音乐
  bgm_enabled?: boolean
  bgm_path?: string
  bgm_volume?: number
  bgm_fade_in?: number
  bgm_fade_out?: number
  // 视频配置
  video_resolution?: string
  video_layout?: string
  video_fps?: number
  platform_preset?: string
  fit_mode?: string
  clip_min_duration?: number
  clip_max_duration?: number
  use_local_videos?: boolean
  local_video_dir?: string
  media_paths?: string[]
  // 转场配置
  transition_enabled?: boolean
  transition_type?: string
  transition_effect?: string
  transition_duration?: number
  // 字幕配置
  subtitle_enabled?: boolean
  subtitle_font?: string
  subtitle_size?: number
  subtitle_color?: string
  subtitle_stroke_color?: string
  subtitle_stroke_width?: number
  subtitle_position?: string
  subtitle_line_spacing?: number
  // 特效配置
  effect_type?: string
  color_filter?: string
  brightness?: number
  contrast?: number
  saturation?: number
  // 输出配置
  output_quality?: string
}

export interface CreateTaskResponse {
  task_id: string
  status: string
}

export interface TaskStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  download_url?: string
  duration?: number
}

export interface VideoTask {
  task_id: string
  topic?: string
  status: number
  progress: number
  duration?: number
  created_at?: string
}

export interface VideoTaskList {
  total: number
  page: number
  page_size: number
  items: VideoTask[]
}

export interface UploadBgmResponse {
  file_path: string
  filename: string
}

export interface UploadImageResponse {
  file_path: string
  filename: string
}

export interface UploadImagesResponse {
  files: UploadImageResponse[]
  count: number
}

export interface UploadVideoResponse {
  file_path: string
  filename: string
  size: number
}

export interface UploadVideosResponse {
  files: UploadVideoResponse[]
  count: number
}

export interface AIProvider {
  id: string
  name: string
  model: string
  available: boolean
}

export interface AIProvidersResponse {
  providers: AIProvider[]
  styles: { value: string; label: string }[]
  durations: { value: string; label: string }[]
}

export interface GenerateScriptRequest {
  topic: string
  provider?: string
  style?: string
  duration?: string
  language?: string
}

export interface GenerateScriptResponse {
  script: string
  provider: string
  topic: string
}

export interface TtsVoice {
  id: number
  short_name: string
  display_name: string
  locale: string
  gender: string
  label: string
}

export interface TtsVoicesResponse {
  voices: TtsVoice[]
  total: number
}

export interface TtsLocalesResponse {
  locales: { value: string; label: string }[]
  speeds: { value: string; label: string }[]
}

// API 方法
export const videoApi = {
  // 获取视频配置选项
  getConfig: () => get<VideoConfig>('/video/config'),

  // 创建视频任务
  createTask: async (data: VideoTaskCreate): Promise<CreateTaskResponse> => {
    const response = await authFetch(`${BASE_URL}/video/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '创建任务失败')
    }

    return response.json()
  },

  // 查询任务状态
  getTaskStatus: async (taskId: string): Promise<TaskStatus> => {
    const response = await authFetch(`${BASE_URL}/video/${taskId}/status`)

    if (!response.ok) {
      throw new Error('查询状态失败')
    }

    return response.json()
  },

  // 轮询任务进度
  pollProgress: (
    taskId: string,
    onProgress: (progress: number, message: string) => void,
    onComplete: (downloadUrl: string, duration?: number) => void,
    onError: (error: string) => void
  ): { stop: () => void } => {
    let stopped = false
    let lastProgress = 0

    const poll = async () => {
      if (stopped) return

      try {
        const status = await videoApi.getTaskStatus(taskId)

        if (status.status === 'completed') {
          onProgress(100, status.message)
          onComplete(status.download_url || videoApi.getDownloadUrl(taskId), status.duration)
          return
        }

        if (status.status === 'failed') {
          onError(status.message || '视频生成失败')
          return
        }

        const newProgress = Math.max(status.progress, lastProgress)
        lastProgress = newProgress

        onProgress(newProgress, status.message)

        if (!stopped) {
          setTimeout(poll, 1000)
        }
      } catch (error) {
        if (!stopped) {
          onError(error instanceof Error ? error.message : '查询失败')
        }
      }
    }

    poll()

    return {
      stop: () => {
        stopped = true
      },
    }
  },

  // 获取下载链接
  getDownloadUrl: (taskId: string): string => {
    return `${BASE_URL}/video/${taskId}/download`
  },

  // 上传背景音乐
  uploadBgm: async (file: File): Promise<UploadBgmResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await authFetch(`${BASE_URL}/video/upload/bgm`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '上传失败')
    }

    return response.json()
  },

  // 上传自定义配音
  uploadCustomAudio: async (file: File): Promise<UploadBgmResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await authFetch(`${BASE_URL}/video/upload/voice`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '上传失败')
    }

    return response.json()
  },

  // 获取任务列表
  getTaskList: async (page: number = 1, pageSize: number = 10): Promise<VideoTaskList> => {
    const response = await authFetch(`${BASE_URL}/video/list?page=${page}&page_size=${pageSize}`)

    if (!response.ok) {
      throw new Error('获取列表失败')
    }

    return response.json()
  },

  // 上传图片素材
  uploadImages: async (files: FileList | File[]): Promise<UploadImagesResponse> => {
    const formData = new FormData()

    for (const file of files) {
      formData.append('files', file)
    }

    const response = await authFetch(`${BASE_URL}/video/upload/images`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '上传失败')
    }

    return response.json()
  },

  // 上传视频素材（最大 150MB）
  uploadVideos: async (files: FileList | File[]): Promise<UploadVideosResponse> => {
    const formData = new FormData()

    for (const file of files) {
      formData.append('files', file)
    }

    const response = await authFetch(`${BASE_URL}/video/upload/videos`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '上传失败')
    }

    return response.json()
  },

  // 获取 AI 服务商列表
  getAIProviders: async (): Promise<AIProvidersResponse> => {
    const response = await authFetch(`${BASE_URL}/video/ai/providers`)

    if (!response.ok) {
      throw new Error('获取 AI 服务商列表失败')
    }

    return response.json()
  },

  // AI 生成文案
  generateScript: async (data: GenerateScriptRequest): Promise<GenerateScriptResponse> => {
    const response = await authFetch(`${BASE_URL}/video/ai/generate-script`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '文案生成失败')
    }

    return response.json()
  },

  // 获取 TTS 音色列表
  getTtsVoices: async (locale?: string, gender?: string): Promise<TtsVoicesResponse> => {
    const params = new URLSearchParams()
    if (locale) params.append('locale', locale)
    if (gender) params.append('gender', gender)

    const response = await fetch(`${BASE_URL}/video/tts/voices?${params.toString()}`)

    if (!response.ok) {
      throw new Error('获取音色列表失败')
    }

    return response.json()
  },

  // 获取 TTS 语言列表
  getTtsLocales: async (): Promise<TtsLocalesResponse> => {
    const response = await fetch(`${BASE_URL}/video/tts/locales`)

    if (!response.ok) {
      throw new Error('获取语言列表失败')
    }

    return response.json()
  },

  // 同步 TTS 音色
  syncTtsVoices: async (): Promise<{ message: string }> => {
    const response = await fetch(`${BASE_URL}/video/tts/sync-voices`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('同步失败')
    }

    return response.json()
  },

  // 生成配音并获取字幕时间戳
  generateAudioWithSubtitles: async (data: {
    text: string
    voice: string
    rate?: string
    volume?: string
    pitch?: string
  }): Promise<{
    audio_url: string
    file_path: string
    word_subtitles: { text: string; start: number; end: number }[]
    sentence_subtitles: { text: string; start: number; end: number; words?: { text: string; start: number; end: number }[] }[]
  }> => {
    const response = await authFetch(`${BASE_URL}/video/tts/generate-audio-with-subtitles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '生成配音失败')
    }

    return response.json()
  },

  // 获取视频信息
  getVideoInfo: async (filePath: string): Promise<{
    duration: number
    width: number
    height: number
    fps: number
  }> => {
    const formData = new FormData()
    formData.append('file_path', filePath)

    const response = await authFetch(`${BASE_URL}/video/media/video-info`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '获取视频信息失败')
    }

    return response.json()
  },

  // 裁剪视频
  trimVideo: async (data: {
    file_path: string
    start_time: number
    end_time: number
  }): Promise<{
    file_path: string
    preview_url: string
    duration: number
    width: number
    height: number
  }> => {
    const response = await authFetch(`${BASE_URL}/video/media/trim-video`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '裁剪视频失败')
    }

    return response.json()
  },

  // 获取视频缩略图
  getVideoThumbnails: async (filePath: string, count: number = 10): Promise<{
    thumbnails: { url: string; time: number }[]
  }> => {
    const formData = new FormData()
    formData.append('file_path', filePath)
    formData.append('count', count.toString())

    const response = await authFetch(`${BASE_URL}/video/media/thumbnails`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '获取缩略图失败')
    }

    return response.json()
  },
}
