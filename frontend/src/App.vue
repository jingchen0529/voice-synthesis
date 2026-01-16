<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import AppHeader from './components/layout/Header.vue'
import AppFooter from './components/layout/Footer.vue'

const route = useRoute()

// 不需要 Layout 的页面
const noLayoutPages = ['/auth', '/forgot-password']
const showLayout = computed(() => !noLayoutPages.includes(route.path))
</script>

<template>
  <div id="app" class="flex flex-col min-h-screen">
    <AppHeader v-if="showLayout" />
    <main class="flex-1">
      <RouterView />
    </main>
    <AppFooter v-if="showLayout" />
  </div>
</template>
