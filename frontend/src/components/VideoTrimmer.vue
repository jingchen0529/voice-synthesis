<template>
  <div class="video-trimmer">
    <!-- 视频预览 -->
    <div class="relative bg-black rounded-xl overflow-hidden">
      <video
        ref="videoRef"
        :src="videoUrl"
        class="w-full max-h-[300px] object-contain"
        @loadedmetadata="onVideoLoaded"
        @timeupdate="onTimeUpdate"
      />
      <!-- 播放控制 -->
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
        <div class="flex items-center gap-3">
          <button @click="togglePlay" class="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white">
            <Pause v-if="isPlaying" :size="16" />
            <Play v-else :size="16" />
          </button>
          <span class="text-white text-xs font-mono">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
        </div>
      </div>
    </div>

    <!-- 时间轴裁剪 -->
    <div class="mt-4 space-y-3">
      <!-- 缩略图时间轴 -->
      <div class="relative h-16 bg-slate-100 rounded-lg overflow-hidden">
        <!-- 缩略图 -->
        <div class="absolute inset-0 flex">
          <div
            v-for="(thumb, idx) in thumbnails"
            :key="idx"
            class="flex-1 h-full bg-cover bg-center border-r border-slate-200 last:border-r-0"
            :style="{ backgroundImage: `url(${thumb.url})` }"
          />
        </div>

        <!-- 选区遮罩 -->
        <div class="absolute inset-0 pointer-events-none">
          <!-- 左侧遮罩 -->
          <div class="absolute top-0 bottom-0 left-0 bg-black/50" :style="{ width: `${startPercent}%` }" />
          <!-- 右侧遮罩 -->
          <div class="absolute top-0 bottom-0 right-0 bg-black/50" :style="{ width: `${100 - endPercent}%` }" />
        </div>

        <!-- 选区边框 -->
        <div
          class="absolute top-0 bottom-0 border-2 border-emerald-500 bg-emerald-500/10"
          :style="{ left: `${startPercent}%`, width: `${endPercent - startPercent}%` }"
        >
          <!-- 左侧拖拽手柄 -->
          <div
            class="absolute -left-2 top-0 bottom-0 w-4 cursor-ew-resize flex items-center justify-center"
            @mousedown="startDrag('start', $event)"
          >
            <div class="w-1 h-8 bg-emerald-500 rounded-full" />
          </div>
          <!-- 右侧拖拽手柄 -->
          <div
            class="absolute -right-2 top-0 bottom-0 w-4 cursor-ew-resize flex items-center justify-center"
            @mousedown="startDrag('end', $event)"
          >
            <div class="w-1 h-8 bg-emerald-500 rounded-full" />
          </div>
        </div>

        <!-- 播放位置指示器 -->
        <div
          class="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg pointer-events-none"
          :style="{ left: `${playPercent}%` }"
        />
      </div>

      <!-- 时间输入 -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <label class="text-xs text-slate-500">开始</label>
          <input
            type="text"
            :value="formatTime(trimStart)"
            @change="onStartTimeChange"
            class="w-20 px-2 py-1 text-sm border border-slate-200 rounded-lg text-center font-mono"
          />
        </div>
        <div class="flex-1 h-px bg-slate-200" />
        <div class="flex items-center gap-2">
          <label class="text-xs text-slate-500">结束</label>
          <input
            type="text"
            :value="formatTime(trimEnd)"
            @change="onEndTimeChange"
            class="w-20 px-2 py-1 text-sm border border-slate-200 rounded-lg text-center font-mono"
          />
        </div>
      </div>

      <!-- 裁剪信息 -->
      <div class="flex items-center justify-between text-sm">
        <span class="text-slate-500">
          裁剪时长: <span class="font-semibold text-emerald-600">{{ formatTime(trimEnd - trimStart) }}</span>
        </span>
        <div class="flex items-center gap-2">
          <button
            @click="previewTrim"
            class="px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-1"
          >
            <Eye :size="14" />
            预览
          </button>
          <button
            @click="confirmTrim"
            :disabled="trimming"
            class="px-3 py-1.5 text-xs font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-lg transition-colors flex items-center gap-1 disabled:opacity-50"
          >
            <Loader2 v-if="trimming" :size="14" class="animate-spin" />
            <Scissors v-else :size="14" />
            {{ trimming ? '裁剪中...' : '确认裁剪' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Play, Pause, Scissors, Eye, Loader2 } from 'lucide-vue-next'
import { videoApi } from '@/api/video'

const props = defineProps<{
  filePath: string
  videoUrl: string
}>()

const emit = defineEmits<{
  (e: 'trimmed', data: { file_path: string; preview_url: string; duration: number }): void
  (e: 'cancel'): void
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const duration = ref(0)
const currentTime = ref(0)
const isPlaying = ref(false)
const trimStart = ref(0)
const trimEnd = ref(0)
const trimming = ref(false)
const thumbnails = ref<{ url: string; time: number }[]>([])

// 拖拽状态
const dragging = ref<'start' | 'end' | null>(null)
const dragStartX = ref(0)
const dragStartValue = ref(0)

// 计算百分比
const startPercent = computed(() => (trimStart.value / duration.value) * 100 || 0)
const endPercent = computed(() => (trimEnd.value / duration.value) * 100 || 100)
const playPercent = computed(() => (currentTime.value / duration.value) * 100 || 0)

// 格式化时间
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 10)
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`
}

// 解析时间字符串
const parseTime = (timeStr: string): number => {
  const parts = timeStr.split(':')
  if (parts.length === 2) {
    const mins = parts[0] ?? '0'
    const secs = parts[1] ?? '0'
    return parseInt(mins) * 60 + parseFloat(secs)
  }
  return parseFloat(timeStr) || 0
}

// 视频加载完成
const onVideoLoaded = () => {
  if (videoRef.value) {
    duration.value = videoRef.value.duration
    trimEnd.value = duration.value
    loadThumbnails()
  }
}

// 时间更新
const onTimeUpdate = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
  }
}

// 播放/暂停
const togglePlay = () => {
  if (!videoRef.value) return

  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    // 从裁剪开始位置播放
    if (videoRef.value.currentTime < trimStart.value || videoRef.value.currentTime >= trimEnd.value) {
      videoRef.value.currentTime = trimStart.value
    }
    videoRef.value.play()
  }
  isPlaying.value = !isPlaying.value
}

// 加载缩略图
const loadThumbnails = async () => {
  try {
    const result = await videoApi.getVideoThumbnails(props.filePath, 10)
    thumbnails.value = result.thumbnails
  } catch (error) {
    console.error('加载缩略图失败:', error)
    // 使用空白占位
    thumbnails.value = Array(10).fill({ url: '', time: 0 })
  }
}

// 开始拖拽
const startDrag = (type: 'start' | 'end', event: MouseEvent) => {
  dragging.value = type
  dragStartX.value = event.clientX
  dragStartValue.value = type === 'start' ? trimStart.value : trimEnd.value

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

// 拖拽中
const onDrag = (event: MouseEvent) => {
  if (!dragging.value) return

  const container = document.querySelector('.video-trimmer .relative.h-16')
  if (!container) return

  const rect = container.getBoundingClientRect()
  const deltaX = event.clientX - dragStartX.value
  const deltaPercent = (deltaX / rect.width) * 100
  const deltaTime = (deltaPercent / 100) * duration.value

  if (dragging.value === 'start') {
    const newStart = Math.max(0, Math.min(trimEnd.value - 1, dragStartValue.value + deltaTime))
    trimStart.value = newStart
  } else {
    const newEnd = Math.max(trimStart.value + 1, Math.min(duration.value, dragStartValue.value + deltaTime))
    trimEnd.value = newEnd
  }
}

// 停止拖拽
const stopDrag = () => {
  dragging.value = null
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 时间输入变化
const onStartTimeChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const time = parseTime(input.value)
  trimStart.value = Math.max(0, Math.min(trimEnd.value - 1, time))
}

const onEndTimeChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const time = parseTime(input.value)
  trimEnd.value = Math.max(trimStart.value + 1, Math.min(duration.value, time))
}

// 预览裁剪
const previewTrim = () => {
  if (!videoRef.value) return
  videoRef.value.currentTime = trimStart.value
  videoRef.value.play()
  isPlaying.value = true

  // 到达结束位置时暂停
  const checkEnd = () => {
    if (videoRef.value && videoRef.value.currentTime >= trimEnd.value) {
      videoRef.value.pause()
      isPlaying.value = false
    } else if (isPlaying.value) {
      requestAnimationFrame(checkEnd)
    }
  }
  checkEnd()
}

// 确认裁剪
const confirmTrim = async () => {
  trimming.value = true
  try {
    const result = await videoApi.trimVideo({
      file_path: props.filePath,
      start_time: trimStart.value,
      end_time: trimEnd.value,
    })
    emit('trimmed', result)
  } catch (error) {
    console.error('裁剪失败:', error)
  } finally {
    trimming.value = false
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})
</script>
