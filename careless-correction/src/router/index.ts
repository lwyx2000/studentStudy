import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/onboarding'
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/child/OnboardingAssessment.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/child/Dashboard.vue')
  },
  {
    path: '/habit',
    name: 'HabitCenter',
    component: () => import('../views/child/HabitPrintableCenter.vue')
  },
  {
    path: '/mistake',
    name: 'TreasureBank',
    component: () => import('../views/child/DiagnosticMistakeBook.vue')
  },
  {
    path: '/tracker',
    name: 'ItemTracker',
    component: () => import('../views/child/ItemTracker.vue')
  },
  {
    path: '/growth',
    name: 'GrowthArchive',
    component: () => import('../views/child/GrowthArchive.vue')
  },
  {
    path: '/time-task',
    name: 'TimeTaskCabin',
    component: () => import('../views/child/TimeTaskCabin.vue')
  },
  {
    path: '/badge',
    name: 'BadgeRoom',
    component: () => import('../views/child/FamilyCovenantBadgeRoom.vue')
  },
  {
    path: '/parent',
    name: 'ParentControl',
    component: () => import('../views/parent/ParentalControlCenter.vue')
  },
  {
    path: '/parent/habit-assign',
    name: 'HabitAssign',
    component: () => import('../views/parent/HabitAssignPage.vue')
  },
  {
    path: '/parent/lab',
    name: 'EvidenceLab',
    component: () => import('../views/parent/EvidenceBasedLab.vue')
  },
  {
    path: '/parent/garden',
    name: 'CommunityGarden',
    component: () => import('../views/parent/CommunityGarden.vue')
  },
  {
    path: '/printable',
    name: 'PrintableChecklist',
    component: () => import('../views/child/A4PrintableChecklist.vue')
  },
  {
    path: '/guide',
    name: 'UsageGuide',
    component: () => import('../views/child/UsageGuide.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router