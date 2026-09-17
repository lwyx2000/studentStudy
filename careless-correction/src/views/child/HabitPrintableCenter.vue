<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGrowthStore, useParentStore, useTaskStore, useUserStore } from '../../stores'
import { api, normalizeSubTask } from '../../utils/api'
import { matchesToday, weekDayToLabel } from '../../utils/constants'
import type { TaskCategory } from '../../types'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()
const userStore = useUserStore()
const parentStore = useParentStore()
const growthStore = useGrowthStore()

const loading = ref(true)

// ── Date: support query param for editing past records ──
const todayStr = new Date().toLocaleDateString('zh-CN')
const queryDate = route.query.date as string | undefined
const activeDate = queryDate || todayStr
const isToday = activeDate === todayStr
const isEditing = !isToday

// ── Daily check state (localStorage, keyed by date) ──
const activeDateObj = queryDate ? new Date(queryDate.replace(/-/g, '/')) : new Date()

const checkStateKey = `cc-checklist-${activeDate}`

function loadCheckState(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(checkStateKey)
    return raw ? JSON.parse(raw) : {}
  } catch { return {} }
}

const checkState = ref<Record<string, boolean>>(loadCheckState())

function saveCheckState() {
  localStorage.setItem(checkStateKey, JSON.stringify(checkState.value))
}

// ── Merge today's tasks with parent task templates ──
const allTasks = computed(() => {
  const parentTasks = parentStore.parentTaskTemplates.map(t => ({
    ...t,
    status: 'pending' as const,
  }))
  const seen = new Set(taskStore.todayTasks.map(t => t.id))
  const merged = [...taskStore.todayTasks]
  for (const pt of parentTasks) {
    if (!seen.has(pt.id)) {
      merged.push(pt)
      seen.add(pt.id)
    }
  }
  return merged
})

// ── Optional sub-task bonus: 可选子任务不完成不影响审核，完成则加分 ──
const OPTIONAL_BONUS_POINTS = 2
// ── 全部完成奖励：当天所有必做小任务都完成后额外奖励 ──
const ALL_DONE_BONUS_POINTS = 10

// ── Build checklist items from subtasks ──
interface ChecklistItem {
  id: string
  title: string
  icon: string
  description: string
  type?: string
  weekDay?: string
  parentTaskId: string
  parentTaskTitle: string
  rewardPoints: number
  isOptional?: boolean
  /** 子任务独立阳光值；未设置时必做默认继承主任务分值，可选⭐默认 +2 */
  subRewardPoints?: number
}

const checklistItems = ref<ChecklistItem[]>([])

async function loadChecklistItems() {
  const tasks = allTasks.value
  const items: ChecklistItem[] = []

  // 构建习惯计分项（按今天匹配的习惯）
  const hItems: HabitChecklistItem[] = []
  for (const h of taskStore.habits) {
    for (const step of h.steps ?? []) {
      hItems.push({
        habitId: h.id,
        habitTitle: h.title,
        stepOrder: step.order,
        instruction: step.instruction,
        pointsPerStep: h.rewardPoints ?? 0,
      })
    }
  }
  habitItems.value = hItems

  await Promise.allSettled(tasks.map(async (task) => {
    let subTasks = task.subTasks || []

    // Load subtasks from backend if task has numeric ID
    if (/^\d+$/.test(task.id)) {
      try {
        const res = await api.tasks.getTask(task.id)
        if (res?.sub_tasks?.length) {
          subTasks = res.sub_tasks.map(normalizeSubTask)
          // Update parent store cache
          const tpl = parentStore.parentTaskTemplates.find(t => t.id === task.id)
          if (tpl) {
            tpl.subTasks = [...subTasks]
            parentStore.updateTaskTemplate(task.id, { subTasks: [...subTasks] })
          }
        }
      } catch { /* offline */ }
    }

    for (const sub of subTasks) {
      // Only show sub-tasks that match today's (or selected date's) day of week
      if (!matchesToday(sub.weekDay, activeDateObj)) continue

      items.push({
        id: sub.id,
        title: sub.title,
        icon: task.icon,
        description: `属于：${task.title}`,
        type: sub.type,
        weekDay: sub.weekDay,
        parentTaskId: task.id,
        parentTaskTitle: task.title,
        rewardPoints: task.rewardPoints,
        isOptional: sub.isOptional,
        subRewardPoints: sub.rewardPoints,
      })
    }
  }))

  checklistItems.value = items
}

