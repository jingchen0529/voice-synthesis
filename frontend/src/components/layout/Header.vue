<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <header class="fixed top-0 left-0 right-0 z-50 shadow-sm border-b border-slate-200/50">
    <div class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 lg:h-20 relative">
        <!-- Left: Logo -->
        <router-link to="/" class="flex items-center gap-2 group z-10">
          <div
            class="w-8 h-8 lg:w-9 lg:h-9 bg-gradient-to-br from-emerald-500 to-green-600 rounded-lg flex items-center justify-center shadow-lg group-hover:shadow-emerald-500/30 transition-all duration-300"
          >
            <span class="text-white font-bold text-lg leading-none">J</span>
          </div>
          <div class="flex flex-col">
            <span
              class="text-lg lg:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700 tracking-tight"
              >JINGCHEN</span
            >
          </div>
        </router-link>

        <!-- Center: Desktop Nav (Flattened & Centered) -->
        <nav
          class="hidden lg:flex items-center gap-1 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        >
          <router-link to="/tts" class="nav-item" active-class="active">
            <Volume2 class="w-4 h-4" />
            <span>语音合成</span>
          </router-link>

          <router-link to="/video" class="nav-item" active-class="active">
            <Film class="w-4 h-4" />
            <span>视频合成</span>
          </router-link>

          <div class="w-px h-4 bg-slate-200 mx-2"></div>
          <router-link to="/leads" class="nav-item" active-class="active">
            <Users class="w-4 h-4" />
            <span>探索获客</span>
          </router-link>
        </nav>

        <!-- Right: Actions -->
        <div class="flex items-center gap-2 lg:gap-4 z-10">
          <!-- 用户信息 / 登录 -->
          <template v-if="userStore.isLoggedIn">
            <a-dropdown placement="bottomRight">
              <button
                class="flex items-center gap-2 p-1 pl-3 pr-1 rounded-full border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all ml-2 bg-white"
              >
                <span class="text-sm font-medium text-slate-700 max-w-[80px] truncate">{{
                  userStore.user?.username
                }}</span>
                <div
                  class="w-8 h-8 bg-gradient-to-br from-emerald-500 to-green-600 rounded-full flex items-center justify-center text-white font-medium text-sm"
                >
                  {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
                </div>
              </button>
              <template #overlay>
                <a-menu class="min-w-[160px] rounded-xl shadow-xl mt-2 p-1">
                  <div class="px-4 py-2 border-b border-slate-100 mb-1">
                    <p class="text-xs text-slate-500">剩余次数</p>
                    <p class="text-lg font-bold text-emerald-600">
                      {{ userStore.user?.remainingUses || 0 }}
                    </p>
                  </div>
                  <a-menu-item key="profile">
                    <router-link to="/profile" class="flex items-center gap-2 py-1">
                      <User class="w-4 h-4" />
                      个人中心
                    </router-link>
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item key="logout" @click="handleLogout">
                    <span class="flex items-center gap-2 text-red-600 py-1">
                      <LogOut class="w-4 h-4" />
                      退出登录
                    </span>
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </template>

          <template v-else>
            <router-link
              to="/login"
              class="ml-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg shadow-lg shadow-emerald-500/30 transition-all duration-300 flex items-center gap-2"
            >
              <LogIn class="w-4 h-4" />
              <span>登录</span>
            </router-link>
          </template>

          <!-- 移动端菜单按钮 -->
          <button
            @click="toggleMobileMenu"
            class="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
          >
            <Menu class="w-6 h-6" />
          </button>
        </div>
      </div>
    </div>

    <!-- 移动端菜单 -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div
        v-if="showMobileMenu"
        class="lg:hidden absolute top-full left-0 right-0 bg-white border-b border-slate-200 shadow-xl max-h-[80vh] overflow-y-auto"
      >
        <nav class="p-4 space-y-1">
          <router-link to="/leads" class="mobile-nav-link" @click="showMobileMenu = false">
            <Users class="w-4 h-4" />
            探索获客
          </router-link>
          <router-link to="/tiktok" class="mobile-nav-link" @click="showMobileMenu = false">
            <Video class="w-4 h-4" />
            TikTok 运营
          </router-link>
          <div class="h-px bg-slate-100 my-2"></div>
          <router-link to="/tts" class="mobile-nav-link" @click="showMobileMenu = false">
            <Volume2 class="w-4 h-4" />
            语音合成
          </router-link>
          <router-link to="/video" class="mobile-nav-link" @click="showMobileMenu = false">
            <Film class="w-4 h-4" />
            视频合成
          </router-link>
        </nav>
      </div>
    </transition>
  </header>
  <!-- Spacer -->
  <div class="h-16 lg:h-20"></div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Users, Volume2, Video, Film, FileText, Menu, User, LogOut, LogIn } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { message } from 'ant-design-vue'

const router = useRouter()
const userStore = useUserStore()
const showMobileMenu = ref(false)

const toggleMobileMenu = () => {
  showMobileMenu.value = !showMobileMenu.value
}

const handleLogout = () => {
  userStore.logout()
  message.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.nav-item {
  @apply px-4 py-2 text-slate-600 font-medium text-sm flex items-center gap-2 rounded-full hover:bg-slate-50 hover:text-emerald-600 transition-all cursor-pointer select-none;
}

.nav-item.active {
  @apply bg-emerald-50 text-emerald-600 font-semibold;
}

.mobile-nav-link {
  @apply flex items-center gap-3 px-3 py-3 text-slate-600 rounded-xl hover:bg-emerald-50 hover:text-emerald-600 transition-all font-medium;
}

.mobile-nav-link.router-link-active {
  @apply bg-emerald-50 text-emerald-600 font-semibold;
}

:deep(.ant-dropdown-menu) {
  padding: 8px;
  border-radius: 12px;
}

:deep(.ant-dropdown-menu-item) {
  border-radius: 8px;
}
</style>
