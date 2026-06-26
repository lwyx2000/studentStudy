import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import type {
  ArticleResource,
  BadgeItem,
  DiagnosticAlert,
  DiscussionPost,
  ExecutiveFunctionAssessment,
  FamilyCovenant,
  GrowthDataPoint,
  HabitSOP,
  ItemLossRecord,
  ItemStorageRecord,
  LlmConfig,
  MistakeRecord,
  ParentSettings,
  RewardItem,
  SOPStep,
  SunlightRecord,
  TaskItem,
  UserProfile,
} from '../types'
import {
  api,
  normalizeAlert,
  normalizeBadge,
  normalizeChild,
  normalizeCovenant,
  normalizeGrowthPoint,
  normalizeHabit,
  normalizeItemLoss,
  normalizeItemStorage,
  normalizeLlmConfig,
  normalizeMistake,
  normalizeParentSettings,
  normalizePost,
  normalizeRewardItem,
  normalizeSunlightRecord,
  normalizeTask,
  normalizeUser,
} from '../utils/api'

function loadState<T>(key: string, fallback: T): T {  if (typeof localStorage === 'undefined') return fallback
  try {
    const raw = localStorage.getItem(key)
    return raw ? { ...fallback, ...JSON.parse(raw) } : fallback
  } catch {
    return fallback
  }
}

function persistState(key: string, state: unknown) {
  if (typeof localStorage === 'undefined') return
  localStorage.setItem(key, JSON.stringify(state))
}


const defaultProfile: UserProfile = {
  id: 'local-child-001',
  name: '',
  grade: 3,
  avatarUrl: '',
  role: 'child',
}

const defaultAssessment: ExecutiveFunctionAssessment = {
  focusAttention: 3,
  organization: 3,
  emotionalControl: 3,
  planning: 3,
  impulseControl: 3,
  recommendedLevel: 2,
}

const defaultRewardItems: RewardItem[] = [
  { id: 'ri-1', name: '亲子电影夜', description: '周末选一部电影全家一起看', cost: 50, icon: '🎬', active: true },
  { id: 'ri-2', name: '乐高自由拼', description: '额外 30 分钟乐高搭建时间', cost: 30, icon: '🧱', active: true },
  { id: 'ri-3', name: '绘本选购', description: '去书店自选一本绘本', cost: 40, icon: '📖', active: true },
  { id: 'ri-4', name: '公园野餐', description: '周末去公园野餐+自由玩耍', cost: 60, icon: '🧺', active: true },
]

