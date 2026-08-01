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
}

const checklistItems = ref<ChecklistItem[]>([])

async function loadChecklistItems() {
  const tasks = allTasks.value
  const items: ChecklistItem[] = []

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

// ── Toggle handlers ──
// For today: locked after submit. For past dates (editing): always editable.
function toggleTaskItem(item: ChecklistItem) {
  if (submitted.value && isToday) return
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

async function submitChecklist() {
  if (submitted.value || submitting.value) return
  if (completedCount.value === 0) {
    submitMessage.value = '请先勾选至少一项再提交'
    return
  }
  submitting.value = true
  submitMessage.value = ''

  let totalPoints = 0
  const completedTaskTitles: string[] = []

  for (const item of checkedTaskItems.value) {
    const points = taskStore.completeTask(item.parentTaskId)
    if (points > 0) {
      totalPoints += points
      completedTaskTitles.push(item.parentTaskTitle)
    }
  }

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
      habitStepCount: 0,
      taskCount: completedTaskTitles.length,
    }).then(() => {
      submitMessage.value = `已提交打卡，等待家长审批 🕐 审批通过后将获得 ${totalPoints} 阳光值`
    }).catch(() => {
      submitMessage.value = `打卡已记录！等待家长审批后获得 ${totalPoints} 阳光值 🕐`
    })
  } else {
    submitMessage.value = '继续保持！'
  }
}

// ── Progress ──
const totalCount = computed(() => checklistItems.value.length)
const completedCount = computed(() =>
  checklistItems.value.filter(item => isTaskItemChecked(item.id)).length
)
const totalPossiblePoints = computed(() =>
  checklistItems.value.reduce((sum, item) =>
    sum + (isTaskItemChecked(item.id) ? item.rewardPoints : 0), 0
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
    const checkedCount = items.filter(i => isTaskItemChecked(i.id)).length
    return {
      taskId,
      taskTitle: first.parentTaskTitle,
      taskIcon: first.icon,
      items,
      allChecked: checkedCount === items.length,
      someChecked: checkedCount > 0 && checkedCount < items.length,
      taskReward: first.rewardPoints,
    }
  })
})

function toggleTaskGroup(group: TaskGroup) {
  if (submitted.value && isToday) return
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
          </span>
        </p>
        <p v-if="submitMessage && submitted" class="lead" style="font-size:14px;color:var(--primary);margin-top:4px">
          {{ submitMessage }}
        </p>
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
            {{ submitting ? '⏳ 提交中...' : `✅ 提交打卡（${completedCount}/${totalCount}）` }}
          </button>
          <div v-else class="submitted-badge">
            <span>✅ 今日已打卡</span>
            <button class="btn ghost reset-btn" @click="resetTodayChecklist">重置今日打卡</button>
          </div>
        </div>

        <!-- Edit mode notice (for past dates) -->
        <div v-else class="edit-mode-notice">
          <span>📋 正在编辑 {{ activeDate }} 的打卡记录</span>
          <button class="btn ghost" @click="backToDashboard">完成编辑</button>
        </div>

        <div class="print-footer">
          <p>{{ isToday ? '每天完成后打 ✓，点击提交即可同步打卡记录' : '修改会自动保存到本地记录' }}</p>
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

@media (max-width: 700px) {
  .print-sheet { padding: 20px; }
  .print-header h1 { font-size: 24px; }
  .print-section h2 { font-size: 18px; }

}
</style>
