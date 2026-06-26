<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useChildSelectStore, useParentStore, useTaskStore, useUserStore } from '../../stores'
import { api, normalizeSubTask } from '../../utils/api'
import type { TaskCategory } from '../../types'
import ChildSelector from '../../components/ChildSelector.vue'

const parentStore = useParentStore()
const taskStore = useTaskStore()
const userStore = useUserStore()
const childSelectStore = useChildSelectStore()

const activeTab = ref<'tasks' | 'habits' | 'print'>('tasks')

// ── Task Management ────────────────────────────────────────────────

const title = ref('')
const description = ref('')
const type = ref<TaskCategory>('study_habit')
const rewardPoints = ref(20)
const icon = ref('☝️')

const categoryOptions: { value: TaskCategory; label: string; icon: string }[] = [
  { value: 'morning_routine', label: '晨间惯例', icon: '🌅' },
  { value: 'study_habit', label: '学习习惯', icon: '📖' },
  { value: 'life_skill', label: '生活技能', icon: '🧹' },
  { value: 'exercise', label: '运动', icon: '⚽' },
  { value: 'reflection', label: '反思', icon: '💭' },
]

const iconOptions = ['☝️', '📖', '✏️', '🎒', '🧠', '🏃', '🧹', '💭', '🌟', '📝', '🔔', '🎯']

async function createTask() {
  if (!title.value.trim()) return
  const childId = childSelectStore.selectedChildId ?? undefined

  // Create local template first
  const template = parentStore.addTaskTemplate({
    title: title.value.trim(),
    description: description.value.trim(),
    type: type.value,
    rewardPoints: rewardPoints.value,
    icon: icon.value,
    status: 'pending',
  })

  // Sync to backend and capture the backend task ID
  if (childId) {
    try {
      const res = await api.tasks.create({
        title: title.value.trim(),
        type: type.value,
        description: description.value.trim(),
        rewardPoints: rewardPoints.value,
        icon: icon.value,
        childId,
      })
      const backendId = String(res.pk_tasks ?? res.task?.pk_tasks ?? '')
      if (backendId) {
        parentStore.updateTaskTemplate(template.id, { id: backendId })
      }
    } catch { /* offline, keep local template */ }
  }

  title.value = ''
  description.value = ''
  type.value = 'study_habit'
  rewardPoints.value = 20
  icon.value = '☝️'
}

function deleteTask(id: string) {
  // Delete from backend if synced (numeric ID)
  if (/^\d+$/.test(id)) {
    api.tasks.delete(id).catch(() => { /* offline */ })
  }
  parentStore.deleteTaskTemplate(id)
  // Auto-switch to another task if the deleted one was active
  if (expandedTaskId.value === id) {
    const remaining = parentStore.parentTaskTemplates
    expandedTaskId.value = remaining.length ? remaining[0].id : null
  }
}

// ── Habit Management ──────────────────────────────────────────────

const editTitle = ref(taskStore.currentWeekHabit.title)
const editWeek = ref(taskStore.currentWeekHabit.weekNumber)
const newStep = ref('')
const newHabitTitle = ref('')

function saveHabit() {
  taskStore.updateCurrentHabit({
    title: editTitle.value.trim() || taskStore.currentWeekHabit.title,
    weekNumber: editWeek.value,
  })
}

function addStep() {
  if (!newStep.value.trim()) return
  taskStore.addStepToHabit(newStep.value.trim())
  newStep.value = ''
}

function removeStep(index: number) {
  taskStore.removeHabitStep(index)
}

function createHabit() {
  if (!newHabitTitle.value.trim()) return
  taskStore.createNewHabit(newHabitTitle.value.trim())
  editTitle.value = taskStore.currentWeekHabit.title
  editWeek.value = taskStore.currentWeekHabit.weekNumber
  newHabitTitle.value = ''
}

async function loadHistory(id: string) {
  await taskStore.loadHabitFromHistory(id)
  editTitle.value = taskStore.currentWeekHabit.title
  editWeek.value = taskStore.currentWeekHabit.weekNumber
}

// ── Sub-task Management ──
const expandedTaskId = ref<string | null>(null)
const newSubtaskTitle = ref('')
const newSubtaskWeekDay = ref('')
const newSubtaskType = ref<TaskCategory | ''>('')

// Drag-and-drop state
const dragSubtaskId = ref<string | null>(null)
const dragOverSubtaskId = ref<string | null>(null)