export const useUserStore = defineStore('user', () => {
  const saved = loadState('cc-user', {
    profile: defaultProfile,
    assessment: defaultAssessment,
    sunlightPoints: 0,
    isOnboarded: false,
    sunlightHistory: [] as SunlightRecord[],
    rewardItems: defaultRewardItems,
  })

  const profile = ref<UserProfile>(saved.profile)
  const assessment = ref<ExecutiveFunctionAssessment>({ ...defaultAssessment, ...saved.assessment })
  const sunlightPoints = ref(saved.sunlightPoints)
  const isOnboarded = ref(saved.isOnboarded)
  const sunlightHistory = ref<SunlightRecord[]>(saved.sunlightHistory || [])
  const rewardItems = ref<RewardItem[]>(saved.rewardItems || defaultRewardItems)

  const isLowGrade = computed(() => profile.value.grade <= 2)
  const isHighGrade = computed(() => profile.value.grade >= 5)

  watch(
    () => ({ profile: profile.value, assessment: assessment.value, sunlightPoints: sunlightPoints.value, isOnboarded: isOnboarded.value, sunlightHistory: sunlightHistory.value, rewardItems: rewardItems.value }),
    value => persistState('cc-user', value),
    { deep: true },
  )

  async function fetchFromApi() {
    try {
      const user = await api.auth.session()
      const u = normalizeUser(user)
      profile.value = u
      sunlightPoints.value = (user as any).sunlight_points ?? sunlightPoints.value
    } catch { /* offline */ }
    try {
      const { balance } = await api.points.getBalance()
      sunlightPoints.value = balance
    } catch { /* offline */ }
    try {
      const res = await api.points.getHistory()
      const raw: any[] = res.history ?? []
      sunlightHistory.value = raw.map(normalizeSunlightRecord)
    } catch { /* offline */ }
    try {
      const res = await api.points.getRewards()
      const raw: any[] = res.rewards ?? []
      if (raw.length) rewardItems.value = raw.map(normalizeRewardItem)
    } catch { /* offline */ }
  }

  function setProfile(p: Partial<UserProfile>) {
    Object.assign(profile.value, p)
    api.auth.updateProfile(p).catch(() => {})
  }

  function setAssessment(a: ExecutiveFunctionAssessment) {
    const merged = { ...defaultAssessment, ...a }
    const avg = (merged.focusAttention + merged.organization + merged.emotionalControl + merged.planning + merged.impulseControl) / 5
    merged.recommendedLevel = Math.max(1, Math.min(5, Math.round(6 - avg)))
    assessment.value = merged
  }

  function completeOnboarding() {
    isOnboarded.value = true
  }

  function addSunlightPoints(pts: number, reason = '任务奖励') {
    sunlightPoints.value = Math.max(0, sunlightPoints.value + pts)
    sunlightHistory.value.unshift({
      id: `sl-${Date.now()}`,
      amount: pts,
      reason,
      type: pts >= 0 ? 'earn' : 'spend',
      timestamp: new Date().toISOString(),
    })
  }

  function redeemItem(itemId: string) {
    const item = rewardItems.value.find(i => i.id === itemId)
    if (!item || !item.active) return false
    if (sunlightPoints.value < item.cost) return false
    sunlightPoints.value -= item.cost
    sunlightHistory.value.unshift({
      id: `sl-${Date.now()}`,
      amount: -item.cost,
      reason: `兑换：${item.name}`,
      type: 'spend',
      timestamp: new Date().toISOString(),
    })
    api.points.redeem(itemId).catch(() => {})
    return true
  }

  function addRewardItem(item: Omit<RewardItem, 'id'>) {
    const next: RewardItem = { ...item, id: `ri-${Date.now()}` }
    rewardItems.value.push(next)
    api.points.createReward(item).then((res: any) => {
      if (res?.reward) {
        next.id = String(res.reward.pk_reward_items ?? next.id)
      }
    }).catch(() => {})
    return next
  }

  function toggleRewardItem(id: string) {
    const item = rewardItems.value.find(i => i.id === id)
    if (item) {
      item.active = !item.active
      api.points.updateReward(id, { active: item.active }).catch(() => {})
    }
  }

  function removeRewardItem(id: string) {
    rewardItems.value = rewardItems.value.filter(i => i.id !== id)
    api.points.deleteReward(id).catch(() => {})
  }

  return {
    profile,
    assessment,
    sunlightPoints,
    isOnboarded,
    sunlightHistory,
    rewardItems,
    isLowGrade,
    isHighGrade,
    fetchFromApi,
    setProfile,
    setAssessment,
    completeOnboarding,
    addSunlightPoints,
    redeemItem,
    addRewardItem,
    toggleRewardItem,
    removeRewardItem,
  }
})

const seededTasks: TaskItem[] = [
  { id: 'habit-read', title: '今日指读任务', description: '动笔前用手指着读题，并圈出大题号、单位和符号。', type: 'study_habit', status: 'pending', rewardPoints: 20, icon: '☝️' },
  { id: 'bag-zone', title: '整理书包 3 分区', description: '把作业区、文具区、回执区各归位一次。', type: 'life_skill', status: 'pending', rewardPoints: 15, icon: '🎒' },
  { id: 'schulte', title: '舒尔特方格', description: '完成 90 秒专注小游戏。', type: 'morning_routine', status: 'pending', rewardPoints: 10, icon: '🧠' },
]

