import { createRouter, createWebHistory } from 'vue-router'
import { getAuthToken } from '../utils/api'
import { useUserStore } from '../stores'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginRegister.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/child/OnboardingAssessment.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/child/Dashboard.vue'),
  },
  {
    path: '/habit',
    name: 'HabitCenter',
    component: () => import('../views/child/HabitPrintableCenter.vue'),
  },
  {
    path: '/mistake',
    name: 'MistakeBook',
    component: () => import('../views/child/DiagnosticMistakeBook.vue'),
  },
  {
    path: '/tracker',
    name: 'ItemTracker',
    component: () => import('../views/child/ItemTracker.vue'),
  },
  {
    path: '/growth',
    name: 'GrowthArchive',
    component: () => import('../views/child/GrowthArchive.vue'),
  },
  {
    path: '/badge',
    name: 'BadgeRoom',
    component: () => import('../views/child/BadgeRoom.vue'),
  },
  {
    path: '/sunlight',
    name: 'SunlightRedemption',
    component: () => import('../views/child/SunlightRedemption.vue'),
  },
  {
    path: '/printable',
    redirect: '/habit',
  },
  // 家长端
  {
    path: '/parent',
    name: 'ParentControl',
    component: () => import('../views/parent/ParentalControlCenter.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/children',
    name: 'ChildManagement',
    component: () => import('../views/parent/ChildManagement.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/tree',
    name: 'SunshineTree',
    component: () => import('../views/child/SunshineTree.vue'),
  },
  {
    path: '/guide',
    name: 'UsageGuide',
    component: () => import('../views/child/UsageGuide.vue'),
  },
  {
    path: '/parent/tasks',
    name: 'TaskHabitManager',
    component: () => import('../views/parent/TaskHabitManager.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/progress',
    name: 'ProgressDashboard',
    component: () => import('../views/parent/ProgressDashboard.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/items',
    name: 'ItemStats',
    component: () => import('../views/parent/ItemStats.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/sunlight',
    name: 'SunlightManagement',
    component: () => import('../views/parent/SunlightManagement.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/badges',
    name: 'ParentBadges',
    component: () => import('../views/parent/ParentBadges.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/llm',
    name: 'LlmConfig',
    component: () => import('../views/parent/LlmConfig.vue'),
    meta: { parentOnly: true },
  },
  {
    path: '/parent/inventory',
    name: 'TaskHabitInventory',
    component: () => import('../views/parent/TaskHabitInventory.vue'),
    meta: { parentOnly: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const token = getAuthToken()

  // 公开路由直接放行
  if (to.meta.public) return true

  // 未登录跳登录页
  if (!token) return '/login'

  if (to.meta.parentOnly) {
    try {
      const store = useUserStore()
      // 刷新页面时 store 的 role 默认是 'child'，主动从 API 加载真实数据
      await store.fetchFromApi()
      if (store.profile.role !== 'parent') return '/dashboard'
    } catch { return '/dashboard' }
  }

  return true
})

export default router