async function showSubTasks(taskId: string) {
  expandedTaskId.value = taskId
  newSubtaskTitle.value = ''
  newSubtaskWeekDay.value = ''
  newSubtaskType.value = ''
  dragSubtaskId.value = null
  dragOverSubtaskId.value = null

  // Only tasks with a numeric backend ID can have backend sub-tasks
  const hasBackendId = /^\d+$/.test(taskId)
  if (!hasBackendId) return

  // Load sub-tasks from backend
  try {
    const res = await api.tasks.getTask(taskId)
    if (res?.sub_tasks?.length) {
      const backendSubTasks = res.sub_tasks.map(normalizeSubTask)
      const task = parentStore.parentTaskTemplates.find(t => t.id === taskId)
      if (task) {
        // Merge: keep local-only sub-tasks (non-numeric IDs), replace rest with backend data
        const localOnly = (task.subTasks || []).filter(s => !/^\d+$/.test(s.id))
        const merged = [...backendSubTasks, ...localOnly]
        task.subTasks = merged
        parentStore.updateTaskTemplate(taskId, { subTasks: [...merged] })
      }
    }
  } catch { /* offline, keep local sub-tasks */ }
}

function addSubtask(taskId: string) {
  if (!newSubtaskTitle.value.trim()) return
  const task = parentStore.parentTaskTemplates.find(t => t.id === taskId)
  if (!task) return
  if (!task.subTasks) task.subTasks = []

  const localId = `st-${Date.now()}`
  const sortOrder = task.subTasks.length

  const subtaskType = (newSubtaskType.value || task.type) as TaskCategory

  task.subTasks.push({
    id: localId,
    title: newSubtaskTitle.value.trim(),
    type: subtaskType,
    weekDay: newSubtaskWeekDay.value || undefined,
    sortOrder,
  })
  parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })

  // Sync to backend if task has a backend ID
  const hasBackendId = /^\d+$/.test(taskId)
  if (hasBackendId) {
    api.tasks.subtasks.add(taskId, {
      title: newSubtaskTitle.value.trim(),
      type: subtaskType,
      weekDay: newSubtaskWeekDay.value || undefined,
      sortOrder,
    }).then((res: any) => {
      const backendId = String(res.pk_sub_tasks ?? '')
      if (backendId) {
        const idx = task.subTasks?.findIndex(s => s.id === localId)
        if (idx !== undefined && idx !== -1 && task.subTasks) {
          task.subTasks[idx].id = backendId
          parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })
        }
      }
    }).catch(() => { /* offline */ })
  }

  newSubtaskTitle.value = ''
  newSubtaskWeekDay.value = ''
  newSubtaskType.value = ''
}

function removeSubtask(taskId: string, subtaskId: string) {
  const task = parentStore.parentTaskTemplates.find(t => t.id === taskId)
  if (!task?.subTasks) return

  // Check if this subtask has a backend ID (numeric) before removing
  const hasBackendId = /^\d+$/.test(subtaskId)

  task.subTasks = task.subTasks.filter(s => s.id !== subtaskId)
  task.subTasks.forEach((s, i) => { s.sortOrder = i })
  parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })

  // Delete from backend if it was synced
  if (hasBackendId) {
    api.tasks.subtasks.remove(taskId, subtaskId).catch(() => { /* offline */ })
  }
}

function subtaskWeekDayLabel(wd?: string): string {
  if (!wd) return '每天'
  if (wd === 'weekday') return '📅 平时'
  if (wd === 'weekend') return '🎉 周末'
  return wd
}

// ── Drag-and-drop handlers ──

function onDragStart(subtaskId: string, event: DragEvent) {
  dragSubtaskId.value = subtaskId
  event.dataTransfer?.setData('text/plain', subtaskId)
  event.dataTransfer!.effectAllowed = 'move'
  // Slight delay so the drag image shows the item in its original position
  requestAnimationFrame(() => {
    if (event.target instanceof HTMLElement) {
      event.target.classList.add('dragging')
    }
  })
}

function onDragEnd(event: DragEvent) {
  dragSubtaskId.value = null
  dragOverSubtaskId.value = null
  if (event.target instanceof HTMLElement) {
    event.target.classList.remove('dragging')
  }
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
}

function onDragEnter(taskId: string, subtaskId: string, event: DragEvent) {
  if (subtaskId === dragSubtaskId.value) return
  // Ignore enter events bubbling from children within the same row
  const target = event.currentTarget as HTMLElement | null
  const related = event.relatedTarget as Node | null
  if (target && target.contains(related)) return
  dragOverSubtaskId.value = subtaskId
}

function onDragLeave(taskId: string, subtaskId: string, event: DragEvent) {
  // Ignore leave events when entering a child element within the same row
  const target = event.currentTarget as HTMLElement | null
  const related = event.relatedTarget as Node | null
  if (target && target.contains(related)) return
  if (dragOverSubtaskId.value === subtaskId) {
    dragOverSubtaskId.value = null
  }
}

