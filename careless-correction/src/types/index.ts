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

export interface TaskItem {
  id: string
  title: string
  description: string
  type: 'habit' | 'game' | 'organization'
  status: 'pending' | 'completed' | 'skipped'
  rewardPoints: number
  icon: string
}

export interface MistakeRecord {
  id: string
  subject: string
  imageUrl: string
  isCarelessness: boolean
  category?: MistakeCategory
  knowledgePoint?: string
  createdAt: string
  reviewScheduledAt: string
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

export interface PomodoroSession {
  id: string
  estimatedMinutes: number
  actualMinutes: number
  subject: string
  uncertainQuestions: number
  timeDrainReason?: string
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

export interface HabitAssignment {
  id: string
  childId: string
  parentId: string
  title: string
  description: string
  icon: string
  rewardPoints: number
  weekNumber: number
  steps: SOPStep[]
  assignedAt: string
  active: boolean
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

// ==================
// 藏宝库 (题库) 类型
// ==================

export type QuestionSubject = 'math' | 'chinese' | 'english' | 'science' | 'other'
export type QuestionType = 'choice' | 'fill' | 'calculation' | 'composition' | 'other'

export interface QuestionItem {
  id: string
  subject: QuestionSubject
  type: QuestionType
  content: string           // 题目正文
  answer?: string           // 参考答案
  imageUrl?: string         // 题目图片
  grade: number             // 适用年级 1-6
  chapter?: string          // 教材章节
  knowledgePoints: string[] // 知识点标签
  difficulty: 1 | 2 | 3 | 4 | 5  // 难度
  tags: string[]            // 自定义标签
  isCarelessness?: boolean  // 是否粗心型
  mistakeCategory?: MistakeCategory // 粗心分类
  reviewCount: number       // 已复习次数
  resolved: boolean         // 是否已解决
  source: 'manual' | 'photo' | 'import' // 来源
  importId?: string         // 关联导入批次
  createdAt: string
  updatedAt: string
}

export interface QuestionBankImport {
  id: string
  fileName: string
  totalCount: number
  importedCount: number
  failedCount: number
  status: 'pending' | 'success' | 'partial' | 'failed'
  errors: string[]
  importedAt: string
}

/** 标准题库导入JSON格式 v1.0 */
export interface QuestionBankExportFormat {
  version: '1.0'
  exportedAt: string
  schoolInfo?: { name?: string; grade?: number }
  questions: QuestionBankExportItem[]
}

export interface QuestionBankExportItem {
  subject: QuestionSubject
  type: QuestionType
  content: string           // 必填
  answer?: string
  grade?: number
  chapter?: string
  knowledgePoints?: string[]
  difficulty?: number
  tags?: string[]
}

export interface WeaknessChartData {
  bySubject: { subject: string; count: number; color: string }[]
  byCategory: { category: string; count: number }[]
  byKnowledgePoint: { point: string; count: number }[]
  byDifficulty: { level: number; label: string; count: number }[]
}

export interface PrintSelection {
  questionIds: string[]
  mode: 'manual' | 'ai'
  title?: string
  includeAnswer: boolean
}