export interface UserProfile {
  id: string
  name: string
  grade: number
  avatarUrl: string
  role: 'child' | 'parent'
}

export interface ExecutiveFunctionAssessment {
  focusAttention: number
  organization: number
  emotionalControl: number
  planning: number
  impulseControl: number
  recommendedLevel: number
}

export type TaskCategory = 'morning_routine' | 'study_habit' | 'life_skill' | 'exercise' | 'reflection'

export interface TaskItem {
  id: string
  title: string
  description: string
  type: TaskCategory
  status: 'pending' | 'completed' | 'skipped'
  rewardPoints: number
  icon: string
}

export interface MistakeRecord {
  id: string
  subject: string
  imageUrl: string
  subjectTag?: string
  createdAt: string
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
}

export interface DiagnosticAlert {
  id: string
  title: string
  description: string
  suggestion: string
  severity: 'info' | 'warning' | 'positive'
  createdAt: string
}

export interface ParentSettings {
  difficultyLevel: number
  dailyReminder: boolean
  achievementNotification: boolean
  weeklyReport: boolean
  schoolSync: boolean
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
  category: string
  type: 'article' | 'video' | 'cbt'
  readingTime: number
  imageUrl: string
  bookmarked: boolean
}