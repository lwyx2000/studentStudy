<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useChildSelectStore, useParentStore } from '../../stores'
import { api, normalizeSubTask } from '../../utils/api'
import type { TaskCategory } from '../../types'
import ChildSelector from '../../components/ChildSelector.vue'

const parentStore = useParentStore()
const childSelectStore = useChildSelectStore()

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

// ── Sub-task Management ──
const expandedTaskId = ref<string | null>(null)
const newSubtaskTitle = ref('')
const newSubtaskWeekDay = ref('')
const newSubtaskType = ref<TaskCategory | ''>('')

// Drag-and-drop state
const dragSubtaskId = ref<string | null>(null)
const dragOverSubtaskId = ref<string | null>(null)

function subtaskWeekDayLabel(wd?: string): string {
  if (!wd) return '每天'
  if (wd === 'weekday') return '📅 平时'
  if (wd === 'weekend') return '🎉 周末'
  return wd
}

function getSubTasks(taskId: string) {
  return parentStore.parentTaskTemplates.find(t => t.id === taskId)?.subTasks
}

async function showSubTasks(taskId: string) {
  expandedTaskId.value = taskId
  newSubtaskTitle.value = ''
  newSubtaskWeekDay.value = ''
  newSubtaskType.value = ''
  dragSubtaskId.value = null
  dragOverSubtaskId.value = null

  // Load sub-tasks from backend if task has numeric ID
  const hasBackendId = /^\d+$/.test(taskId)
  if (!hasBackendId) return
  try {
    const res = await api.tasks.getTask(taskId)
    if (res?.sub_tasks?.length) {
      const backendSubTasks = res.sub_tasks.map(normalizeSubTask)
      const task = parentStore.parentTaskTemplates.find(t => t.id === taskId)
      if (task) {
        const localOnly = (task.subTasks || []).filter(s => !/^\d+$/.test(s.id))
        const merged = [...backendSubTasks, ...localOnly]
        task.subTasks = merged
        parentStore.updateTaskTemplate(taskId, { subTasks: [...merged] })
      }
    }
  } catch { /* offline */ }
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

  // Sync to backend
  const hasBackendId = /^\d+$/.test(taskId)
  if (hasBackendId) {
    api.tasks.subtasks.add(taskId, {
      title: newSubtaskTitle.value.trim(),
      type: subtaskType,
      weekDay: newSubtaskWeekDay.value || undefined,
      sortOrder,
    }).then((res: any) => {
      const backendId = String(res.pk_sub_tasks ?? '')
      if (backendId && task.subTasks) {
        const idx = task.subTasks.findIndex(s => s.id === localId)
        if (idx !== -1) {
          task.subTasks[idx].id = backendId
          parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })
        }
      }
    }).catch(() => {})
  }

  newSubtaskTitle.value = ''
  newSubtaskWeekDay.value = ''
  newSubtaskType.value = ''
}

function removeSubtask(taskId: string, subtaskId: string) {
  const task = parentStore.parentTaskTemplates.find(t => t.id === taskId)
  if (!task?.subTasks) return
  const hasBackendId = /^\d+$/.test(subtaskId)
  task.subTasks = task.subTasks.filter(s => s.id !== subtaskId)
  task.subTasks.forEach((s, i) => { s.sortOrder = i })
  parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })
  if (hasBackendId) {
    api.tasks.subtasks.remove(taskId, subtaskId).catch(() => {})
  }
}

// ── Drag-and-drop handlers ──

function onDragStart(subtaskId: string, event: DragEvent) {
  dragSubtaskId.value = subtaskId
  event.dataTransfer?.setData('text/plain', subtaskId)
  event.dataTransfer!.effectAllowed = 'move'
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
  const target = event.currentTarget as HTMLElement | null
  const related = event.relatedTarget as Node | null
  if (target && target.contains(related)) return
  dragOverSubtaskId.value = subtaskId
}

function onDragLeave(taskId: string, subtaskId: string, event: DragEvent) {
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

  const [moved] = task.subTasks.splice(fromIdx, 1)
  task.subTasks.splice(toIdx, 0, moved)
  task.subTasks.forEach((s, i) => { s.sortOrder = i })
  parentStore.updateTaskTemplate(taskId, { subTasks: [...task.subTasks] })

  dragSubtaskId.value = null
  dragOverSubtaskId.value = null
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

// ── Task CRUD ──

async function createTask() {
  if (!title.value.trim()) return
  const childId = childSelectStore.selectedChildId ?? undefined

  const template = parentStore.addTaskTemplate({
    title: title.value.trim(),
    description: description.value.trim(),
    type: type.value,
    rewardPoints: rewardPoints.value,
    icon: icon.value,
    status: 'pending',
  })

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
    } catch { /* offline */ }
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
    api.tasks.delete(id).catch(() => {})
  }
  parentStore.deleteTaskTemplate(id)
  // Auto-switch to another task if the deleted one was active
  if (expandedTaskId.value === id) {
    const remaining = parentStore.parentTaskTemplates
    expandedTaskId.value = remaining.length ? remaining[0].id : null
  }
}
</script>