const defaultHabit: HabitSOP = {
  id: 'week-3-read-circle',
  title: '读题圈号 SOP',
  weekNumber: 3,
  steps: [
    { order: 1, instruction: '手指跟着题干逐字移动，遇到数字停一下。' },
    { order: 2, instruction: '圈出大题号、单位、运算符号三处关键点。' },
    { order: 3, instruction: '动笔前复述：题目要我求什么？' },
  ],
}

export const useTaskStore = defineStore('task', () => {
  const saved = loadState('cc-task', {
    todayTasks: seededTasks,
    currentWeekHabit: defaultHabit,
    habitHistory: [] as HabitSOP[],
  })
  const todayTasks = ref<TaskItem[]>(saved.todayTasks?.length ? saved.todayTasks : seededTasks)
  const currentWeekHabit = ref<HabitSOP>(saved.currentWeekHabit || defaultHabit)
  const habitHistory = ref<HabitSOP[]>(saved.habitHistory || [])
  const weeklyProgress = computed(() => todayTasks.value.filter(task => task.status === 'completed').length)

  watch(
    () => ({ todayTasks: todayTasks.value, currentWeekHabit: currentWeekHabit.value, habitHistory: habitHistory.value }),
    value => persistState('cc-task', value),
    { deep: true },
  )

  async function fetchFromApi(childId?: string) {
    try {
      const res = await api.tasks.getToday(childId)
      const raw: any[] = res.tasks ?? []
      if (raw.length) todayTasks.value = raw.map(normalizeTask)
    } catch { /* offline */ }
    try {
      const res = await api.habits.getCurrent()
      if (res?.habit) currentWeekHabit.value = normalizeHabit(res.habit)
    } catch { /* offline */ }
    try {
      const res = await api.habits.getHistory()
      const raw: any[] = res.history ?? []
      if (raw.length) habitHistory.value = raw.map(normalizeHabit)
    } catch { /* offline */ }
  }

  function completeTask(id: string) {
    const task = todayTasks.value.find(t => t.id === id)
    if (!task || task.status === 'completed') return 0
    task.status = 'completed'
    api.tasks.complete(id).catch(() => {})
    return task.rewardPoints
  }

  function setTodayTasks(tasks: TaskItem[]) {
    todayTasks.value = tasks
  }

  function resetTodayTasks() {
    todayTasks.value = seededTasks.map(task => ({ ...task, status: 'pending' }))
  }

  function updateCurrentHabit(data: Partial<HabitSOP>) {
    Object.assign(currentWeekHabit.value, data)
    api.habits.updateCurrent({
      title: data.title,
      weekNumber: data.weekNumber,
      steps: currentWeekHabit.value.steps.map(s => ({ instruction: s.instruction, order: s.order })),
    }).catch((e) => console.warn('更新习惯同步失败', e))
  }

  function setHabitSteps(steps: SOPStep[]) {
    currentWeekHabit.value.steps = steps.map((s, i) => ({ ...s, order: i + 1 }))
    syncStepsToBackend()
  }

  function addStepToHabit(instruction: string) {
    currentWeekHabit.value.steps.push({
      order: currentWeekHabit.value.steps.length + 1,
      instruction,
    })
    syncStepsToBackend()
  }

  function removeHabitStep(index: number) {
    currentWeekHabit.value.steps = currentWeekHabit.value.steps
      .filter((_, i) => i !== index)
      .map((s, i) => ({ ...s, order: i + 1 }))
    syncStepsToBackend()
  }

  function syncStepsToBackend() {
    const habitId = currentWeekHabit.value.id
    if (/^\d+$/.test(habitId)) {
      api.habits.updateCurrent({ steps: currentWeekHabit.value.steps.map(s => ({ instruction: s.instruction, order: s.order })) })
        .catch((e) => console.warn('同步步骤失败', e))
    }
  }

  function archiveCurrentHabit() {
    const existing = habitHistory.value.find(h => h.id === currentWeekHabit.value.id)
    if (!existing) habitHistory.value.unshift({ ...currentWeekHabit.value })
  }

  function createNewHabit(title: string) {
    archiveCurrentHabit()
    const nextWeek = currentWeekHabit.value.weekNumber + 1
    const next: HabitSOP = {
      id: `habit-${Date.now()}`,
      title,
      weekNumber: nextWeek,
      steps: [],
    }
    currentWeekHabit.value = next
    api.habits.create({ title, weekNumber: nextWeek }).then((res: any) => {
      if (res?.habit?.pk_habit_sops) {
        next.id = String(res.habit.pk_habit_sops)
      }
    }).catch((e) => console.warn('创建习惯同步失败', e))
    return next
  }

  async function loadHabitFromHistory(id: string) {
    const local = habitHistory.value.find(h => h.id === id)
    if (/^\d+$/.test(id)) {
      try {
        const res = await api.habits.getDetail(id)
        if (res?.habit) {
          const habit = normalizeHabit(res.habit)
          currentWeekHabit.value = habit
          const existing = habitHistory.value.find(h => h.id === id)
          if (existing) Object.assign(existing, habit)
          return
        }
      } catch { /* fallback to local */ }
    }
    if (local) currentWeekHabit.value = { ...local }
  }

  return {
    todayTasks,
    currentWeekHabit,
    habitHistory,
    weeklyProgress,
    fetchFromApi,
    completeTask,
    setTodayTasks,
    resetTodayTasks,
    updateCurrentHabit,
    setHabitSteps,
    addStepToHabit,
    removeHabitStep,
    archiveCurrentHabit,
    createNewHabit,
    loadHabitFromHistory,
  }
})

