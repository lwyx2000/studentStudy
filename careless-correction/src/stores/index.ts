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
  HabitAssignment,
  ItemLossRecord,
  MistakeCategory,
  MistakeRecord,
  ParentSettings,
  PomodoroSession,
  TaskItem,
  UserProfile,
  QuestionItem,
  QuestionBankImport,
  QuestionBankExportFormat,
  QuestionBankExportItem,
  QuestionSubject,
  QuestionType,
  SOPStep,
} from '../types'

function loadState<T>(key: string, fallback: T): T {
  if (typeof localStorage === 'undefined') return fallback
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

function daysFromNow(days: number) {
  const date = new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString()
}

const defaultProfile: UserProfile = {
  id: 'local-child-001',
  name: 'Leo',
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

export const useUserStore = defineStore('user', () => {
  const saved = loadState('cc-user', {
    profile: defaultProfile,
    assessment: defaultAssessment,
    sunlightPoints: 120,
    isOnboarded: false,
  })

  const profile = ref<UserProfile>(saved.profile)
  const assessment = ref<ExecutiveFunctionAssessment>({ ...defaultAssessment, ...saved.assessment })
  const sunlightPoints = ref(saved.sunlightPoints)
  const isOnboarded = ref(saved.isOnboarded)

  const isLowGrade = computed(() => profile.value.grade <= 2)
  const isHighGrade = computed(() => profile.value.grade >= 5)

  watch(
    () => ({ profile: profile.value, assessment: assessment.value, sunlightPoints: sunlightPoints.value, isOnboarded: isOnboarded.value }),
    value => persistState('cc-user', value),
    { deep: true },
  )

  function setProfile(p: Partial<UserProfile>) {
    Object.assign(profile.value, p)
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

  function addSunlightPoints(pts: number) {
    sunlightPoints.value = Math.max(0, sunlightPoints.value + pts)
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

const seededTasks: TaskItem[] = [
  { id: 'habit-read', title: '今日指读任务', description: '动笔前用手指着读题，并圈出大题号、单位和符号。', type: 'habit', status: 'pending', rewardPoints: 20, icon: '☝️' },
  { id: 'bag-zone', title: '整理书包 3 分区', description: '把作业区、文具区、回执区各归位一次。', type: 'organization', status: 'pending', rewardPoints: 15, icon: '🎒' },
  { id: 'schulte', title: '舒尔特方格', description: '完成 90 秒专注小游戏。', type: 'game', status: 'pending', rewardPoints: 10, icon: '🧠' },
]

export const useTaskStore = defineStore('task', () => {
  const saved = loadState('cc-task', { todayTasks: seededTasks, habitAssignments: [] as HabitAssignment[] })
  const todayTasks = ref<TaskItem[]>(saved.todayTasks?.length ? saved.todayTasks : seededTasks)
  const habitAssignments = ref<HabitAssignment[]>(saved.habitAssignments || [])
  const currentWeekHabit = ref<HabitSOP>({
    id: 'week-3-read-circle',
    title: '读题圈号 SOP',
    weekNumber: 3,
    steps: [
      { order: 1, instruction: '手指跟着题干逐字移动，遇到数字停一下。' },
      { order: 2, instruction: '圈出大题号、单位、运算符号三处关键点。' },
      { order: 3, instruction: '动笔前复述：题目要我求什么？' },
    ],
  })
  const weeklyProgress = computed(() => todayTasks.value.filter(task => task.status === 'completed').length)
  const activeHabits = computed(() => habitAssignments.value.filter(h => h.active))

  watch(() => ({ todayTasks: todayTasks.value, habitAssignments: habitAssignments.value }), value => persistState('cc-task', value), { deep: true })

  function completeTask(id: string) {
    const task = todayTasks.value.find(t => t.id === id)
    if (!task || task.status === 'completed') return 0
    task.status = 'completed'
    return task.rewardPoints
  }

  function setTodayTasks(tasks: TaskItem[]) {
    todayTasks.value = tasks
  }

  function resetTodayTasks() {
    todayTasks.value = seededTasks.map(task => ({ ...task, status: 'pending' }))
  }

  async function fetchHabits(childId: string) {
    try {
      const { api } = await import('../utils/api')
      const habits = await api.habits.list(childId)
      habitAssignments.value = habits
      const active = habits.filter(h => h.active)
      if (active.length > 0) {
        const latest = active[0]
        currentWeekHabit.value = {
          id: latest.id,
          title: latest.title,
          weekNumber: latest.weekNumber,
          steps: latest.steps,
        }
        const habitTasks: TaskItem[] = active.map(h => ({
          id: h.id,
          title: h.title,
          description: h.description,
          type: 'habit' as const,
          status: 'pending' as const,
          rewardPoints: h.rewardPoints,
          icon: h.icon,
        }))
        const extraTasks = seededTasks.filter(t => t.type !== 'habit')
        todayTasks.value = [...habitTasks, ...extraTasks]
      }
    } catch {
      // API不可用时保持本地缓存数据
    }
  }

  function addHabitAssignment(data: Omit<HabitAssignment, 'id' | 'assignedAt'>) {
    const habit: HabitAssignment = { ...data, id: `ha-${Date.now()}`, assignedAt: new Date().toISOString() }
    habitAssignments.value.unshift(habit)
    if (habit.active) {
      todayTasks.value.unshift({
        id: habit.id,
        title: habit.title,
        description: habit.description,
        type: 'habit',
        status: 'pending',
        rewardPoints: habit.rewardPoints,
        icon: habit.icon,
      })
      currentWeekHabit.value = { id: habit.id, title: habit.title, weekNumber: habit.weekNumber, steps: habit.steps }
    }
    return habit
  }

  function deactivateHabit(id: string) {
    const habit = habitAssignments.value.find(h => h.id === id)
    if (habit) habit.active = false
    todayTasks.value = todayTasks.value.filter(t => t.id !== id)
  }

  return { todayTasks, habitAssignments, currentWeekHabit, weeklyProgress, activeHabits, completeTask, setTodayTasks, resetTodayTasks, fetchHabits, addHabitAssignment, deactivateHabit }
})

const categoryLabels: Record<MistakeCategory, string> = {
  symbol_error: '看错符号',
  unit_missing: '漏写单位',
  misread_details: '读题遗漏',
  copying_error: '抄写错误',
  skipped_step: '跳步计算',
  rushing: '急于求成',
  lost_focus: '注意力涣散',
  messy_writing: '书写混乱',
  format_error: '格式错误',
  spelling_slip: '笔误/拼写',
  wild_guess: '盲目猜测',
  something_else: '其他原因',
}

export const useMistakeStore = defineStore('mistake', () => {
  const saved = loadState('cc-mistake', {
    records: [
      { id: 'm-1', subject: '数学', imageUrl: '', isCarelessness: true, category: 'symbol_error' as MistakeCategory, createdAt: daysFromNow(-1), reviewScheduledAt: daysFromNow(0) },
      { id: 'm-2', subject: '语文', imageUrl: '', isCarelessness: false, knowledgePoint: '阅读细节定位', createdAt: daysFromNow(-3), reviewScheduledAt: daysFromNow(1) },
    ] as MistakeRecord[],
  })
  const records = ref<MistakeRecord[]>(saved.records)
  const todayReviewCount = computed(() => records.value.filter(record => new Date(record.reviewScheduledAt) <= new Date()).length)
  const categoryStats = computed(() => records.value.reduce<Record<string, number>>((stats, record) => {
    const key = record.category ? categoryLabels[record.category] : record.knowledgePoint ? '知识点归档' : '未分类'
    stats[key] = (stats[key] || 0) + 1
    return stats
  }, {}))

  watch(() => ({ records: records.value }), value => persistState('cc-mistake', value), { deep: true })

  function addRecord(record: Omit<MistakeRecord, 'id' | 'createdAt' | 'reviewScheduledAt'>) {
    const next: MistakeRecord = {
      ...record,
      id: `m-${Date.now()}`,
      createdAt: new Date().toISOString(),
      reviewScheduledAt: daysFromNow(record.isCarelessness ? 3 : 1),
    }
    records.value.unshift(next)
    return next
  }

  return { records, todayReviewCount, categoryStats, addRecord }
})

const seededBadges: BadgeItem[] = [
  { id: 'read-7', name: '指读先锋', description: '连续 7 天完成指读圈号', icon: '☝️', color: '#fbe270', unlocked: true, unlockedAt: daysFromNow(-2), requirement: '连续 7 天完成主线习惯' },
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

  function unlockBadge(id: string) {
    const badge = badges.value.find(b => b.id === id)
    if (badge && !badge.unlocked) {
      badge.unlocked = true
      badge.unlockedAt = new Date().toISOString()
      confettiActive.value = true
      setTimeout(() => { confettiActive.value = false }, 3000)
    }
  }

  function addCovenant(covenant: Omit<FamilyCovenant, 'id' | 'createdAt' | 'status'>) {
    const next: FamilyCovenant = { ...covenant, id: `c-${Date.now()}`, createdAt: new Date().toISOString(), status: 'active' }
    covenants.value.unshift(next)
    return next
  }

  return { badges, covenants, confettiActive, unlockedCount, unlockBadge, addCovenant }
})

export const useGrowthStore = defineStore('growth', () => {
  const saved = loadState('cc-growth', {
    trendData: [
      { date: '1年级', mistakeRate: 0.31, itemLossRate: 7, taskCompletionRate: 0.52 },
      { date: '2年级', mistakeRate: 0.26, itemLossRate: 6, taskCompletionRate: 0.61 },
      { date: '3年级', mistakeRate: 0.18, itemLossRate: 4, taskCompletionRate: 0.82 },
    ] as GrowthDataPoint[],
    alerts: [
      { id: 'a-1', title: '💡 阶段性发展发现', description: '近 7 天“看错符号错误”环比上升 25%。', suggestion: '写 20 分钟休息 5 分钟，并调高台灯亮度一档。', severity: 'info' as const, createdAt: daysFromNow(0) },
    ] as DiagnosticAlert[],
    itemLossRecords: [
      { id: 'i-1', itemName: '橡皮', lostLocation: '教室抽屉', lostDate: daysFromNow(-4), estimatedCost: 3, frequency: 3 },
      { id: 'i-2', itemName: '2B 铅笔', lostLocation: '培训班', lostDate: daysFromNow(-2), estimatedCost: 5, frequency: 2 },
    ] as ItemLossRecord[],
  })
  const trendData = ref<GrowthDataPoint[]>(saved.trendData)
  const alerts = ref<DiagnosticAlert[]>(saved.alerts)
  const itemLossRecords = ref<ItemLossRecord[]>(saved.itemLossRecords)
  const totalLossCost = computed(() => itemLossRecords.value.reduce((sum, item) => sum + item.estimatedCost * item.frequency, 0))
  const highFrequencyItems = computed(() => itemLossRecords.value.filter(item => item.frequency >= 3))

  watch(() => ({ trendData: trendData.value, alerts: alerts.value, itemLossRecords: itemLossRecords.value }), value => persistState('cc-growth', value), { deep: true })

  function addItemLossRecord(record: Omit<ItemLossRecord, 'id' | 'lostDate' | 'frequency'> & { frequency?: number }) {
    const existing = itemLossRecords.value.find(item => item.itemName === record.itemName)
    if (existing) {
      existing.frequency += 1
      existing.lostDate = new Date().toISOString()
      existing.lostLocation = record.lostLocation
      return existing
    }
    const next: ItemLossRecord = { ...record, id: `i-${Date.now()}`, lostDate: new Date().toISOString(), frequency: record.frequency || 1 }
    itemLossRecords.value.unshift(next)
    return next
  }

  return { trendData, alerts, itemLossRecords, totalLossCost, highFrequencyItems, addItemLossRecord }
})

export const usePomodoroStore = defineStore('pomodoro', () => {
  const saved = loadState('cc-pomodoro', { sessions: [] as PomodoroSession[] })
  const sessions = ref<PomodoroSession[]>(saved.sessions)
  const isRunning = ref(false)
  const remainingSeconds = ref(25 * 60)
  const activeSessionId = ref<string | null>(null)
  const uncertainCount = computed(() => activeSessionId.value ? sessions.value.find(s => s.id === activeSessionId.value)?.uncertainQuestions || 0 : 0)

  watch(() => ({ sessions: sessions.value }), value => persistState('cc-pomodoro', value), { deep: true })

  function startSession(estimatedMinutes = 30, subject = '数学') {
    const session: PomodoroSession = { id: `p-${Date.now()}`, estimatedMinutes, actualMinutes: 0, subject, uncertainQuestions: 0 }
    sessions.value.unshift(session)
    activeSessionId.value = session.id
    remainingSeconds.value = 25 * 60
    isRunning.value = true
    return session.id
  }

  function pauseSession() {
    isRunning.value = false
  }

  function tick() {
    if (!isRunning.value || remainingSeconds.value <= 0) return
    remainingSeconds.value -= 1
    if (remainingSeconds.value === 0) isRunning.value = false
  }

  function markUncertain() {
    const session = sessions.value.find(s => s.id === activeSessionId.value)
    if (session) session.uncertainQuestions += 1
    return session?.uncertainQuestions || 0
  }

  function finishSession(actualMinutes: number, timeDrainReason?: string) {
    const session = sessions.value.find(s => s.id === activeSessionId.value)
    if (!session) return null
    session.actualMinutes = actualMinutes
    session.timeDrainReason = timeDrainReason
    isRunning.value = false
    activeSessionId.value = null
    return session
  }

  return { sessions, isRunning, remainingSeconds, activeSessionId, uncertainCount, startSession, pauseSession, tick, markUncertain, finishSession }
})

export const useParentStore = defineStore('parent', () => {
  const saved = loadState('cc-parent', {
    settings: { difficultyLevel: 2, dailyReminder: true, achievementNotification: true, weeklyReport: true, schoolSync: false } as ParentSettings,
    discussionPosts: [
      { id: 'post-1', title: '三分区书包第 5 天反馈', content: '只改透明回执袋后，漏交明显减少。', author: '匿名家长', tags: ['收纳'], replyCount: 8, hasExpertAnswer: true, createdAt: daysFromNow(-1) },
      { id: 'post-2', title: '如何温和提醒不催促？', content: '把提醒改成环境提示卡。', author: '匿名家长', tags: ['边界感'], replyCount: 5, hasExpertAnswer: false, createdAt: daysFromNow(-2) },
    ] as DiscussionPost[],
    articles: [
      { id: 'article-1', title: '执行功能不是智力', summary: '理解粗心背后的计划、抑制和工作记忆。', category: '执行功能', type: 'article' as const, readingTime: 8, imageUrl: '', bookmarked: false },
      { id: 'article-2', title: '非物质奖励保护内驱力', summary: '为什么亲子电影夜比现金奖励更适合习惯形成。', category: '奖励系统', type: 'cbt' as const, readingTime: 6, imageUrl: '', bookmarked: true },
    ] as ArticleResource[],
  })
  const settings = ref<ParentSettings>(saved.settings)
  const discussionPosts = ref<DiscussionPost[]>(saved.discussionPosts)
  const articles = ref<ArticleResource[]>(saved.articles)

  watch(() => ({ settings: settings.value, discussionPosts: discussionPosts.value, articles: articles.value }), value => persistState('cc-parent', value), { deep: true })

  function updateSettings(s: Partial<ParentSettings>) {
    Object.assign(settings.value, s)
  }

  function createPost(data: { title: string; content: string; tags: string[] }) {
    discussionPosts.value.unshift({ id: `post-${Date.now()}`, author: '匿名家长', replyCount: 0, hasExpertAnswer: false, createdAt: new Date().toISOString(), ...data })
  }

  return { settings, discussionPosts, articles, updateSettings, createPost }
})

// ==================
// 藏宝库（题库）Store
// ==================

const categoryLabelsBank: Record<string, string> = {
  symbol_error: '看错符号', unit_missing: '漏写单位', misread_details: '读题遗漏',
  copying_error: '抄写错误', skipped_step: '跳步计算', rushing: '急于求成',
  lost_focus: '注意力涣散', messy_writing: '书写混乱', format_error: '格式错误',
  spelling_slip: '笔误/拼写', wild_guess: '盲目猜测', something_else: '其他原因',
}

const subjectLabels: Record<string, string> = {
  math: '数学', chinese: '语文', english: '英语', science: '科学', other: '其他',
}

const subjectColors: Record<string, string> = {
  math: '#f87171', chinese: '#60a5fa', english: '#34d399', science: '#fbbf24', other: '#c4b5fd',
}

const difficultyLabels = ['', '★ 简单', '★★ 较易', '★★★ 中等', '★★★★ 较难', '★★★★★ 困难']

const seededQuestions: QuestionItem[] = [
  {
    id: 'q-1', subject: 'math', type: 'calculation', content: '计算：3.25 × 4 + 0.5 =',
    answer: '13.5', grade: 3, chapter: '第3单元 小数乘法', knowledgePoints: ['小数乘法', '混合运算'],
    difficulty: 2, tags: ['易错'], isCarelessness: true, mistakeCategory: 'symbol_error',
    reviewCount: 1, resolved: false, source: 'manual',
    createdAt: daysFromNow(-5), updatedAt: daysFromNow(-5),
  },
  {
    id: 'q-2', subject: 'chinese', type: 'fill', content: '把下列词语补充完整：一( )千里，( )往直前',
    answer: '日；义', grade: 3, chapter: '第5单元 成语积累', knowledgePoints: ['成语', '字义辨析'],
    difficulty: 3, tags: [], isCarelessness: false,
    reviewCount: 0, resolved: false, source: 'manual',
    createdAt: daysFromNow(-3), updatedAt: daysFromNow(-3),
  },
  {
    id: 'q-3', subject: 'math', type: 'choice', content: '下列分数中，最小的是：A. 3/4  B. 5/6  C. 2/3  D. 7/8',
    answer: 'C', grade: 4, chapter: '第4单元 分数比较', knowledgePoints: ['分数大小比较', '通分'],
    difficulty: 2, tags: ['易错', '常考'], isCarelessness: true, mistakeCategory: 'misread_details',
    reviewCount: 2, resolved: false, source: 'manual',
    createdAt: daysFromNow(-7), updatedAt: daysFromNow(-2),
  },
]

export const useQuestionBankStore = defineStore('questionBank', () => {
  const saved = loadState('cc-qbank', { questions: seededQuestions, imports: [] as QuestionBankImport[] })
  const questions = ref<QuestionItem[]>(saved.questions?.length ? saved.questions : seededQuestions)
  const imports = ref<QuestionBankImport[]>(saved.imports || [])
  const selectedIds = ref<Set<string>>(new Set())
  const printPreviewVisible = ref(false)
  const printIncludeAnswer = ref(false)

  watch(
    () => ({ questions: questions.value, imports: imports.value }),
    value => persistState('cc-qbank', value),
    { deep: true },
  )

  // 统计 computed
  const totalCount = computed(() => questions.value.length)
  const unresolvedCount = computed(() => questions.value.filter(q => !q.resolved).length)
  const todayAddedCount = computed(() => {
    const today = new Date().toDateString()
    return questions.value.filter(q => new Date(q.createdAt).toDateString() === today).length
  })

  // 薄弱点图表数据
  const weaknessChartData = computed(() => {
    const bySubjectMap: Record<string, number> = {}
    const byCategoryMap: Record<string, number> = {}
    const byKPMap: Record<string, number> = {}
    const byDiffMap: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }

    for (const q of questions.value.filter(x => !x.resolved)) {
      const subLabel = subjectLabels[q.subject] || q.subject
      bySubjectMap[subLabel] = (bySubjectMap[subLabel] || 0) + 1
      if (q.mistakeCategory) {
        const catLabel = categoryLabelsBank[q.mistakeCategory] || q.mistakeCategory
        byCategoryMap[catLabel] = (byCategoryMap[catLabel] || 0) + 1
      }
      for (const kp of q.knowledgePoints) {
        byKPMap[kp] = (byKPMap[kp] || 0) + 1
      }
      byDiffMap[q.difficulty] = (byDiffMap[q.difficulty] || 0) + 1
    }

    const bySubject = Object.entries(bySubjectMap).map(([subject, count]) => ({
      subject, count,
      color: subjectColors[Object.keys(subjectLabels).find(k => subjectLabels[k] === subject) || ''] || '#c4b5fd',
    }))
    const byCategory = Object.entries(byCategoryMap).map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count)
    const byKnowledgePoint = Object.entries(byKPMap).map(([point, count]) => ({ point, count }))
      .sort((a, b) => b.count - a.count).slice(0, 10)
    const byDifficulty = [1, 2, 3, 4, 5].map(level => ({ level, label: difficultyLabels[level], count: byDiffMap[level] }))

    return { bySubject, byCategory, byKnowledgePoint, byDifficulty }
  })

  // AI 推荐选题：优先选复习次数少、难度高、且未解决的题目
  const aiRecommendedIds = computed(() => {
    const pool = questions.value
      .filter(q => !q.resolved)
      .sort((a, b) => {
        const scoreA = (5 - a.reviewCount) * 2 + a.difficulty
        const scoreB = (5 - b.reviewCount) * 2 + b.difficulty
        return scoreB - scoreA
      })
    return pool.slice(0, 10).map(q => q.id)
  })

  const selectedQuestions = computed(() =>
    questions.value.filter(q => selectedIds.value.has(q.id))
  )

  // CRUD
  function addQuestion(data: Omit<QuestionItem, 'id' | 'reviewCount' | 'resolved' | 'createdAt' | 'updatedAt'>) {
    const now = new Date().toISOString()
    const q: QuestionItem = { ...data, id: `q-${Date.now()}`, reviewCount: 0, resolved: false, createdAt: now, updatedAt: now }
    questions.value.unshift(q)
    return q
  }

  function updateQuestion(id: string, patch: Partial<QuestionItem>) {
    const q = questions.value.find(x => x.id === id)
    if (q) Object.assign(q, patch, { updatedAt: new Date().toISOString() })
  }

  function deleteQuestion(id: string) {
    questions.value = questions.value.filter(q => q.id !== id)
    selectedIds.value.delete(id)
  }

  function markResolved(id: string) {
    updateQuestion(id, { resolved: true })
  }

  function incrementReview(id: string) {
    const q = questions.value.find(x => x.id === id)
    if (q) updateQuestion(id, { reviewCount: q.reviewCount + 1 })
  }

  // 选题管理
  function toggleSelect(id: string) {
    if (selectedIds.value.has(id)) selectedIds.value.delete(id)
    else selectedIds.value.add(id)
  }

  function selectAll(ids: string[]) {
    ids.forEach(id => selectedIds.value.add(id))
  }

  function clearSelection() {
    selectedIds.value.clear()
  }

  function applyAiSelection() {
    clearSelection()
    aiRecommendedIds.value.forEach(id => selectedIds.value.add(id))
  }

  // 导入题库
  function importQuestions(raw: QuestionBankExportFormat, fileName: string): QuestionBankImport {
    const now = new Date().toISOString()
    let importedCount = 0
    const errors: string[] = []
    const importId = `imp-${Date.now()}`

    if (raw.version !== '1.0') {
      const rec: QuestionBankImport = { id: importId, fileName, totalCount: 0, importedCount: 0, failedCount: 0, status: 'failed', errors: ['版本号不支持，仅支持 version: "1.0"'], importedAt: now }
      imports.value.unshift(rec)
      return rec
    }

    const validSubjects = ['math', 'chinese', 'english', 'science', 'other']
    const validTypes = ['choice', 'fill', 'calculation', 'composition', 'other']

    for (let i = 0; i < raw.questions.length; i++) {
      const item = raw.questions[i]
      if (!item.content?.trim()) { errors.push(`第${i + 1}题: content(题目正文)为必填项`); continue }
      if (!validSubjects.includes(item.subject)) { errors.push(`第${i + 1}题: subject 不合法，应为 ${validSubjects.join('/')}`); continue }
      if (!validTypes.includes(item.type)) { errors.push(`第${i + 1}题: type 不合法，应为 ${validTypes.join('/')}`); continue }
      const grade = item.grade ?? raw.schoolInfo?.grade ?? 3
      const difficulty = Math.min(5, Math.max(1, item.difficulty ?? 3)) as 1|2|3|4|5
      const q: QuestionItem = {
        id: `q-${Date.now()}-${i}`, subject: item.subject as QuestionSubject, type: item.type as QuestionType,
        content: item.content.trim(), answer: item.answer, grade, chapter: item.chapter,
        knowledgePoints: item.knowledgePoints ?? [], difficulty, tags: item.tags ?? [],
        reviewCount: 0, resolved: false, source: 'import', importId,
        createdAt: now, updatedAt: now,
      }
      questions.value.unshift(q)
      importedCount++
    }

    const status = errors.length === 0 ? 'success' : importedCount > 0 ? 'partial' : 'failed'
    const rec: QuestionBankImport = { id: importId, fileName, totalCount: raw.questions.length, importedCount, failedCount: errors.length, status, errors, importedAt: now }
    imports.value.unshift(rec)
    return rec
  }

  // 导出为标准格式
  function exportQuestions(ids?: string[]): QuestionBankExportFormat {
    const list = ids ? questions.value.filter(q => ids.includes(q.id)) : questions.value
    return {
      version: '1.0',
      exportedAt: new Date().toISOString(),
      questions: list.map(q => ({
        subject: q.subject, type: q.type, content: q.content, answer: q.answer,
        grade: q.grade, chapter: q.chapter, knowledgePoints: q.knowledgePoints,
        difficulty: q.difficulty, tags: q.tags,
      })),
    }
  }

  return {
    questions, imports, selectedIds, selectedQuestions, printPreviewVisible, printIncludeAnswer,
    totalCount, unresolvedCount, todayAddedCount, weaknessChartData, aiRecommendedIds,
    addQuestion, updateQuestion, deleteQuestion, markResolved, incrementReview,
    toggleSelect, selectAll, clearSelection, applyAiSelection,
    importQuestions, exportQuestions,
  }
})
