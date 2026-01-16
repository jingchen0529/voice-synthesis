import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/tts',
    },
    {
      path: '/auth',
      name: 'auth',
      component: () => import('@/views/AuthView.vue'),
      meta: { hideForAuth: true },
    },
    {
      path: '/login',
      redirect: '/auth?mode=login',
    },
    {
      path: '/tts',
      name: 'tts',
      component: () => import('@/views/TtsView.vue'),
    },
    {
      path: '/video',
      name: 'video',
      component: () => import('@/views/VideoView.vue'),
    },
    {
      path: '/leads',
      name: 'leads',
      component: () => import('@/views/LeadView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // 已登录用户访问登录页，跳转到首页
  if (to.meta.hideForAuth && userStore.isLoggedIn) {
    next('/tts')
    return
  }

  // 需要登录的页面（如个人中心）
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({
      path: '/auth',
      query: { redirect: to.fullPath },
    })
    return
  }

  next()
})

export default router