export const useMistakeStore = defineStore('mistake', () => {
  const saved = loadState('cc-mistake', {
    records: [] as MistakeRecord[],
  })
  const records = ref<MistakeRecord[]>(saved.records)

  watch(() => ({ records: records.value }), value => persistState('cc-mistake', value), { deep: true })

  function addRecord(record: Omit<MistakeRecord, 'id' | 'createdAt'>) {
    const next: MistakeRecord = {
      ...record,
      id: `m-${Date.now()}`,
      createdAt: new Date().toISOString(),
    }
    records.value.unshift(next)
    const { recordDataPoint } = useGrowthStore()
    recordDataPoint({ mistakeRate: records.value.length / Math.max(records.value.length + 10, 1) })
    api.mistakes.create({ subject: record.subject, imageUrl: record.imageUrl, knowledgePoint: record.subjectTag }).then((res: any) => {
      if (res?.record?.pk_mistake_records) next.id = String(res.record.pk_mistake_records)
    }).catch(() => {})
    return next
  }

  function removeRecord(id: string) {
    records.value = records.value.filter(r => r.id !== id)
    api.mistakes.delete(id).catch(() => {})
  }

  async function fetchFromApi(childId?: string) {
    try {
      const res = await api.mistakes.list(childId)
      const raw: any[] = res.records ?? []
      records.value = raw.map(normalizeMistake)
    } catch { /* offline */ }
  }

  return { records, addRecord, removeRecord, fetchFromApi }
})

const seededBadges: BadgeItem[] = [
  { id: 'read-7', name: '指读先锋', description: '连续 7 天完成指读圈号', icon: '☝️', color: '#fbe270', unlocked: false, requirement: '连续 7 天完成主线习惯' },
  { id: 'space-7', name: '镜面空间', description: '连续整理书桌 7 天', icon: '🪞', color: '#80dc67', unlocked: false, requirement: '连续整理书桌 7 天' },
  { id: 'detective', name: '复盘小侦探', description: '完成 10 次黄金一问', icon: '🔎', color: '#92e3ff', unlocked: false, requirement: '累计记录 10 道错题诊断' },
  { id: 'captain', name: '时间船长', description: '完成 5 次番茄钟复盘', icon: '⏱️', color: '#ffd9c7', unlocked: false, requirement: '完成 5 次番茄钟' },
]

