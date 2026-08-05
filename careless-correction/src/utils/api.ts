import type {
  ArticleResource, BadgeItem, DiagnosticAlert,
  GrowthDataPoint, HabitSOP, ItemLossRecord, ItemStorageRecord, LlmConfig,
  MistakeCategory, MistakeRecord, ParentSettings, RewardItem, SubTaskItem, SunlightRecord, TaskItem, UserProfile,
} from '../types'

const API_BASE = '/api/v1'

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
  if (token) localStorage.setItem('cc-auth-token', token)
  else localStorage.removeItem('cc-auth-token')
}

export function getAuthToken(): string | null {
  if (!authToken) authToken = localStorage.getItem('cc-auth-token')
  return authToken
}

export function clearAuthToken() {
  setAuthToken(null)
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken()
  const isFormData = options?.body instanceof FormData
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    if (res.status === 401) clearAuthToken()
    throw new Error(body.detail || body.error || `API Error: ${res.status}`)
  }
  return res.json()
}

// ── 数据规范化：后端 snake_case → 前端 camelCase ──────────────────────────

export function normalizeUser(u: any): UserProfile {
  return {
    id: String(u.pk_users ?? u.id ?? ''),
    name: u.name ?? '',
    loginName: u.login_name ?? u.loginName,
    grade: u.grade ?? 3,
    avatarUrl: u.avatar_url ?? u.avatarUrl ?? '',
    role: u.role ?? 'child',
    parentId: u.fk_users_parent ?? u.parentId,
    sunlightPoints: u.sunlight_points ?? u.sunlightPoints,
    apples: u.apples ?? 0,
    streakDays: u.streak_days ?? u.streakDays,
    isOnboarded: u.is_onboarded ?? u.isOnboarded,
  }
}

export interface ChildProfile {
  id: string
  name: string
  loginName?: string
  grade: number
  avatarUrl: string
  sunlightPoints: number
  apples: number
  streakDays: number
  isOnboarded: boolean
}

export function normalizeChild(c: any): ChildProfile {
  return {
    id: String(c.pk_users ?? c.id ?? ''),
    name: c.name ?? '',
    loginName: c.login_name ?? c.loginName,
    grade: c.grade ?? 3,
    avatarUrl: c.avatar_url ?? c.avatarUrl ?? '',
    sunlightPoints: c.sunlight_points ?? 0,
    apples: c.apples ?? 0,
    streakDays: c.streak_days ?? 0,
    isOnboarded: c.is_onboarded ?? false,
  }
}

export function normalizeSubTask(s: any): SubTaskItem {
  return {
    id: String(s.pk_sub_tasks ?? s.id ?? ''),
    title: s.title ?? '',
    type: s.type ?? undefined,
    weekDay: s.week_day ?? s.weekDay,
    sortOrder: s.sort_order ?? s.sortOrder ?? 0,
  }
}

export function normalizeTask(t: any): TaskItem {
  return {
    id: String(t.pk_tasks ?? t.id ?? ''),
    title: t.title ?? '',
    description: t.description ?? '',
    type: t.type ?? 'study_habit',
    status: t.status ?? 'pending',
    rewardPoints: t.reward_points ?? t.rewardPoints ?? 10,
    icon: t.icon ?? '📋',
    weekDay: t.week_day ?? t.weekDay,
    assignedDate: t.assigned_date ?? t.assignedDate,
    completedAt: t.completed_at ?? t.completedAt,
    completionPhotoUrl: t.completion_photo_url ?? t.completionPhotoUrl,
    habitSopId: t.fk_habit_sops ?? t.habitSopId,
    active: t.active ?? true,
    createdAt: t.created_at ?? t.createdAt,
    subTasks: Array.isArray(t.sub_tasks ?? t.subTasks) ? (t.sub_tasks ?? t.subTasks).map(normalizeSubTask) : undefined,
  }
}

