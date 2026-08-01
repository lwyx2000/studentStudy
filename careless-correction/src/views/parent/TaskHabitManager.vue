<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useChildSelectStore, useParentStore, useTaskStore, useUserStore } from '../../stores'
import { api, normalizeSubTask, normalizeTask } from '../../utils/api'
import { weekDayToLabel } from '../../utils/constants'
import type { TaskCategory, TaskItem } from '../../types'
import ChildSelector from '../../components/ChildSelector.vue'
import WeekdayPicker from '../../components/WeekdayPicker.vue'
import InventoryPickerModal from '../../components/InventoryPickerModal.vue'

const parentStore = useParentStore()
const taskStore = useTaskStore()
const userStore = useUserStore()
const childSelectStore = useChildSelectStore()

const downloading = ref(false)
const loadingData = ref(false)
const now = new Date()
const dateStr = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`

// ── Load data from API ──
async function loadData() {
  loadingData.value = true
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    // Load ALL tasks (including completed) from inventory endpoint
    const taskRes = await api.tasks.getInventory(childId)
    const tasks = (taskRes.tasks ?? []).map(normalizeTask)
    parentStore.parentTaskTemplates.splice(0, parentStore.parentTaskTemplates.length, ...tasks)
  } catch { /* offline */ }
  try {
    // Load habits
    await taskStore.fetchFromApi(childId)
  } catch { /* offline */ }
  loadingData.value = false
}

// Watch child change → reload data
watch(() => childSelectStore.selectedChildId, async () => {
  await loadData()
  if (parentStore.parentTaskTemplates.length) {
    showSubTasks(parentStore.parentTaskTemplates[0].id)
  }
  await loadAllSubtasks()
  loadSubTaskLibrary().catch(() => {})
  loadStepLibrary().catch(() => {})
})

const activeTab = ref<'tasks' | 'habits'>('tasks')

// ── Task Management ────────────────────────────────────────────────

const title = ref('')
const description = ref('')
const type = ref<TaskCategory>('study_habit')
const rewardPoints = ref(5)
const icon = ref('☝️')

const categoryOptions: { value: TaskCategory; label: string; icon: string }[] = [
  { value: 'morning_routine', label: '晨间惯例', icon: '🌅' },
  { value: 'study_habit', label: '学习习惯', icon: '📖' },
  { value: 'life_skill', label: '生活技能', icon: '🧹' },
  { value: 'exercise', label: '运动', icon: '⚽' },
  { value: 'reflection', label: '反思', icon: '💭' },
]

const iconOptions = ['☝️', '📖', '✏️', '🎒', '🧠', '🏃', '🧹', '💭', '🌟', '📝', '🔔', '🎯']

const taskWeekDay = ref('')
const showWeekdayPicker = ref(false)
const showSubtaskWeekdayPicker = ref(false)

// ── Inventory Picker Modal (for sub-tasks and steps) ──
const subTaskPickerVisible = ref(false)
const stepPickerVisible = ref(false)
const subTaskLibrary = ref<any[]>([])
const stepLibrary = ref<any[]>([])

async function loadSubTaskLibrary() {
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    const res = await api.tasks.getSubTaskLibrary(childId)
    subTaskLibrary.value = res.subtasks ?? []
  } catch { /* offline */ }
}

async function loadStepLibrary() {
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    const res = await api.habits.getStepLibrary(childId)
    stepLibrary.value = res.steps ?? []
  } catch { /* offline */ }
}

async function openSubTaskPicker() {
  await loadSubTaskLibrary()
  subTaskPickerVisible.value = true
}

async function openStepPicker() {
  await loadStepLibrary()
  stepPickerVisible.value = true
}

function onSubTaskSelected(selected: any[]) {
  if (!expandedTaskId.value) return
  const task = parentStore.parentTaskTemplates.find(t => t.id === expandedTaskId.value)
  if (!task) return
  if (!task.subTasks) task.subTasks = []

  for (const s of selected) {
    const localId = `st-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
    task.subTasks.push({
      id: localId,
      title: s.title,
      type: s.type || task.type,
      weekDay: s.week_day || undefined,
      sortOrder: task.subTasks.length,
    })
    // Sync to backend
    if (/^\d+$/.test(expandedTaskId.value)) {
      api.tasks.subtasks.add(expandedTaskId.value, {
        title: s.title,
        type: s.type || task.type,
        weekDay: s.week_day || undefined,
        sortOrder: task.subTasks.length - 1,
      }).then((res: any) => {
        const backendId = String(res.pk_sub_tasks ?? '')
        if (backendId && task.subTasks) {
          const idx = task.subTasks.findIndex(st => st.id === localId)
          if (idx !== -1) task.subTasks[idx].id = backendId
        }
      }).catch(() => {})
    }
  }
  parentStore.updateTaskTemplate(expandedTaskId.value, { subTasks: [...task.subTasks] })
}