export const useBadgeStore = defineStore('badge', () => {
  const saved = loadState('cc-badge', { badges: seededBadges, covenants: [] as FamilyCovenant[], confettiActive: false })
  const badges = ref<BadgeItem[]>(saved.badges?.length ? saved.badges : seededBadges)
  const covenants = ref<FamilyCovenant[]>(saved.covenants)
  const confettiActive = ref(false)
  const unlockedCount = computed(() => badges.value.filter(b => b.unlocked).length)

  watch(() => ({ badges: badges.value, covenants: covenants.value }), value => persistState('cc-badge', value), { deep: true })

  async function fetchFromApi() {
    try {
      const res = await api.badges.list()
      const raw: any[] = res.badges ?? []
      if (raw.length) badges.value = raw.map(normalizeBadge)
    } catch { /* offline */ }
    try {
      const res = await api.covenants.list()
      const raw: any[] = res.covenants ?? []
      covenants.value = raw.map(normalizeCovenant)
    } catch { /* offline */ }
  }

  function unlockBadge(id: string) {
    const badge = badges.value.find(b => b.id === id)
    if (badge && !badge.unlocked) {
      badge.unlocked = true
      badge.unlockedAt = new Date().toISOString()
      confettiActive.value = true
      setTimeout(() => { confettiActive.value = false }, 3000)
      api.badges.unlock(id).catch(() => {})
    }
  }

  function addCovenant(covenant: Omit<FamilyCovenant, 'id' | 'createdAt' | 'status'>) {
    const next: FamilyCovenant = { ...covenant, id: `c-${Date.now()}`, createdAt: new Date().toISOString(), status: 'active' }
    covenants.value.unshift(next)
    api.covenants.create({ goal: covenant.goal, reward: covenant.reward }).then((res: any) => {
      if (res?.covenant?.pk_covenants) next.id = String(res.covenant.pk_covenants)
    }).catch(() => {})
    return next
  }

  return { badges, covenants, confettiActive, unlockedCount, fetchFromApi, unlockBadge, addCovenant }
})

