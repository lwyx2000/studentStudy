import type {
  BadgeItem, DiagnosticAlert, DiscussionPost, FamilyCovenant,
  GrowthDataPoint, HabitSOP, ItemLossRecord, ItemStorageRecord, LlmConfig,
  MistakeRecord, ParentSettings, RewardItem, SunlightRecord, TaskItem, UserProfile,
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
    grade: u.grade ?? 3,
    avatarUrl: u.avatar_url ?? u.avatarUrl ?? '',
    role: u.role ?? 'child',
  }
}

export interface ChildProfile {
  id: string
  name: string
  grade: number
  avatarUrl: string
  sunlightPoints: number
  streakDays: number
  isOnboarded: boolean
}

export function normalizeChild(c: any): ChildProfile {
  return {
    id: String(c.pk_users ?? c.id ?? ''),
    name: c.name ?? '',
    grade: c.grade ?? 3,
    avatarUrl: c.avatar_url ?? c.avatarUrl ?? '',
    sunlightPoints: c.sunlight_points ?? 0,
    streakDays: c.streak_days ?? 0,
    isOnboarded: c.is_onboarded ?? false,
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
  }
}

export function normalizeMistake(r: any): MistakeRecord {
  return {
    id: String(r.pk_mistake_records ?? r.id ?? ''),
    subject: r.subject ?? '',
    imageUrl: r.image_url ?? r.imageUrl ?? '',
    subjectTag: r.knowledge_point ?? r.category ?? r.subjectTag,
    createdAt: r.created_at ?? r.createdAt ?? new Date().toISOString(),
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

export function normalizeCovenant(c: any): FamilyCovenant {
  return {
    id: String(c.pk_covenants ?? c.id ?? ''),
    goal: c.goal ?? '',
    reward: c.reward ?? '',
    childSignature: c.child_signature ?? c.childSignature ?? '',
    parentSignature: c.parent_signature ?? c.parentSignature ?? '',
    createdAt: c.created_at ?? c.createdAt ?? new Date().toISOString(),
    status: c.status ?? 'active',
  }
}

export function normalizeGrowthPoint(s: any): GrowthDataPoint {
  return {
    date: s.snapshot_date ?? s.date ?? '',
    mistakeRate: Number(s.mistake_rate ?? s.mistakeRate ?? 0),
    itemLossRate: Number(s.item_loss_rate ?? s.itemLossRate ?? 0),
    taskCompletionRate: Number(s.task_completion_rate ?? s.taskCompletionRate ?? 0),
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
  }
}

export function normalizeHabit(h: any): HabitSOP {
  return {
    id: String(h.pk_habit_sops ?? h.id ?? ''),
    title: h.title ?? '',
    weekNumber: h.week_number ?? h.weekNumber ?? 1,
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
    difficultyLevel: s.difficulty_level ?? s.difficultyLevel ?? 2,
    dailyReminder: s.daily_reminder ?? s.dailyReminder ?? true,
    achievementNotification: s.achievement_notification ?? s.achievementNotification ?? true,
    weeklyReport: s.weekly_report ?? s.weeklyReport ?? true,
    schoolSync: s.school_sync ?? s.schoolSync ?? false,
  }
}

export function normalizePost(p: any): DiscussionPost {
  return {
    id: String(p.pk_community_posts ?? p.id ?? ''),
    title: p.title ?? '',
    content: p.content ?? '',
    author: p.is_anonymous ? '匿名家长' : (p.author ?? '匿名家长'),
    tags: Array.isArray(p.tags) ? p.tags : Object.values(p.tags ?? {}),
    replyCount: p.reply_count ?? p.replyCount ?? 0,
    hasExpertAnswer: p.has_expert_answer ?? p.hasExpertAnswer ?? false,
    createdAt: p.created_at ?? p.createdAt ?? new Date().toISOString(),
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
    complete: (taskId: string) =>
      request<any>(`/tasks/${taskId}/complete`, { method: 'POST' }),
    checkin: (formData: FormData) =>
      request<{ photoUrl: string; recognized: boolean }>('/tasks/checkin', { method: 'POST', body: formData }),
    getCheckinHistory: (childId?: string) =>
      request<any>(`/tasks/checkin/history${childId ? `?child_id=${childId}` : ''}`),
    create: (data: { title: string; type: string; description?: string; rewardPoints?: number; icon?: string; childId?: string }) => {
      const params = new URLSearchParams({ title: data.title, type: data.type })
      if (data.description) params.set('description', data.description)
      if (data.rewardPoints) params.set('reward_points', String(data.rewardPoints))
      if (data.icon) params.set('icon', data.icon)
      if (data.childId) params.set('child_id', data.childId)
      return request<any>(`/tasks/?${params}`, { method: 'POST' })
    },
    delete: (taskId: string) =>
      request<any>(`/tasks/${taskId}`, { method: 'DELETE' }),
  },

  habits: {
    getCurrent: () =>
      request<any>('/habits/current'),
    updateCurrent: (data: { title?: string; weekNumber?: number; gradeRange?: string; difficultyLevel?: number }) => {
      const params = new URLSearchParams()
      if (data.title) params.set('title', data.title)
      if (data.weekNumber) params.set('week_number', String(data.weekNumber))
      return request<any>(`/habits/current?${params}`, { method: 'PUT' })
    },
    create: (data: { title: string; weekNumber?: number; gradeRange?: string; difficultyLevel?: number }) => {
      const params = new URLSearchParams({ title: data.title })
      if (data.weekNumber) params.set('week_number', String(data.weekNumber))
      return request<any>(`/habits/?${params}`, { method: 'POST' })
    },
    getHistory: () =>
      request<any>('/habits/history'),
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
    getAnalysis: (childId?: string) =>
      request<any>(`/mistakes/analysis${childId ? `?child_id=${childId}` : ''}`),
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
    getLossStats: (childId?: string) =>
      request<any>(`/items/stats${childId ? `?child_id=${childId}` : ''}`),
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
    getBalance: () =>
      request<{ balance: number }>('/points/balance'),
    getHistory: () =>
      request<any>('/points/history'),
    redeem: (rewardItemId: string) =>
      request<{ success: boolean; pointsSpent: number; itemName: string }>(`/points/redeem?reward_item_id=${rewardItemId}`, { method: 'POST' }),
    getRewards: () =>
      request<any>('/points/rewards'),
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
  },

  badges: {
    list: () =>
      request<any>('/badges/'),
    unlock: (badgeId: string) =>
      request<any>(`/badges/${badgeId}/unlock`, { method: 'POST' }),
  },

  covenants: {
    list: () =>
      request<any>('/covenants/'),
    create: (data: { goal: string; reward: string; rewardType?: string; childId?: string }) => {
      const params = new URLSearchParams({ goal: data.goal, reward: data.reward })
      if (data.rewardType) params.set('reward_type', data.rewardType)
      if (data.childId) params.set('child_id', data.childId)
      return request<any>(`/covenants/?${params}`, { method: 'POST' })
    },
  },

  growth: {
    triggerAssessment: (childId?: string) =>
      request<any>(`/growth/assessment${childId ? `?child_id=${childId}` : ''}`, { method: 'POST' }),
    getTrend: (childId?: string) =>
      request<any>(`/growth/trend${childId ? `?child_id=${childId}` : ''}`),
    getReport: (childId?: string) =>
      request<any>(`/growth/report${childId ? `?child_id=${childId}` : ''}`),
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
      if (data.difficultyLevel !== undefined) params.set('difficulty_level', String(data.difficultyLevel))
      if (data.dailyReminder !== undefined) params.set('daily_reminder', String(data.dailyReminder))
      if (data.achievementNotification !== undefined) params.set('achievement_notification', String(data.achievementNotification))
      if (data.weeklyReport !== undefined) params.set('weekly_report', String(data.weeklyReport))
      if (data.schoolSync !== undefined) params.set('school_sync', String(data.schoolSync))
      return request<any>(`/parent/settings?${params}`, { method: 'PUT' })
    },
  },

  community: {
    getPosts: (page: number) =>
      request<any>(`/community/posts?page=${page}`),
    createPost: (data: { title: string; content: string; tags: string[] }) => {
      const params = new URLSearchParams({ title: data.title, content: data.content })
      return request<any>(`/community/posts?${params}`, { method: 'POST' })
    },
  },

  articles: {
    list: (category?: string) =>
      request<any>(`/articles${category ? `?category=${category}` : ''}`),
    getSuggested: () =>
      request<any>('/articles/suggested'),
  },
}
