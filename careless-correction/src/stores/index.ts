import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type {
  ArticleResource,
  BadgeItem,
  DiagnosticAlert,
  ExecutiveFunctionAssessment,
  GrowthDataPoint,
  HabitAssignment,
  HabitSOP,
  ItemLossRecord,
  ItemStorageRecord,
  LlmConfig,
  MistakeRecord,
  ParentSettings,
  RewardItem,
  SunlightRecord,
  TaskItem,
  UserProfile,
} from '../types'
import {
  api,
  normalizeAlert,
  normalizeArticle,
  normalizeBadge,
  normalizeChild,
  normalizeGrowthPoint,
  normalizeHabit,
  normalizeItemLoss,
  normalizeItemStorage,
  normalizeLlmConfig,
  normalizeMistake,
  normalizeParentSettings,
  normalizeRewardItem,
  normalizeSunlightRecord,
  normalizeTask,
  normalizeUser,
} from '../utils/api'


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

export interface AppleRecord {
  id: string
  amount: number
  reason: string
  type: 'grow' | 'redeem'
  timestamp: string
}

export interface PendingSunlightItem {
  id: number
  amount: number
  reason: string
  createdAt: string
}

const SUNLIGHT_PER_APPLE = 100

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile>({ ...defaultProfile })
  const assessment = ref<ExecutiveFunctionAssessment>({ ...defaultAssessment })
  const sunlightPoints = ref(0)
  const isOnboarded = ref(false)
  const sunlightHistory = ref<SunlightRecord[]>([])
  const rewardItems = ref<RewardItem[]>([...defaultRewardItems])
  const apples = ref(0)
  const appleHistory = ref<AppleRecord[]>([])

  // ── 待收集阳光（家长审批通过后生成，孩子点击收集后正式变为阳光值）──
  const pendingSunlight = ref<PendingSunlightItem[]>([])

  const isLowGrade = computed(() => profile.value.grade <= 2)
  const isHighGrade = computed(() => profile.value.grade >= 5)

  async function fetchFromApi(childId?: string) {
    try {
      const user = await api.auth.session()
      const u = normalizeUser(user)
      profile.value = u
      sunlightPoints.value = (user as any).sunlight_points ?? sunlightPoints.value
      apples.value = (user as any).apples ?? apples.value
    } catch { /* offline */ }
    try {
      const { balance } = await api.points.getBalance(childId)
      sunlightPoints.value = balance
    } catch { /* offline */ }
    try {
      const res = await api.points.getHistory(childId)
      const raw: any[] = res.history ?? []
      sunlightHistory.value = raw.map(normalizeSunlightRecord)
    } catch { /* offline */ }
    try {
      const res = await api.points.getRewards(childId)
      const raw: any[] = res.rewards ?? []
      rewardItems.value = raw.map(normalizeRewardItem)
    } catch { /* offline */ }
    // 加载苹果数据
    try {
      const res = await api.points.getApples(childId)
      apples.value = res.apples
      sunlightPoints.value = res.sunlightPoints
      const rawHistory: any[] = res.history ?? []
      appleHistory.value = rawHistory.map((h: any) => ({
        id: String(h.pk_apple_history ?? h.id ?? ''),
        amount: h.amount ?? 0,
        reason: h.reason ?? '',
        type: h.type ?? 'grow',
        timestamp: h.created_at ?? h.timestamp ?? new Date().toISOString(),
      }))
    } catch { /* offline */ }
    // 加载待收集阳光
    try {
      const res = await api.points.getPendingSunlight(childId)
      pendingSunlight.value = (res.pending ?? []).map((p: any) => ({
        id: p.id,
        amount: p.amount,
        reason: p.reason ?? '',
        createdAt: p.createdAt ?? p.created_at ?? new Date().toISOString(),
      }))
    } catch { /* offline */ }
  }

  async function fetchPendingSunlight() {
    try {
      const res = await api.points.getPendingSunlight()
      pendingSunlight.value = (res.pending ?? []).map((p: any) => ({
        id: p.id,
        amount: p.amount,
        reason: p.reason ?? '',
        createdAt: p.createdAt ?? p.created_at ?? new Date().toISOString(),
      }))
    } catch { /* offline */ }
  }

  async function collectSunlight(sunlightId: number): Promise<boolean> {
    const item = pendingSunlight.value.find(p => p.id === sunlightId)
    if (!item) return false
    // 乐观更新：先移除待收集项，增加阳光值
    pendingSunlight.value = pendingSunlight.value.filter(p => p.id !== sunlightId)
    sunlightPoints.value += item.amount
    try {
      const res = await api.points.collectSunlight(sunlightId)
      if (res?.balance !== undefined) sunlightPoints.value = res.balance
      return true
    } catch {
      // 回滚
      sunlightPoints.value -= item.amount
      pendingSunlight.value.unshift(item)
      return false
    }
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

  const sunlightPerApple = SUNLIGHT_PER_APPLE

  const canGrowApple = computed(() => sunlightPoints.value >= SUNLIGHT_PER_APPLE)
  const appleYuanValue = computed(() => apples.value)

  function growApple() {
    if (sunlightPoints.value < SUNLIGHT_PER_APPLE) return false
    // 乐观更新 UI
    sunlightPoints.value -= SUNLIGHT_PER_APPLE
    apples.value += 1
    appleHistory.value.unshift({
      id: `ap-${Date.now()}`,
      amount: 1,
      reason: '阳光兑换苹果',
      type: 'grow',
      timestamp: new Date().toISOString(),
    })
    // 调用后端持久化
    api.points.growApple().then(res => {
      // 用后端返回的真实数据同步
      if (res?.apples !== undefined) apples.value = res.apples
      if (res?.sunlightPoints !== undefined) sunlightPoints.value = res.sunlightPoints
    }).catch(() => {
      // 失败时回滚
      sunlightPoints.value += SUNLIGHT_PER_APPLE
      apples.value -= 1
      appleHistory.value.shift()
    })
    return true
  }

  function redeemApple(count: number, reason: string) {
    if (count <= 0 || apples.value < count) return false
    // 乐观更新 UI
    apples.value -= count
    appleHistory.value.unshift({
      id: `ap-${Date.now()}`,
      amount: -count,
      reason: reason || `兑换 ${count} 元`,
      type: 'redeem',
      timestamp: new Date().toISOString(),
    })
    // 调用后端持久化
    api.points.redeemApple(count, reason).then(res => {
      if (res?.apples !== undefined) apples.value = res.apples
    }).catch(() => {
      // 失败时回滚
      apples.value += count
      appleHistory.value.shift()
    })
    return true
  }

  return {
    profile,
    assessment,
    sunlightPoints,
    isOnboarded,
    sunlightHistory,
    rewardItems,
    apples,
    appleHistory,
    sunlightPerApple,
    canGrowApple,
    appleYuanValue,
    isLowGrade,
    isHighGrade,
    fetchFromApi,
    setProfile,
    setAssessment,
    completeOnboarding,
    redeemItem,
    addRewardItem,
    toggleRewardItem,
    removeRewardItem,
    growApple,
    redeemApple,
    pendingSunlight,
    fetchPendingSunlight,
    collectSunlight,
  }
})