// ── Submitted state (persists in localStorage) ──
const submittedKey = `cc-checklist-submitted-${activeDate}`
const submitted = ref<boolean>(localStorage.getItem(submittedKey) === 'true')
const submitting = ref(false)
const submitMessage = ref('')

// ── 打卡审批状态（从后端拉取，展示驳回原因/通过横幅）──
interface CheckinStatusInfo {
  id: number
  status: 'pending' | 'approved' | 'rejected'
  rejectReason: string | null
}
const checkinStatus = ref<CheckinStatusInfo | null>(null)

async function loadCheckinStatus() {
  if (!/^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/.test(activeDate)) return
  try {
    const res = await api.checkins.getMine(60)
    const normalized = activeDate.replace(/\//g, '-')
    const match = (res.checkins ?? []).find((c: any) => {
      const d = String(c.checkDate ?? '').replace(/\//g, '-')
      const parts = d.split('-')
      // 归一化比较：补零到两位
      if (parts.length === 3) {
        const key = `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`
        return key === normalized
      }
      return d === normalized
    })
    if (match) {
      checkinStatus.value = {
        id: match.id,
        status: match.status,
        rejectReason: match.rejectReason ?? null,
      }
    }
  } catch { /* offline */ }
}

// ── Toggle handlers ──
// 允许今日多次提交：提交后仍可勾选新任务再次提交
function toggleTaskItem(item: ChecklistItem) {
  const key = `task-${item.id}`
  checkState.value[key] = !checkState.value[key]
  saveCheckState()
}

function isTaskItemChecked(itemId: string): boolean {
  return !!checkState.value[`task-${itemId}`]
}

// ── Submit: sync checked tasks to backend & award points ──
const checkedTaskItems = computed(() =>
  checklistItems.value.filter(item => isTaskItemChecked(item.id))
)
// 必做项（可选子任务不算必做）
const requiredItems = computed(() => checklistItems.value.filter(item => !item.isOptional))
const checkedRequiredItems = computed(() => requiredItems.value.filter(item => isTaskItemChecked(item.id)))
// 已完成的可选子任务（加分项）
const checkedOptionalItems = computed(() =>
  checklistItems.value.filter(item => item.isOptional && isTaskItemChecked(item.id))
)
const optionalBonusPoints = computed(() => checkedOptionalItems.value.length * OPTIONAL_BONUS_POINTS)

/** 小任务分值：家长单独设置的优先，否则可选⭐默认 +2，必做默认继承主任务分值 */
function itemPoints(item: ChecklistItem): number {
  if (item.subRewardPoints !== undefined && item.subRewardPoints !== null) return item.subRewardPoints
  return item.isOptional ? OPTIONAL_BONUS_POINTS : item.rewardPoints
}
/** 已勾选必做小任务的总分（每项独立计分） */
const checkedRequiredPoints = computed(() =>
  checkedRequiredItems.value.reduce((sum, item) => sum + itemPoints(item), 0)
)
/** 是否所有必做小任务都已完成（触发全部完成奖励） */
const allRequiredDone = computed(() =>
  requiredItems.value.length > 0 && checkedRequiredItems.value.length === requiredItems.value.length
)

async function submitChecklist() {
  if (submitted.value || submitting.value) return
  if (checkedRequiredItems.value.length === 0) {
    submitMessage.value = '请先勾选至少一项必做任务再提交（可选 ⭐ 项不完成也没关系）'
    return
  }
  submitting.value = true
  submitMessage.value = ''

  let totalPoints = 0
  const completedTaskTitles: string[] = []

  // 标记主任务完成（同步到后端）并统计完成任务数，分数改由子任务独立计分
  const completedParentTasks = new Set<string>()
  for (const item of checkedTaskItems.value) {
    if (completedParentTasks.has(item.parentTaskId)) continue
    completedParentTasks.add(item.parentTaskId)
    taskStore.completeTask(item.parentTaskId)
    completedTaskTitles.push(item.parentTaskTitle)
  }

  // 每个必做小任务按各自分值独立计分
  totalPoints += checkedRequiredPoints.value

  // 可选子任务加分项
  totalPoints += optionalBonusPoints.value

  // 全部完成奖励：所有必做小任务都完成时额外 +10
  if (allRequiredDone.value) {
    totalPoints += ALL_DONE_BONUS_POINTS
  }

  // 习惯步骤计分（勾选的习惯步骤 × 各习惯分值）
  totalPoints += habitPoints.value

  // Record growth data
  const done = taskStore.todayTasks.filter(t => t.status === 'completed').length
  growthStore.recordDataPoint({ taskCompletionRate: done / Math.max(taskStore.todayTasks.length, 1) })

  // Submit check-in to backend for parent approval
  submitted.value = true
  submitting.value = false
  localStorage.setItem(submittedKey, 'true')
  localStorage.setItem(`cc-checklist-points-${activeDate}`, String(totalPoints))

  if (totalPoints > 0) {
    api.checkins.submit({
      checkDate: activeDate,
      totalPoints,
      habitStepCount: checkedHabitSteps.value.length,
      taskCount: completedTaskTitles.length,
      requiredPoints: checkedRequiredPoints.value,
      optionalBonus: optionalBonusPoints.value,
      allDoneBonus: allRequiredDone.value ? ALL_DONE_BONUS_POINTS : 0,
      habitPoints: habitPoints.value,
      completedTasks: checkedTaskItems.value.map(item => ({
        title: item.title,
        icon: item.icon,
        points: itemPoints(item),
      })),
    }).then(() => {
      const extras: string[] = []
      if (allRequiredDone.value) extras.push(`全部完成奖励 +${ALL_DONE_BONUS_POINTS}`)
      if (optionalBonusPoints.value > 0) extras.push(`可选 ⭐ 加分 +${optionalBonusPoints.value}`)
      if (habitPoints.value > 0) extras.push(`习惯打卡 +${habitPoints.value}`)
      const extraText = extras.length ? `（含 ${extras.join(' · ')}）` : ''
      submitMessage.value = `已提交打卡，等待家长审批 🕐 ${extraText}通过后将获得 ${totalPoints} 阳光值`
    }).catch(() => {
      submitMessage.value = `打卡已记录！等待家长审批后获得 ${totalPoints} 阳光值 🕐`
    })
  } else {
    submitMessage.value = '继续保持！'
  }
}

// ── 习惯计分：勾选完成的习惯步骤按各习惯分值计分 ──
interface HabitChecklistItem {
  habitId: string
  habitTitle: string
  stepOrder: number
  instruction: string
  pointsPerStep: number
}
const habitItems = ref<HabitChecklistItem[]>([])
const checkedHabitSteps = computed(() =>
  habitItems.value.filter(h => !!checkState.value[`habit-${h.habitId}-${h.stepOrder}`])
)
const habitPoints = computed(() =>
  checkedHabitSteps.value.reduce((sum, h) => sum + h.pointsPerStep, 0)
)

function toggleHabitItem(h: HabitChecklistItem) {
  const key = `habit-${h.habitId}-${h.stepOrder}`
  checkState.value[key] = !checkState.value[key]
  saveCheckState()
}

// ── Progress ──
const totalCount = computed(() => requiredItems.value.length)
const completedCount = computed(() => checkedRequiredItems.value.length)
const totalPossiblePoints = computed(() =>
  checklistItems.value.reduce((sum, item) =>
    sum + (isTaskItemChecked(item.id) ? itemPoints(item) : 0), 0
  )
)
const progressPercent = computed(() =>
  Math.round((completedCount.value / Math.max(totalCount.value, 1)) * 100)
)

// ── Group items by parent task ──
interface TaskGroup {
  taskId: string
  taskTitle: string
  taskIcon: string
  items: ChecklistItem[]
  allChecked: boolean
  someChecked: boolean
  taskReward: number
}

const taskGroups = computed<TaskGroup[]>(() => {
  const map = new Map<string, ChecklistItem[]>()
  for (const item of checklistItems.value) {
    const key = item.parentTaskId
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(item)
  }
  return Array.from(map.entries()).map(([taskId, items]) => {
    const first = items[0]
    // 必做项决定任务完成状态；可选 ⭐ 项只算加分
    const required = items.filter(i => !i.isOptional)
    const checkedRequiredCount = required.filter(i => isTaskItemChecked(i.id)).length
    const anyChecked = items.some(i => isTaskItemChecked(i.id))
    return {
      taskId,
      taskTitle: first.parentTaskTitle,
      taskIcon: first.icon,
      items,
      allChecked: required.length > 0 && checkedRequiredCount === required.length,
      someChecked: checkedRequiredCount < required.length && anyChecked,
      taskReward: first.rewardPoints,
    }
  })
})

function toggleTaskGroup(group: TaskGroup) {
  const newState = !group.allChecked
  for (const item of group.items) {
    const key = `task-${item.id}`
    checkState.value[key] = newState
  }
  saveCheckState()
}

// ── Category helpers ──
const categoryOptions: { value: TaskCategory; label: string }[] = [
  { value: 'morning_routine', label: '晨间惯例' },
  { value: 'study_habit', label: '学习习惯' },
  { value: 'life_skill', label: '生活技能' },
  { value: 'exercise', label: '运动' },
  { value: 'reflection', label: '反思' },
]

const userName = computed(() => userStore.profile.name || '我的')

function resetTodayChecklist() {
  checkState.value = {}
  submitted.value = false
  submitMessage.value = ''
  saveCheckState()
  localStorage.removeItem(submittedKey)
  localStorage.removeItem(`cc-checklist-points-${activeDate}`)
}

function backToDashboard() {
  router.push('/dashboard')
}

onMounted(async () => {
  loading.value = true
  await Promise.allSettled([
    loadChecklistItems(),
    userStore.fetchFromApi(),
    loadCheckinStatus(),
  ])
  loading.value = false
})
</script>

<template>
  <div class="page checklist-page">
    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <button v-if="isEditing" class="btn ghost back-btn" @click="backToDashboard">← 返回打卡历史</button>
        <span class="eyebrow">{{ isEditing ? '✏️ 编辑打卡记录' : '✅ 每日打卡' }}</span>
        <h1>{{ isEditing ? `${activeDate} 打卡清单` : '今日打卡清单' }}</h1>
        <p class="lead">{{ isEditing ? '查看和修改历史打卡记录，修改后自动保存。' : '完成子任务后，点击对应的方框打勾即可。坚持每天打卡，积攒阳光值！' }}</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>{{ isEditing ? '打卡进度' : '今日进度' }}</h2>
          <span class="tag">{{ completedCount }}/{{ totalCount }}</span>
        </div>
        <div class="progress">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>
        <p class="lead" style="margin-top:8px">
          ☀️ {{ userStore.sunlightPoints }} 阳光值
          <span class="muted" style="font-size:13px;font-weight:700">
            · 已勾选可获 +{{ totalPossiblePoints || 0 }} 阳光值
            <template v-if="checkedOptionalItems.length">
              · ⭐ 加分 {{ checkedOptionalItems.length }} 项 +{{ optionalBonusPoints }}
            </template>
            <template v-if="allRequiredDone">
              · 🎉 全部完成 +{{ ALL_DONE_BONUS_POINTS }}
            </template>
          </span>
        </p>
        <p class="muted" style="font-size:12px;margin-top:2px">
          💡 完成每个小任务获得各自阳光值；<template v-if="checklistItems.some(i => i.isOptional)">带 ⭐ 的是可选加分项，不完成不影响审核；</template>所有必做小任务全部完成，额外奖励 +{{ ALL_DONE_BONUS_POINTS }} 阳光值
        </p>
        <p v-if="submitMessage && submitted" class="lead" style="font-size:14px;color:var(--primary);margin-top:4px">
          {{ submitMessage }}
        </p>
        <!-- 审批状态横幅 -->
        <div v-if="checkinStatus?.status === 'approved'" class="status-banner status-approved-banner">
          ✅ 家长已通过 {{ activeDate }} 的打卡，去阳光树收集阳光吧！
        </div>
        <div v-else-if="checkinStatus?.status === 'rejected'" class="status-banner status-rejected-banner">
          ❌ {{ activeDate }} 的打卡被驳回<template v-if="checkinStatus.rejectReason">：{{ checkinStatus.rejectReason }}</template><template v-else>，可以补充完成后重新提交打卡</template>
        </div>
        <div v-else-if="checkinStatus?.status === 'pending'" class="status-banner status-pending-banner">
          🕐 {{ activeDate }} 的打卡等待家长审批中
        </div>
      </div>
    </section>

    <!-- Loading -->
    <div v-if="loading" class="panel" style="text-align:center;padding:48px">
      <p style="font-size:18px;font-weight:700;color:var(--muted)">⏳ 正在加载打卡数据...</p>
    </div>

    <!-- Checklist Sheet (same style as print preview) -->
    <template v-else>
      <div class="print-sheet">
        <div class="print-header">
          <h1>{{ userName }} 的每日打卡清单</h1>
          <p class="print-date">{{ activeDate }}</p>
        </div>

        <!-- Tasks Section (grouped by parent task) -->
        <div class="print-section">
          <h2>📋 每日任务清单</h2>
          <div v-if="taskGroups.length" class="task-groups">
            <div v-for="group in taskGroups" :key="group.taskId" class="task-group">
              <!-- Task header → tap to toggle all -->
              <div
                class="task-group-header clickable"
                :class="{
                  'group-all-checked': group.allChecked,
                  'group-some-checked': group.someChecked,
                }"
                @click="toggleTaskGroup(group)"
              >
                <span class="tgh-icon">{{ group.taskIcon }}</span>
                <div class="tgh-info">
                  <strong>{{ group.taskTitle }}</strong>
                  <span class="tgh-progress">
                    <span v-if="group.allChecked">✅ 全部完成</span>
                    <span v-else-if="group.someChecked">⏳ 部分完成</span>
                    <span v-else>⬜ 待打卡</span>
                    · {{ group.items.filter(i => isTaskItemChecked(i.id)).length }}/{{ group.items.length }}
                  </span>
                </div>
                <span class="tgh-check-all">☀️ +{{ group.taskReward }}</span>
              </div>

              <!-- Sub-items under this task -->
              <div class="task-subitems">
                <div
                  v-for="item in group.items"
                  :key="item.id"
                  class="ptr-row clickable"
                  :class="{ 'row-checked': isTaskItemChecked(item.id) }"
                  @click="toggleTaskItem(item)"
                >
                  <div class="ptr-info">
                    <strong>{{ item.title }}</strong>
                    <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
                      <span v-if="item.type" class="ptr-sub-badge">{{ categoryOptions.find(c => c.value === item.type)?.label || item.type }}</span>
                      <span v-if="item.weekDay" class="ptr-sub-badge ptr-sub-day">{{ weekDayToLabel(item.weekDay) }}</span>
                      <span class="ptr-sub-badge ptr-sub-points">☀️ +{{ itemPoints(item) }}</span>
                      <span
                        v-if="item.isOptional"
                        class="ptr-sub-badge"
                        style="background:#fff8d9;color:#8a6d3b;font-weight:800"
                      >⭐ 可选</span>
                    </div>
                  </div>
                  <span class="ptr-check touch-check" :class="{ checked: isTaskItemChecked(item.id) }">
                    {{ isTaskItemChecked(item.id) ? '✓' : '□' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <p v-else class="muted">暂无任务子项，请先在家长端「任务管理」中添加子任务。</p>
        </div>

        <!-- 习惯打卡计分区 -->
        <div v-if="habitItems.length" class="print-section">
          <h3>🌱 习惯打卡（每完成一步得阳光值）</h3>
          <div class="task-subitems">
            <div
              v-for="h in habitItems"
              :key="`${h.habitId}-${h.stepOrder}`"
              class="ptr-row clickable"
              :class="{ 'row-checked': !!checkState[`habit-${h.habitId}-${h.stepOrder}`] }"
              @click="toggleHabitItem(h)"
            >
              <div class="ptr-info">
                <strong>{{ h.habitTitle }} · 第 {{ h.stepOrder }} 步</strong>
                <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
                  <span class="ptr-sub-badge">{{ h.instruction }}</span>
                  <span class="ptr-sub-badge ptr-sub-points">☀️ +{{ h.pointsPerStep }}</span>
                </div>
              </div>
              <span class="ptr-check touch-check" :class="{ checked: !!checkState[`habit-${h.habitId}-${h.stepOrder}`] }">
                {{ checkState[`habit-${h.habitId}-${h.stepOrder}`] ? '✓' : '□' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Submit Section (only for today) -->
        <div v-if="isToday" class="submit-section">
          <div v-if="submitMessage" class="submit-message" :class="{ 'submit-error': !submitted }">
            {{ submitMessage }}
          </div>
          <button
            v-if="!submitted"
            class="btn submit-btn"
            :disabled="submitting || completedCount === 0"
            @click="submitChecklist"
          >
            {{ submitting ? '⏳ 提交中...' : `✅ 提交打卡（必做 ${checkedRequiredItems.length}/${totalCount}${checkedOptionalItems.length ? ` · ⭐ ${checkedOptionalItems.length}` : ''}${checkedHabitSteps.length ? ` · 🌱 ${checkedHabitSteps.length} 步` : ''}）` }}
          </button>
          <div v-else class="submitted-badge">
            <span>✅ 今日已打卡</span>
            <button class="btn ghost reset-btn" @click="resetTodayChecklist">重置今日打卡</button>
          </div>
        </div>

        <!-- Edit mode notice (for past dates) -->
        <div v-else class="edit-mode-notice">
          <span>📋 正在回看 {{ activeDate }} 的打卡清单（勾选状态仅保存在本设备，提交记录以家长审批结果为准）</span>
          <button class="btn ghost" @click="backToDashboard">返回历史</button>
        </div>

        <div class="print-footer">
          <p>{{ isToday ? '每天完成后打 ✓，点击提交即可同步打卡记录' : '此页为历史记录回看，勾选不会修改已提交的打卡' }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.checklist-page {
  width: 100%;
}

/* ── Print Sheet (same as parent print preview) ── */
.print-sheet {
  background: #fff;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.06);
  border: 1px solid #eee;
}

.print-header {
  text-align: center;
  border-bottom: 3px solid var(--primary);
  padding-bottom: 18px;
  margin-bottom: 24px;
}
.print-header h1 {
  font-size: 30px;
  font-weight: 800;
  color: var(--primary);
  margin: 0 0 6px;
}
.print-date {
  color: var(--muted);
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.print-section {
  margin-bottom: 24px;
}
.print-section h2 {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Task Groups ── */
.task-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-group {
  background: #fafcfa;
  border-radius: 18px;
  border: 1.5px solid #d4e8d0;
  overflow: hidden;
}

.task-group-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #f0f9ee;
  border-bottom: 1px solid #d4e8d0;
  cursor: pointer;
  transition: background .12s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  min-height: 56px;
}

.task-group-header:active {
  background: #ddf0d8;
}

.task-group-header.group-all-checked {
  background: #e8f5e0;
}
.task-group-header.group-some-checked {
  background: #f5fce8;
}

.tgh-icon {
  font-size: 30px;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  background: #fff;
  border-radius: 14px;
}

.tgh-info {
  flex: 1;
  min-width: 0;
}
.tgh-info strong {
  display: block;
  font-size: 20px;
  font-weight: 800;
}
.tgh-progress {
  font-size: 14px;
  font-weight: 700;
  color: #666;
  margin-top: 2px;
  display: block;
}

.tgh-check-all {
  font-size: 15px;
  font-weight: 800;
  color: #2e7d32;
  background: #fff;
  padding: 8px 14px;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
}

.task-subitems {
  padding: 4px 0;
}

.ptr-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-bottom: 1px solid #e8ede8;
  min-height: 52px;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}
.ptr-row:last-child {
  border-bottom: none;
}
.ptr-check {
  font-size: 38px;
  line-height: 1;
  color: #111;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #fff;
  border: 2px solid #d4d8d4;
  transition: all .12s ease;
}
.touch-check {
  font-size: 28px;
}
.ptr-check.checked {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.ptr-info {
  flex: 1;
  min-width: 0;
}
.ptr-info strong {
  display: block;
  font-size: 18px;
  font-weight: 800;
}
.ptr-sub-badge {
  font-size: 13px;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 700;
  display: inline-block;
}
.ptr-sub-day {
  background: #fff3e0;
  color: #e65100;
}
.ptr-sub-points {
  background: #fff9e0;
  color: #a67c00;
}

/* ── Interactive styles ── */
.clickable {
  cursor: pointer;
  transition: background .12s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
.clickable:hover {
  background: #f5fdf0;
}
.clickable:active {
  background: #e4f5dc;
}
.row-checked {
  background: #f0f9e8;
}
.row-checked .ptr-info strong {
  text-decoration: line-through;
  opacity: .5;
}

/* ── Tablet / Touch ── */
@media (hover: none) and (pointer: coarse) {
  .task-group-header {
    padding: 20px 24px;
    min-height: 64px;
  }
  .ptr-row {
    padding: 18px 24px;
    min-height: 60px;
  }
  .ptr-check {
    width: 48px;
    height: 48px;
    font-size: 42px;
  }
  .touch-check {
    font-size: 30px;
  }
  .ptr-info strong {
    font-size: 20px;
  }
  .tgh-icon {
    width: 52px;
    height: 52px;
    font-size: 32px;
  }
  .submit-btn {
    padding: 20px;
    font-size: 20px;
    min-height: 60px;
  }
  .tgh-check-all {
    padding: 10px 18px;
    font-size: 17px;
  }
  .print-sheet {
    padding: 24px 18px;
  }
}

.print-footer {
  text-align: center;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 14px;
  font-weight: 600;
}

/* ── Submit Section ── */
.submit-section {
  margin: 24px 0 8px;
  text-align: center;
}
.back-btn {
  margin-bottom: 12px;
  padding: 6px 14px;
  font-size: 14px;
}
.edit-mode-notice {
  margin: 24px 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 16px;
  border-radius: 14px;
  background: #e3f2fd;
  border: 2px solid #64b5f6;
}
.edit-mode-notice span {
  font-size: 16px;
  font-weight: 800;
  color: #1565c0;
}
.submit-btn {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  font-weight: 800;
  border-radius: 14px;
}
.submit-btn:disabled {
  opacity: .5;
  cursor: not-allowed;
}
.submit-message {
  padding: 12px 16px;
  margin-bottom: 12px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  background: #e8f5e9;
  color: #2e7d32;
}
.submit-message.submit-error {
  background: #fff3e0;
  color: #e65100;
}
.submitted-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 16px;
  border-radius: 14px;
  background: #e8f5e9;
  border: 2px solid var(--primary);
}
.submitted-badge span {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
}
.reset-btn {
  padding: 8px 16px;
  font-size: 14px;
}

/* ── 审批状态横幅 ── */
.status-banner {
  margin-top: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
}
.status-approved-banner {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}
.status-rejected-banner {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ef9a9a;
}
.status-pending-banner {
  background: #fff8e1;
  color: #b28704;
  border: 1px solid #ffe082;
}

@media (max-width: 700px) {
  .print-sheet { padding: 20px; }
  .print-header h1 { font-size: 24px; }
  .print-section h2 { font-size: 18px; }

}
</style>