export const useGrowthStore = defineStore('growth', () => {
  const saved = loadState('cc-growth', {
    trendData: [] as GrowthDataPoint[],
    alerts: [] as DiagnosticAlert[],
    itemLossRecords: [] as ItemLossRecord[],
    storageRecords: [] as ItemStorageRecord[],
  })
  const trendData = ref<GrowthDataPoint[]>(saved.trendData)
  const alerts = ref<DiagnosticAlert[]>(saved.alerts)
  const itemLossRecords = ref<ItemLossRecord[]>(saved.itemLossRecords)
  const storageRecords = ref<ItemStorageRecord[]>(saved.storageRecords || [])
  const totalLossCost = computed(() => itemLossRecords.value.reduce((sum, item) => sum + item.estimatedCost * item.frequency, 0))
  const highFrequencyItems = computed(() => itemLossRecords.value.filter(item => item.frequency >= 3))

  watch(() => ({ trendData: trendData.value, alerts: alerts.value, itemLossRecords: itemLossRecords.value, storageRecords: storageRecords.value }), value => persistState('cc-growth', value), { deep: true })

  async function fetchFromApi(childId?: string) {
    try {
      const res = await api.growth.getTrend(childId)
      const raw: any[] = res.trend ?? []
      if (raw.length) trendData.value = raw.map(normalizeGrowthPoint)
    } catch { /* offline */ }
    try {
      const res = await api.growth.getAlerts(childId)
      const raw: any[] = res.alerts ?? []
      alerts.value = raw.map(normalizeAlert)
    } catch { /* offline */ }
    try {
      const res = await api.items.getLossList(childId)
      const raw: any[] = res.records ?? []
      itemLossRecords.value = raw.map(normalizeItemLoss)
    } catch { /* offline */ }
    try {
      const res = await api.items.getStorageList(childId)
      const raw: any[] = res.records ?? []
      storageRecords.value = raw.map(normalizeItemStorage)
    } catch { /* offline */ }
  }

  function recordDataPoint(override?: Partial<GrowthDataPoint>) {
    const totalLoss = itemLossRecords.value.reduce((s, i) => s + i.frequency, 0)
    const point: GrowthDataPoint = {
      date: new Date().toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
      mistakeRate: override?.mistakeRate ?? 0,
      itemLossRate: totalLoss,
      taskCompletionRate: override?.taskCompletionRate ?? 0,
      ...override,
    }
    const exists = trendData.value.find(d => d.date === point.date)
    if (!exists) trendData.value.push(point)
  }

  function addItemLossRecord(record: Omit<ItemLossRecord, 'id' | 'lostDate' | 'frequency'> & { frequency?: number }) {
    const existing = itemLossRecords.value.find(item => item.itemName === record.itemName)
    if (existing) {
      existing.frequency += 1
      existing.lostDate = new Date().toISOString()
      existing.lostLocation = record.lostLocation
      recordDataPoint()
      return existing
    }
    const next: ItemLossRecord = { ...record, id: `i-${Date.now()}`, lostDate: new Date().toISOString(), frequency: record.frequency || 1 }
    itemLossRecords.value.unshift(next)
    recordDataPoint()
    api.items.reportLoss({ itemName: record.itemName, lostLocation: record.lostLocation, estimatedCost: record.estimatedCost }).then((res: any) => {
      if (res?.record?.pk_item_loss_records) next.id = String(res.record.pk_item_loss_records)
    }).catch(() => {})
    return next
  }

  function addStorageRecord(record: Omit<ItemStorageRecord, 'id' | 'storageDate'>) {
    const next: ItemStorageRecord = {
      ...record,
      id: `sr-${Date.now()}`,
      storageDate: new Date().toISOString(),
    }
    storageRecords.value.unshift(next)
    api.items.addStorage(record).then((res: any) => {
      if (res?.record?.pk_item_storage_records) next.id = String(res.record.pk_item_storage_records)
    }).catch(() => {})
    return next
  }

  return { trendData, alerts, itemLossRecords, storageRecords, totalLossCost, highFrequencyItems, fetchFromApi, addItemLossRecord, addStorageRecord, recordDataPoint }
})

const defaultLlmConfig: LlmConfig = {
  endpoint: 'https://api.openai.com/v1',
  apiKey: '',
  model: 'gpt-4o-mini',
  mistakePrompt: '你是一位小学教育专家。分析这张错题图片，判断：\n1. 错误类型：粗心（看错符号/抄错数/漏题）还是知识漏洞（概念不清/公式记错）\n2. 涉及的知识点\n3. 改进建议（一句话，适合 1-3 年级孩子理解）\n返回 JSON 格式：{ "type": "careless|knowledge", "detail": "...", "knowledgePoint": "...", "suggestion": "..." }',
  assessmentPrompt: '基于以下孩子的成长数据，生成阶段性评估报告：\n- 错题总数：{mistakeCount}\n- 任务完成率：{completionRate}%\n- 物品丢失次数：{itemLossCount}\n- 当前习惯：{habitTitle}\n要求指出进步方面、需要关注的方面、以及给家长的具体建议。\n返回 JSON 格式：{ "progress": "...", "concerns": "...", "suggestions": "..." }',
  assessmentCron: 'weekly',
  enabled: false,
}

// ── 家长端：当前选中的孩子 ───────────────────────────────────────────────