const seededTasks: TaskItem[] = [
  { id: 'habit-read', title: '今日指读任务', description: '动笔前用手指着读题，并圈出大题号、单位和符号。', type: 'study_habit', status: 'pending', rewardPoints: 20, icon: '☝️' },
  { id: 'bag-zone', title: '整理书包 3 分区', description: '把作业区、文具区、回执区各归位一次。', type: 'life_skill', status: 'pending', rewardPoints: 15, icon: '🎒' },
  { id: 'schulte', title: '舒尔特方格', description: '完成 90 秒专注小游戏。', type: 'morning_routine', status: 'pending', rewardPoints: 10, icon: '🧠' },
]

export const useTaskStore = defineStore('task', () => {
  const todayTasks = ref<TaskItem[]>([])
  const habits = ref<HabitSOP[]>([])
  // 习惯布置记录（与 habits 同源：来自后端习惯库，额外携带描述/图标/周数等展示字段）
  const habitAssignments = ref<HabitAssignment[]>([])
  const weeklyProgress = computed(() => todayTasks.value.filter(task => task.status === 'completed').length)
  const activeHabits = computed(() => habitAssignments.value.filter(h => h.active))

  // ── 习惯布置（HabitAssignPage）─────────────────────────────────────────
  // 后端习惯模型不包含描述/图标/周数等展示字段，用 localStorage 持久化以便跨刷新保留
  const HABIT_ASSIGN_KEY = 'cc-habit-assignments'

  function loadLocalAssignments(): HabitAssignment[] {
    try {
      const raw = localStorage.getItem(HABIT_ASSIGN_KEY)
      return raw ? JSON.parse(raw) : []
    } catch { return [] }
  }

  function saveLocalAssignments() {
    try { localStorage.setItem(HABIT_ASSIGN_KEY, JSON.stringify(habitAssignments.value)) } catch { /* ignore */ }
  }

  async function fetchFromApi(childId?: string) {
    try {
      const res = await api.tasks.getToday(childId)
      const raw: any[] = res.tasks ?? []
      todayTasks.value = raw.map(normalizeTask)
    } catch { /* offline */ }
    try {
      const res = await api.habits.getAll(childId)
      const raw: any[] = res.habits ?? []
      habits.value = raw.map(normalizeHabit)
    } catch { /* offline */ }
  }

  function completeTask(id: string) {
    const task = todayTasks.value.find(t => t.id === id)
    if (!task || task.status === 'completed') return 0
    task.status = 'completed'
    // 后端只标记任务完成，不再自动加阳光值
    // 阳光值由家长审批打卡 (checkins/approve) 后统一发放
    api.tasks.complete(id).catch(() => {})
    return task.rewardPoints
  }

  function setTodayTasks(tasks: TaskItem[]) {
    todayTasks.value = tasks
  }

  function resetTodayTasks() {
    todayTasks.value = seededTasks.map(task => ({ ...task, status: 'pending' }))
  }

  function updateHabit(id: string, data: Partial<HabitSOP>) {
    const habit = habits.value.find(h => h.id === id)
    if (!habit) return
    Object.assign(habit, data)
    if (/^\d+$/.test(id)) {
      api.habits.update({
        id,
        title: data.title,
        rewardPoints: data.rewardPoints,
        steps: habit.steps.map(s => ({ instruction: s.instruction, order: s.order })),
      }).catch((e) => console.warn('更新习惯同步失败', e))
    }
  }

  function addStepToHabit(habitId: string, instruction: string) {
    const habit = habits.value.find(h => h.id === habitId)
    if (!habit) return
    habit.steps.push({ order: habit.steps.length + 1, instruction })
    syncStepsToBackend(habitId)
  }

  function removeHabitStep(habitId: string, index: number) {
    const habit = habits.value.find(h => h.id === habitId)
    if (!habit) return
    habit.steps = habit.steps.filter((_, i) => i !== index).map((s, i) => ({ ...s, order: i + 1 }))
    syncStepsToBackend(habitId)
  }

  function syncStepsToBackend(habitId: string) {
    const habit = habits.value.find(h => h.id === habitId)
    if (!habit || !/^\d+$/.test(habitId)) return
    api.habits.update({ id: habitId, steps: habit.steps.map(s => ({ instruction: s.instruction, order: s.order })) })
      .catch((e) => console.warn('同步步骤失败', e))
  }

  function createNewHabit(title: string, rewardPoints = 5) {
    const next: HabitSOP = {
      id: `habit-${Date.now()}`,
      title,
      rewardPoints,
      steps: [],
    }
    habits.value.push(next)
    api.habits.create({ title, rewardPoints }).then((res: any) => {
      if (res?.habit?.pk_habit_sops) {
        next.id = String(res.habit.pk_habit_sops)
      }
    }).catch((e) => console.warn('创建习惯同步失败', e))
    return next
  }

  function deleteHabit(id: string) {
    // 软删除：从活跃列表中移除，但保留在 inventory 中
    const habit = habits.value.find(h => h.id === id)
    if (habit) habit.active = false
    if (/^\d+$/.test(id)) {
      api.habits.delete(id).catch(() => { /* offline */ })
    }
  }

  // 永久删除习惯
  function permanentDeleteHabit(id: string) {
    habits.value = habits.value.filter(h => h.id !== id)
    if (/^\d+$/.test(id)) {
      api.habits.deletePermanent(id).catch(() => { /* offline */ })
    }
  }

  // 重新启用习惯
  function restoreHabit(id: string) {
    const habit = habits.value.find(h => h.id === id)
    if (habit) {
      habit.active = true
      if (/^\d+$/.test(id)) {
        api.habits.update({ ...habit, id }).catch(() => {})
      }
    }
  }

  // ── 习惯布置（HabitAssignPage）─────────────────────────────────────────

  // 从后端加载已布置习惯，并与本地记录合并（本地优先保留描述/图标/周数等展示字段）
  async function fetchHabits(childId?: string) {
    const local = loadLocalAssignments()
    try {
      const res = await api.habits.getAll(childId)
      const raw: any[] = res.habits ?? []
      const merged: HabitAssignment[] = raw.map((h: any) => {
        const id = String(h.pk_habit_sops ?? h.id ?? '')
        const loc = local.find(x => x.id === id)
        return {
          id,
          childId: loc?.childId ?? '',
          parentId: loc?.parentId ?? '',
          title: h.title ?? loc?.title ?? '',
          description: loc?.description ?? (h as any).description ?? '',
          icon: loc?.icon ?? (h as any).icon ?? '✅',
          rewardPoints: h.reward_points ?? h.rewardPoints ?? loc?.rewardPoints ?? 5,
          weekNumber: loc?.weekNumber ?? (h as any).week_number ?? (h as any).weekNumber ?? 1,
          steps: (h.steps ?? loc?.steps ?? []).map((s: any) => ({
            order: s.order,
            instruction: s.instruction,
            imageUrl: s.image_url ?? s.imageUrl,
            gifUrl: s.gif_url ?? s.gifUrl,
          })),
          assignedAt: loc?.assignedAt ?? h.created_at ?? h.createdAt ?? new Date().toISOString(),
          active: h.active ?? loc?.active ?? true,
        }
      })
      // 本地有但后端未返回的记录（如离线创建尚未同步）也保留
      const backendIds = new Set(merged.map(x => x.id))
      for (const l of local) {
        if (!backendIds.has(l.id)) merged.push(l)
      }
      habitAssignments.value = merged
      saveLocalAssignments()
    } catch { /* offline：保留本地数据 */ }
  }

  // 布置新习惯：乐观更新本地（并持久化）+ 同步后端（title/rewardPoints/steps 持久化）
  function addHabitAssignment(data: Omit<HabitAssignment, 'id' | 'assignedAt'>) {
    const habit: HabitAssignment = { ...data, id: `ha-${Date.now()}`, assignedAt: new Date().toISOString() }
    habitAssignments.value.unshift(habit)
    saveLocalAssignments()
    const sop: HabitSOP = {
      id: habit.id,
      title: habit.title,
      steps: habit.steps,
      rewardPoints: habit.rewardPoints,
      active: true,
      createdAt: habit.assignedAt,
    }
    habits.value.unshift(sop)
    api.habits.create({
      title: habit.title,
      rewardPoints: habit.rewardPoints,
      steps: habit.steps.map(s => ({ instruction: s.instruction, order: s.order })),
    }).then((res: any) => {
      if (res?.habit?.pk_habit_sops) {
        const backendId = String(res.habit.pk_habit_sops)
        habit.id = backendId
        sop.id = backendId
        saveLocalAssignments()
      }
    }).catch(() => { /* offline：保持本地记录 */ })
    return habit
  }

  // 停用习惯（软删除，复用 deleteHabit 同步后端与 habits 列表）
  function deactivateHabit(id: string) {
    const habit = habitAssignments.value.find(h => h.id === id)
    if (habit) {
      habit.active = false
      saveLocalAssignments()
    }
    deleteHabit(id)
  }

  return {
    todayTasks,
    habits,
    habitAssignments,
    weeklyProgress,
    activeHabits,
    fetchFromApi,
    fetchHabits,
    addHabitAssignment,
    deactivateHabit,
    completeTask,
    setTodayTasks,
    resetTodayTasks,
    updateHabit,
    addStepToHabit,
    removeHabitStep,
    createNewHabit,
    deleteHabit,
    permanentDeleteHabit,
    restoreHabit,
  }
})

