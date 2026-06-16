<script setup lang="ts">
import { computed, ref } from 'vue'
import { categoryLabels, weekdaysShort } from '../../utils/constants'
import { useParentStore, useTaskStore, useUserStore } from '../../stores'

const taskStore = useTaskStore()
const userStore = useUserStore()
const parentStore = useParentStore()

const selectedIds = ref<Set<string>>(new Set(taskStore.todayTasks.map(t => t.id)))

const progressPercent = computed(() =>
  Math.round((taskStore.weeklyProgress / Math.max(taskStore.todayTasks.length, 1)) * 100)
)

const allAvailableTasks = computed(() => {
  const parentTasks = parentStore.parentTaskTemplates.map(t => ({
    ...t,
    status: 'pending' as const,
  }))
  // merge seeded + parent; avoid duplicating by id
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

const selectedTasks = computed(() =>
  allAvailableTasks.value.filter(t => selectedIds.value.has(t.id))
)

function toggleTask(id: string) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
}

function printChecklist() {
  window.setTimeout(() => window.print(), 150)
}
</script>

<template>
  <div class="page habit-page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">✅ 每日打卡中心</span>
        <h1>选择今天的打卡任务</h1>
        <p class="lead">勾选要纳入打印清单的任务。家长可在「任务管理」中创建自定义任务，所有任务支持每日打卡追踪。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>本周进度 {{ taskStore.weeklyProgress }}/{{ taskStore.todayTasks.length }}</h2>
          <span class="tag">第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span>
        </div>
        <div class="progress">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>
        <p class="lead">主线习惯：{{ taskStore.currentWeekHabit.title }}</p>
      </div>
    </section>

    <section class="grid-3">
      <div
        v-for="step in taskStore.currentWeekHabit.steps"
        :key="step.order"
        class="step"
      >
        <b>{{ step.order }}</b>
        <h3>{{ step.instruction }}</h3>
        <p class="muted">完成后在纸质打卡单对应格子打勾。</p>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>选择打卡任务</h2>
          <span class="tag">{{ selectedTasks.length }} 个已选</span>
        </div>
        <div class="list">
          <div
            v-for="task in allAvailableTasks"
            :key="task.id"
            class="list-row task-select-row"
            :class="{ active: selectedIds.has(task.id) }"
            @click="toggleTask(task.id)"
          >
            <div class="task-info">
              <span class="task-icon">{{ task.icon }}</span>
              <div>
                <strong>{{ task.title }}</strong>
                <span class="muted">{{ task.description }}</span>
              </div>
            </div>
            <div class="task-meta">
              <span class="mini-tag">{{ categoryLabels[task.type] || task.type }}</span>
              <input
                type="checkbox"
                :checked="selectedIds.has(task.id)"
                class="check-box"
                @click.stop
                @change="toggleTask(task.id)"
              />
            </div>
          </div>
        </div>
        <p v-if="!allAvailableTasks.length" class="muted" style="text-align:center;padding:24px">
          暂无可选任务，请前往家长端「任务管理」创建。
        </p>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>A4 打印预览</h2>
          <span class="tag">{{ selectedTasks.length }} 个任务</span>
        </div>
        <div class="preview-paper">
          <h3>{{ userStore.profile.name }} 的本周打卡单</h3>
          <div class="list">
            <div v-for="day in weekdaysShort" :key="day" class="list-row">
              <span style="font-weight:800">{{ day }}</span>
              <span v-if="!selectedTasks.length" class="muted">请先选择任务</span>
              <span v-for="task in selectedTasks" :key="task.id" class="check-cell">
                {{ task.icon }} □
              </span>
            </div>
          </div>
        </div>
        <button class="btn" style="margin-top:16px;width:100%" @click="printChecklist">
          🖨️ 打印打卡单
        </button>
        <p class="lead" style="margin-top:8px;text-align:center">
          每日打卡完成勾选，周末拍照上传至题库存档。
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.task-select-row {
  cursor: pointer;
  transition: background .15s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.task-select-row:hover {
  background: rgba(128, 220, 103, .12);
}
.task-select-row.active {
  background: #ecffd9;
  border-color: var(--primary);
}
.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.task-info strong {
  display: block;
  font-size: 16px;
}
.task-info .muted {
  font-size: 13px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-icon {
  font-size: 28px;
  flex-shrink: 0;
}
.task-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.mini-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}
.check-box {
  width: 22px;
  height: 22px;
  accent-color: var(--primary);
  cursor: pointer;
}
.check-cell {
  font-size: 14px;
  white-space: nowrap;
}
@media print {
  .hero-card, .btn, .task-select-row, .task-meta { display: none !important; }
}
</style>