export function normalizeMistake(r: any): MistakeRecord {
  return {
    id: String(r.pk_mistake_records ?? r.id ?? ''),
    subject: r.subject ?? '',
    imageUrl: r.image_url ?? r.imageUrl ?? '',
    subjectTag: r.subject_tag ?? r.subjectTag ?? r.knowledge_point,
    createdAt: r.created_at ?? r.createdAt ?? new Date().toISOString(),
    isCarelessness: r.is_carelessness ?? r.isCarelessness,
    category: r.category as MistakeCategory | undefined,
    knowledgePoint: r.knowledge_point ?? r.knowledgePoint,
    recognizedText: r.recognized_text ?? r.recognizedText,
    grade: r.grade,
    curriculumChapter: r.curriculum_chapter ?? r.curriculumChapter,
    reviewStrategy: r.review_strategy ?? r.reviewStrategy,
    nextReviewAt: r.next_review_at ?? r.nextReviewAt,
    reviewCount: r.review_count ?? r.reviewCount,
    resolved: r.resolved,
  }
}

export function normalizeItemLoss(r: any): ItemLossRecord {
  return {
    id: String(r.pk_item_loss_records ?? r.id ?? ''),
    itemName: r.item_name ?? r.itemName ?? '',
    lostLocation: r.lost_location ?? r.lostLocation ?? '',
    lostDate: r.lost_date ?? r.lostDate ?? new Date().toISOString(),
    estimatedCost: Number(r.estimated_cost ?? r.estimatedCost ?? 0),
    frequency: r.frequency_30d ?? r.frequency ?? 1,
    isHighFrequency: r.is_high_frequency ?? r.isHighFrequency ?? false,
    suggestion: r.suggestion ?? undefined,
  }
}

export function normalizeItemStorage(r: any): ItemStorageRecord {
  return {
    id: String(r.pk_item_storage_records ?? r.id ?? ''),
    itemName: r.item_name ?? r.itemName ?? '',
    storageLocation: r.storage_location ?? r.storageLocation ?? '',
    storageDate: r.storage_date ?? r.storageDate ?? new Date().toISOString(),
    notes: r.notes,
  }
}

export function normalizeSunlightRecord(r: any): SunlightRecord {
  return {
    id: String(r.pk_sunlight_history ?? r.id ?? ''),
    amount: r.amount ?? 0,
    reason: r.reason ?? '',
    type: r.type ?? 'earn',
    timestamp: r.created_at ?? r.timestamp ?? new Date().toISOString(),
  }
}

export function normalizeRewardItem(r: any): RewardItem {
  return {
    id: String(r.pk_reward_items ?? r.id ?? ''),
    name: r.name ?? '',
    description: r.description ?? '',
    cost: r.cost ?? 0,
    icon: r.icon ?? '🎁',
    active: r.active ?? true,
  }
}

export function normalizeBadge(b: any): BadgeItem {
  return {
    id: String(b.pk_badges ?? b.id ?? ''),
    name: b.name ?? '',
    description: b.description ?? '',
    icon: b.icon ?? '🏅',
    color: b.color ?? '#fbe270',
    unlocked: b.unlocked ?? false,
    unlockedAt: b.unlocked_at ?? b.unlockedAt,
    requirement: b.requirement ?? '',
  }
}

export function normalizeGrowthPoint(s: any): GrowthDataPoint {
  return {
    date: s.snapshot_date ?? s.date ?? '',
    mistakeRate: Number(s.mistake_rate ?? s.mistakeRate ?? 0),
    itemLossRate: Number(s.item_loss_rate ?? s.itemLossRate ?? 0),
    taskCompletionRate: Number(s.task_completion_rate ?? s.taskCompletionRate ?? 0),
    focusScore: s.focus_score ?? s.focusScore,
    neatnessScore: s.neatness_score ?? s.neatnessScore,
    metacognitionScore: s.metacognition_score ?? s.metacognitionScore,
    emotionScore: s.emotion_score ?? s.emotionScore,
    source: s.source,
  }
}