export const useMistakeStore = defineStore('mistake', () => {
  const records = ref<MistakeRecord[]>([])

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

  const dueReviews = computed(() =>
    records.value.filter(r => !r.resolved && r.nextReviewAt && new Date(r.nextReviewAt) <= new Date()),
  )

  async function reviewRecord(id: string, canResolve: boolean, confidenceLevel?: number) {
    const record = records.value.find(r => r.id === id)
    if (!record) return
    try {
      const res = await api.mistakes.review(id, { canResolve, confidenceLevel })
      if (res?.record) {
        const updated = normalizeMistake(res.record)
        const idx = records.value.findIndex(r => r.id === id)
        if (idx !== -1) records.value[idx] = updated
      }
    } catch { /* offline */ }
  }

  return { records, addRecord, removeRecord, fetchFromApi, dueReviews, reviewRecord }
})

export interface BadgeItemWithProgress extends BadgeItem {
  requirementType?: string
  requirementValue?: number
  progress?: number
}

export const useBadgeStore = defineStore('badge', () => {
  const badges = ref<BadgeItemWithProgress[]>([])
  const confettiActive = ref(false)
  const unlockedCount = computed(() => badges.value.filter(b => b.unlocked).length)
  const lastNewlyUnlocked = ref<BadgeItemWithProgress[]>([])

  async function fetchFromApi(childId?: string) {
    try {
      const res = await api.badges.list(childId)
      const raw: any[] = res.badges ?? []
      badges.value = raw.map(b => {
        const base = normalizeBadge(b)
        return {
          ...base,
          requirementType: b.requirement_type ?? b.requirementType,
          requirementValue: b.requirement_value ?? b.requirementValue,
          progress: b.progress ?? 0,
        }
      })
    } catch { /* offline */ }
  }

  /** Check and auto-unlock badges. Call after key actions. */
  async function checkAndUnlock(childId?: string) {
    try {
      const res = await api.badges.checkUnlocks(childId)
      if (res.newly_unlocked && res.newly_unlocked.length > 0) {
        // Refresh badge list to reflect the changes
        await fetchFromApi(childId)
        lastNewlyUnlocked.value = res.newly_unlocked.map(b => ({
          id: String(b.pk_badges ?? ''),
          name: b.name ?? '',
          description: '',
          icon: b.icon ?? '🏅',
          color: '#fbe270',
          unlocked: true,
          unlockedAt: new Date().toISOString(),
          requirement: '',
          rewardPoints: b.reward_points,
        }))
        // Trigger confetti
        confettiActive.value = true
        setTimeout(() => { confettiActive.value = false }, 3000)
      }
      return res.newly_unlocked ?? []
    } catch {
      return []
    }
  }

  function unlockBadge(id: string, childId?: string) {
    const badge = badges.value.find(b => b.id === id)
    if (badge && !badge.unlocked) {
      badge.unlocked = true
      badge.unlockedAt = new Date().toISOString()
      confettiActive.value = true
      setTimeout(() => { confettiActive.value = false }, 3000)
      api.badges.unlock(id, childId).catch(() => {})
    }
  }

  return { badges, confettiActive, unlockedCount, lastNewlyUnlocked, fetchFromApi, checkAndUnlock, unlockBadge }
})

