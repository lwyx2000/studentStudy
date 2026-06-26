import { createRouter, createWebHistory } from 'vue-router'
import { getAuthToken } from '../utils/api'

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
    component: () => import('../views/child/FamilyCovenantBadgeRoom.vue'),
  },
  {
    path: '/sunlight',
    name: 'SunlightRedemption',
    component: () => import('../views/child/SunlightRedemption.vue'),
  },
  {
    path: '/printable',
    name: 'PrintableChecklist',
    component: () => import('../views/child/A4PrintableChecklist.vue'),
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
    path: '/parent/garden',
    name: 'CommunityGarden',
    component: () => import('../views/parent/CommunityGarden.vue'),
    meta: { parentOnly: true },
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = getAuthToken()

  // 公开路由直接放行
  if (to.meta.public) return true

  // 未登录跳登录页
  if (!token) return '/login'

  // 家长专属路由：需要从 store 判断角色
  // 这里用 localStorage 存的 profile 快速判断，避免循环依赖
  if (to.meta.parentOnly) {
    try {
      const saved = localStorage.getItem('cc-user')
      const profile = saved ? JSON.parse(saved)?.profile : null
      if (profile?.role !== 'parent') return '/dashboard'
    } catch { /* 跳过 */ }
  }

  return true
})

export default router