export function normalizeAlert(a: any): DiagnosticAlert {
  return {
    id: String(a.pk_diagnostic_alerts ?? a.id ?? ''),
    title: a.title ?? '',
    description: a.description ?? '',
    suggestion: a.suggestion ?? '',
    severity: a.severity ?? 'info',
    createdAt: a.created_at ?? a.createdAt ?? new Date().toISOString(),
    relatedMetric: a.related_metric ?? a.relatedMetric,
    metricChange: a.metric_change ?? a.metricChange,
    isRead: a.is_read ?? a.isRead,
  }
}

export function normalizeHabit(h: any): HabitSOP {
  return {
    id: String(h.pk_habit_sops ?? h.id ?? ''),
    title: h.title ?? '',
    rewardPoints: h.reward_points ?? h.rewardPoints ?? 5,
    active: h.active ?? true,
    createdAt: h.created_at ?? h.createdAt,
    steps: (h.steps ?? []).map((s: any) => ({
      order: s.order,
      instruction: s.instruction,
      imageUrl: s.image_url ?? s.imageUrl,
      gifUrl: s.gif_url ?? s.gifUrl,
    })),
  }
}

export function normalizeLlmConfig(c: any): LlmConfig {
  return {
    endpoint: c.endpoint ?? 'https://api.openai.com/v1',
    apiKey: c.api_key ?? c.apiKey ?? '',
    model: c.model ?? 'gpt-4o-mini',
    mistakePrompt: c.mistake_prompt ?? c.mistakePrompt ?? '',
    assessmentPrompt: c.assessment_prompt ?? c.assessmentPrompt ?? '',
    assessmentCron: c.assessment_cron ?? c.assessmentCron ?? 'weekly',
    enabled: c.enabled ?? false,
  }
}

export function normalizeParentSettings(s: any): ParentSettings {
  return {
    dailyReminder: s.daily_reminder ?? s.dailyReminder ?? true,
    achievementNotification: s.achievement_notification ?? s.achievementNotification ?? true,
    weeklyReport: s.weekly_report ?? s.weeklyReport ?? true,
    schoolSync: s.school_sync ?? s.schoolSync ?? false,
    schoolSyncCode: s.school_sync_code ?? s.schoolSyncCode,
  }
}

export function normalizeArticle(a: any): ArticleResource {
  return {
    id: String(a.pk_articles ?? a.id ?? ''),
    title: a.title ?? '',
    summary: a.summary ?? '',
    contentUrl: a.content_url ?? a.contentUrl,
    category: a.category ?? '',
    type: a.type ?? 'article',
    readingTime: a.reading_time_minutes ?? a.readingTime ?? 5,
    readingTimeMinutes: a.reading_time_minutes ?? a.readingTimeMinutes,
    imageUrl: a.image_url ?? a.imageUrl ?? '',
    author: a.author ?? '',
    publishedAt: a.published_at ?? a.publishedAt,
    bookmarked: false,
  }
}

// ── API 调用 ───────────────────────────────────────────────────────────────

