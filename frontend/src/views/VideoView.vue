<template>
  <div class="min-h-screen lg:py-10 text-slate-800">
    <main class="max-w-7xl mx-auto p-6 lg:p-8">
      <!-- 头部 - 步骤指示（所有状态可见） -->
      <div class="mb-10 bg-white/30 p-4 rounded-2xl border transition-all">
        <a-steps :current="currentStep" :items="stepItems" label-placement="vertical"></a-steps>
      </div>

      <!-- idle 状态 -->
      <div v-if="currentState === 'idle'" class="space-y-6">
        <!-- 主内容网格 - 两行布局 -->
        <div class="space-y-6">
          <!-- 第一行：文案编辑 + 素材资源 -->
          <div class="grid grid-cols-12 gap-6 items-stretch">
            <!-- 文案编辑器 -->
            <section
              class="col-span-12 lg:col-span-7 group relative bg-white/30 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all flex flex-col">
              <div
                class="absolute -left-px top-6 bottom-6 w-1 bg-emerald-500 rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity">
              </div>
              <div class="p-6 space-y-5 flex-1 flex flex-col">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="p-2.5 bg-slate-100 rounded-xl">
                      <FileText :size="20" />
                    </div>
                    <div>
                      <h3 class="text-base font-bold">文案编辑</h3>
                      <p class="text-xs text-slate-400 font-medium">STEP 1</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <a-select v-model:value="selectedProvider" size="small" style="min-width: 100px">
                      <a-select-option value="auto">自动</a-select-option>
                      <a-select-option v-for="p in aiProviders.filter(x => x.available)" :key="p.id" :value="p.id">{{
                        p.name }}</a-select-option>
                    </a-select>
                    <a-select v-model:value="selectedStyle" size="small" style="min-width: 90px">
                      <a-select-option v-for="s in aiStyles" :key="s.value" :value="s.value">{{ s.label
                        }}</a-select-option>
                    </a-select>
                    <button @click="generateScript" :disabled="generatingScript"
                      class="text-emerald-600 hover:bg-emerald-50 px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5 whitespace-nowrap">
                      <Loader2 v-if="generatingScript" :size="14" class="animate-spin" />
                      <Wand2 v-else :size="14" />
                      AI生成
                    </button>
                  </div>
                </div>

                <input v-model="form.topic" type="text" placeholder="输入视频主题（用于 AI 生成文案）"
                  class="w-full text-lg font-semibold placeholder:text-slate-300 border-none bg-transparent focus:ring-0 px-0 py-2 border-b border-slate-100 focus:border-emerald-500 transition-colors outline-none" />
                <div class="relative">
                  <textarea v-model="form.script" :rows="scriptRows" placeholder="在这里输入视频文案内容..."
                    class="w-full bg-slate-50 hover:bg-slate-100/80 focus:bg-white border border-slate-200 focus:border-emerald-400 rounded-xl p-5 text-sm leading-relaxed resize-none focus:ring-4 focus:ring-emerald-500/5 outline-none transition-all placeholder:text-slate-400"></textarea>
                  <div class="absolute bottom-3 right-3">
                    <span
                      class="text-xs font-medium text-slate-400 bg-white/80 backdrop-blur px-2 py-1 rounded-md border border-slate-100">
                      {{ form.script.length }} / 5000
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <!-- 素材资源 -->
            <section
              class="col-span-12 lg:col-span-5 group relative bg-white/30 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col">
              <div
                class="absolute -left-px top-6 bottom-6 w-1 bg-emerald-500 rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity">
              </div>
              <div class="p-6 space-y-5 flex-1 flex flex-col">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="p-2.5 bg-slate-100 rounded-xl">
                      <ImageIcon :size="20" />
                    </div>
                    <div>
                      <h3 class="text-base font-bold">素材资源</h3>
                      <p class="text-xs text-slate-400 font-medium">STEP 3</p>
                    </div>
                  </div>
                  <input ref="mediaInputRef" type="file" accept=".jpg,.jpeg,.png,.webp,.gif,.mp4,.mov,.avi,.mkv,.webm"
                    multiple class="hidden" @change="handleMediaUpload" />
                  <button @click="mediaInputRef?.click()" :disabled="uploadingMedia"
                    class="text-emerald-600 hover:bg-emerald-50 px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors flex items-center gap-1.5">
                    <Loader2 v-if="uploadingMedia" :size="14" class="animate-spin" />
                    <Upload v-else :size="14" />
                    上传
                  </button>
                </div>

                <!-- 已上传素材预览 -->
                <div v-if="uploadedImages.length > 0 || uploadedVideos.length > 0" class="flex flex-wrap gap-2">
                  <a-image-preview-group>
                    <div v-for="(img, idx) in uploadedImages" :key="'img-' + idx" class="relative group/item">
                      <div class="w-16 h-16 rounded-lg overflow-hidden border border-slate-200">
                        <a-image :src="getMediaUrl(img.file_path)" class="w-full h-full object-cover" :preview="{ src: getMediaUrl(img.file_path) }" />
                      </div>
                      <button @click.stop="removeImage(idx)"
                        class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center opacity-0 group-hover/item:opacity-100 transition-opacity z-10">×</button>
                    </div>
                  </a-image-preview-group>
                  <div v-for="(vid, idx) in uploadedVideos" :key="'vid-' + idx" class="relative group/item">
                    <div class="w-16 h-16 rounded-lg overflow-hidden border border-slate-200 bg-slate-900 relative cursor-pointer" @click="previewVideo(vid.file_path)">
                      <video :src="getMediaUrl(vid.file_path)" class="w-full h-full object-cover" muted></video>
                      <div class="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/40 transition-colors">
                        <Play :size="16" class="text-white" />
                      </div>
                    </div>
                    <button @click.stop="removeVideo(idx)"
                      class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center opacity-0 group-hover/item:opacity-100 transition-opacity z-10">×</button>
                  </div>
                </div>

                <!-- 拖拽上传区 -->
                <div @click="mediaInputRef?.click()"
                  class="flex-1 border-2 border-dashed border-slate-200 hover:border-emerald-400 rounded-xl bg-slate-50/50 flex flex-col items-center justify-center py-8 px-4 text-center cursor-pointer transition-colors group/drop min-h-[120px]">
                  <div
                    class="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center text-slate-400 group-hover/drop:text-emerald-500 group-hover/drop:scale-110 transition-all mb-3">
                    <ImageIcon :size="24" />
                  </div>
                  <h4 class="font-semibold text-slate-600 text-sm">拖拽文件到这里</h4>
                  <p class="text-xs text-slate-400 mt-1">图片 ≤10MB | 视频 ≤150MB</p>
                </div>
              </div>
            </section>
          </div>

          <!-- 第二行：AI配音 + 视频配置 -->
          <div class="grid grid-cols-12 gap-6 items-start">
            <!-- AI 配音设置 -->
            <section
              class="col-span-12 lg:col-span-7 group relative bg-white/30 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col">
              <div
                class="absolute -left-px top-6 bottom-6 w-1 bg-emerald-500 rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity">
              </div>
              <div class="p-6 space-y-5 flex-1">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div class="p-2.5 bg-slate-100 rounded-xl">
                      <Mic :size="20" />
                    </div>
                    <div>
                      <h3 class="text-base font-bold">配音设置</h3>
                      <p class="text-xs text-slate-400 font-medium">STEP 2</p>
                    </div>
                  </div>
                  <!-- 预估时长显示 -->
                  <div v-if="audioDuration > 0" class="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 border border-emerald-200 text-emerald-600">
                    <Clock :size="12" />
                    预估视频 {{ formatTime(audioDuration) }}
                  </div>
                </div>

                <!-- 配音类型切换 -->
                <div class="flex gap-2 p-1 bg-slate-100 rounded-lg">
                  <button @click="voiceType = 'tts'" 
                    :class="`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-all ${voiceType === 'tts' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`">
                    <span class="flex items-center justify-center gap-1.5">
                      <Mic :size="14" />
                      AI 配音
                    </span>
                  </button>
                  <button @click="voiceType = 'custom'" 
                    :class="`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-all ${voiceType === 'custom' ? 'bg-white text-emerald-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`">
                    <span class="flex items-center justify-center gap-1.5">
                      <Upload :size="14" />
                      上传配音
                    </span>
                  </button>
                </div>

                <!-- TTS 配音设置 -->
                <div v-if="voiceType === 'tts'" class="space-y-4">
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div class="space-y-1.5">
                      <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider pl-1">语言</label>
                      <a-select v-model:value="selectedLocale" class="w-full" size="small" @change="onLocaleChange"
                        :loading="loadingVoices">
                        <a-select-option v-for="loc in ttsLocales" :key="loc.value" :value="loc.value">{{ loc.label
                          }}</a-select-option>
                      </a-select>
                    </div>
                    <div class="space-y-1.5">
                      <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider pl-1">音色</label>
                      <a-select v-model:value="form.voice_name" class="w-full" size="small" show-search
                        :filter-option="filterVoiceOption" :loading="loadingVoices" @change="clearAudioPreview">
                        <a-select-option v-for="voice in ttsVoices" :key="voice.short_name" :value="voice.short_name">{{
                          voice.label }}</a-select-option>
                      </a-select>
                    </div>
                    <div class="space-y-1.5">
                      <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider pl-1">语速</label>
                      <a-select v-model:value="form.voice_speed" class="w-full" size="small" @change="clearAudioPreview">
                        <a-select-option v-for="spd in ttsSpeeds" :key="spd.value" :value="spd.value">{{ spd.label
                          }}</a-select-option>
                      </a-select>
                    </div>
                    <div class="space-y-1.5">
                      <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider pl-1">音调</label>
                      <a-select v-model:value="form.voice_pitch" class="w-full" size="small" @change="clearAudioPreview">
                        <a-select-option value="-20Hz">很低</a-select-option>
                        <a-select-option value="-10Hz">较低</a-select-option>
                        <a-select-option value="+0Hz">正常</a-select-option>
                        <a-select-option value="+10Hz">较高</a-select-option>
                        <a-select-option value="+20Hz">很高</a-select-option>
                      </a-select>
                    </div>
                  </div>

                  <!-- 音频播放器 -->
                  <div class="rounded-xl p-1">
                    <div class="flex items-center gap-3 bg-white rounded-lg p-2.5">
                      <!-- 播放按钮 -->
                      <button @click="handleAudioAction" :disabled="audioState === 'generating'" :class="`relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 flex-shrink-0
                          ${audioState === 'generating' ? 'bg-slate-100 text-slate-400 cursor-wait'
                          : audioState === 'playing' ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 scale-105'
                          : 'bg-emerald-500 text-white hover:bg-emerald-600 hover:scale-105 shadow-md'}`">
                      <Loader2 v-if="audioState === 'generating'" :size="18" class="animate-spin" />
                      <Pause v-else-if="audioState === 'playing'" :size="18" fill="currentColor" />
                      <Play v-else :size="18" fill="currentColor" class="ml-0.5" />
                      <span v-if="audioState === 'playing'"
                        class="absolute inset-0 rounded-full border border-emerald-400 animate-ping opacity-20"></span>
                    </button>

                    <!-- 波形可视化 -->
                    <div class="flex-1 flex flex-col justify-center gap-1 min-h-[40px]">
                      <div class="flex justify-between items-center px-1">
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          {{ audioState === 'idle' ? '点击播放试听' : audioState === 'generating' ? '生成中...' : '配音预览' }}
                        </span>
                        <span v-if="audioState === 'playing' || audioState === 'ready'"
                          class="text-[10px] font-mono text-emerald-600 font-medium">
                          {{ formatTime(currentTime) }} / {{ formatTime(audioDuration) }}
                        </span>
                      </div>
                      <div class="relative h-6 w-full flex items-center gap-[2px] overflow-hidden">
                        <div v-for="i in 50" :key="i"
                          :class="`w-1 rounded-full transition-all duration-150 ${audioState === 'playing' ? 'bg-emerald-500' : (i / 50) * 100 < playbackProgress ? 'bg-emerald-500' : 'bg-emerald-500/20'}`"
                          :style="{ height: audioState === 'playing' ? `${Math.max(15, 20 + Math.sin(i * 0.5 + waveOffset) * 40 + Math.random() * 15)}%` : (i / 50) * 100 < playbackProgress ? `${20 + Math.sin(i * 0.5) * 30}%` : '4px' }">
                        </div>
                      </div>
                    </div>

                    <!-- 音量滑块 -->
                    <div class="flex items-center gap-2 w-28">
                      <Volume2 :size="14" class="text-slate-400 flex-shrink-0" />
                      <a-slider v-model:value="previewVolume" :min="0" :max="100" :step="5" size="small" class="flex-1" @change="onPreviewVolumeChange" />
                    </div>
                  </div>
                  
                  <!-- 实时字幕显示 -->
                  <div v-if="audioState === 'playing' && currentSubtitle" 
                    class="mt-2 px-4 py-2 text-center transition-all">
                    <p class="text-slate-700 text-sm font-medium animate-fadeIn">{{ currentSubtitle }}</p>
                  </div>
                </div>
                </div>

                <!-- 自定义配音上传 -->
                <div v-else class="space-y-4">
                  <div class="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-emerald-300 transition-colors" 
                    :class="{ 'cursor-pointer': !customAudioFile }"
                    @click="!customAudioFile && customAudioInputRef?.click()">
                    <input ref="customAudioInputRef" type="file" accept=".mp3,.wav,.m4a,.ogg" class="hidden" @change="handleCustomAudioUpload" />
                    <div v-if="!customAudioFile" class="space-y-3">
                      <div class="w-12 h-12 mx-auto bg-slate-100 rounded-full flex items-center justify-center">
                        <Upload :size="24" class="text-slate-400" />
                      </div>
                      <div>
                        <span class="text-sm font-medium text-emerald-600 hover:text-emerald-700">
                          点击上传配音文件
                        </span>
                        <p class="text-xs text-slate-400 mt-1">支持 MP3、WAV、M4A、OGG 格式，最大 50MB</p>
                      </div>
                    </div>
                    <div v-else class="space-y-3" @click.stop>
                      <div class="flex items-center justify-center gap-3">
                        <div class="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                          <CheckCircle :size="20" class="text-emerald-600" />
                        </div>
                        <div class="text-left">
                          <p class="text-sm font-medium text-slate-700 truncate max-w-[200px]">{{ customAudioFile.name }}</p>
                          <p class="text-xs text-slate-400">{{ (customAudioFile.size / 1024 / 1024).toFixed(2) }} MB</p>
                        </div>
                        <button @click="removeCustomAudio" class="p-1.5 hover:bg-slate-100 rounded-full transition-colors">
                          <X :size="16" class="text-slate-400" />
                        </button>
                      </div>
                      <!-- 自定义配音播放器 -->
                      <div class="flex items-center gap-3 bg-white rounded-lg p-2.5 border border-slate-100">
                        <button @click="handleCustomAudioPlay" :class="`w-8 h-8 rounded-full flex items-center justify-center transition-all ${customAudioPlaying ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`">
                          <Pause v-if="customAudioPlaying" :size="14" fill="currentColor" />
                          <Play v-else :size="14" fill="currentColor" class="ml-0.5" />
                        </button>
                        <div class="flex-1 text-xs text-slate-500">
                          {{ formatTime(customAudioCurrentTime) }} / {{ formatTime(customAudioDuration) }}
                        </div>
                      </div>
                      <!-- 自定义配音实时字幕 -->
                      <div v-if="customAudioPlaying && currentCustomSubtitle" 
                        class="px-4 py-2 text-center">
                        <p class="text-slate-700 text-sm font-medium">{{ currentCustomSubtitle }}</p>
                      </div>
                    </div>
                  </div>
                  <p class="text-xs text-slate-400 text-center">
                    <Info :size="12" class="inline mr-1" />
                    上传的配音时长将决定最终视频时长，字幕将根据文案自动生成
                  </p>
                </div>

                <!-- 隐藏的audio元素 -->
                <audio ref="audioPreviewRef" :src="audioPreviewUrl || undefined" class="hidden"
                  @timeupdate="onTimeUpdate" @loadedmetadata="onLoadedMetadata" @ended="onAudioEnded"
                  @canplay="onCanPlay"></audio>
                <audio ref="customAudioRef" :src="customAudioUrl || undefined" class="hidden"
                  @timeupdate="onCustomAudioTimeUpdate" @loadedmetadata="onCustomAudioLoaded" @ended="onCustomAudioEnded"></audio>
              </div>
            </section>

            <!-- 视频配置 -->
            <section
              class="col-span-12 lg:col-span-5 group relative bg-white/30 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all overflow-hidden">
              <div
                class="absolute -left-px top-6 bottom-6 w-1 bg-emerald-500 rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity">
              </div>
              <div class="p-6 space-y-4">
                <div class="flex items-center gap-3">
                  <div class="p-2.5 bg-slate-100 rounded-xl">
                    <Settings :size="20" />
                  </div>
                  <div>
                    <h3 class="text-base font-bold">视频配置</h3>
                    <p class="text-xs text-slate-400 font-medium">STEP 4</p>
                  </div>
                </div>

                <!-- 标签切换 -->
                <div class="flex border-b border-slate-100">
                  <button @click="activeTab = 'video'"
                    class="flex-1 py-2 text-sm font-semibold transition-colors relative"
                    :class="activeTab === 'video' ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'">
                    视频
                    <div v-if="activeTab === 'video'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500">
                    </div>
                  </button>
                  <button @click="activeTab = 'audio'"
                    class="flex-1 py-2 text-sm font-semibold transition-colors relative"
                    :class="activeTab === 'audio' ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'">
                    音频
                    <div v-if="activeTab === 'audio'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500">
                    </div>
                  </button>
                  <button @click="activeTab = 'subtitle'"
                    class="flex-1 py-2 text-sm font-semibold transition-colors relative"
                    :class="activeTab === 'subtitle' ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'">
                    字幕
                    <div v-if="activeTab === 'subtitle'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500">
                    </div>
                  </button>
                  <button @click="activeTab = 'style'"
                    class="flex-1 py-2 text-sm font-semibold transition-colors relative"
                    :class="activeTab === 'style' ? 'text-emerald-600' : 'text-slate-400 hover:text-slate-600'">
                    效果
                    <div v-if="activeTab === 'style'" class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500">
                    </div>
                  </button>
                </div>

                <div class="pt-1">
                  <!-- 视频配置 -->
                  <div v-if="activeTab === 'video'" class="space-y-3 animate-fadeIn">
                    <!-- 平台预设 -->
                    <div class="space-y-1.5">
                      <label class="text-xs font-semibold text-slate-400">平台预设</label>
                      <a-select v-model:value="form.platform_preset" class="w-full" size="small" allow-clear placeholder="自定义" @change="onPlatformPresetChange">
                        <a-select-option value="douyin">抖音/TikTok (9:16)</a-select-option>
                        <a-select-option value="kuaishou">快手 (9:16)</a-select-option>
                        <a-select-option value="xiaohongshu">小红书 (3:4)</a-select-option>
                        <a-select-option value="bilibili">B站 (16:9)</a-select-option>
                        <a-select-option value="youtube">YouTube (16:9)</a-select-option>
                        <a-select-option value="instagram_reels">Instagram Reels (9:16)</a-select-option>
                        <a-select-option value="instagram_feed">Instagram Feed (1:1)</a-select-option>
                        <a-select-option value="weixin">微信视频号 (9:16)</a-select-option>
                      </a-select>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">布局</label>
                        <a-select v-model:value="form.video_layout" class="w-full" size="small">
                          <a-select-option value="9:16">竖屏 9:16</a-select-option>
                          <a-select-option value="3:4">竖屏 3:4</a-select-option>
                          <a-select-option value="1:1">方形 1:1</a-select-option>
                          <a-select-option value="4:3">横屏 4:3</a-select-option>
                          <a-select-option value="16:9">横屏 16:9</a-select-option>
                          <a-select-option value="21:9">宽银幕 21:9</a-select-option>
                        </a-select>
                      </div>
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">分辨率</label>
                        <a-select v-model:value="form.video_resolution" class="w-full" size="small">
                          <a-select-option value="480p">480p 标清</a-select-option>
                          <a-select-option value="720p">720p 高清</a-select-option>
                          <a-select-option value="1080p">1080p 全高清</a-select-option>
                          <a-select-option value="2k">2K</a-select-option>
                          <a-select-option value="4k">4K 超清</a-select-option>
                        </a-select>
                      </div>
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">帧率</label>
                        <a-select v-model:value="form.video_fps" class="w-full" size="small">
                          <a-select-option :value="24">24 fps 电影</a-select-option>
                          <a-select-option :value="25">25 fps PAL</a-select-option>
                          <a-select-option :value="30">30 fps 标准</a-select-option>
                          <a-select-option :value="50">50 fps 高帧率</a-select-option>
                          <a-select-option :value="60">60 fps 流畅</a-select-option>
                        </a-select>
                      </div>
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">素材适配</label>
                        <a-select v-model:value="form.fit_mode" class="w-full" size="small">
                          <a-select-option value="crop">裁剪填充</a-select-option>
                          <a-select-option value="fit">适应填充</a-select-option>
                          <a-select-option value="stretch">拉伸填充</a-select-option>
                        </a-select>
                      </div>
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">输出质量</label>
                        <a-select v-model:value="form.output_quality" class="w-full" size="small">
                          <a-select-option value="low">低质量</a-select-option>
                          <a-select-option value="medium">中等</a-select-option>
                          <a-select-option value="high">高质量</a-select-option>
                          <a-select-option value="ultra">极高</a-select-option>
                        </a-select>
                      </div>
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">单片段时长</label>
                        <div class="flex items-center gap-1">
                          <a-input-number v-model:value="form.clip_min_duration" :min="1" :max="30" size="small"
                            class="flex-1" />
                          <span class="text-slate-400 text-xs">~</span>
                          <a-input-number v-model:value="form.clip_max_duration" :min="1" :max="60" size="small"
                            class="flex-1" />
                        </div>
                        <p class="text-[10px] text-slate-400">每个素材片段的时长范围</p>
                      </div>
                    </div>
                  </div>

                  <!-- 音频配置 -->
                  <div v-if="activeTab === 'audio'" class="space-y-4 animate-fadeIn">
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <span class="text-sm font-medium">背景音乐</span>
                      <a-switch v-model:checked="form.bgm_enabled" size="small" />
                    </div>
                    <div v-if="form.bgm_enabled" class="space-y-3">
                      <div class="flex items-center gap-2">
                        <input ref="bgmInputRef" type="file" accept=".mp3,.wav,.m4a" class="hidden"
                          @change="handleBgmUpload" />
                        <button @click="bgmInputRef?.click()"
                          class="text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1">
                          <Upload :size="12" /> 选择文件
                        </button>
                        <span v-if="bgmFileName"
                          class="text-xs text-emerald-600 flex items-center gap-1 truncate max-w-[120px]">
                          <CheckCircle :size="12" /> {{ bgmFileName }}
                        </span>
                      </div>
                      <div class="space-y-1.5">
                        <div class="flex justify-between">
                          <label class="text-xs font-semibold text-slate-400">音量</label>
                          <span class="text-xs font-bold text-emerald-600">{{ ((form.bgm_volume ?? 0.3) *
                            100).toFixed(0) }}%</span>
                        </div>
                        <a-slider v-model:value="form.bgm_volume" :min="0" :max="1" :step="0.05" />
                      </div>
                      <div class="grid grid-cols-2 gap-3">
                        <div class="space-y-1.5">
                          <label class="text-xs font-semibold text-slate-400">淡入时长</label>
                          <a-slider v-model:value="form.bgm_fade_in" :min="0" :max="5" :step="0.5" />
                          <span class="text-xs text-slate-400">{{ form.bgm_fade_in }}秒</span>
                        </div>
                        <div class="space-y-1.5">
                          <label class="text-xs font-semibold text-slate-400">淡出时长</label>
                          <a-slider v-model:value="form.bgm_fade_out" :min="0" :max="5" :step="0.5" />
                          <span class="text-xs text-slate-400">{{ form.bgm_fade_out }}秒</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 字幕配置（独立标签页） -->
                  <div v-if="activeTab === 'subtitle'" class="space-y-4 animate-fadeIn">
                    <!-- 开关 -->
                    <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <span class="text-sm font-medium">开启字幕</span>
                      <a-switch v-model:checked="form.subtitle_enabled" size="small" />
                    </div>
                    
                    <div v-if="form.subtitle_enabled" class="space-y-4">
                      <!-- 字幕预览按钮 -->
                      <div class="space-y-1.5">
                        <button @click="showSubtitlePreview = true" 
                          class="w-full h-10 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm font-medium text-slate-600 flex items-center justify-center gap-2 transition-colors">
                          <Eye :size="16" />
                          预览字幕效果
                        </button>
                      </div>

                      <!-- 字幕位置 -->
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">字幕位置</label>
                        <a-select v-model:value="form.subtitle_position" class="w-full" size="small">
                          <a-select-option v-for="pos in subtitlePositionOptions" :key="pos.value" :value="pos.value">
                            {{ pos.label }}
                          </a-select-option>
                        </a-select>
                      </div>

                      <!-- 字体和字号 -->
                      <div class="grid grid-cols-2 gap-3">
                        <div class="space-y-1.5">
                          <label class="text-xs font-semibold text-slate-400">字幕字体</label>
                          <a-select v-model:value="form.subtitle_font" class="w-full" size="small">
                            <a-select-option value="Heiti-SC-Medium">黑体</a-select-option>
                            <a-select-option value="Songti-SC-Bold">宋体</a-select-option>
                            <a-select-option value="PingFang-SC-Medium">苹方</a-select-option>
                            <a-select-option value="STKaiti">楷体</a-select-option>
                            <a-select-option value="Arial-Bold">Arial Bold</a-select-option>
                          </a-select>
                        </div>
                        <div class="space-y-1.5">
                          <label class="text-xs font-semibold text-slate-400">字体大小</label>
                          <a-select v-model:value="form.subtitle_size" class="w-full" size="small">
                            <a-select-option :value="24">24 小</a-select-option>
                            <a-select-option :value="32">32</a-select-option>
                            <a-select-option :value="40">40</a-select-option>
                            <a-select-option :value="48">48 中</a-select-option>
                            <a-select-option :value="56">56</a-select-option>
                            <a-select-option :value="64">64 大</a-select-option>
                            <a-select-option :value="72">72</a-select-option>
                            <a-select-option :value="80">80 特大</a-select-option>
                          </a-select>
                        </div>
                      </div>

                      <!-- 字幕行数 -->
                      <div class="space-y-1.5">
                        <label class="text-xs font-semibold text-slate-400">字幕行数</label>
                        <a-select v-model:value="form.subtitle_line_spacing" class="w-full" size="small">
                          <a-select-option :value="1">1 行</a-select-option>
                          <a-select-option :value="2">2 行</a-select-option>
                          <a-select-option :value="3">3 行</a-select-option>
                        </a-select>
                      </div>

                      <!-- 颜色配置 -->
                      <div class="grid grid-cols-2 gap-3">
                        <div class="space-y-1.5">
                          <label class="text-xs font-semibold text-slate-400">字幕颜色</label>
                          <div class="flex items-center gap-2">
                            <input type="color" v-model="form.subtitle_color"
                              class="w-10 h-8 rounded cursor-pointer border border-slate-200" />
                            <input type="text" v-model="form.subtitle_color" 
                              class="flex-1 h-8 px-2 text-xs border border-slate-200 rounded" />
                          </div>
                        </div>
                        <div class="space-y-1.5">
                          <label class="text-xs font-semibold text-slate-400">描边颜色</label>
                          <div class="flex items-center gap-2">
                            <input type="color" v-model="form.subtitle_stroke_color"
                              class="w-10 h-8 rounded cursor-pointer border border-slate-200" />
                            <input type="text" v-model="form.subtitle_stroke_color" 
                              class="flex-1 h-8 px-2 text-xs border border-slate-200 rounded" />
                          </div>
                        </div>
                      </div>

                      <!-- 描边宽度 -->
                      <div class="space-y-1.5">
                        <div class="flex justify-between">
                          <label class="text-xs font-semibold text-slate-400">描边宽度</label>
                          <span class="text-xs text-emerald-600">{{ form.subtitle_stroke_width }}</span>
                        </div>
                        <a-slider v-model:value="form.subtitle_stroke_width" :min="0" :max="5" :step="0.5" />
                      </div>
                    </div>
                  </div>

                  <!-- 效果配置 -->
                  <div v-if="activeTab === 'style'" class="space-y-4 animate-fadeIn">
                    <!-- 转场效果 -->
                    <div class="space-y-2">
                      <label class="text-xs font-semibold text-slate-400">转场效果</label>
                      <div class="flex items-center justify-between mb-2">
                        <span class="text-sm">启用转场</span>
                        <a-switch v-model:checked="form.transition_enabled" size="small" />
                      </div>
                      <div v-if="form.transition_enabled" class="space-y-2">
                        <div class="grid grid-cols-4 gap-2">
                          <div v-for="t in ['none', 'fade', 'dissolve', 'slide_left', 'slide_right', 'zoom_in', 'zoom_out', 'wipe_left']" :key="t" @click="form.transition_type = t"
                            class="text-center py-1.5 border rounded-lg text-xs font-medium cursor-pointer transition-colors"
                            :class="form.transition_type === t ? 'border-emerald-500 bg-emerald-50 text-emerald-600' : 'border-slate-200 hover:border-emerald-300'">
                            {{ { none: '无', fade: '淡入淡出', dissolve: '溶解', slide_left: '左滑', slide_right: '右滑', zoom_in: '放大', zoom_out: '缩小', wipe_left: '擦除' }[t] }}
                          </div>
                        </div>
                        <div class="space-y-1">
                          <label class="text-xs text-slate-400">转场时长: {{ form.transition_duration }}秒</label>
                          <a-slider v-model:value="form.transition_duration" :min="0.3" :max="2" :step="0.1" />
                        </div>
                      </div>
                    </div>
                    
                    <!-- 视频特效 -->
                    <div class="space-y-2 pt-2 border-t border-slate-100">
                      <label class="text-xs font-semibold text-slate-400">视频特效</label>
                      <div class="grid grid-cols-2 gap-2">
                        <div class="space-y-1">
                          <label class="text-xs text-slate-400">动效</label>
                          <a-select v-model:value="form.effect_type" class="w-full" size="small">
                            <a-select-option value="none">无</a-select-option>
                            <a-select-option value="ken_burns_in">Ken Burns 放大</a-select-option>
                            <a-select-option value="ken_burns_out">Ken Burns 缩小</a-select-option>
                            <a-select-option value="zoom_in">缩放进入</a-select-option>
                            <a-select-option value="zoom_out">缩放退出</a-select-option>
                            <a-select-option value="pan_left">左平移</a-select-option>
                            <a-select-option value="pan_right">右平移</a-select-option>
                            <a-select-option value="pan_up">上平移</a-select-option>
                            <a-select-option value="pan_down">下平移</a-select-option>
                            <a-select-option value="shake">抖动</a-select-option>
                          </a-select>
                        </div>
                        <div class="space-y-1">
                          <label class="text-xs text-slate-400">滤镜</label>
                          <a-select v-model:value="form.color_filter" class="w-full" size="small">
                            <a-select-option value="none">原始</a-select-option>
                            <a-select-option value="grayscale">黑白</a-select-option>
                            <a-select-option value="vintage">复古</a-select-option>
                            <a-select-option value="warm">暖色调</a-select-option>
                            <a-select-option value="cool">冷色调</a-select-option>
                            <a-select-option value="high_contrast">高对比度</a-select-option>
                            <a-select-option value="soft">柔和</a-select-option>
                          </a-select>
                        </div>
                      </div>
                      <div class="space-y-2">
                        <div class="space-y-1">
                          <label class="text-xs text-slate-400">亮度: {{ form.brightness?.toFixed(1) }}</label>
                          <a-slider v-model:value="form.brightness" :min="0.5" :max="2" :step="0.1" />
                        </div>
                        <div class="space-y-1">
                          <label class="text-xs text-slate-400">对比度: {{ form.contrast?.toFixed(1) }}</label>
                          <a-slider v-model:value="form.contrast" :min="0.5" :max="2" :step="0.1" />
                        </div>
                        <div class="space-y-1">
                          <label class="text-xs text-slate-400">饱和度: {{ form.saturation?.toFixed(1) }}</label>
                          <a-slider v-model:value="form.saturation" :min="0" :max="2" :step="0.1" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        <!-- 底部操作栏 - 试听 + 生成视频 -->
        <div class="mt-6 flex items-center gap-4">
          <!-- 试听配音按钮 -->
          <button @click="handleAudioAction" :disabled="audioState === 'generating'"
            :class="`flex-1 h-12 rounded-full text-sm font-bold transition-all flex items-center justify-center gap-2
              ${audioState === 'generating' ? 'bg-slate-100 text-slate-400 cursor-wait'
                : audioState === 'playing' ? 'bg-emerald-100 text-emerald-600 border-2 border-emerald-500'
                  : 'bg-white text-slate-700 border-2 border-slate-200 hover:border-emerald-500 hover:text-emerald-600'}`">
            <Loader2 v-if="audioState === 'generating'" :size="18" class="animate-spin" />
            <Pause v-else-if="audioState === 'playing'" :size="18" />
            <Play v-else :size="18" />
            {{ audioState === 'generating' ? '生成中...' : audioState === 'playing' ? '暂停试听' : '试听配音' }}
          </button>
          <!-- 生成视频按钮 -->
          <button @click="handleGenerate"
            class="flex-1 h-12 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white hover:from-emerald-600 hover:to-emerald-700 rounded-full text-sm font-bold shadow-lg shadow-emerald-500/25 transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2">
            <Sparkles :size="18" />
            生成视频
          </button>
        </div>
      </div>

      <!-- 生成中状态 -->
      <div v-if="currentState === 'generating'" class="max-w-3xl mx-auto mt-20">
        <div class="bg-white rounded-2xl border border-slate-200 p-8 shadow-lg text-center">
          <Loader2 class="w-14 h-14 text-emerald-500 animate-spin mx-auto mb-5" />
          <h3 class="text-xl font-bold text-slate-800 mb-2">视频生成中...</h3>
          <p class="text-sm text-slate-500 mb-6">{{ progressMessage }}</p>
          <a-progress :percent="progress" :stroke-color="'#10b981'" :show-info="true" />
          <p class="text-xs text-slate-400 mt-4">请勿刷新页面，生成过程可能需要几分钟</p>
        </div>
      </div>

      <!-- 完成状态 -->
      <div v-if="currentState === 'complete'" class="max-w-3xl mx-auto mt-10">
        <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-lg">
          <div class="text-center mb-5">
            <CheckCircle class="w-14 h-14 text-emerald-500 mx-auto mb-3" />
            <h3 class="text-xl font-bold text-emerald-600">视频生成完成！</h3>
            <p class="text-sm text-slate-500 mt-1" v-if="videoDuration">时长: {{ formatDuration(videoDuration) }}</p>
          </div>
          <div class="bg-slate-100 rounded-xl p-3 mb-5">
            <video controls class="w-full rounded-lg max-h-[400px]" :src="generatedVideoUrl!">
              您的浏览器不支持视频播放
            </video>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <button @click="handleDownload"
              class="h-11 rounded-xl font-semibold flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white transition-colors">
              <Download :size="18" /> 下载视频
            </button>
            <button @click="handleReset"
              class="h-11 rounded-xl font-semibold flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors">
              <RefreshCw :size="18" /> 重新生成
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 字幕预览弹窗 - 左右分栏 -->
  <a-modal 
    v-model:open="showSubtitlePreview" 
    title="字幕配置" 
    :footer="null" 
    :width="480"
    centered
  >
    <div class="flex gap-6">
      <!-- 左侧：预览区域 -->
      <div class="w-64 flex-shrink-0">
        <div class="text-xs font-semibold text-slate-400 mb-2">预览</div>
        <div class="relative rounded-lg overflow-hidden bg-slate-900" :style="{ aspectRatio: previewAspectRatio, maxHeight: '680px' }">
          <!-- 背景图片/视频 -->
          <img v-if="previewBackgroundUrl" :src="previewBackgroundUrl" class="absolute inset-0 w-full h-full object-cover" />
          <div v-else class="absolute inset-0 bg-gradient-to-b from-slate-700 to-slate-900"></div>
          
          <!-- 字幕文字 -->
          <div 
            class="absolute px-2 py-1 text-center max-w-[90%] leading-tight"
            :style="subtitlePreviewModalStyle">
            {{ subtitlePreviewText }}
          </div>
        </div>
      </div>
      
      <!-- 右侧：位置选择 -->
      <div class="w-36 flex-shrink-0">
        <div class="text-xs font-semibold text-slate-400 mb-2">字幕位置</div>
        <div class="grid grid-cols-1 gap-2">
          <button v-for="pos in subtitlePositionOptions" :key="pos.value"
            @click="form.subtitle_position = pos.value"
            class="py-2.5 px-3 text-sm font-medium rounded-lg border transition-all text-left flex items-center gap-2"
            :class="form.subtitle_position === pos.value ? 'border-emerald-500 bg-emerald-50 text-emerald-600 shadow-sm' : 'border-slate-200 hover:border-emerald-300 text-slate-600 hover:bg-slate-50'">
            <span class="w-2 h-2 rounded-full" :class="form.subtitle_position === pos.value ? 'bg-emerald-500' : 'bg-slate-300'"></span>
            {{ pos.label }}
          </button>
        </div>
      </div>
    </div>
  </a-modal>

  <!-- 视频预览弹窗 -->
  <a-modal 
    v-model:open="showVideoPreview" 
    title="视频预览" 
    :footer="null" 
    :width="600"
    centered
    :destroyOnClose="true"
  >
    <video 
      v-if="previewVideoUrl" 
      :src="previewVideoUrl" 
      controls 
      autoplay 
      class="w-full rounded-lg max-h-[70vh]"
    ></video>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  Video, FileText, Sparkles, Mic, Music, Settings, Upload, Wand2,
  CheckCircle, Download, RefreshCw, Loader2, Layers, Image as ImageIcon, Play, Pause, Volume2, Eye,
  X, Info, Clock,
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { videoApi, type VideoTaskCreate, type AIProvider, type TtsVoice } from '@/api/video'

const router = useRouter()
const userStore = useUserStore()


type State = 'idle' | 'generating' | 'complete'
const currentState = ref<State>('idle')
const progress = ref(0)
const progressMessage = ref('')

const currentStep = computed(() => {
  switch (currentState.value) {
    case 'idle': return 0
    case 'generating': return 1
    case 'complete': return 2
    default: return 0
  }
})

const stepItems = computed(() => [
  {
    title: '编辑',
  },
  {
    title:  currentState.value === 'generating' ? '合成中...' : '合成',
  },
  {
    title: currentState.value === 'complete' ? '完成' : '下载',
  },
])

const generatedVideoUrl = ref<string | null>(null)
const videoDuration = ref<number | null>(null)
const bgmInputRef = ref<HTMLInputElement | null>(null)
const mediaInputRef = ref<HTMLInputElement | null>(null)
const audioPreviewRef = ref<HTMLAudioElement | null>(null)
const bgmFileName = ref('')
const generatingScript = ref(false)
const uploadingMedia = ref(false)
const uploadedImages = ref<{ file_path: string, filename: string }[]>([])
const uploadedVideos = ref<{ file_path: string, filename: string, size: number }[]>([])
const audioPreviewUrl = ref<string | null>(null)
const activeTab = ref<'video' | 'audio' | 'subtitle' | 'style'>('video')
const showSubtitlePreview = ref(false)
const showVideoPreview = ref(false)
const previewVideoUrl = ref<string | null>(null)

// 配音类型切换
const voiceType = ref<'tts' | 'custom'>('tts')

// 自定义配音相关
const customAudioInputRef = ref<HTMLInputElement | null>(null)
const customAudioRef = ref<HTMLAudioElement | null>(null)
const customAudioFile = ref<File | null>(null)
const customAudioUrl = ref<string | null>(null)
const customAudioPlaying = ref(false)
const customAudioCurrentTime = ref(0)
const customAudioDuration = ref(0)

// TTS 字幕相关
const ttsSubtitles = ref<{ text: string; start: number; end: number }[]>([])

// 自定义配音字幕
const customAudioSubtitles = ref<{ text: string; start: number; end: number }[]>([])

// 当前显示的字幕（根据播放时间）
const currentSubtitle = computed(() => {
  if (audioState.value !== 'playing' || ttsSubtitles.value.length === 0) {
    return ''
  }
  const time = currentTime.value
  const subtitle = ttsSubtitles.value.find(s => time >= s.start && time <= s.end)
  return subtitle?.text || ''
})

// 自定义配音当前字幕
const currentCustomSubtitle = computed(() => {
  if (!customAudioPlaying.value || customAudioSubtitles.value.length === 0) {
    return ''
  }
  const time = customAudioCurrentTime.value
  const subtitle = customAudioSubtitles.value.find(s => time >= s.start && time <= s.end)
  return subtitle?.text || ''
})

// 音频播放器状态
const audioState = ref<'idle' | 'generating' | 'ready' | 'playing'>('idle')
const playbackProgress = ref(0)
const currentTime = ref(0)
const audioDuration = ref(0)
const waveOffset = ref(0)
const previewVolume = ref(80)
let waveAnimationId: number | null = null

let pollController: { stop: () => void } | null = null

// AI 配置
const aiProviders = ref<AIProvider[]>([])
const aiStyles = ref<{ value: string, label: string }[]>([])
const selectedProvider = ref('auto')
const selectedStyle = ref('口播')

// TTS 配置
const selectedLocale = ref('zh-CN')
const ttsLocales = ref<{ value: string, label: string }[]>([])
const ttsVoices = ref<TtsVoice[]>([])
const ttsSpeeds = ref<{ value: string, label: string }[]>([])
const loadingVoices = ref(false)

const form = ref<VideoTaskCreate>({
  topic: '',
  script: '',
  script_language: 'zh',
  voice_language: 'zh-CN',
  voice_name: 'zh-CN-XiaoxiaoNeural',
  voice_speed: '+0%',
  voice_volume: '+0%',
  voice_pitch: '+0Hz',
  // 背景音乐
  bgm_enabled: false,
  bgm_path: '',
  bgm_volume: 0.3,
  bgm_fade_in: 0,
  bgm_fade_out: 0,
  // 视频配置
  video_resolution: '1080p',
  video_layout: '9:16',
  video_fps: 30,
  platform_preset: 'douyin',
  fit_mode: 'crop',
  clip_min_duration: 3,
  clip_max_duration: 10,
  use_local_videos: false,
  local_video_dir: '',
  media_paths: [],
  // 转场配置
  transition_enabled: true,
  transition_type: 'fade',
  transition_effect: 'fade',
  transition_duration: 0.5,
  // 字幕配置
  subtitle_enabled: true,
  subtitle_font: 'Heiti-SC-Medium',
  subtitle_size: 48,
  subtitle_color: '#FFFFFF',
  subtitle_stroke_color: '#000000',
  subtitle_stroke_width: 2,
  subtitle_position: 'bottom',
  subtitle_line_spacing: 2,
  // 特效配置
  effect_type: 'none',
  color_filter: 'none',
  brightness: 1.0,
  contrast: 1.0,
  saturation: 1.0,
  // 输出配置
  output_quality: 'high',
})

const scriptRows = computed(() => {
  const lines = form.value.script.split('\n').length
  const charLines = Math.ceil(form.value.script.length / 50)
  return Math.max(6, Math.min(14, Math.max(lines, charLines)))
})

// 字幕位置选项
const subtitlePositionOptions = [
  { value: 'top_left', label: '顶部靠左' },
  { value: 'top', label: '顶部中心' },
  { value: 'top_right', label: '顶部靠右' },
  { value: 'left', label: '左中' },
  { value: 'center', label: '中心' },
  { value: 'right', label: '右中' },
  { value: 'bottom_left', label: '底部靠左' },
  { value: 'bottom', label: '底部中心' },
  { value: 'bottom_right', label: '底部靠右' },
]

// 预览区域宽高比
const previewAspectRatio = computed(() => {
  const layout = form.value.video_layout || '9:16'
  const [w, h] = layout.split(':').map(Number)
  return `${w}/${h}`
})

// 字幕预览样式
const subtitlePreviewStyle = computed(() => {
  const pos = form.value.subtitle_position || 'bottom'
  const fontSize = Math.max(10, Math.min(16, (form.value.subtitle_size || 48) / 4))
  const color = form.value.subtitle_color || '#FFFFFF'
  const strokeColor = form.value.subtitle_stroke_color || '#000000'
  const strokeWidth = (form.value.subtitle_stroke_width || 2) / 2
  
  // 位置映射
  const positionMap: Record<string, { top?: string; bottom?: string; left?: string; right?: string; transform: string }> = {
    'top_left': { top: '8%', left: '5%', transform: 'none' },
    'top': { top: '8%', left: '50%', transform: 'translateX(-50%)' },
    'top_right': { top: '8%', right: '5%', transform: 'none' },
    'left': { top: '50%', left: '5%', transform: 'translateY(-50%)' },
    'center': { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
    'right': { top: '50%', right: '5%', transform: 'translateY(-50%)' },
    'bottom_left': { bottom: '8%', left: '5%', transform: 'none' },
    'bottom': { bottom: '8%', left: '50%', transform: 'translateX(-50%)' },
    'bottom_right': { bottom: '8%', right: '5%', transform: 'none' },
  }
  
  const posStyle = positionMap[pos] || positionMap['bottom']
  
  return {
    ...posStyle,
    fontSize: `${fontSize}px`,
    color: color,
    textShadow: `${strokeWidth}px ${strokeWidth}px 0 ${strokeColor}, -${strokeWidth}px -${strokeWidth}px 0 ${strokeColor}, ${strokeWidth}px -${strokeWidth}px 0 ${strokeColor}, -${strokeWidth}px ${strokeWidth}px 0 ${strokeColor}`,
    fontWeight: 'bold',
  }
})

// 字幕预览文字 - 取文案前15个字符
const subtitlePreviewText = computed(() => {
  const script = form.value.script?.trim()
  if (!script) return '字幕预览'
  // 取第一句或前15个字符
  const firstSentence = script.split(/[。！？.!?\n]/)[0]
  return firstSentence?.slice(0, 15) || script.slice(0, 15)
})

// 预览背景URL - 使用上传的第一张图片或视频
// 预览背景URL - 使用上传的第一张图片或视频
const previewBackgroundUrl = computed(() => {
  if (uploadedImages.value.length > 0 && uploadedImages.value[0]) {
    return getMediaUrl(uploadedImages.value[0].file_path)
  }
  if (uploadedVideos.value.length > 0) {
    // 视频无法直接作为背景，返回null使用渐变
    return null
  }
  return null
})

// 弹窗中的字幕样式（更大的字体）
const subtitlePreviewModalStyle = computed(() => {
  const pos = form.value.subtitle_position || 'bottom'
  const fontSize = Math.max(14, Math.min(24, (form.value.subtitle_size || 48) / 2.5))
  const color = form.value.subtitle_color || '#FFFFFF'
  const strokeColor = form.value.subtitle_stroke_color || '#000000'
  const strokeWidth = Math.max(1, (form.value.subtitle_stroke_width || 2) / 1.5)
  
  // 位置映射
  const positionMap: Record<string, { top?: string; bottom?: string; left?: string; right?: string; transform: string }> = {
    'top_left': { top: '5%', left: '5%', transform: 'none' },
    'top': { top: '5%', left: '50%', transform: 'translateX(-50%)' },
    'top_right': { top: '5%', right: '5%', transform: 'none' },
    'left': { top: '50%', left: '5%', transform: 'translateY(-50%)' },
    'center': { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
    'right': { top: '50%', right: '5%', transform: 'translateY(-50%)' },
    'bottom_left': { bottom: '5%', left: '5%', transform: 'none' },
    'bottom': { bottom: '5%', left: '50%', transform: 'translateX(-50%)' },
    'bottom_right': { bottom: '5%', right: '5%', transform: 'none' },
  }
  
  const posStyle = positionMap[pos] || positionMap['bottom']
  
  return {
    ...posStyle,
    fontSize: `${fontSize}px`,
    color: color,
    textShadow: `${strokeWidth}px ${strokeWidth}px 0 ${strokeColor}, -${strokeWidth}px -${strokeWidth}px 0 ${strokeColor}, ${strokeWidth}px -${strokeWidth}px 0 ${strokeColor}, -${strokeWidth}px ${strokeWidth}px 0 ${strokeColor}`,
    fontWeight: 'bold',
  }
})

// 获取位置指示点样式
const getPositionIndicatorStyle = (position: string) => {
  const positionMap: Record<string, { top?: string; bottom?: string; left?: string; right?: string; transform: string }> = {
    'top_left': { top: '8%', left: '5%', transform: 'none' },
    'top': { top: '8%', left: '50%', transform: 'translateX(-50%)' },
    'top_right': { top: '8%', right: '5%', transform: 'none' },
    'left': { top: '50%', left: '5%', transform: 'translateY(-50%)' },
    'center': { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
    'right': { top: '50%', right: '5%', transform: 'translateY(-50%)' },
    'bottom_left': { bottom: '8%', left: '5%', transform: 'none' },
    'bottom': { bottom: '8%', left: '50%', transform: 'translateX(-50%)' },
    'bottom_right': { bottom: '8%', right: '5%', transform: 'none' },
  }
  return positionMap[position] || positionMap['bottom']
}

const getMediaUrl = (filePath: string) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || 'http://localhost:8000'
  return `${baseUrl}/static/uploads/${filePath.replace('uploads/', '')}`
}

const previewVideo = (filePath: string) => {
  previewVideoUrl.value = getMediaUrl(filePath)
  showVideoPreview.value = true
}

const filterVoiceOption = (input: string, option: { children?: { children?: string }[] }) => {
  return option.children?.[0]?.children?.toLowerCase().includes(input.toLowerCase()) ?? false
}

const onLocaleChange = async (locale: string) => {
  form.value.voice_name = ''
  clearAudioPreview()
  await loadTtsVoices(locale)
}

// 监听文案变化，清除配音缓存
watch(() => form.value.script, () => {
  if (audioPreviewUrl.value) {
    clearAudioPreview()
  }
})

// 平台预设配置
const PLATFORM_PRESETS: Record<string, { resolution: string; layout: string; fps: number }> = {
  douyin: { resolution: '1080p', layout: '9:16', fps: 30 },
  kuaishou: { resolution: '1080p', layout: '9:16', fps: 30 },
  xiaohongshu: { resolution: '1080p', layout: '3:4', fps: 30 },
  bilibili: { resolution: '1080p', layout: '16:9', fps: 30 },
  youtube: { resolution: '1080p', layout: '16:9', fps: 30 },
  instagram_reels: { resolution: '1080p', layout: '9:16', fps: 30 },
  instagram_feed: { resolution: '1080p', layout: '1:1', fps: 30 },
  weixin: { resolution: '1080p', layout: '9:16', fps: 30 },
}

const onPlatformPresetChange = (preset: string) => {
  if (preset && PLATFORM_PRESETS[preset]) {
    const config = PLATFORM_PRESETS[preset]
    form.value.video_resolution = config.resolution
    form.value.video_layout = config.layout
    form.value.video_fps = config.fps
  }
}

const clearAudioPreview = () => {
  if (audioPreviewRef.value) {
    audioPreviewRef.value.pause()
    audioPreviewRef.value.currentTime = 0
  }
  audioPreviewUrl.value = null
  audioState.value = 'idle'
  playbackProgress.value = 0
  currentTime.value = 0
  audioDuration.value = 0
  ttsSubtitles.value = []  // 清除字幕
  stopWaveAnimation()
}

// 格式化时间
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 波形动画
const startWaveAnimation = () => {
  const animate = () => {
    waveOffset.value += 0.15
    waveAnimationId = requestAnimationFrame(animate)
  }
  animate()
}

const stopWaveAnimation = () => {
  if (waveAnimationId) {
    cancelAnimationFrame(waveAnimationId)
    waveAnimationId = null
  }
}

// 音频事件处理
const onTimeUpdate = () => {
  if (audioPreviewRef.value && audioDuration.value > 0) {
    currentTime.value = audioPreviewRef.value.currentTime
    playbackProgress.value = (currentTime.value / audioDuration.value) * 100
  }
}

const onLoadedMetadata = () => {
  if (audioPreviewRef.value) {
    audioDuration.value = audioPreviewRef.value.duration
  }
}

const onCanPlay = () => {
  if (audioState.value === 'generating') {
    audioState.value = 'ready'
  }
}

const onAudioEnded = () => {
  audioState.value = 'ready'
  playbackProgress.value = 0
  currentTime.value = 0
  stopWaveAnimation()
}

const onPreviewVolumeChange = (val: number) => {
  if (audioPreviewRef.value) {
    audioPreviewRef.value.volume = val / 100
  }
}

// 播放/暂停/生成
const handleAudioAction = async () => {
  if (audioState.value === 'idle' || !audioPreviewUrl.value) {
    // 需要先生成音频
    await generateAudioPreview()
  } else if (audioState.value === 'playing') {
    // 暂停
    audioPreviewRef.value?.pause()
    audioState.value = 'ready'
    stopWaveAnimation()
  } else if (audioState.value === 'ready') {
    // 播放
    audioPreviewRef.value?.play()
    audioState.value = 'playing'
    startWaveAnimation()
  }
}

const generateAudioPreview = async () => {
  if (!form.value.script.trim()) {
    message.warning('请先输入文案')
    return
  }
  if (!form.value.voice_name) {
    message.warning('请选择配音音色')
    return
  }

  audioState.value = 'generating'
  try {
    const result = await videoApi.generateAudioWithSubtitles({
      text: form.value.script,
      voice: form.value.voice_name || '',
      rate: form.value.voice_speed || '+0%',
      volume: form.value.voice_volume || '+0%',
      pitch: form.value.voice_pitch || '+0Hz',
    })
    audioPreviewUrl.value = result.audio_url
    // 保存字幕数据
    ttsSubtitles.value = result.sentence_subtitles || []
    // 等待音频加载后自动播放
    setTimeout(() => {
      if (audioPreviewRef.value && audioState.value === 'ready') {
        audioPreviewRef.value.play()
        audioState.value = 'playing'
        startWaveAnimation()
      }
    }, 300)
    message.success('配音生成成功')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '生成配音失败')
    audioState.value = 'idle'
  }
}

const loadTtsVoices = async (locale?: string) => {
  loadingVoices.value = true
  try {
    const data = await videoApi.getTtsVoices(locale)
    ttsVoices.value = data.voices
    if (data.voices.length > 0 && !form.value.voice_name && data.voices[0]) {
      form.value.voice_name = data.voices[0].short_name
    }
  } catch (error) {
    console.error('加载音色失败:', error)
  } finally {
    loadingVoices.value = false
  }
}

const generateScript = async () => {
  if (!form.value.topic) {
    message.warning('请先输入视频主题')
    return
  }
  generatingScript.value = true
  try {
    const result = await videoApi.generateScript({
      topic: form.value.topic,
      provider: selectedProvider.value,
      style: selectedStyle.value,
      duration: '1分钟',
      language: form.value.script_language || 'zh'
    })
    form.value.script = result.script
    message.success(`文案生成成功`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '文案生成失败')
  } finally {
    generatingScript.value = false
  }
}

// 自定义配音上传
const handleCustomAudioUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  if (file.size > 50 * 1024 * 1024) {
    message.error('文件大小不能超过 50MB')
    return
  }
  
  customAudioFile.value = file
  customAudioUrl.value = URL.createObjectURL(file)
  
  // 上传到服务器
  try {
    const result = await videoApi.uploadCustomAudio(file)
    form.value.voice_audio_url = result.file_path
    message.success('配音文件上传成功')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '上传失败')
  }
}

const removeCustomAudio = () => {
  if (customAudioUrl.value) {
    URL.revokeObjectURL(customAudioUrl.value)
  }
  customAudioFile.value = null
  customAudioUrl.value = null
  customAudioDuration.value = 0
  customAudioCurrentTime.value = 0
  customAudioSubtitles.value = []  // 清除字幕
  form.value.voice_audio_url = undefined
}

const handleCustomAudioPlay = () => {
  const audio = customAudioRef.value
  if (!audio) return
  
  if (customAudioPlaying.value) {
    audio.pause()
    customAudioPlaying.value = false
  } else {
    audio.play()
    customAudioPlaying.value = true
  }
}

const onCustomAudioTimeUpdate = () => {
  const audio = customAudioRef.value
  if (audio) {
    customAudioCurrentTime.value = audio.currentTime
  }
}

const onCustomAudioLoaded = () => {
  const audio = customAudioRef.value
  if (audio) {
    customAudioDuration.value = audio.duration
    // 更新预估视频时长
    audioDuration.value = audio.duration
    
    // 根据文案生成简单的字幕时间戳（按句子均匀分配）
    if (form.value.script) {
      generateSubtitlesFromScript(audio.duration)
    }
  }
}

// 根据文案和音频时长生成字幕时间戳
const generateSubtitlesFromScript = (duration: number) => {
  const script = form.value.script.trim()
  if (!script) return
  
  // 按标点分割句子
  const sentences = script.split(/[。！？.!?\n]+/).filter(s => s.trim())
  if (sentences.length === 0) return
  
  const avgDuration = duration / sentences.length
  const subtitles: { text: string; start: number; end: number }[] = []
  
  sentences.forEach((sentence, index) => {
    subtitles.push({
      text: sentence.trim(),
      start: index * avgDuration,
      end: (index + 1) * avgDuration
    })
  })
  
  customAudioSubtitles.value = subtitles
}

const onCustomAudioEnded = () => {
  customAudioPlaying.value = false
  customAudioCurrentTime.value = 0
}

const handleBgmUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (file.size > 20 * 1024 * 1024) {
    message.error('文件大小不能超过 20MB')
    return
  }
  try {
    const result = await videoApi.uploadBgm(file)
    form.value.bgm_path = result.file_path
    bgmFileName.value = result.filename
    message.success('BGM 上传成功')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '上传失败')
  }
}

const handleMediaUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  const imageFiles: File[] = []
  const videoFiles: File[] = []
  const imageTypes = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
  const videoTypes = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

  for (const file of files) {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (imageTypes.includes(ext)) {
      if (file.size > 10 * 1024 * 1024) {
        message.error(`图片 ${file.name} 超过 10MB 限制`)
        continue
      }
      imageFiles.push(file)
    } else if (videoTypes.includes(ext)) {
      if (file.size > 150 * 1024 * 1024) {
        message.error(`视频 ${file.name} 超过 150MB 限制`)
        continue
      }
      videoFiles.push(file)
    }
  }

  uploadingMedia.value = true
  try {
    if (imageFiles.length > 0) {
      const imgResult = await videoApi.uploadImages(imageFiles)
      uploadedImages.value.push(...imgResult.files)
    }
    if (videoFiles.length > 0) {
      const vidResult = await videoApi.uploadVideos(videoFiles)
      uploadedVideos.value.push(...vidResult.files)
    }
    form.value.media_paths = [
      ...uploadedImages.value.map(i => i.file_path),
      ...uploadedVideos.value.map(v => v.file_path)
    ]
    const total = imageFiles.length + videoFiles.length
    if (total > 0) message.success(`成功上传 ${total} 个素材`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '上传失败')
  } finally {
    uploadingMedia.value = false
    target.value = ''
  }
}

const removeImage = (idx: number) => {
  uploadedImages.value.splice(idx, 1)
  form.value.media_paths = [...uploadedImages.value.map(i => i.file_path), ...uploadedVideos.value.map(v => v.file_path)]
}

const removeVideo = (idx: number) => {
  uploadedVideos.value.splice(idx, 1)
  form.value.media_paths = [...uploadedImages.value.map(i => i.file_path), ...uploadedVideos.value.map(v => v.file_path)]
}

const handleGenerate = async () => {
  if (!form.value.script.trim()) {
    message.warning('请生成文案后再试')
    return
  }
  if (!userStore.isLoggedIn) {
    message.warning('请先登录')
    router.push({ path: '/auth', query: { redirect: '/video' } })
    return
  }
  currentState.value = 'generating'
  progress.value = 0
  progressMessage.value = '正在创建任务...'
  try {
    const task = await videoApi.createTask(form.value)
    pollController = videoApi.pollProgress(
      task.task_id,
      (prog, msg) => { progress.value = prog; progressMessage.value = msg },
      (downloadUrl, duration) => {
        progress.value = 100
        progressMessage.value = '视频生成完成'
        generatedVideoUrl.value = downloadUrl
        videoDuration.value = duration || null
        currentState.value = 'complete'
        userStore.refreshQuotas()
        message.success('视频生成成功！')
      },
      (error) => { message.error(error); currentState.value = 'idle' }
    )
  } catch (error) {
    message.error(error instanceof Error ? error.message : '创建任务失败')
    currentState.value = 'idle'
  }
}

const handleDownload = () => {
  if (generatedVideoUrl.value) {
    const link = document.createElement('a')
    link.href = generatedVideoUrl.value
    link.download = 'generated_video.mp4'
    link.click()
  }
}

const handleReset = () => {
  currentState.value = 'idle'
  progress.value = 0
  progressMessage.value = ''
  generatedVideoUrl.value = null
  videoDuration.value = null
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (pollController) pollController.stop()
  stopWaveAnimation()
})

onMounted(async () => {
  try {
    const data = await videoApi.getAIProviders()
    aiProviders.value = data.providers
    aiStyles.value = data.styles
  } catch (error) {
    console.error('获取 AI 配置失败:', error)
  }
  try {
    const ttsData = await videoApi.getTtsLocales()
    ttsLocales.value = ttsData.locales
    ttsSpeeds.value = ttsData.speeds
    if (ttsData.speeds.length > 2 && ttsData.speeds[2]) form.value.voice_speed = ttsData.speeds[2].value
    await loadTtsVoices(selectedLocale.value)
  } catch (error) {
    console.error('获取 TTS 配置失败:', error)
  }
})
</script>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  color: white !important;
}

:deep(.ant-select-selector) {
  border-radius: 8px !important;
}

:deep(.ant-select:hover .ant-select-selector),
:deep(.ant-select-focused .ant-select-selector) {
  border-color: #10b981 !important;
}

:deep(.ant-select-focused .ant-select-selector) {
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1) !important;
}

:deep(.ant-switch-checked) {
  background: #10b981 !important;
}

:deep(.ant-slider-track) {
  background-color: #10b981 !important;
}

:deep(.ant-slider-handle) {
  border-color: #10b981 !important;
}

:deep(.ant-input-number:hover),
:deep(.ant-input-number-focused) {
  border-color: #10b981 !important;
}

:deep(.ant-progress-bg) {
  background: linear-gradient(90deg, #10b981 0%, #059669 100%) !important;
}

:deep(.ant-steps-item-process .ant-steps-item-icon) {
  background-color: #10b981 !important;
  border-color: #10b981 !important;
}

:deep(.ant-steps-item-finish .ant-steps-item-icon) {
  background-color: #d1fae5 !important;
  border-color: #10b981 !important;
}

:deep(.ant-steps-item-finish .ant-steps-item-icon > .ant-steps-icon) {
  color: #10b981 !important;
}

:deep(.ant-steps-item-finish > .ant-steps-item-container > .ant-steps-item-content > .ant-steps-item-title::after) {
  background-color: #10b981 !important;
}

:deep(.ant-steps-item:not(.ant-steps-item-active):not(.ant-steps-item-process) > .ant-steps-item-container[role='button']:hover .ant-steps-item-icon) {
  border-color: #10b981 !important;
}

:deep(.ant-steps-item:not(.ant-steps-item-active):not(.ant-steps-item-process) > .ant-steps-item-container[role='button']:hover .ant-steps-item-icon .ant-steps-icon) {
  color: #10b981 !important;
}

:deep(.ant-steps-item:not(.ant-steps-item-active):not(.ant-steps-item-process) > .ant-steps-item-container[role='button']:hover .ant-steps-item-title),
:deep(.ant-steps-item:not(.ant-steps-item-active):not(.ant-steps-item-process) > .ant-steps-item-container[role='button']:hover .ant-steps-item-description) {
  color: #10b981 !important;
}
</style>