export const useGrowthStore = defineStore('growth', () => {
  const trendData = ref<GrowthDataPoint[]>([])
  const alerts = ref<DiagnosticAlert[]>([])
  const itemLossRecords = ref<ItemLossRecord[]>([])
  const storageRecords = ref<ItemStorageRecord[]>([])
  const totalLossCost = computed(() => itemLossRecords.value.reduce((sum, item) => sum + item.estimatedCost * item.frequency, 0))
  const highFrequencyItems = computed(() => itemLossRecords.value.filter(item => item.frequency >= 3))

  async function fetchFromApi(childId?: string) {
    try {
      const res = await api.growth.getTrend(childId)
      const raw: any[] = res.trend ?? []
      trendData.value = raw.map(normalizeGrowthPoint)
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
      api.items.reportLoss({ itemName: record.itemName, lostLocation: record.lostLocation, estimatedCost: record.estimatedCost }).then((res: any) => {
        if (res?.record) Object.assign(existing, normalizeItemLoss(res.record))
      }).catch(() => {})
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

// ── 家长端：当前选中的孩子 ───────────────────────────────────────────────

export const useChildSelectStore = defineStore('childSelect', () => {
  type Child = ReturnType<typeof normalizeChild>

  const children = ref<Child[]>([])
  const selectedChildId = ref<string | null>(null)
  const selectedChild = computed(
    () => children.value.find(c => c.id === selectedChildId.value) ?? children.value[0] ?? null,
  )

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

export const useParentStore = defineStore('parent', () => {
  const settings = ref<ParentSettings>({ dailyReminder: true, achievementNotification: true, weeklyReport: true, schoolSync: false })
  const articles = ref<ArticleResource[]>([])
  const parentTaskTemplates = ref<TaskItem[]>([])
  const llmConfig = ref<LlmConfig>({ endpoint: 'https://api.openai.com/v1', apiKey: '', model: 'gpt-4o-mini', mistakePrompt: '', assessmentPrompt: '', assessmentCron: 'weekly', enabled: false })

  async function fetchFromApi(childId?: string) {
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
      const res = await api.articles.list()
      const raw: any[] = res.articles ?? []
      articles.value = raw.map(normalizeArticle)
    } catch { /* offline */ }
    try {
      const res = await api.tasks.getToday(childId)
      const raw: any[] = res.tasks ?? []
      parentTaskTemplates.value = raw.map(t => {
        const task = normalizeTask(t)
        const existing = parentTaskTemplates.value.find(e => e.id === task.id)
        if (existing?.subTasks?.length && !task.subTasks?.length) {
          task.subTasks = existing.subTasks
        }
        return task
      })
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
    // 软删除：从活跃列表中移除，但保留在 inventory 中
    const template = parentTaskTemplates.value.find(t => t.id === id)
    if (template) template.active = false
  }

  // 永久删除任务
  function permanentDeleteTaskTemplate(id: string) {
    parentTaskTemplates.value = parentTaskTemplates.value.filter(t => t.id !== id)
    if (/^\d+$/.test(id)) {
      api.tasks.deletePermanent(id).catch(() => { /* offline */ })
    }
  }

  // 重新启用任务
  function restoreTaskTemplate(id: string) {
    const template = parentTaskTemplates.value.find(t => t.id === id)
    if (template) {
      template.active = true
      if (/^\d+$/.test(id)) {
        api.tasks.update(id, { active: true }).catch(() => {})
      }
    }
  }

  // 从清单中加载所有任务（包括 inactive）
  const allTaskInventory = computed(() =>
    parentTaskTemplates.value.slice().sort((a, b) => {
      // active 的排前面，然后按创建时间倒序
      if (a.active !== b.active) return a.active ? -1 : 1
      return 0
    })
  )

  return { settings, articles, parentTaskTemplates, llmConfig, fetchFromApi, updateSettings, updateLlmConfig, addTaskTemplate, updateTaskTemplate, deleteTaskTemplate, permanentDeleteTaskTemplate, restoreTaskTemplate, allTaskInventory }
})
