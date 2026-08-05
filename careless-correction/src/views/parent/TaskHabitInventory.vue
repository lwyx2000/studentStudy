<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useChildSelectStore } from '../../stores'
import { api } from '../../utils/api'
import { categoryLabels, weekDayToLabel } from '../../utils/constants'
import ChildSelector from '../../components/ChildSelector.vue'

const childSelectStore = useChildSelectStore()

function formatDate(dateStr?: string): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '—'
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  const dateLabel = `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
  if (diffDays === 0) return `今天 · ${dateLabel}`
  if (diffDays === 1) return `昨天 · ${dateLabel}`
  if (diffDays < 30) return `${diffDays}天前 · ${dateLabel}`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}个月前 · ${dateLabel}`
  return `${Math.floor(diffDays / 365)}年前 · ${dateLabel}`
}

const activeTab = ref<'subtasks' | 'habits'>('subtasks')
const subTaskLibrary = ref<any[]>([])
const habitStepLibrary = ref<any[]>([])
const loading = ref(false)

const totalSubTasks = computed(() => subTaskLibrary.value.length)
const totalHabitSteps = computed(() => habitStepLibrary.value.length)

// 按来源习惯分组
const groupedSteps = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const step of habitStepLibrary.value) {
    const key = step.habit_title || '未分类'
    if (!groups[key]) groups[key] = []
    groups[key].push(step)
  }
  return Object.entries(groups).map(([title, steps]) => ({
    title,
    steps: steps.sort((a, b) => a.order - b.order),
    count: steps.length,
  }))
})

async function loadLibraries() {
  loading.value = true
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    const res = await api.tasks.getSubTaskLibrary(childId)
    subTaskLibrary.value = res.subtasks ?? []
  } catch { /* offline */ }
  try {
    const res = await api.habits.getStepLibrary(childId)
    habitStepLibrary.value = res.steps ?? []
  } catch { /* offline */ }
  loading.value = false
}

watch(() => childSelectStore.selectedChildId, () => loadLibraries())
onMounted(loadLibraries)
</script>