function onDrop(taskId: string, targetSubtaskId: string, event: DragEvent) {
  event.preventDefault()
  const draggedId = event.dataTransfer?.getData('text/plain')
  if (!draggedId || draggedId === targetSubtaskId) {
    dragSubtaskId.value = null
    dragOverSubtaskId.value = null
    return
  }

  const task = parentStore.parentTaskTemplates.find(t => t.id === taskId)
  if (!task?.subTasks) {
    dragSubtaskId.value = null
    dragOverSubtaskId.value = null
    return
  }

  const fromIdx = task.subTasks.findIndex(s => s.id === draggedId)
  const toIdx = task.subTasks.findIndex(s => s.id === targetSubtaskId)
  if (fromIdx === -1 || toIdx === -1) {
    dragSubtaskId.value = null
    dragOverSubtaskId.value = null
    return
  }

  // Reorder
  const [moved] = task.subTasks.splice(fromIdx, 1)
  task.subTasks.splice(toIdx, 0, moved)
  // Reindex sortOrder
  task.subTasks.forEach((s, i) => { s.sortOrder = i })
  parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })

  dragSubtaskId.value = null
  dragOverSubtaskId.value = null
}

// Helper to get sub-tasks for the expanded task (safer for template access)
function getSubTasks(taskId: string) {
  return parentStore.parentTaskTemplates.find(t => t.id === taskId)?.subTasks
}

// ── Auto-expand first task on mount ──
onMounted(() => {
  if (parentStore.parentTaskTemplates.length) {
    showSubTasks(parentStore.parentTaskTemplates[0].id)
  }
})

watch(() => parentStore.parentTaskTemplates.length, (len) => {
  if (len && !expandedTaskId.value) {
    showSubTasks(parentStore.parentTaskTemplates[0].id)
  }
})


// ── Print Preview ─────────────────────────────────────────────────

const selectedTaskIds = ref<Set<string>>(new Set(parentStore.parentTaskTemplates.map(t => t.id)))

const allTasks = computed(() => parentStore.parentTaskTemplates)

const selectedTasks = computed(() =>
  allTasks.value.filter(t => selectedTaskIds.value.has(t.id))
)

// Build checklist from selected tasks (ONLY sub-tasks appear, never tasks)
function buildChecklist() {
  const items: Array<{
    id: string
    title: string
    icon: string
    description: string
    type?: string
    weekDay?: string
    parentTaskTitle?: string
  }> = []
  for (const task of selectedTasks.value) {
    if (!task.subTasks?.length) continue
    for (const sub of task.subTasks) {
      items.push({
        id: sub.id,
        title: sub.title,
        icon: task.icon,
        description: `属于：${task.title}`,
        type: sub.type,
        weekDay: sub.weekDay,
        parentTaskTitle: task.title,
      })
    }
  }
  checklistItems.value = items
}

const checklistItems = ref<any[]>([])
const printLoading = ref(false)

function toggleTaskSelection(id: string) {
  if (selectedTaskIds.value.has(id)) selectedTaskIds.value.delete(id)
  else selectedTaskIds.value.add(id)
  // Rebuild checklist when selection changes
  if (activeTab.value === 'print') buildChecklist()
}

function selectAllTasks() {
  selectedTaskIds.value = new Set(allTasks.value.map(t => t.id))
  if (activeTab.value === 'print') buildChecklist()
}

function deselectAllTasks() {
  selectedTaskIds.value = new Set()
  if (activeTab.value === 'print') buildChecklist()
}

async function switchToPrint() {
  activeTab.value = 'print'
  selectAllTasks()
  printLoading.value = true
  await loadAllSubtasks()
  buildChecklist()
  printLoading.value = false
}

// ── Load sub-tasks for all tasks (used by print tab) ──
async function loadAllSubtasks() {
  const tasks = allTasks.value.filter(t => /^\d+$/.test(t.id))
  if (!tasks.length) return
  await Promise.allSettled(tasks.map(async (t) => {
    try {
      const res = await api.tasks.getTask(t.id)
      if (res?.sub_tasks?.length) {
        const backendSubTasks = res.sub_tasks.map(normalizeSubTask)
        const task = parentStore.parentTaskTemplates.find(pt => pt.id === t.id)
        if (task) {
          const localOnly = (task.subTasks || []).filter(s => !/^\d+$/.test(s.id))
          task.subTasks = [...backendSubTasks, ...localOnly]
          parentStore.updateTaskTemplate(t.id, { subTasks: [...task.subTasks] })
        }
      }
    } catch { /* offline */ }
  }))
}

const downloading = ref(false)

const selectedChildName = computed(() =>
  childSelectStore.selectedChild?.name ?? userStore.profile.name ?? '我的'
)

