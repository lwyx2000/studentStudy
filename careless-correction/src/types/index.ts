export interface UserProfile {
  id: string
  name: string
  loginName?: string
  grade: number
  avatarUrl: string
  role: 'child' | 'parent'
  parentId?: string
  sunlightPoints?: number
  streakDays?: number
  isOnboarded?: boolean
}

export interface ExecutiveFunctionAssessment {
  focusAttention: number
  organization: number
  emotionalControl: number
  planning: number
  impulseControl: number
  recommendedLevel: number
  taskDensity?: 'low' | 'medium' | 'high'
  source?: 'initial' | 'dynamic'
}

export type TaskCategory = 'morning_routine' | 'study_habit' | 'life_skill' | 'exercise' | 'reflection'

export interface SubTaskItem {
  id: string
  title: string
  type?: TaskCategory
  weekDay?: 'weekday' | 'weekend' | string
  sortOrder: number
}

export interface TaskItem {
  id: string
  title: string
  description: string
  type: TaskCategory
  status: 'pending' | 'completed' | 'skipped'
  rewardPoints: number
  icon: string
  weekDay?: string
  assignedDate?: string
  completedAt?: string
  completionPhotoUrl?: string
  habitSopId?: string
  subTasks?: SubTaskItem[]
}

export interface MistakeRecord {
  id: string
  subject: string
  imageUrl: string
  subjectTag?: string
  createdAt: string
  isCarelessness?: boolean
  category?: MistakeCategory
  knowledgePoint?: string
  recognizedText?: string
  grade?: number
  curriculumChapter?: string
  reviewStrategy?: '3day-repeat' | 'weekly-review' | 'monthly-check'
  nextReviewAt?: string
  reviewCount?: number
  resolved?: boolean
}

export type MistakeCategory =
  | 'symbol_error'
  | 'unit_missing'
  | 'misread_details'
  | 'copying_error'
  | 'skipped_step'
  | 'rushing'
  | 'lost_focus'
  | 'messy_writing'
  | 'format_error'
  | 'spelling_slip'
  | 'wild_guess'
  | 'something_else'

export const MISTAKE_CATEGORY_LABELS: Record<MistakeCategory, string> = {
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
  something_else: '其他',
}

export interface ItemStorageRecord {
  id: string
  itemName: string
  storageLocation: string
  storageDate: string
  notes?: string
}

export interface ItemLossRecord {
  id: string
  itemName: string
  lostLocation: string
  lostDate: string
  estimatedCost: number
  frequency: number
}

export interface GrowthDataPoint {
  date: string
  mistakeRate: number
  itemLossRate: number
  taskCompletionRate: number
  focusScore?: number
  neatnessScore?: number
  metacognitionScore?: number
  emotionScore?: number
  source?: 'daily' | 'weekly' | 'monthly'
}

export interface BadgeItem {
  id: string
  name: string
  description: string
  icon: string
  color: string
  unlocked: boolean
  unlockedAt?: string
  requirement: string
}

export interface FamilyCovenant {
  id: string
  goal: string
  reward: string
  childSignature: string
  parentSignature: string
  createdAt: string
  status: 'active' | 'completed' | 'expired'
  rewardType?: 'experience' | 'material' | 'custom'
  nudgeMessage?: string
  completedAt?: string
}

export interface DiagnosticAlert {
  id: string
  title: string
  description: string
  suggestion: string
  severity: 'info' | 'warning' | 'positive'
  createdAt: string
  relatedMetric?: string
  metricChange?: number
  isRead?: boolean
}

export interface ParentSettings {
  difficultyLevel: number
  dailyReminder: boolean
  achievementNotification: boolean
  weeklyReport: boolean
  schoolSync: boolean
  schoolSyncCode?: string
}

export interface HabitSOP {
  id: string
  title: string
  steps: SOPStep[]
  weekNumber: number
}

export interface SOPStep {
  order: number
  instruction: string
  imageUrl?: string
  gifUrl?: string
}

export interface DiscussionPost {
  id: string
  title: string
  content: string
  author: string
  tags: string[]
  replyCount: number
  hasExpertAnswer: boolean
  createdAt: string
}

export interface SunlightRecord {
  id: string
  amount: number
  reason: string
  type: 'earn' | 'spend'
  timestamp: string
}

export interface RewardItem {
  id: string
  name: string
  description: string
  cost: number
  icon: string
  active: boolean
}

export interface LlmConfig {
  endpoint: string
  apiKey: string
  model: string
  mistakePrompt: string
  assessmentPrompt: string
  assessmentCron: 'daily' | 'weekly' | 'monthly'
  enabled: boolean
}

export interface ArticleResource {
  id: string
  title: string
  summary: string
  contentUrl?: string
  category: string
  type: 'article' | 'video' | 'cbt'
  readingTime: number
  readingTimeMinutes?: number
  imageUrl: string
  author?: string
  publishedAt?: string
  bookmarked: boolean
}