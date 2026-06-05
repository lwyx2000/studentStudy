import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  UserProfile,
  ExecutiveFunctionAssessment,
  TaskItem,
  MistakeRecord,
  BadgeItem,
  FamilyCovenant,
  ParentSettings,
  GrowthDataPoint,
  DiagnosticAlert,
  ItemLossRecord,
  PomodoroSession,
  HabitSOP,
  DiscussionPost,
  ArticleResource,
} from '../types'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile>({
    id: '',
    name: '',
    grade: 1,
    avatarUrl: '',
    role: 'child',
  })
  const assessment = ref<ExecutiveFunctionAssessment>({
    focusAttention: 3,
    organization: 3,
    emotionalControl: 3,
    recommendedLevel: 2,
  })
  const sunlightPoints = ref(0)
  const isOnboarded = ref(false)

  const isLowGrade = computed(() => profile.value.grade <= 2)
  const isHighGrade = computed(() => profile.value.grade >= 5)

  function setProfile(p: Partial<UserProfile>) {
    Object.assign(profile.value, p)
  }

  function setAssessment(a: ExecutiveFunctionAssessment) {
    assessment.value = a
    const avg = (a.focusAttention + a.organization + a.emotionalControl) / 3
    assessment.value.recommendedLevel = Math.max(1, Math.min(5, Math.round(6 - avg)))
  }

  function completeOnboarding() {
    isOnboarded.value = true
  }

  function addSunlightPoints(pts: number) {
    sunlightPoints.value += pts
  }

  return {
    profile,
    assessment,
    sunlightPoints,
    isOnboarded,
    isLowGrade,
    isHighGrade,
    setProfile,
    setAssessment,
    completeOnboarding,
    addSunlightPoints,
  }
})

export const useTaskStore = defineStore('task', () => {
  const todayTasks = ref<TaskItem[]>([])
  const currentWeekHabit = ref<HabitSOP | null>(null)
  const weeklyProgress = ref(0)

  function completeTask(id: string) {
    const task = todayTasks.value.find(t => t.id === id)
    if (task) {
      task.status = 'completed'
    }
  }

  function setTodayTasks(tasks: TaskItem[]) {
    todayTasks.value = tasks
  }

  return { todayTasks, currentWeekHabit, weeklyProgress, completeTask, setTodayTasks }
})

export const useMistakeStore = defineStore('mistake', () => {
  const records = ref<MistakeRecord[]>([])
  const todayReviewCount = ref(0)

  function addRecord(record: MistakeRecord) {
    records.value.push(record)
  }

  return { records, todayReviewCount, addRecord }
})

export const useBadgeStore = defineStore('badge', () => {
  const badges = ref<BadgeItem[]>([])
  const covenants = ref<FamilyCovenant[]>([])
  const confettiActive = ref(false)

  function unlockBadge(id: string) {
    const badge = badges.value.find(b => b.id === id)
    if (badge) {
      badge.unlocked = true
      badge.unlockedAt = new Date().toISOString()
      confettiActive.value = true
      setTimeout(() => { confettiActive.value = false }, 3000)
    }
  }

  function addCovenant(covenant: FamilyCovenant) {
    covenants.value.push(covenant)
  }

  return { badges, covenants, confettiActive, unlockBadge, addCovenant }
})

export const useGrowthStore = defineStore('growth', () => {
  const trendData = ref<GrowthDataPoint[]>([])
  const alerts = ref<DiagnosticAlert[]>([])
  const itemLossRecords = ref<ItemLossRecord[]>([])

  return { trendData, alerts, itemLossRecords }
})

export const usePomodoroStore = defineStore('pomodoro', () => {
  const sessions = ref<PomodoroSession[]>([])
  const isRunning = ref(false)
  const remainingSeconds = ref(25 * 60)

  function startSession() {
    isRunning.value = true
  }

  function pauseSession() {
    isRunning.value = false
  }

  return { sessions, isRunning, remainingSeconds, startSession, pauseSession }
})

export const useParentStore = defineStore('parent', () => {
  const settings = ref<ParentSettings>({
    difficultyLevel: 2,
    dailyReminder: true,
    achievementNotification: true,
    weeklyReport: true,
    schoolSync: false,
  })
  const discussionPosts = ref<DiscussionPost[]>([])
  const articles = ref<ArticleResource[]>([])

  function updateSettings(s: Partial<ParentSettings>) {
    Object.assign(settings.value, s)
  }

  return { settings, discussionPosts, articles, updateSettings }
})