async function downloadPrint() {
  if (downloading.value) return
  downloading.value = true
  try {
    const element = document.getElementById('print-area')
    if (!element) return

    // Dynamically load html2canvas + jspdf from CDN
    const html2canvas = (await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js', 'html2canvas'))
    const { jsPDF } = (await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js', 'jspdf'))

    // Wait a tick for fonts/layout to settle
    await new Promise(r => setTimeout(r, 200))

    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width

    let remainingHeight = pdfHeight
    let srcY = 0
    const pageHeight = pdf.internal.pageSize.getHeight()

    while (remainingHeight > 0) {
      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = Math.min(canvas.width * pageHeight / pdfWidth, canvas.height - srcY)
      const ctx = pageCanvas.getContext('2d')!
      ctx.drawImage(canvas, 0, srcY, canvas.width, pageCanvas.height, 0, 0, canvas.width, pageCanvas.height)
      const pageData = pageCanvas.toDataURL('image/png')

      if (srcY > 0) pdf.addPage()
      pdf.addImage(pageData, 'PNG', 0, 0, pdfWidth, (pageCanvas.height * pdfWidth) / canvas.width)
      srcY += pageCanvas.height
      remainingHeight -= pageCanvas.height
    }

    pdf.save(`${selectedChildName.value}的每日打卡清单_第${taskStore.currentWeekHabit.weekNumber}周.pdf`)
  } catch {
    alert('下载失败，请检查网络连接后重试')
  } finally {
    downloading.value = false
  }
}

function loadScript(url: string, name: 'html2canvas' | 'jspdf'): Promise<any> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${url}"]`)
    if (existing) {
      if (name === 'jspdf') resolve({ jsPDF: (window as any).jspdf.jsPDF })
      else resolve((window as any).html2canvas)
      return
    }
    const script = document.createElement('script')
    script.src = url
    script.onload = () => {
      if (name === 'jspdf') resolve({ jsPDF: (window as any).jspdf.jsPDF })
      else resolve((window as any).html2canvas)
    }
    script.onerror = reject
    document.head.appendChild(script)
  })
}
</script>