function onStepSelected(selected: any[]) {
  if (!editingHabitId.value) return
  for (const s of selected) {
    taskStore.addStepToHabit(editingHabitId.value, s.instruction)
  }
}

// Ensure sub-task library is pre-loaded for speed
onMounted(() => {
  loadSubTaskLibrary().catch(() => {})
  loadStepLibrary().catch(() => {})
})

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
    weekDay: taskWeekDay.value || undefined,
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
        weekDay: taskWeekDay.value || undefined,
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
  rewardPoints.value = 5
  icon.value = '☝️'
  taskWeekDay.value = ''
}

function deleteTask(id: string) {
  if (!confirm('确定要停用该任务吗？可在「任务清单」中恢复。')) return
  if (/^\d+$/.test(id)) {
    api.tasks.delete(id).catch(() => { /* offline */ })
  }
  parentStore.deleteTaskTemplate(id)
  // Auto-switch to another task if the deleted one was active
  if (expandedTaskId.value === id) {
    const remaining = parentStore.parentTaskTemplates.filter(t => t.active !== false)
    expandedTaskId.value = remaining.length ? remaining[0].id : null
  }
    if (taskEditId.value === id) cancelEdit()
}

// ── Inline Edit Task ──
const taskEditId = ref<string | null>(null)
const taskEditTitle = ref('')
const taskEditDesc = ref('')
const taskEditType = ref<TaskCategory>('study_habit')
const taskEditPoints = ref(5)
const taskEditIcon = ref('☝️')

function startEdit(task: TaskItem) {
  taskEditId.value = task.id
  taskEditTitle.value = task.title
  taskEditDesc.value = task.description
  taskEditType.value = task.type
  taskEditPoints.value = task.rewardPoints
  taskEditIcon.value = task.icon
}

function saveEdit(id: string) {
  if (!taskEditTitle.value.trim()) return
  parentStore.updateTaskTemplate(id, {
    title: taskEditTitle.value.trim(),
    description: taskEditDesc.value.trim(),
    type: taskEditType.value,
    rewardPoints: taskEditPoints.value,
    icon: taskEditIcon.value,
  })
  const hasBackendId = /^\d+$/.test(id)
  if (hasBackendId) {
    api.tasks.update(id, {
      title: taskEditTitle.value.trim(),
      description: taskEditDesc.value.trim(),
      type: taskEditType.value,
      rewardPoints: taskEditPoints.value,
      icon: taskEditIcon.value,
    }).catch(() => {})
  }
  taskEditId.value = null
}

function cancelEdit() {
  taskEditId.value = null
}

// ── Habit Management ──────────────────────────────────────────────

const editingHabitId = ref<string | null>(null)
const editTitle = ref('')
const editRewardPoints = ref(5)
const newStep = ref('')
const newHabitTitle = ref('')