export const api = {
  auth: {
    register: (data: { name: string; password: string }) =>
      request<any>(`/auth/register?name=${encodeURIComponent(data.name)}&password=${encodeURIComponent(data.password)}`, { method: 'POST' }),
    login: (data: { name: string; password: string }) =>
      request<any>(`/auth/login?name=${encodeURIComponent(data.name)}&password=${encodeURIComponent(data.password)}`, { method: 'POST' }),
    session: () =>
      request<any>('/auth/session'),
    updateProfile: (data: { name?: string; grade?: number; avatarUrl?: string }) => {
      const params = new URLSearchParams()
      if (data.name) params.set('name', data.name)
      if (data.grade) params.set('grade', String(data.grade))
      if (data.avatarUrl) params.set('avatar_url', data.avatarUrl)
      return request<any>(`/auth/profile?${params}`, { method: 'PUT' })
    },
    changePassword: (oldPassword: string, newPassword: string) =>
      request<{ success: boolean }>(`/auth/password?old_password=${encodeURIComponent(oldPassword)}&new_password=${encodeURIComponent(newPassword)}`, { method: 'PUT' }),
    saveAssessment: (data: { focusAttention: number; organization: number; emotionalControl: number; planning: number; impulseControl: number; recommendedLevel: number; taskDensity?: string }) => {
      const params = new URLSearchParams({
        focus_attention: String(data.focusAttention),
        organization: String(data.organization),
        emotional_control: String(data.emotionalControl),
        planning: String(data.planning),
        impulse_control: String(data.impulseControl),
        recommended_level: String(data.recommendedLevel),
      })
      if (data.taskDensity) params.set('task_density', data.taskDensity)
      return request<{ success: boolean; is_onboarded: boolean }>(`/auth/assessment?${params}`, { method: 'POST' })
    },
  },

  children: {
    list: () =>
      request<any>('/children/'),
    add: (data: { name: string; grade: number }) =>
      request<any>(`/children/?name=${encodeURIComponent(data.name)}&grade=${data.grade}`, { method: 'POST' }),
    update: (id: string, data: { name?: string; grade?: number }) => {
      const params = new URLSearchParams()
      if (data.name) params.set('name', data.name)
      if (data.grade) params.set('grade', String(data.grade))
      return request<any>(`/children/${id}?${params}`, { method: 'PUT' })
    },
    remove: (id: string) =>
      request<any>(`/children/${id}`, { method: 'DELETE' }),
    switchToken: (childId: string) =>
      request<any>(`/children/${childId}/switch-token`, { method: 'POST' }),
  },

  tasks: {
    getToday: (childId?: string) =>
      request<any>(`/tasks/today${childId ? `?child_id=${childId}` : ''}`),
    getTask: (taskId: string) =>
      request<any>(`/tasks/${taskId}`),
    complete: (taskId: string) =>
      request<any>(`/tasks/${taskId}/complete`, { method: 'POST' }),
    create: (data: { title: string; type: string; description?: string; rewardPoints?: number; icon?: string; weekDay?: string; childId?: string }) => {
      const params = new URLSearchParams({ title: data.title, type: data.type })
      if (data.description) params.set('description', data.description)
      if (data.rewardPoints) params.set('reward_points', String(data.rewardPoints))
      if (data.icon) params.set('icon', data.icon)
      if (data.weekDay) params.set('week_day', data.weekDay)
      if (data.childId) params.set('child_id', data.childId)
      return request<any>(`/tasks/?${params}`, { method: 'POST' })
    },
    update: (taskId: string, data: { title?: string; description?: string; type?: string; rewardPoints?: number; icon?: string; weekDay?: string; active?: boolean }) => {
      const params = new URLSearchParams()
      if (data.title) params.set('title', data.title)
      if (data.description !== undefined) params.set('description', data.description)
      if (data.type) params.set('type', data.type)
      if (data.rewardPoints !== undefined) params.set('reward_points', String(data.rewardPoints))
      if (data.icon) params.set('icon', data.icon)
      if (data.weekDay !== undefined) params.set('week_day', data.weekDay)
      if (data.active !== undefined) params.set('active', String(data.active))
      return request<any>(`/tasks/${taskId}?${params}`, { method: 'PUT' })
    },
    delete: (taskId: string) =>
      request<any>(`/tasks/${taskId}`, { method: 'DELETE' }),
    deletePermanent: (taskId: string) =>
      request<any>(`/tasks/${taskId}/permanent`, { method: 'DELETE' }),
    getInventory: (childId?: string) =>
      request<any>(`/tasks/inventory${childId ? `?child_id=${childId}` : ''}`),
    getSubTaskLibrary: (childId?: string) =>
      request<any>(`/tasks/subtasks/library${childId ? `?child_id=${childId}` : ''}`),
    subtasks: {
      add: (taskId: string, data: { title: string; type?: string; weekDay?: string; sortOrder?: number }) => {
        const params = new URLSearchParams({ title: data.title })
        if (data.type) params.set('type', data.type)
        if (data.weekDay) params.set('week_day', data.weekDay)
        if (data.sortOrder !== undefined) params.set('sort_order', String(data.sortOrder))
        return request<any>(`/tasks/${taskId}/subtasks?${params}`, { method: 'POST' })
      },
      update: (taskId: string, subtaskId: string, data: { title?: string; type?: string; weekDay?: string; sortOrder?: number }) => {
        const params = new URLSearchParams()
        if (data.title) params.set('title', data.title)
        if (data.type) params.set('type', data.type)
        if (data.weekDay) params.set('week_day', data.weekDay)
        if (data.sortOrder !== undefined) params.set('sort_order', String(data.sortOrder))
        return request<any>(`/tasks/${taskId}/subtasks/${subtaskId}?${params}`, { method: 'PUT' })
      },
      remove: (taskId: string, subtaskId: string) =>
        request<any>(`/tasks/${taskId}/subtasks/${subtaskId}`, { method: 'DELETE' }),
    },
  },

  habits: {
    getAll: (childId?: string) =>
      request<any>(`/habits/${childId ? `?child_id=${childId}` : ''}`),
    update: (data: { id: string; title?: string; gradeRange?: string; difficultyLevel?: number; rewardPoints?: number; steps?: Array<{ instruction: string; order: number }> }) =>
      request<any>(`/habits/${data.id}`, { method: 'PUT', body: JSON.stringify(data) }),
    create: (data: { title: string; gradeRange?: string; difficultyLevel?: number; rewardPoints?: number; steps?: Array<{ instruction: string; order: number }>; childId?: string }) => {
      const path = data.childId ? `/habits/?child_id=${data.childId}` : '/habits/'
      return request<any>(path, { method: 'POST', body: JSON.stringify(data) })
    },
    getDetail: (habitId: string) =>
      request<any>(`/habits/${habitId}`),
    delete: (habitId: string) =>
      request<any>(`/habits/${habitId}`, { method: 'DELETE' }),
    deletePermanent: (habitId: string) =>
      request<any>(`/habits/${habitId}/permanent`, { method: 'DELETE' }),
    getInventory: (childId?: string) =>
      request<any>(`/habits/inventory${childId ? `?child_id=${childId}` : ''}`),
    getStepLibrary: (childId?: string) =>
      request<any>(`/habits/steps/library${childId ? `?child_id=${childId}` : ''}`),
  },

  mistakes: {
    uploadImage: (formData: FormData) =>
      request<{ imageUrl: string }>('/mistakes/upload', { method: 'POST', body: formData }),
    create: (data: { subject: string; imageUrl: string; isCarelessness?: boolean; category?: string; knowledgePoint?: string; grade?: number; childId?: string }) => {
      const params = new URLSearchParams({ subject: data.subject, image_url: data.imageUrl })
      if (data.isCarelessness !== undefined) params.set('is_carelessness', String(data.isCarelessness))
      if (data.category) params.set('category', data.category)
      if (data.knowledgePoint) params.set('knowledge_point', data.knowledgePoint)
      if (data.grade) params.set('grade', String(data.grade))
      if (data.childId) params.set('child_id', data.childId)
      return request<any>(`/mistakes/?${params}`, { method: 'POST' })
    },
    list: (childId?: string) =>
      request<any>(`/mistakes/${childId ? `?child_id=${childId}` : ''}`),
    delete: (id: string) =>
      request<{ success: boolean }>(`/mistakes/${id}`, { method: 'DELETE' }),
    review: (recordId: string, data: { canResolve: boolean; confidenceLevel?: number }) => {
      const params = new URLSearchParams({ can_resolve: String(data.canResolve) })
      if (data.confidenceLevel !== undefined) params.set('confidence_level', String(data.confidenceLevel))
      return request<any>(`/mistakes/${recordId}/review?${params}`, { method: 'POST' })
    },
  },

  items: {
    getLossList: (childId?: string) =>
      request<any>(`/items/loss${childId ? `?child_id=${childId}` : ''}`),
    reportLoss: (data: { itemName: string; lostLocation: string; estimatedCost?: number; childId?: string }) => {
      const params = new URLSearchParams({ item_name: data.itemName, lost_location: data.lostLocation })
      if (data.estimatedCost) params.set('estimated_cost', String(data.estimatedCost))
      if (data.childId) params.set('child_id', data.childId)
      return request<any>(`/items/loss?${params}`, { method: 'POST' })
    },
    addStorage: (data: { itemName: string; storageLocation: string; notes?: string; childId?: string }) => {
      const params = new URLSearchParams({ item_name: data.itemName, storage_location: data.storageLocation })
      if (data.notes) params.set('notes', data.notes)
      if (data.childId) params.set('child_id', data.childId)
      return request<any>(`/items/storage?${params}`, { method: 'POST' })
    },
    getStorageList: (childId?: string) =>
      request<any>(`/items/storage${childId ? `?child_id=${childId}` : ''}`),
  },

  points: {
    getBalance: (childId?: string) =>
      request<{ balance: number }>(`/points/balance${childId ? `?child_id=${childId}` : ''}`),
    getHistory: (childId?: string) =>
      request<any>(`/points/history${childId ? `?child_id=${childId}` : ''}`),
    award: (amount: number, reason?: string, childId?: string) => {
      const params = new URLSearchParams({ amount: String(amount) })
      if (reason) params.set('reason', reason)
      if (childId) params.set('child_id', childId)
      return request<{ balance: number; awarded: number }>(`/points/award?${params}`, { method: 'POST' })
    },
    redeem: (rewardItemId: string) =>
      request<{ success: boolean; pointsSpent: number; itemName: string }>(`/points/redeem?reward_item_id=${rewardItemId}`, { method: 'POST' }),
    getRewards: (childId?: string) =>
      request<any>(`/points/rewards${childId ? `?child_id=${childId}` : ''}`),
    createReward: (data: { name: string; description?: string; cost: number; icon?: string }) => {
      const params = new URLSearchParams({ name: data.name, cost: String(data.cost) })
      if (data.description) params.set('description', data.description)
      if (data.icon) params.set('icon', data.icon)
      return request<any>(`/points/rewards?${params}`, { method: 'POST' })
    },
    updateReward: (id: string, data: { name?: string; description?: string; cost?: number; icon?: string; active?: boolean }) => {
      const params = new URLSearchParams()
      if (data.name) params.set('name', data.name)
      if (data.description) params.set('description', data.description)
      if (data.cost !== undefined) params.set('cost', String(data.cost))
      if (data.icon) params.set('icon', data.icon)
      if (data.active !== undefined) params.set('active', String(data.active))
      return request<any>(`/points/rewards/${id}?${params}`, { method: 'PUT' })
    },
    deleteReward: (id: string) =>
      request<{ success: boolean }>(`/points/rewards/${id}`, { method: 'DELETE' }),

    // ── 苹果相关 API ──
    getApples: (childId?: string) =>
      request<{ apples: number; sunlightPoints: number; sunlightPerApple: number; history: any[] }>(`/points/apples${childId ? `?child_id=${childId}` : ''}`),
    growApple: (childId?: string) =>
      request<{ success: boolean; apples: number; sunlightPoints: number }>(`/points/apples/grow${childId ? `?child_id=${childId}` : ''}`, { method: 'POST' }),
    redeemApple: (count: number, reason: string, childId?: string) => {
      const params = new URLSearchParams({ count: String(count), reason })
      if (childId) params.set('child_id', childId)
      return request<{ success: boolean; apples: number; redeemed: number }>(`/points/apples/redeem?${params}`, { method: 'POST' })
    },
  },

  checkins: {
    submit: (data: { checkDate: string; totalPoints?: number; habitStepCount?: number; taskCount?: number }) => {
      const params = new URLSearchParams({ check_date: data.checkDate })
      if (data.totalPoints) params.set('total_points', String(data.totalPoints))
      if (data.habitStepCount) params.set('habit_step_count', String(data.habitStepCount))
      if (data.taskCount) params.set('task_count', String(data.taskCount))
      return request<any>(`/checkins/?${params}`, { method: 'POST' })
    },
    getPending: () =>
      request<{ pending: any[] }>('/checkins/pending'),
    approve: (id: number) =>
      request<{ success: boolean; awarded: number }>(`/checkins/${id}/approve`, { method: 'POST' }),
    reject: (id: number) =>
      request<{ success: boolean }>(`/checkins/${id}/reject`, { method: 'POST' }),
    getDetails: (id: number) =>
      request<{ checkin: any; completedTasks: any[]; pendingTasks: any[]; habits: any[] }>(`/checkins/${id}/details`),
  },

  badges: {
    list: (childId?: string) =>
      request<any>(`/badges/${childId ? `?child_id=${childId}` : ''}`),
    unlock: (badgeId: string, childId?: string) =>
      request<any>(`/badges/${badgeId}/unlock${childId ? `?child_id=${childId}` : ''}`, { method: 'POST' }),
    checkUnlocks: (childId?: string) =>
      request<{ newly_unlocked: any[]; total_unlocked: number }>(`/badges/check-unlocks${childId ? `?child_id=${childId}` : ''}`, { method: 'POST' }),
  },

  growth: {
    getTrend: (childId?: string) =>
      request<any>(`/growth/trend${childId ? `?child_id=${childId}` : ''}`),
    getAlerts: (childId?: string) =>
      request<any>(`/growth/alerts${childId ? `?child_id=${childId}` : ''}`),
  },

  llm: {
    getConfig: () =>
      request<any>('/llm/config'),
    updateConfig: (data: Partial<LlmConfig>) => {
      const params = new URLSearchParams()
      if (data.endpoint) params.set('endpoint', data.endpoint)
      if (data.apiKey) params.set('api_key', data.apiKey)
      if (data.model) params.set('model', data.model)
      if (data.mistakePrompt) params.set('mistake_prompt', data.mistakePrompt)
      if (data.assessmentPrompt) params.set('assessment_prompt', data.assessmentPrompt)
      if (data.assessmentCron) params.set('assessment_cron', data.assessmentCron)
      if (data.enabled !== undefined) params.set('enabled', String(data.enabled))
      return request<any>(`/llm/config?${params}`, { method: 'PUT' })
    },
    test: () =>
      request<{ success: boolean; result: string }>('/llm/test', { method: 'POST' }),
  },

  parent: {
    getSettings: () =>
      request<any>('/parent/settings'),
    updateSettings: (data: Partial<ParentSettings>) => {
      const params = new URLSearchParams()
      if (data.dailyReminder !== undefined) params.set('daily_reminder', String(data.dailyReminder))
      if (data.achievementNotification !== undefined) params.set('achievement_notification', String(data.achievementNotification))
      if (data.weeklyReport !== undefined) params.set('weekly_report', String(data.weeklyReport))
      if (data.schoolSync !== undefined) params.set('school_sync', String(data.schoolSync))
      return request<any>(`/parent/settings?${params}`, { method: 'PUT' })
    },
  },

  articles: {
    list: (category?: string) =>
      request<any>(`/articles${category ? `?category=${category}` : ''}`),
  },
}