<template>
  <div class="page">
    <ChildSelector />

    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📋 任务与习惯管理</span>
        <h1>管理任务模板和核心习惯</h1>
        <p class="lead">创建每日任务模板，设定每周主线习惯 SOP，所有内容会同步到孩子的打卡页面。完成后可在打印预览生成清单。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center">
        <div class="card-title">
          <h2>概览</h2>
          <span class="tag">{{ allTasks.length }} 个任务 · {{ taskStore.currentWeekHabit.steps.length }} 个步骤</span>
        </div>
        <div class="stat-row">
          <div class="mini-stat">
            <strong>{{ allTasks.length }}</strong>
            <span>任务模板</span>
          </div>
          <div class="mini-stat">
            <strong>{{ taskStore.currentWeekHabit.title || '—' }}</strong>
            <span>当前习惯</span>
          </div>
          <div class="mini-stat">
            <strong>第 {{ taskStore.currentWeekHabit.weekNumber }} 周</strong>
            <span>习惯周数</span>
          </div>
          <div class="mini-stat">
            <strong>{{ taskStore.habitHistory.length }}</strong>
            <span>历史习惯</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tab Bar -->
    <section class="tab-bar-section">
      <div class="tab-bar-manager">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'tasks' }"
          @click="activeTab = 'tasks'"
        >
          📋 任务管理
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'habits' }"
          @click="activeTab = 'habits'"
        >
          ✅ 习惯管理
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'print' }"
          @click="switchToPrint()"
        >
          🖨️ 打印预览
        </button>
        <div class="tab-slider-manager" :class="`slide-${activeTab}`" />
      </div>
    </section>

    <!-- ── Tab 1: Task Management ── -->
    <section v-show="activeTab === 'tasks'">
      <div class="grid-2">
        <div class="panel">
          <div class="card-title">
            <h2>添加新任务</h2>
            <span class="tag">{{ categoryOptions.find(c => c.value === type)?.icon }} {{ categoryOptions.find(c => c.value === type)?.label }}</span>
          </div>
          <label style="display:block;font-weight:800;margin-bottom:6px">
            任务标题
            <input v-model="title" class="input" style="margin-top:6px" placeholder="例如：晨间朗读 10 分钟" />
          </label>
          <label style="display:block;font-weight:800;margin-top:14px;margin-bottom:6px">
            任务描述
            <input v-model="description" class="input" style="margin-top:6px" placeholder="具体要求和步骤说明" />
          </label>
          <div class="grid-2" style="margin-top:14px">
            <label style="font-weight:800">
              任务类别
              <select v-model="type" class="input" style="margin-top:6px">
                <option v-for="cat in categoryOptions" :key="cat.value" :value="cat.value">{{ cat.icon }} {{ cat.label }}</option>
              </select>
            </label>
            <label style="font-weight:800">
              奖励阳光值
              <input v-model.number="rewardPoints" class="input" style="margin-top:6px" type="number" min="5" max="100" step="5" />
            </label>
          </div>
          <label style="display:block;font-weight:800;margin-top:14px;margin-bottom:6px">
            图标选择
            <div class="icon-picker" style="margin-top:6px">
              <button v-for="ico in iconOptions" :key="ico" class="icon-btn" :class="{ active: icon === ico }" @click="icon = ico">{{ ico }}</button>
            </div>
          </label>
          <button class="btn" style="margin-top:20px;width:100%" :disabled="!title.trim()" @click="createTask">✨ 创建任务</button>
        </div>

        <div class="panel">
          <div class="card-title">
            <h2>已创建任务</h2>
            <span class="tag">{{ allTasks.length }} 项</span>
          </div>
          <div v-if="allTasks.length" class="list">
            <div
              v-for="template in allTasks"
              :key="template.id"
              class="list-row task-row"
              :class="{ 'task-row-active': expandedTaskId === template.id }"
              @click="showSubTasks(template.id)"
            >
              <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
                <span style="font-size:28px;flex-shrink:0">{{ template.icon }}</span>
                <div style="min-width:0">
                  <strong>{{ template.title }}</strong>
                  <span class="muted" style="display:block;font-size:13px">{{ template.description || '无描述' }}</span>
                  <div style="display:flex;gap:6px;margin-top:4px">
                    <span class="mini-tag">{{ categoryOptions.find(c => c.value === template.type)?.label || template.type }}</span>
                    <span class="mini-tag">☀️ +{{ template.rewardPoints }}</span>
                  </div>
                </div>
              </div>
              <div style="display:flex;gap:6px;flex-shrink:0;align-items:center" @click.stop>
                <button class="btn ghost" style="padding:6px 12px;font-size:13px" @click="deleteTask(template.id)">删除</button>
              </div>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:32px">还没有创建任务模板。在左侧表单中创建第一个任务吧 ✨</p>
        </div>
      </div>
    </section>

    <!-- ── Sub-task panel (expanded) ── -->
    <section v-if="expandedTaskId && activeTab === 'tasks'" class="subtask-section">
      <div class="panel subtask-panel">
        <div class="card-title">
          <h2>📋 子任务管理</h2>
          <span class="tag">{{ parentStore.parentTaskTemplates.find(t => t.id === expandedTaskId)?.title }}</span>
          <button class="btn ghost" style="padding:6px 14px;font-size:13px" @click="expandedTaskId = null">关闭</button>
        </div>
        <p class="lead" style="font-size:14px;margin-bottom:12px">
          子任务用于区分同一任务在<b>平时</b>和<b>周末</b>的不同内容。选择任务时即包含其下所有子任务。
        </p>

        <!-- Existing sub-tasks (draggable) -->
        <div
          v-if="getSubTasks(expandedTaskId!)?.length"
          class="subtask-list"
          style="margin-bottom:14px"
          @dragover="onDragOver"
        >
          <div
            v-for="sub in getSubTasks(expandedTaskId!)"
            :key="sub.id"
            :class="[
              'list-row',
              'subtask-row',
              { 'drag-over': dragOverSubtaskId === sub.id },
              { 'dragging': dragSubtaskId === sub.id },
            ]"
            draggable="true"
            @dragstart="onDragStart(sub.id, $event)"
            @dragend="onDragEnd"
            @dragenter="onDragEnter(expandedTaskId!, sub.id, $event)"
            @dragleave="onDragLeave(expandedTaskId!, sub.id, $event)"
            @drop="onDrop(expandedTaskId!, sub.id, $event)"
          >
            <span class="subtask-drag">⠿</span>
            <div style="flex:1;min-width:0">
              <strong>{{ sub.title }}</strong>
              <div style="display:flex;gap:6px;margin-top:4px">
                <span class="mini-tag">{{ categoryOptions.find(c => c.value === sub.type)?.label || sub.type }}</span>
                <span class="mini-tag">{{ subtaskWeekDayLabel(sub.weekDay) }}</span>
              </div>
            </div>
            <button class="btn ghost" style="padding:4px 10px;font-size:12px;color:#c00" @click="removeSubtask(expandedTaskId!, sub.id)">删除</button>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:16px;font-size:14px">暂无子任务，请在下方添加。</p>

        <!-- Add sub-task form -->
        <div class="subtask-add-form">
          <input
            v-model="newSubtaskTitle"
            class="input"
            placeholder="子任务名称（如：晨间朗读语文课文）"
            @keyup.enter="addSubtask(expandedTaskId!)"
          />
          <select v-model="newSubtaskType" class="input subtask-category-select">
            <option value="">继承任务类别 ({{ categoryOptions.find(c => c.value === parentStore.parentTaskTemplates.find(t => t.id === expandedTaskId)?.type)?.label }})</option>
            <option v-for="cat in categoryOptions" :key="cat.value" :value="cat.value">{{ cat.icon }} {{ cat.label }}</option>
          </select>
          <select v-model="newSubtaskWeekDay" class="input subtask-weekday-select">
            <option value="">每天</option>
            <option value="weekday">📅 平时</option>
            <option value="weekend">🎉 周末</option>
          </select>
          <button
            class="btn"
            :disabled="!newSubtaskTitle.trim()"
            @click="addSubtask(expandedTaskId!)"
          >
            + 添加
          </button>
        </div>
      </div>
    </section>

    <!-- ── Tab 2: Habit Management ── -->
    <section v-show="activeTab === 'habits'">
      <div class="grid-2">
        <div class="panel">
          <div class="card-title">
            <h2>编辑当前习惯</h2>
            <button class="btn secondary" @click="saveHabit">保存</button>
          </div>
          <label style="font-weight:800;display:block;margin-bottom:4px">习惯名称</label>
          <input v-model="editTitle" class="input" style="margin-bottom:12px" placeholder="习惯名称" />
          <label style="font-weight:800;display:block;margin-bottom:4px">周数</label>
          <input v-model.number="editWeek" class="input" type="number" min="1" style="margin-bottom:16px;width:120px" />

          <h3 style="margin:16px 0 10px">步骤列表</h3>
          <div v-if="taskStore.currentWeekHabit.steps.length" class="list" style="margin-bottom:12px">
            <div v-for="(step, index) in taskStore.currentWeekHabit.steps" :key="index" class="list-row" style="justify-content:flex-start;gap:12px">
              <b class="step-num">{{ step.order }}</b>
              <span style="flex:1">{{ step.instruction }}</span>
              <button class="btn ghost" style="padding:6px 12px;font-size:12px;color:#c00" @click="removeStep(index)">删除</button>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:12px">暂无步骤，请添加</p>

          <div style="display:flex;gap:8px">
            <input v-model="newStep" class="input" placeholder="新步骤说明" @keyup.enter="addStep" />
            <button class="btn" :disabled="!newStep.trim()" @click="addStep">添加</button>
          </div>
        </div>

        <div class="panel">
          <div class="card-title">
            <h2>创建新习惯</h2>
            <span class="tag">当前第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span>
          </div>
          <p class="lead" style="margin-bottom:12px;font-size:14px">创建后将自动归档当前习惯到历史记录。</p>
          <div style="display:flex;gap:8px">
            <input v-model="newHabitTitle" class="input" placeholder="新习惯名称（如：整理书包 SOP）" @keyup.enter="createHabit" />
            <button class="btn secondary" :disabled="!newHabitTitle.trim()" @click="createHabit">创建</button>
          </div>

          <h3 style="margin:24px 0 10px">历史习惯</h3>
          <div v-if="taskStore.habitHistory.length" class="list">
            <div v-for="habit in taskStore.habitHistory" :key="habit.id" class="list-row" :style="{ cursor: 'pointer' }" @click="loadHistory(habit.id)">
              <div>
                <strong>{{ habit.title }}</strong>
                <span class="muted" style="display:block;font-size:13px">第 {{ habit.weekNumber }} 周 · {{ habit.steps.length }} 个步骤</span>
              </div>
              <span class="tag" style="flex-shrink:0;font-size:12px">载入</span>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:16px;font-size:14px">暂无历史习惯。创建新习惯时当前习惯会自动归档。</p>
        </div>
      </div>
    </section>

    <!-- ── Tab 3: Print Preview ── -->
    <section v-show="activeTab === 'print'" class="print-tab">
      <!-- Selector -->
      <div class="panel" style="margin-bottom:18px">
        <div class="card-title">
          <h2>选择要打印的任务</h2>
          <div style="display:flex;gap:8px">
            <button class="btn ghost" style="padding:6px 14px;font-size:13px" @click="selectAllTasks">全选</button>
            <button class="btn ghost" style="padding:6px 14px;font-size:13px" @click="deselectAllTasks">取消</button>
          </div>
        </div>
        <div v-if="allTasks.length" class="task-select-grid">
          <label v-for="task in allTasks" :key="task.id" class="task-check-card" :class="{ checked: selectedTaskIds.has(task.id) }">
            <input type="checkbox" :checked="selectedTaskIds.has(task.id)" @change="toggleTaskSelection(task.id)" />
            <span class="tci">{{ task.icon }}</span>
            <div class="tci-text">
              <strong>{{ task.title }}</strong>
              <span class="muted">{{ task.description || '无描述' }}</span>
            </div>
            <span class="mini-tag">☀️ +{{ task.rewardPoints }}</span>
          </label>
        </div>
        <p v-else class="muted" style="text-align:center;padding:20px">暂无任务模板，请先在「任务管理」中创建。</p>
      </div>

      <!-- Print Preview -->
      <div class="panel print-panel">
        <div class="card-title">
          <h2>🖨️ 打印预览</h2>
          <button class="btn" :disabled="downloading" @click="downloadPrint">
            {{ downloading ? '⏳ 生成中...' : '📥 下载 PDF' }}
          </button>
        </div>

        <div id="print-area" class="print-sheet">
          <div class="print-header">
            <h1>{{ selectedChildName }} 的每日打卡清单</h1>
            <p class="print-date">生成日期：{{ new Date().toLocaleDateString('zh-CN') }} · 第 {{ taskStore.currentWeekHabit.weekNumber }} 周</p>
          </div>

          <!-- Habits Section -->
          <div class="print-section">
            <h2>本周习惯：{{ taskStore.currentWeekHabit.title }}</h2>
            <div v-if="taskStore.currentWeekHabit.steps.length" class="print-steps">
              <div v-for="step in taskStore.currentWeekHabit.steps" :key="step.order" class="print-step-row">
                <span class="ps-order">{{ step.order }}</span>
                <span class="ps-text">{{ step.instruction }}</span>
                <span class="ps-check">□</span>
              </div>
            </div>
            <p v-else class="muted">暂无习惯步骤。</p>
          </div>

          <!-- Tasks Section -->
          <div class="print-section">
            <h2>每日任务清单</h2>
            <div v-if="printLoading" class="print-loading">
              <p>⏳ 正在加载子任务数据...</p>
            </div>
            <div v-else-if="checklistItems.length" class="print-tasks-vertical">
              <div v-for="item in checklistItems" :key="item.id" class="ptr-row">
                <div class="ptr-info">
                  <strong>{{ item.title }}</strong>
                  <span class="muted">{{ item.description }}</span>
                  <div style="display:flex;gap:4px;margin-top:2px;flex-wrap:wrap">
                    <span v-if="item.type" class="ptr-sub-badge">{{ categoryOptions.find(c => c.value === item.type)?.label || item.type }}</span>
                    <span v-if="item.weekDay" class="ptr-sub-badge ptr-sub-day">{{ subtaskWeekDayLabel(item.weekDay) }}</span>
                  </div>
                </div>
                <span class="ptr-check">□</span>
              </div>
            </div>
            <p v-else class="muted">所选任务暂无子任务，请先在「任务管理」中添加子任务。</p>
          </div>

          <div class="print-footer">
            <p>每天完成后打 ✓，周末拍照上传</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ── Tab Bar ── */