function startEditHabit(id: string) {
  const h = taskStore.habits.find(x => x.id === id)
  if (!h) return
  editingHabitId.value = id
  editTitle.value = h.title
  editRewardPoints.value = h.rewardPoints
}

function saveHabit() {
  if (!editingHabitId.value) return
  taskStore.updateHabit(editingHabitId.value, {
    title: editTitle.value.trim(),
    rewardPoints: editRewardPoints.value,
  })
  alert('习惯保存成功 ✅')
}

function addStep() {
  if (!editingHabitId.value || !newStep.value.trim()) return
  taskStore.addStepToHabit(editingHabitId.value, newStep.value.trim())
  newStep.value = ''
}

function removeStep(habitId: string, index: number) {
  taskStore.removeHabitStep(habitId, index)
}

function createHabit() {
  if (!newHabitTitle.value.trim()) return
  const habit = taskStore.createNewHabit(newHabitTitle.value.trim())
  newHabitTitle.value = ''
  startEditHabit(habit.id)
}

function deleteHabit(id: string, title: string) {
  if (!confirm(`确定要停用习惯「${title}」吗？可在「任务清单」中恢复。`)) return
  if (editingHabitId.value === id) editingHabitId.value = null
  taskStore.deleteHabit(id)
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
  const parentTask = parentStore.parentTaskTemplates.find(t => t.id === taskId)
  newSubtaskWeekDay.value = parentTask?.weekDay ?? ''
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

function onDragEnter(_taskId: string, subtaskId: string, event: DragEvent) {
  if (subtaskId === dragSubtaskId.value) return
  // Ignore enter events bubbling from children within the same row
  const target = event.currentTarget as HTMLElement | null
  const related = event.relatedTarget as Node | null
  if (target && target.contains(related)) return
  dragOverSubtaskId.value = subtaskId
}

function onDragLeave(_taskId: string, subtaskId: string, event: DragEvent) {
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
  if (/^\d+$/.test(taskId)) {
    task.subTasks.forEach(s => {
      if (/^\d+$/.test(s.id)) {
        api.tasks.subtasks.update(taskId, s.id, { sortOrder: s.sortOrder }).catch(() => {})
      }
    })
  }

  dragSubtaskId.value = null
  dragOverSubtaskId.value = null
}

// Helper to get sub-tasks for the expanded task (safer for template access)
function getSubTasks(taskId: string) {
  return parentStore.parentTaskTemplates.find(t => t.id === taskId)?.subTasks
}

// ── Auto-expand first task on mount + load all subtasks ──
onMounted(async () => {
  await loadData()
  if (parentStore.parentTaskTemplates.length) {
    showSubTasks(parentStore.parentTaskTemplates[0].id)
  }
  await loadAllSubtasks()
})

watch(() => parentStore.parentTaskTemplates.length, (len) => {
  if (len && !expandedTaskId.value) {
    showSubTasks(parentStore.parentTaskTemplates[0].id)
  }
})


// Load all subtasks for all tasks (so child page can see them)
async function loadAllSubtasks() {
  const tasks = parentStore.parentTaskTemplates.filter(t => /^\d+$/.test(t.id))
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

const allTasks = computed(() => parentStore.parentTaskTemplates.filter(t => t.active !== false))

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

async function downloadPdf() {
  if (downloading.value) return
  downloading.value = true
  try {
    const element = document.getElementById('printable-sheet-pdf')
    if (!element) return

    const html2canvas = await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js', 'html2canvas')
    const { jsPDF } = await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js', 'jspdf')

    await new Promise(r => setTimeout(r, 300))

    const canvas = await html2canvas(element, {
      scale: 3,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width

    let srcY = 0
    let remainingHeight = pdfHeight
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

    pdf.save(`${userStore.profile.name || '孩子'}的每日任务与习惯清单.pdf`)
  } catch {
    alert('下载失败，请检查网络连接后重试')
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <div class="page">
    <ChildSelector />

    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📋 任务与习惯管理</span>
        <h1>管理任务和核心习惯</h1>
        <p class="lead">创建每日任务，设定每周主线习惯 SOP，所有内容会同步到孩子的打卡页面。完成后可在打印预览生成清单。</p>
        <div style="margin-top:14px;display:flex;gap:10px">
          <button class="btn secondary" :disabled="downloading" @click="downloadPdf">
            {{ downloading ? '⏳ 生成中...' : '📥 导出 PDF' }}
          </button>
        </div>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center">
        <div class="card-title">
          <h2>概览</h2>
          <span class="tag">{{ allTasks.length }} 个任务 · {{ taskStore.habits.reduce((s, h) => s + h.steps.length, 0) }} 个步骤</span>
        </div>
        <div class="stat-row">
          <div class="mini-stat">
            <strong>{{ allTasks.length }}</strong>
            <span>任务</span>
          </div>
          <div class="mini-stat">
            <strong>{{ taskStore.habits.length }}</strong>
            <span>习惯总数</span>
          </div>

          <div class="mini-stat">
            <strong>{{ taskStore.habits.reduce((s, h) => s + h.steps.length, 0) }}</strong>
            <span>总步骤数</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tab Bar -->
    <section class="tab-bar-section">
      <div class="tab-bar-manager two-tabs">
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
            适用日期
            <button
              type="button"
              class="btn weekday-btn"
              style="margin-top:6px;width:100%"
              @click="showWeekdayPicker = true"
            >
              {{ weekDayToLabel(taskWeekDay) }}
            </button>
            <WeekdayPicker v-model="taskWeekDay" v-model:visible="showWeekdayPicker" />
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
          <label style="display:block;margin-top:14px;margin-bottom:6px">
            <input v-model="description" class="input" style="margin-top:6px" placeholder="任务描述（可选）" />
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
              <template v-if="taskEditId === template.id">
                <div style="display:flex;flex-direction:column;gap:8px;flex:1;min-width:0">
                  <input v-model="taskEditTitle" class="input" placeholder="任务标题" @keyup.enter="saveEdit(template.id)" />
                  <input v-model="taskEditDesc" class="input" placeholder="任务描述" @keyup.enter="saveEdit(template.id)" />
                  <div style="display:flex;gap:8px;flex-wrap:wrap">
                    <select v-model="taskEditType" class="input" style="flex:1;min-width:100px">
                      <option v-for="cat in categoryOptions" :key="cat.value" :value="cat.value">{{ cat.icon }} {{ cat.label }}</option>
                    </select>
                    <input v-model.number="taskEditPoints" class="input" type="number" min="5" max="100" step="5" style="width:80px" />
                    <div class="icon-picker" style="display:flex;gap:4px;flex-wrap:wrap">
                      <button v-for="ico in iconOptions" :key="ico" class="icon-btn-sm" :class="{ active: taskEditIcon === ico }" @click="taskEditIcon = ico">{{ ico }}</button>
                    </div>
                  </div>
                  <div style="display:flex;gap:6px">
                    <button class="btn" style="padding:4px 14px;font-size:13px" @click="saveEdit(template.id)">保存</button>
                    <button class="btn ghost" style="padding:4px 14px;font-size:13px" @click="cancelEdit">取消</button>
                  </div>
                </div>
              </template>
              <template v-else>
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
                  <button class="btn ghost" style="padding:6px 12px;font-size:13px" @click="startEdit(template)">编辑</button>
                  <button class="btn ghost" style="padding:6px 12px;font-size:13px" @click="deleteTask(template.id)">删除</button>
                </div>
              </template>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:32px">还没有创建任务。在左侧表单中创建第一个任务吧 ✨</p>
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
          子任务默认继承任务的适用日期，每个子任务也可以单独调整。子任务仅在匹配的日期显示给孩子。
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
                <span class="mini-tag">{{ weekDayToLabel(sub.weekDay) }}</span>

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
          <button
            type="button"
            class="btn ghost subtask-weekday-btn"
            @click="showSubtaskWeekdayPicker = true"
          >
            {{ weekDayToLabel(newSubtaskWeekDay) }}
          </button>
          <WeekdayPicker v-model="newSubtaskWeekDay" v-model:visible="showSubtaskWeekdayPicker" />
          <button
            class="btn"
            :disabled="!newSubtaskTitle.trim()"
            @click="addSubtask(expandedTaskId!)"
          >
            + 添加
          </button>
          <button
            class="btn secondary"
            style="font-size:13px;padding:4px 12px"
            @click="openSubTaskPicker"
          >
            📦 从库选择
          </button>
        </div>
      </div>
    </section>

    <!-- ── Tab 2: Habit Management ── -->
    <section v-show="activeTab === 'habits'">
      <div class="grid-2">
        <div class="panel">
          <div class="card-title">
            <h2>所有习惯</h2>
            <span class="tag">{{ taskStore.habits.length }} 个</span>
          </div>
          <p class="lead" style="font-size:14px;margin-bottom:12px">点击习惯名称展开编辑，所有习惯并列展示给孩子。</p>
          <div v-if="taskStore.habits.length" class="list">
            <div v-for="habit in taskStore.habits" :key="habit.id" class="list-row" style="flex-direction:column;align-items:stretch;gap:8px;cursor:pointer" @click="startEditHabit(habit.id)">
              <div style="display:flex;align-items:center;gap:12px">
                <strong :style="{ flex: 1, color: editingHabitId === habit.id ? 'var(--primary)' : '' }">{{ habit.title }}</strong>
                <span class="muted" style="font-size:13px">{{ habit.steps.length }} 步 · ☀️ +{{ habit.rewardPoints }}/步</span>
                <button class="btn ghost" style="padding:4px 10px;font-size:12px;color:#c00" @click.stop="deleteHabit(habit.id, habit.title)">删除</button>
              </div>
              <!-- Expanded editor -->
              <div v-if="editingHabitId === habit.id" class="habit-editor" style="padding:12px;background:var(--bg);border-radius:12px;margin-top:4px" @click.stop>
                <div class="card-title" style="margin-bottom:8px">
                  <h3>编辑习惯</h3>
                  <button class="btn secondary" style="font-size:13px;padding:4px 14px" @click="saveHabit">保存</button>
                </div>
                <label style="font-weight:800;display:block;margin-bottom:4px;font-size:13px">习惯名称</label>
                <input v-model="editTitle" class="input" style="margin-bottom:10px" placeholder="习惯名称" />
                <label style="font-weight:800;display:block;margin-bottom:4px;font-size:13px">每步奖励阳光值</label>
                <input v-model.number="editRewardPoints" class="input" type="number" min="1" max="100" step="1" style="margin-bottom:12px;width:100px" />

                <h4 style="margin:12px 0 8px;font-size:13px">步骤</h4>
                <div v-if="habit.steps.length" class="list" style="margin-bottom:8px">
                  <div v-for="(step, sIdx) in habit.steps" :key="sIdx" class="list-row" style="justify-content:flex-start;gap:10px;padding:6px 10px">
                    <b class="step-num" style="width:24px;height:24px;font-size:12px">{{ step.order }}</b>
                    <span style="flex:1;font-size:14px">{{ step.instruction }}</span>
                    <button class="btn ghost" style="padding:4px 8px;font-size:11px;color:#c00" @click="removeStep(habit.id, sIdx)">删除</button>
                  </div>
                </div>
                <p v-else class="muted" style="text-align:center;padding:8px;font-size:13px">暂无步骤</p>
                <div style="display:flex;gap:6px">
                  <input v-model="newStep" class="input" style="font-size:13px" placeholder="新步骤说明" @keyup.enter="addStep" />
                  <button class="btn" style="font-size:13px;padding:4px 12px" :disabled="!newStep.trim()" @click="addStep">添加</button>
                  <button class="btn secondary" style="font-size:13px;padding:4px 12px" @click="openStepPicker">📦 从库选择</button>
                </div>
              </div>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:24px">暂无习惯，请在右侧创建第一个习惯 ✨</p>
        </div>

        <div class="panel">
          <div class="card-title">
            <h2>创建新习惯</h2>
          </div>
          <p class="lead" style="margin-bottom:12px;font-size:14px">新习惯会直接添加到列表中，所有习惯并列展示。</p>
          <div style="display:flex;gap:8px">
            <input v-model="newHabitTitle" class="input" placeholder="习惯名称（如：整理书包 SOP）" @keyup.enter="createHabit" />
            <button class="btn secondary" :disabled="!newHabitTitle.trim()" @click="createHabit">创建</button>
          </div>
        </div>
      </div>
    </section>
  </div>

    <!-- ── Sub-task Picker Modal ── -->
    <InventoryPickerModal
      :visible="subTaskPickerVisible"
      type="subtask"
      :items="subTaskLibrary"
      @close="subTaskPickerVisible = false"
      @select="onSubTaskSelected"
    />

    <!-- ── Step Picker Modal ── -->
    <InventoryPickerModal
      :visible="stepPickerVisible"
      type="step"
      :items="stepLibrary"
      @close="stepPickerVisible = false"
      @select="onStepSelected"
    />

    <!-- ── PDF Printable Sheet (hidden) ── -->
    <div id="printable-sheet-pdf" class="pdf-sheet">
      <div class="pdf-top">
        <div class="pdf-title-row">
          <h1>每日计划清单</h1>
          <div class="pdf-info">
            <span>{{ userStore.profile.name || '______' }}</span>
            <span class="pdf-dot">·</span>
            <span>{{ userStore.profile.grade ? userStore.profile.grade + '年级' : '______' }}</span>
            <span class="pdf-dot">·</span>
            <span>{{ dateStr }}</span>
          </div>
        </div>
      </div>

      <div class="pdf-body">
        <div class="pdf-col">
          <h2 class="pdf-col-title">📋 今日任务</h2>
          <div v-if="allTasks.length" class="pdf-items">
            <div v-for="task in allTasks" :key="task.id" class="pdf-item">
              <div class="pdf-item-top">
                <span class="pdf-box">□</span>
                <span class="pdf-item-icon">{{ task.icon }}</span>
                <span class="pdf-item-label">{{ task.title }}</span>
                <span class="pdf-item-pts">+{{ task.rewardPoints }}</span>
              </div>
              <div v-if="task.subTasks?.length" class="pdf-subs">
                <div v-for="sub in task.subTasks" :key="sub.id" class="pdf-sub">
                  <span class="pdf-box pdf-box-sm">□</span>
                  <span>{{ sub.title }}</span>
                </div>
              </div>
            </div>
            <div class="pdf-item pdf-item-note">
              <div class="pdf-item-top">
                <span class="pdf-box">□</span>
                <span class="pdf-item-icon">💬</span>
                <span class="pdf-item-label">家长寄语</span>
              </div>
            </div>
          </div>
          <div v-else class="pdf-empty">暂无任务</div>
        </div>

        <div class="pdf-col">
          <h2 class="pdf-col-title">🌱 每日习惯</h2>
          <div v-if="taskStore.habits.length" class="pdf-items">
            <div v-for="habit in taskStore.habits" :key="habit.id" class="pdf-habit-block">
              <div class="pdf-habit-head">
                <span>{{ habit.title }}</span>
                <span class="pdf-item-pts">+{{ habit.rewardPoints }}/步</span>
              </div>
              <div v-if="habit.steps.length" class="pdf-subs">
                <div v-for="step in habit.steps" :key="step.order" class="pdf-sub">
                  <span class="pdf-box pdf-box-sm">□</span>
                  <span>{{ step.instruction }}</span>
                </div>
              </div>
              <div v-else class="pdf-empty" style="padding:4px 0;border:none">暂未设置步骤</div>
            </div>
          </div>
          <div v-else class="pdf-empty">暂无习惯</div>
        </div>
      </div>
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
.tab-bar-manager.two-tabs {
  grid-template-columns: 1fr 1fr;
}
.tab-slider-manager {
  position: absolute;
  top: 6px; bottom: 6px;
  width: calc(50% - 8px);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tab-slider-manager.slide-tasks { transform: translateX(0); left: 6px; }
.tab-slider-manager.slide-habits { transform: translateX(100%); left: 6px; }

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

button:disabled {
  opacity: .5;
  cursor: not-allowed;
}
.weekday-btn {
  background: #e3f2fd;
  border: 2px solid #90caf9;
  color: #1565c0;
  font-weight: 800;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  box-shadow: none;
  transition: all .12s ease;
}
.weekday-btn:hover {
  background: #bbdefb;
  box-shadow: none;
  transform: none;
}
.icon-btn-sm {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 2px solid var(--line);
  background: #fff;
  font-size: 16px;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all .12s ease;
  padding: 0;
}
.icon-btn-sm:hover {
  border-color: var(--primary);
  background: #ecffd9;
}
.icon-btn-sm.active {
  border-color: var(--primary);
  background: #d9f5c8;
}

@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .tab-btn { font-size: 13px; padding: 12px 8px; }
}

/* ── PDF Printable Sheet (hidden from screen) ── */
.pdf-sheet {
  position: absolute;
  left: -9999px;
  top: 0;
  width: 794px;
  background: #fff;
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 500;
  padding: 32px 36px;
  font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  line-height: 1.6;
}

/* ── Top Header ── */
.pdf-top {
  border-bottom: 2px solid #333;
  padding-bottom: 14px;
  margin-bottom: 20px;
}
.pdf-title-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
}
.pdf-title-row h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: #1a1a1a;
}
.pdf-info {
  font-size: 13px;
  color: #555;
  font-weight: 500;
}
.pdf-dot {
  margin: 0 6px;
  color: #bbb;
}

/* ── Two-Column Body ── */
.pdf-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}
.pdf-col {
  min-width: 0;
}
.pdf-col-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #ccc;
  color: #1a1a1a;
}

/* ── Task & Habit Items ── */
.pdf-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.pdf-item {
  border: 1px solid #ccc;
  padding: 8px 10px;
}
.pdf-item-note {
  border-style: dashed;
  opacity: .7;
}
.pdf-item-top {
  display: flex;
  align-items: center;
  gap: 6px;
}
.pdf-box {
  font-size: 16px;
  color: #333;
  flex-shrink: 0;
  line-height: 1;
}
.pdf-box-sm {
  font-size: 13px;
}
.pdf-item-icon {
  font-size: 16px;
  flex-shrink: 0;
  line-height: 1;
}
.pdf-item-label {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  min-width: 0;
}
.pdf-item-pts {
  font-size: 11px;
  color: #888;
  flex-shrink: 0;
}

/* ── Subtasks ── */
.pdf-subs {
  margin-top: 4px;
  padding-left: 22px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.pdf-sub {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #444;
}

/* ── Habit Block ── */
.pdf-habit-block {
  border: 1px solid #ccc;
  padding: 8px 10px;
}
.pdf-habit-block + .pdf-habit-block {
  margin-top: 4px;
}
.pdf-habit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  padding-bottom: 4px;
  margin-bottom: 4px;
  border-bottom: 1px solid #ddd;
}

/* ── Empty ── */
.pdf-empty {
  text-align: center;
  padding: 20px;
  color: #bbb;
  font-size: 13px;
  border: 1px dashed #ddd;
}
</style>