export const useChildSelectStore = defineStore('childSelect', () => {
  type Child = ReturnType<typeof normalizeChild>

  const children = ref<Child[]>([])
  const selectedChildId = ref<string | null>(
    localStorage.getItem('cc-selected-child') ?? null,
  )
  const selectedChild = computed(
    () => children.value.find(c => c.id === selectedChildId.value) ?? children.value[0] ?? null,
  )

  watch(selectedChildId, id => {
    if (id) localStorage.setItem('cc-selected-child', id)
    else localStorage.removeItem('cc-selected-child')
  })

  async function loadChildren() {
    try {
      const res = await api.children.list()
      children.value = Array.isArray(res) ? res.map(normalizeChild) : []
      if (children.value.length && !children.value.find(c => c.id === selectedChildId.value)) {
        selectedChildId.value = children.value[0].id
      }
    } catch { /* offline */ }
  }

  function selectChild(id: string) {
    selectedChildId.value = id
  }

  return { children, selectedChildId, selectedChild, loadChildren, selectChild }
})

export const useParentStore = defineStore('parent', () => {  const saved = loadState('cc-parent', {
    settings: { difficultyLevel: 2, dailyReminder: true, achievementNotification: true, weeklyReport: true, schoolSync: false } as ParentSettings,
    discussionPosts: [] as DiscussionPost[],
    articles: [] as ArticleResource[],
    parentTaskTemplates: [] as TaskItem[],
    llmConfig: defaultLlmConfig,
  })
  const settings = ref<ParentSettings>(saved.settings)
  const discussionPosts = ref<DiscussionPost[]>(saved.discussionPosts)
  const articles = ref<ArticleResource[]>(saved.articles)
  const parentTaskTemplates = ref<TaskItem[]>(saved.parentTaskTemplates || [])
  const llmConfig = ref<LlmConfig>(saved.llmConfig || defaultLlmConfig)

  watch(() => ({ settings: settings.value, discussionPosts: discussionPosts.value, articles: articles.value, parentTaskTemplates: parentTaskTemplates.value, llmConfig: llmConfig.value }), value => persistState('cc-parent', value), { deep: true })

  async function fetchFromApi() {
    try {
      const res = await api.parent.getSettings()
      const raw = res.settings ?? res
      settings.value = normalizeParentSettings(raw)
    } catch { /* offline */ }
    try {
      const res = await api.llm.getConfig()
      const raw = res.config ?? res
      if (raw?.endpoint) llmConfig.value = normalizeLlmConfig(raw)
    } catch { /* offline */ }
    try {
      const res = await api.community.getPosts(1)
      const raw: any[] = res.posts ?? []
      discussionPosts.value = raw.map(normalizePost)
    } catch { /* offline */ }
  }

  function updateSettings(s: Partial<ParentSettings>) {
    Object.assign(settings.value, s)
    api.parent.updateSettings(s).catch(() => {})
  }

  function updateLlmConfig(c: Partial<LlmConfig>) {
    Object.assign(llmConfig.value, c)
    api.llm.updateConfig(c).catch(() => {})
  }

  function createPost(data: { title: string; content: string; tags: string[] }) {
    const localPost: DiscussionPost = { id: `post-${Date.now()}`, author: '匿名家长', replyCount: 0, hasExpertAnswer: false, createdAt: new Date().toISOString(), ...data }
    discussionPosts.value.unshift(localPost)
    api.community.createPost(data).then((res: any) => {
      if (res?.post) {
        const idx = discussionPosts.value.findIndex(p => p.id === localPost.id)
        if (idx !== -1) discussionPosts.value[idx] = normalizePost(res.post)
      }
    }).catch(() => {})
  }

  function addTaskTemplate(task: Omit<TaskItem, 'id'>) {
    const next: TaskItem = { ...task, id: `pt-${Date.now()}` }
    parentTaskTemplates.value.unshift(next)
    return next
  }

  function updateTaskTemplate(id: string, updates: Partial<TaskItem>) {
    const template = parentTaskTemplates.value.find(t => t.id === id)
    if (template) Object.assign(template, updates)
  }

  function deleteTaskTemplate(id: string) {
    parentTaskTemplates.value = parentTaskTemplates.value.filter(t => t.id !== id)
  }

  return { settings, discussionPosts, articles, parentTaskTemplates, llmConfig, fetchFromApi, updateSettings, updateLlmConfig, createPost, addTaskTemplate, updateTaskTemplate, deleteTaskTemplate }
})