.tab-bar-section {
  margin-bottom: 18px;
}
.tab-bar-manager {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  background: #f1f5f1;
  border-radius: 18px;
  padding: 6px;
}
.tab-btn {
  position: relative;
  z-index: 2;
  border: none;
  background: transparent;
  padding: 14px 12px;
  border-radius: 14px;
  font-weight: 800;
  font-size: 15px;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.2s;
}
.tab-btn.active { color: #2e7d32; }
.tab-slider-manager {
  position: absolute;
  top: 6px; bottom: 6px;
  width: calc(33.333% - 8px);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tab-slider-manager.slide-tasks { transform: translateX(0); left: 6px; }
.tab-slider-manager.slide-habits { transform: translateX(100%); left: 6px; }
.tab-slider-manager.slide-print { transform: translateX(200%); left: 6px; }

/* ── Task Row ── */
.task-row {
  align-items: center;
  cursor: pointer;
  transition: background .12s ease, border-color .12s ease;
}
.task-row:hover {
  background: #f0f7ee;
}
.task-row-active {
  border-color: var(--primary) !important;
  background: #e8f5e0;
}
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.icon-btn {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  border: 2px solid var(--line);
  background: #fff;
  font-size: 22px;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all .12s ease;
}
.icon-btn:hover {
  border-color: var(--primary);
  background: #ecffd9;
}
.icon-btn.active {
  border-color: var(--primary);
  background: #d9f5c8;
  box-shadow: 0 4px 12px rgba(16, 110, 0, .18);
}
.mini-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
}

/* ── Sub-task ── */
.subtask-section {
  margin-top: -12px;
  margin-bottom: 18px;
}
.subtask-panel {
  border: 2px solid var(--primary-2);
  background: #fafff5;
}
.subtask-row {
  align-items: center;
  border-radius: 12px;
  padding: 10px 14px;
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
  border: 2px solid transparent;
  user-select: none;
}
.subtask-row:hover {
  background: #ecffd9;
}
.subtask-row.dragging {
  opacity: .4;
  transform: scale(.97);
  background: #e0f0d0;
}
.subtask-row.drag-over {
  border-color: var(--primary);
  background: #d9f5c8;
  transform: translateY(2px);
  box-shadow: 0 4px 12px rgba(16, 110, 0, .15);
}
.subtask-drag {
  color: #aaa;
  font-size: 18px;
  cursor: grab;
  flex-shrink: 0;
  transition: color .12s ease;
  touch-action: none;
}
.subtask-row:hover .subtask-drag {
  color: var(--primary);
}
.subtask-row:active .subtask-drag {
  cursor: grabbing;
}
.subtask-add-form {
  display: flex;
  gap: 8px;
  align-items: center;
}
.subtask-add-form .input {
  flex: 1;
}
.subtask-weekday-select {
  width: auto;
  min-width: 110px;
  flex: 0 0 auto;
}
.subtask-category-select {
  width: auto;
  min-width: 150px;
  flex: 0 0 auto;
}
.subtask-add-form .btn {
  white-space: nowrap;
  flex-shrink: 0;
}
@media (max-width: 600px) {
  .subtask-add-form {
    flex-wrap: wrap;
  }
  .subtask-add-form .input {
    flex: 1 1 100%;
  }
}

/* ── Step Num ── */
.step-num {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  flex-shrink: 0;
}

/* ── Overview Stats ── */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.mini-stat {
  text-align: center;
  padding: 12px 8px;
  border-radius: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.mini-stat strong {
  display: block;
  font-size: 18px;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mini-stat span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

/* ── Task Select Grid (Print Tab) ── */
.task-select-grid {
  display: grid;
  gap: 8px;
}
.task-check-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 2px solid var(--line);
  background: #fff;
  cursor: pointer;
  transition: all .12s ease;
}
.task-check-card:hover {
  border-color: var(--primary-2);
  background: #f6fddc;
}
.task-check-card.checked {
  border-color: var(--primary);
  background: #ecffd9;
}
.task-check-card input { display: none; }
.tci { font-size: 28px; flex-shrink: 0; }
.tci-text { flex: 1; min-width: 0; }
.tci-text strong { display: block; font-size: 15px; }
.tci-text .muted { font-size: 13px; }

/* ── Print Preview ── */
.print-panel {
  border: 2px dashed var(--line);
}
.print-sheet {
  background: #fff;
  border-radius: 20px;
  padding: 36px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.06);
  border: 1px solid #eee;
}
@media print {
  .print-sheet {
    box-shadow: none;
    border: 0;
    border-radius: 0;
    padding: 20px;
  }
  .ps-check,
  .ptr-check {
    font-size: 26px !important;
    color: #000 !important;
  }
  .ptr-row {
    border-bottom-color: #ccc !important;
  }
  .ptr-sub-badge {
    background: #e8f5e9 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .print-step-row {
    border-bottom-color: #ccc !important;
  }
  .print-header {
    border-bottom-color: #000 !important;
  }
}
.print-header {
  text-align: center;
  border-bottom: 3px solid var(--primary);
  padding-bottom: 18px;
  margin-bottom: 24px;
}
.print-header h1 {
  font-size: 26px;
  color: var(--primary);
  margin: 0 0 6px;
}
.print-date {
  color: var(--muted);
  font-size: 14px;
  margin: 0;
}
.print-section {
  margin-bottom: 24px;
}
.print-section h2 {
  font-size: 18px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.print-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.print-step-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid #e0e0e0;
}
.print-step-row:last-child {
  border-bottom: none;
}
.ps-order {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 14px;
  flex-shrink: 0;
}
.ps-text { flex: 1; font-weight: 600; }
.ps-check { font-size: 28px; color: #111; line-height: 1; }

/* ── Vertical Task Checklist ── */
.print-tasks-vertical {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ptr-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
}
.ptr-row:last-child {
  border-bottom: none;
}
.ptr-check {
  font-size: 30px;
  line-height: 1;
  color: #111;
  flex-shrink: 0;
}
.ptr-info {
  flex: 1;
  min-width: 0;
}
.ptr-info strong {
  display: block;
  font-size: 16px;
}
.ptr-info .muted {
  display: block;
  font-size: 13px;
  color: #666;
  margin-top: 2px;
}
.ptr-sub-badge {
  font-size: 10px;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 700;
}
.ptr-sub-day {
  background: #fff3e0;
  color: #e65100;
}

.print-loading {
  text-align: center;
  padding: 32px 16px;
  color: var(--muted);
  font-size: 15px;
}

.print-footer {
  text-align: center;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
}

button:disabled {
  opacity: .5;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .tab-btn { font-size: 13px; padding: 12px 8px; }
}
</style>
