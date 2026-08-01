<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useChildSelectStore } from '../../stores'
import { api } from '../../utils/api'
import { categoryLabels, weekDayToLabel } from '../../utils/constants'

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

import ChildSelector from '../../components/ChildSelector.vue'

const childSelectStore = useChildSelectStore()

const activeTab = ref<'subtasks' | 'steps'>('subtasks')
const subTaskLibrary = ref<any[]>([])
const stepLibrary = ref<any[]>([])
const loading = ref(false)

const totalSubTasks = computed(() => subTaskLibrary.value.length)
const totalSteps = computed(() => stepLibrary.value.length)

async function loadLibraries() {
  loading.value = true
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    const res = await api.tasks.getSubTaskLibrary(childId)
    subTaskLibrary.value = res.subtasks ?? []
  } catch { /* offline */ }
  try {
    const res = await api.habits.getStepLibrary(childId)
    stepLibrary.value = res.steps ?? []
  } catch { /* offline */ }
  loading.value = false
}

onMounted(loadLibraries)
</script>

<template>
  <div class="page">
    <ChildSelector />

    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📦 复用库</span>
        <h1>子任务与步骤库</h1>
        <p class="lead">
          此处显示所有已创建的子任务和习惯步骤。<strong>在创建任务或习惯时可直接从库中选择</strong>，避免重复输入相同的内容。
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
            <strong>{{ totalSteps }}</strong>
            <span>习惯步骤</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tabs -->
    <section class="tab-bar-section">
      <div class="tab-bar-manager two-tabs">
        <button class="tab-btn" :class="{ active: activeTab === 'subtasks' }" @click="activeTab = 'subtasks'">
          📋 子任务库
          <span class="badge">{{ totalSubTasks }}</span>
        </button>
        <button class="tab-btn" :class="{ active: activeTab === 'steps' }" @click="activeTab = 'steps'">
          📝 步骤库
          <span class="badge">{{ totalSteps }}</span>
        </button>
        <div class="tab-slider-manager" :class="`slide-${activeTab}`" />
      </div>
    </section>

    <!-- Sub-task Library -->
    <section v-show="activeTab === 'subtasks'">
      <div v-if="subTaskLibrary.length" class="list">
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
      <p v-else class="muted" style="text-align:center;padding:32px">
        暂无子任务，在「任务管理」中创建任务并添加子任务后就会出现在这里。
      </p>
    </section>

    <!-- Step Library -->
    <section v-show="activeTab === 'steps'">
      <div v-if="stepLibrary.length" class="list">
        <div v-for="(s, i) in stepLibrary" :key="s.pk_sop_steps || i" class="list-row">
          <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
            <span class="sub-index">{{ s.order || i + 1 }}</span>
            <div style="min-width:0">
              <strong>{{ s.instruction }}</strong>
              <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
                <span class="mini-tag" style="background:#f0fdf4;color:#166534">源自：{{ s.habit_title || '未知习惯' }}</span>
                <span v-if="s.image_url || s.gif_url" class="mini-tag" style="background:#fef3c7">🖼️ 有图示</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="muted" style="text-align:center;padding:32px">
        暂无习惯步骤，在「习惯管理」中创建习惯并添加步骤后就会出现在这里。
      </p>
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
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.tab-btn.active { color: #2e7d32; }
.tab-slider-manager {
  position: absolute;
  top: 6px; bottom: 6px;
  width: calc(50% - 8px);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tab-slider-manager.slide-subtasks { transform: translateX(0); left: 6px; }
.tab-slider-manager.slide-steps { transform: translateX(100%); left: 6px; }
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
  grid-template-columns: repeat(2, 1fr);
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
  transition: all .12s ease;
}
.list-row + .list-row {
  margin-top: 6px;
}
.list-row:hover {
  border-color: var(--primary-2);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
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
</style>
