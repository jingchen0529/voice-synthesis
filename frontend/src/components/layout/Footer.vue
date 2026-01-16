<!-- eslint-disable vue/multi-word-component-names -->
<template>
    <footer class="bg-slate-50/80 backdrop-blur-md border-t border-slate-200 mt-auto">
        <div class="container mx-auto max-w-6xl px-4 py-4">
            <div class="flex items-center justify-center gap-3 text-sm text-slate-600">
                <div
                    class="w-5 h-5 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded flex items-center justify-center flex-shrink-0">
                    <Zap class="w-3 h-3 text-white" />
                </div>
                <span>多平台集成服务，提供 TTS、视频混剪、TikTok 等功能，为您的创作提供强大支持</span>
                <span class="text-slate-400">|</span>
                <span>© {{ currentYear }} Integration Platform</span>
            </div>
        </div>
    </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Zap } from 'lucide-vue-next'

const currentYear = computed(() => new Date().getFullYear())
</script>