<template>
  <div class="page">
    <ChildSelector />
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📋 任务管理中心</span>
        <h1>创建和管理孩子的每日任务</h1>
        <p class="lead">自定义任务会出现在孩子的仪表盘和每日打卡页面中。按类别整理任务，帮助孩子建立结构化的日常习惯。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>任务模板库</h2>
          <span class="tag">{{ parentStore.parentTaskTemplates.length }} 个模板</span>
        </div>
        <div class="kpi">
          <strong>{{ parentStore.parentTaskTemplates.length }}</strong>
          <span>已创建任务模板</span>
        </div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <span
            v-for="cat in categoryOptions"
            :key="cat.value"
            class="tag"
          >
            {{ cat.icon }} {{ cat.label }}
          </span>
        </div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>添加新任务</h2>
          <span class="tag">{{ categoryOptions.find(c => c.value === type)?.icon }} {{ categoryOptions.find(c => c.value === type)?.label }}</span>
        </div>
        <label style="display:block;font-weight:800;margin-bottom:6px">
          任务标题
          <input
            v-model="title"
            class="input"
            style="margin-top:6px"
            placeholder="例如：晨间朗读 10 分钟"
          />
        </label>
        <label style="display:block;font-weight:800;margin-top:14px;margin-bottom:6px">
          任务描述
          <input
            v-model="description"
            class="input"
            style="margin-top:6px"
            placeholder="具体要求和步骤说明"
          />
        </label>
        <div class="grid-2" style="margin-top:14px">
          <label style="font-weight:800">
            任务类别
            <select v-model="type" class="input" style="margin-top:6px">
              <option
                v-for="cat in categoryOptions"
                :key="cat.value"
                :value="cat.value"
              >
                {{ cat.icon }} {{ cat.label }}
              </option>
            </select>
          </label>
          <label style="font-weight:800">
            奖励阳光值
            <input
              v-model.number="rewardPoints"
              class="input"
              style="margin-top:6px"
              type="number"
              min="5"
              max="100"
              step="5"
            />
          </label>
        </div>
        <label style="display:block;font-weight:800;margin-top:14px;margin-bottom:6px">
          图标选择
          <div class="icon-picker" style="margin-top:6px">
            <button
              v-for="ico in iconOptions"
              :key="ico"
              class="icon-btn"
              :class="{ active: icon === ico }"
              @click="icon = ico"
            >
              {{ ico }}
            </button>
          </div>
        </label>
        <button
          class="btn"
          style="margin-top:20px;width:100%"
          :disabled="!title.trim()"
          @click="createTask"
        >
          ✨ 创建任务
        </button>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>已创建任务</h2>
          <span class="tag">{{ parentStore.parentTaskTemplates.length }} 项</span>
        </div>
        <div v-if="parentStore.parentTaskTemplates.length" class="list">
          <div
            v-for="template in parentStore.parentTaskTemplates"
            :key="template.id"
            class="list-row task-row"
            :class="{ 'task-row-active': expandedTaskId === template.id }"
            @click="showSubTasks(template.id)"
          >
            <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
              <span style="font-size:28px;flex-shrink:0">{{ template.icon }}</span>
              <div style="min-width:0">
                <strong>{{ template.title }}</strong>
                <span class="muted" style="display:block;font-size:13px">
                  {{ template.description || '无描述' }}
                </span>
                <div style="display:flex;gap:6px;margin-top:4px">
                  <span class="mini-tag">
                    {{ categoryOptions.find(c => c.value === template.type)?.label || template.type }}
                  </span>
                  <span class="mini-tag">☀️ +{{ template.rewardPoints }}</span>
                </div>
              </div>
            </div>
            <div style="display:flex;gap:6px;flex-shrink:0;align-items:center" @click.stop>
              <button class="btn ghost" style="padding:6px 12px;font-size:13px" @click="deleteTask(template.id)">删除</button>
            </div>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">
          还没有创建任务模板。在左侧表单中创建第一个任务吧 ✨
        </p>
      </div>
    </section>

    <!-- ── Sub-task panel (expanded) ── -->
    <section v-if="expandedTaskId" class="subtask-section">
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
          <button class="btn" :disabled="!newSubtaskTitle.trim()" @click="addSubtask(expandedTaskId!)">+ 添加</button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
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

/* ── Sub-task ── */
.subtask-section {
  margin-top: 6px;
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
  flex-shrink: 0;
  transition: color .12s ease;
  touch-action: none;
  cursor: grab;
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

button:disabled {
  opacity: .5;
  cursor: not-allowed;
}
</style>