<template>
  <div class="page">
    <ChildSelector />

    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📦 复用库</span>
        <h1>子任务与习惯步骤库</h1>
        <p class="lead">
          此处显示所有已创建的子任务和习惯步骤，可在创建任务或习惯时直接复用，避免重复输入。
        </p>
        <button class="btn secondary" :disabled="loading" @click="loadLibraries">
          {{ loading ? '⏳ 加载中...' : '🔄 刷新' }}
        </button>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center">
        <div class="card-title">
          <h2>统计</h2>
        </div>
        <div class="stat-row">
          <div class="mini-stat">
            <strong>{{ totalSubTasks }}</strong>
            <span>子任务</span>
          </div>
          <div class="mini-stat">
            <strong>{{ totalHabitSteps }}</strong>
            <span>习惯步骤</span>
          </div>
          <div class="mini-stat">
            <strong>{{ groupedSteps.length }}</strong>
            <span>来源习惯</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tabs -->
    <section class="tab-bar-section">
      <div class="tab-bar-manager">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'subtasks' }"
          @click="activeTab = 'subtasks'"
        >
          📋 子任务库
          <span class="badge">{{ totalSubTasks }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'habits' }"
          @click="activeTab = 'habits'"
        >
          🌱 习惯库
          <span class="badge">{{ totalHabitSteps }}</span>
        </button>
        <div class="tab-slider" :class="{ 'slide-right': activeTab === 'habits' }" />
      </div>
    </section>

    <!-- 子任务库 -->
    <section v-show="activeTab === 'subtasks'">
      <div v-if="loading" class="panel" style="text-align:center;padding:24px">
        <p class="muted">⏳ 加载中...</p>
      </div>
      <div v-else-if="subTaskLibrary.length" class="list">
        <div v-for="(s, i) in subTaskLibrary" :key="s.pk_sub_tasks || i" class="list-row">
          <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
            <span class="sub-index">{{ i + 1 }}</span>
            <div style="min-width:0">
              <strong>{{ s.title }}</strong>
              <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
                <span class="mini-tag">{{ categoryLabels[s.type] || s.type }}</span>
                <span v-if="s.week_day" class="mini-tag" style="background:#e3f2fd">📅 {{ weekDayToLabel(s.week_day) }}</span>
                <span class="mini-tag" style="background:#f0fdf4;color:#166534">源自：{{ s.task_title || '未知任务' }}</span>
              </div>
            </div>
          </div>
          <div class="stat-chip" style="flex-shrink:0">
            🕐 {{ formatDate(s.created_at) }}
          </div>
        </div>
      </div>
      <div v-else class="panel" style="text-align:center;padding:32px">
        <p class="muted">暂无子任务，在「任务与习惯」中创建任务并添加子任务后就会出现在这里。</p>
      </div>
    </section>

    <!-- 习惯库（按来源习惯分组展示可复用步骤） -->
    <section v-show="activeTab === 'habits'">
      <div v-if="loading" class="panel" style="text-align:center;padding:24px">
        <p class="muted">⏳ 加载中...</p>
      </div>
      <template v-else-if="habitStepLibrary.length">
        <div
          v-for="(group, gIdx) in groupedSteps"
          :key="gIdx"
          class="habit-group"
        >
          <div class="group-header">
            <span class="group-icon">🌱</span>
            <strong>{{ group.title }}</strong>
            <span class="mini-tag" style="background:#e8f5e9;color:#2e7d32">{{ group.count }} 个可复用步骤</span>
          </div>
          <div class="list">
            <div
              v-for="(step, sIdx) in group.steps"
              :key="step.pk_sop_steps || sIdx"
              class="list-row step-row"
            >
              <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
                <b class="step-num">{{ step.order }}</b>
                <div style="min-width:0;flex:1">
                  <strong>{{ step.instruction }}</strong>
                  <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
                    <span class="mini-tag" style="background:#f0fdf4;color:#166534">源自：{{ step.habit_title }}</span>
                    <span v-if="step.image_url" class="mini-tag">🖼️ 有图示</span>
                    <span v-if="step.gif_url" class="mini-tag">🎬 有动图</span>
                  </div>
                </div>
              </div>
              <span class="reuse-hint">可复用</span>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="panel" style="text-align:center;padding:32px">
        <p class="muted">暂无习惯步骤，在「任务与习惯」中创建习惯并添加步骤后就会出现在这里。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.tab-bar-section {
  margin-bottom: 18px;
}
.tab-bar-manager {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
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
  transition: color 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.tab-btn.active {
  color: #2e7d32;
}
.tab-slider {
  position: absolute;
  top: 6px;
  bottom: 6px;
  left: 6px;
  width: calc(50% - 8px);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1;
}
.tab-slider.slide-right {
  transform: translateX(100%);
}
.badge {
  background: #e8f5e9;
  color: #2e7d32;
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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
}
.mini-stat span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.list-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: #fff;
  transition: all 0.12s ease;
}
.list-row + .list-row {
  margin-top: 6px;
}
.list-row:hover {
  border-color: var(--primary-2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
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
.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  background: var(--surface);
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  white-space: nowrap;
}
.sub-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--primary-2);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  flex-shrink: 0;
}

/* 习惯库分组样式 */
.habit-group {
  margin-bottom: 20px;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 8px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f0fdf4, #e8f5e9);
  border: 1px solid #c8e6c9;
}
.group-header strong {
  font-size: 15px;
  color: #1b5e20;
}
.group-icon {
  font-size: 18px;
}
.step-row {
  padding: 12px 16px;
}
.step-num {
  display: inline-grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-size: 13px;
  flex-shrink: 0;
}
.reuse-hint {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  background: #e8f5e9;
  color: #2e7d32;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
  flex-shrink: 0;
  border: 1px solid #c8e6c9;
}

@media (max-width: 700px) {
  .stat-row { grid-template-columns: 1fr; }
  .tab-bar-manager { grid-template-columns: 1fr; }
  .tab-slider { display: none; }
  .tab-btn.active { background: #fff; border-radius: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
}
</style>
