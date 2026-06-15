import type { ArticleResource, BadgeItem, DiagnosticAlert, DiscussionPost, FamilyCovenant, GrowthDataPoint, HabitSOP, HabitAssignment, ItemLossRecord, MistakeRecord, ParentSettings, PomodoroSession, TaskItem, QuestionItem, QuestionBankImport, QuestionBankExportFormat, WeaknessChartData } from '../types'

const API_BASE = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options?.headers,
    },
  })
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}

export const api = {
  auth: {
    register: (data: { name: string; grade: number; role: string }) =>
      request<{ id: string }>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    login: (data: { name: string; role: string }) =>
      request<{ token: string }>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  },
  assessment: {
    submit: (data: { userId: string; focusAttention: number; organization: number; emotionalControl: number; planning: number; impulseControl: number }) =>
      request<{ recommendedLevel: number }>('/assessments', { method: 'POST', body: JSON.stringify(data) }),
    getResult: (userId: string) =>
      request<{ recommendedLevel: number }>(`/assessments/${userId}`),
  },
  tasks: {
    getToday: (userId: string) => request<TaskItem[]>(`/tasks/today/${userId}`),
    complete: (taskId: string) => request<{ points: number }>(`/tasks/${taskId}/complete`, { method: 'POST' }),
    getHabitSOP: (userId: string) => request<HabitSOP>(`/tasks/habit-sop/${userId}`),
  },
  habits: {
    list: (childId: string) => request<HabitAssignment[]>(`/habits/${childId}`),
    create: (data: Omit<HabitAssignment, 'id' | 'assignedAt'>) =>
      request<HabitAssignment>('/habits', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<HabitAssignment>) =>
      request<HabitAssignment>(`/habits/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    deactivate: (id: string) =>
      request<{ active: boolean }>(`/habits/${id}/deactivate`, { method: 'POST' }),
  },
  mistakes: {
    uploadImage: (formData: FormData) => request<{ imageUrl: string }>('/mistakes/upload', { method: 'POST', body: formData }),
    create: (data: { subject: string; imageUrl: string; isCarelessness: boolean; category?: string; knowledgePoint?: string }) =>
      request<MistakeRecord>('/mistakes', { method: 'POST', body: JSON.stringify(data) }),
    list: (userId: string) => request<MistakeRecord[]>(`/mistakes/${userId}`),
    getTodayReview: (userId: string) => request<number>(`/mistakes/today-review/${userId}`),
  },
  items: {
    reportLoss: (data: { itemName: string; lostLocation: string; estimatedCost?: number }) =>
      request<ItemLossRecord>('/items/loss', { method: 'POST', body: JSON.stringify(data) }),
    getLossList: (userId: string) => request<ItemLossRecord[]>(`/items/loss/${userId}`),
    getLossStats: (userId: string) => request<{ radarData: Record<string, number>; totalCost: number }>(`/items/stats/${userId}`),
    uploadBeforeAfter: (data: FormData) => request<{ points: number }>('/items/before-after', { method: 'POST', body: data }),
  },
  growth: {
    getTrend: (userId: string, period: string) => request<GrowthDataPoint[]>(`/growth/trend/${userId}?period=${period}`),
    getPeerComparison: (userId: string) => request<Record<string, number>>(`/growth/peer-comparison/${userId}`),
    getAlerts: (userId: string) => request<DiagnosticAlert[]>(`/growth/alerts/${userId}`),
    generateReport: (userId: string) => request<{ pdfUrl: string }>(`/growth/report/${userId}`, { method: 'POST' }),
  },
  badges: {
    list: (userId: string) => request<BadgeItem[]>(`/badges/${userId}`),
    unlock: (badgeId: string) => request<{ unlocked: boolean }>(`/badges/${badgeId}/unlock`, { method: 'POST' }),
  },
  covenants: {
    create: (data: { goal: string; reward: string; childSignature?: string; parentSignature?: string }) =>
      request<FamilyCovenant>('/covenants', { method: 'POST', body: JSON.stringify(data) }),
    list: (userId: string) => request<FamilyCovenant[]>(`/covenants/${userId}`),
  },
  pomodoro: {
    start: (data: { estimatedMinutes: number; subject: string }) =>
      request<{ sessionId: string }>('/pomodoro/start', { method: 'POST', body: JSON.stringify(data) }),
    finish: (sessionId: string, data: { actualMinutes: number; timeDrainReason?: string }) =>
      request<PomodoroSession>(`/pomodoro/${sessionId}/finish`, { method: 'POST', body: JSON.stringify(data) }),
    markUncertain: (sessionId: string) => request<{ count: number }>(`/pomodoro/${sessionId}/uncertain`, { method: 'POST' }),
    getHistory: (userId: string) => request<PomodoroSession[]>(`/pomodoro/history/${userId}`),
  },
  print: {
    generateChecklist: (userId: string) => request<{ pdfUrl: string }>(`/print/checklist/${userId}`, { method: 'POST' }),
    scanUpload: (formData: FormData) => request<{ recognized: boolean; checkedCount?: number; report?: string }>('/print/scan', { method: 'POST', body: formData }),
  },
  parent: {
    getSettings: (userId: string) => request<ParentSettings>(`/parent/settings/${userId}`),
    updateSettings: (userId: string, data: Partial<ParentSettings>) =>
      request<ParentSettings>(`/parent/settings/${userId}`, { method: 'PUT', body: JSON.stringify(data) }),
  },
  community: {
    getPosts: (page: number) => request<DiscussionPost[]>(`/community/posts?page=${page}`),
    createPost: (data: { title: string; content: string; tags: string[] }) =>
      request<DiscussionPost>('/community/posts', { method: 'POST', body: JSON.stringify(data) }),
    getSharedCovenants: () => request<FamilyCovenant[]>('/community/covenants'),
  },
  articles: {
    list: (category?: string) => request<ArticleResource[]>(`/articles${category ? `?category=${category}` : ''}`),
    getSuggested: (userId: string) => request<ArticleResource[]>(`/articles/suggested/${userId}`),
  },
  questions: {
    list: (userId: string, params?: { page?: number; pageSize?: number; subject?: string; resolved?: boolean; source?: string }) => {
      const q = new URLSearchParams()
      if (params?.page) q.set('page', String(params.page))
      if (params?.pageSize) q.set('pageSize', String(params.pageSize))
      if (params?.subject) q.set('subject', params.subject)
      if (params?.resolved !== undefined) q.set('resolved', String(params.resolved))
      if (params?.source) q.set('source', params.source)
      return request<{ total: number; list: QuestionItem[] }>(`/questions/${userId}?${q}`)
    },
    create: (data: Partial<QuestionItem>) =>
      request<QuestionItem>('/questions', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<QuestionItem>) =>
      request<QuestionItem>(`/questions/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) =>
      request<{ deleted: boolean }>(`/questions/${id}`, { method: 'DELETE' }),
    resolve: (id: string) =>
      request<{ resolved: boolean }>(`/questions/${id}/resolve`, { method: 'POST' }),
    review: (id: string) =>
      request<{ reviewCount: number }>(`/questions/${id}/review`, { method: 'POST' }),
    stats: (userId: string) =>
      request<{ totalCount: number; unresolvedCount: number; todayAddedCount: number }>(`/questions/stats/${userId}`),
    aiRecommend: (userId: string, data?: { maxCount?: number; subject?: string; difficultyMin?: number }) =>
      request<{ recommendedIds: string[]; reason: string }>(`/questions/ai-recommend/${userId}`, { method: 'POST', body: JSON.stringify(data || {}) }),
    print: (data: { questionIds: string[]; mode: 'manual' | 'ai'; title?: string; includeAnswer?: boolean }) =>
      request<{ pdfUrl: string; questionCount: number }>(`/questions/print`, { method: 'POST', body: JSON.stringify(data) }),
    importFile: (formData: FormData) =>
      request<QuestionBankImport>('/questions/import', { method: 'POST', body: formData }),
    export: (data?: { questionIds?: string[]; format?: string }) =>
      request<QuestionBankExportFormat>('/questions/export', { method: 'POST', body: JSON.stringify(data || {}) }),
    imports: (userId: string, page?: number) =>
      request<{ total: number; list: QuestionBankImport[] }>(`/questions/imports/${userId}?page=${page || 1}`),
    weakness: (userId: string) =>
      request<WeaknessChartData>(`/questions/weakness/${userId}`),
  },
}
