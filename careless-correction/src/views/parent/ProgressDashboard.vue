<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { categoryLabels } from '../../utils/constants'
import { useChildSelectStore, useGrowthStore, useMistakeStore, useParentStore, useUserStore } from '../../stores'
import { api, normalizeTask } from '../../utils/api'
import ChildSelector from '../../components/ChildSelector.vue'

const userStore = useUserStore()
const mistakeStore = useMistakeStore()
const growthStore = useGrowthStore()
const parentStore = useParentStore()
const childSelectStore = useChildSelectStore()
const selectedChild = computed(() => childSelectStore.selectedChild)

const loadingData = ref(false)

// ── 待审批打卡提醒 ──
const pendingCheckins = ref<any[]>([])

async function loadPendingCheckins() {
  try {
    const res = await api.checkins.getPending()
    pendingCheckins.value = res.pending ?? []
  } catch { /* offline */ }
}

async function quickApprove(id: number) {
  try {
    await api.checkins.approve(id)
    pendingCheckins.value = pendingCheckins.value.filter(c => c.id !== id)
  } catch { /* offline */ }
}

async function quickReject(id: number) {
  try {
    await api.checkins.reject(id)
    pendingCheckins.value = pendingCheckins.value.filter(c => c.id !== id)
  } catch { /* offline */ }
}

async function loadData() {
  loadingData.value = true
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    const res = await api.tasks.getInventory(childId)
    const tasks = (res.tasks ?? []).map(normalizeTask)
    parentStore.parentTaskTemplates.splice(0, parentStore.parentTaskTemplates.length, ...tasks)
  } catch { /* offline */ }
  try {
    await growthStore.fetchFromApi(childId)
  } catch { /* offline */ }
  try {
    await mistakeStore.fetchFromApi(childId)
  } catch { /* offline */ }
  // 加载待审批打卡
  await loadPendingCheckins()
  loadingData.value = false
}

watch(() => childSelectStore.selectedChildId, async () => {
  currentPage.value = 1
  await loadData()
})

onMounted(() => {
  loadData()
})

// ── 任务数据 ──
const allTasks = computed(() => parentStore.parentTaskTemplates)
const completedTasks = computed(() =>
  allTasks.value
    .filter(t => t.status === 'completed')
    .sort((a, b) => {
      const da = a.completedAt ? new Date(a.completedAt).getTime() : 0
      const db = b.completedAt ? new Date(b.completedAt).getTime() : 0
      return db - da
    }),
)
const pendingTasks = computed(() => allTasks.value.filter(t => t.status === 'pending' && t.active !== false))
const totalActiveTasks = computed(() => allTasks.value.filter(t => t.active !== false).length)

// ── 分页 ──
const currentPage = ref(1)
const pageSize = 8
const totalPages = computed(() => Math.max(1, Math.ceil(completedTasks.value.length / pageSize)))
const pagedCompletedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return completedTasks.value.slice(start, start + pageSize)
})
function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}
// 显示分页按钮（最多 5 个）
const pageNumbers = computed(() => {
  const pages: number[] = []
  const max = totalPages.value
  let start = Math.max(1, currentPage.value - 2)
  let end = Math.min(max, start + 4)
  start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// ── 真实统计 ──
const completedCount = computed(() => completedTasks.value.length)
const streakDays = computed(() => selectedChild.value?.streakDays ?? userStore.profile.streakDays ?? 0)
const totalMistakes = computed(() => mistakeStore.records.length)
const totalLossItems = computed(() => growthStore.itemLossRecords.reduce((s, i) => s + i.frequency, 0))
const totalStorage = computed(() => growthStore.storageRecords.length)
const completionRate = computed(() => {
  const total = totalActiveTasks.value
  if (total === 0) return 0
  return Math.round((completedCount.value / total) * 100)
})

// ── 今日完成 ──
const todayCompleted = computed(() => {
  const today = new Date().toDateString()
  return completedTasks.value.filter(t => {
    if (!t.completedAt) return false
    return new Date(t.completedAt).toDateString() === today
  }).length
})

function formatDateShort(dateStr?: string): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '—'
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 30) return `${diffDays}天前`
  return `${d.getMonth() + 1}月${d.getDate()}日`
}
</script>

<template>
  <div class="page">
    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📊 进度查看</span>
        <h1>任务完成进度</h1>
        <p class="lead">查看孩子的任务完成情况和成长数据，了解每日打卡与连续坚持的成果。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>{{ selectedChild?.name ?? userStore.profile.name ?? 'Leo' }} 的成长概览</h2>
          <span class="tag">Lv{{ userStore.assessment.recommendedLevel }}</span>
        </div>
        <div class="stat-row">
          <div class="mini-stat">
            <strong>{{ totalMistakes }}</strong>
            <span>错题库</span>
          </div>
          <div class="mini-stat">
            <strong>{{ totalLossItems }}</strong>
            <span>物品流失</span>
          </div>
          <div class="mini-stat">
            <strong>{{ totalStorage }}</strong>
            <span>收纳记录</span>
          </div>
          <div class="mini-stat">
            <strong>☀️ {{ selectedChild?.sunlightPoints ?? userStore.sunlightPoints }}</strong>
            <span>阳光值</span>
          </div>
        </div>
      </div>
    </section>

    <ChildSelector />

    <!-- ⏳ 待审批打卡提醒 -->
    <section v-if="pendingCheckins.length" class="pending-banner">
      <div class="pending-banner-header">
        <h2>⏳ {{ pendingCheckins.length }} 条待审批打卡</h2>
        <span class="pending-count">{{ pendingCheckins.length }}</span>
      </div>
      <p class="pending-desc">孩子已提交打卡，请尽快审批。审批通过后阳光会出现在阳光树上，孩子点击收集后正式变为阳光值。</p>
      <div class="pending-list">
        <div
          v-for="ci in pendingCheckins"
          :key="ci.id"
          class="pending-item"
        >
          <div class="pending-item-info">
            <strong>{{ ci.childName }}</strong>
            <span class="muted">{{ ci.checkDate }} · {{ ci.totalPoints }} 阳光 · {{ ci.taskCount }} 任务</span>
          </div>
          <div class="pending-actions">
            <button class="btn approve-btn" @click="quickApprove(ci.id)">✅ 通过</button>
            <button class="btn reject-btn" @click="quickReject(ci.id)">❌ 驳回</button>
          </div>
        </div>
      </div>
    </section>

    <!-- 加载提示 -->
    <section v-if="loadingData" class="panel" style="text-align:center;padding:24px">
      <p class="muted">⏳ 加载数据中...</p>
    </section>

    <template v-else>
      <!-- 统计卡片 -->
      <section class="grid-4">
        <div class="soft-card stat-card">
          <div class="icon-tile">✅</div>
          <strong>{{ completedCount }}</strong>
          <span class="muted">已完成任务</span>
          <div class="progress" style="margin-top:8px">
            <span :style="{ width: `${completionRate}%` }"></span>
          </div>
          <span class="muted" style="font-size:11px;margin-top:2px">完成率 {{ completionRate }}%</span>
        </div>
        <div class="soft-card stat-card">
          <div class="icon-tile">📋</div>
          <strong>{{ totalActiveTasks }}</strong>
          <span class="muted">总任务数</span>
          <span class="muted" style="font-size:11px;margin-top:2px">待完成 {{ pendingTasks.length }} 项</span>
        </div>
        <div class="soft-card stat-card streak-card">
          <div class="icon-tile">🔥</div>
          <strong>{{ streakDays }}</strong>
          <span class="muted">连续打卡天数</span>
          <span v-if="streakDays > 0" class="streak-hint">坚持中，继续加油！</span>
          <span v-else class="muted" style="font-size:11px;margin-top:2px">完成打卡开启连胜</span>
        </div>
        <div class="soft-card stat-card">
          <div class="icon-tile">📅</div>
          <strong>{{ todayCompleted }}</strong>
          <span class="muted">今日完成</span>
          <span class="muted" style="font-size:11px;margin-top:2px">今日已完成任务数</span>
        </div>
      </section>

      <!-- 已完成任务列表（分页） -->
      <section class="panel">
        <div class="card-title">
          <h2>✅ 已完成进度列表</h2>
          <span class="tag">{{ completedTasks.length }} 条记录</span>
        </div>

        <div v-if="pagedCompletedTasks.length" class="list">
          <div
            v-for="task in pagedCompletedTasks"
            :key="task.id"
            class="list-row completed-row"
          >
            <div style="display:flex;align-items:center;gap:12px;min-width:0;flex:1">
              <span style="font-size:24px;flex-shrink:0">{{ task.icon }}</span>
              <div style="min-width:0">
                <strong>{{ task.title }}</strong>
                <span class="muted" style="display:block;font-size:13px">{{ task.description || '无描述' }}</span>
                <div style="display:flex;gap:6px;margin-top:4px;flex-wrap:wrap">
                  <span class="mini-tag">{{ categoryLabels[task.type] || task.type }}</span>
                  <span class="mini-tag" style="background:#d9f5c8;color:var(--primary)">✓ 已完成</span>
                  <span class="mini-tag">☀️ +{{ task.rewardPoints }}</span>
                  <span v-if="task.subTasks?.length" class="mini-tag">📝 {{ task.subTasks.length }} 子任务</span>
                </div>
              </div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0">
              <span class="completion-date">{{ formatDateShort(task.completedAt) }}</span>
              <span class="completion-time">{{ task.completedAt ? new Date(task.completedAt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '' }}</span>
            </div>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">
          暂无已完成任务，孩子完成任务后将在此显示 🎯
        </p>

        <!-- 分页控件 -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="page-btn"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            ‹ 上一页
          </button>
          <div class="page-numbers">
            <button
              v-for="p in pageNumbers"
              :key="p"
              class="page-num"
              :class="{ active: p === currentPage }"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
          </div>
          <button
            class="page-btn"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页 ›
          </button>
        </div>
        <div v-if="totalPages > 1" class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 页，共 {{ completedTasks.length }} 条记录
        </div>
      </section>

      <!-- 成长趋势数据 -->
      <section v-if="growthStore.trendData.length" class="panel">
        <div class="card-title">
          <h2>📈 成长趋势</h2>
          <span class="tag">{{ growthStore.trendData.length }} 个数据点</span>
        </div>
        <div class="list">
          <div
            v-for="point in growthStore.trendData.slice().reverse().slice(0, 10)"
            :key="point.date"
            class="list-row"
          >
            <span style="font-weight:800">{{ point.date }}</span>
            <div style="display:flex;gap:16px;font-size:13px;flex-wrap:wrap">
              <span>粗心率 {{ Math.round(point.mistakeRate * 100) }}%</span>
              <span>丢失率 {{ point.itemLossRate }}次</span>
              <span>完成率 {{ Math.round(point.taskCompletionRate * 100) }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 提示 -->
      <section class="panel" style="text-align:center">
        <p class="lead">
          💡 <strong>提示：</strong>数据随时间累积会越来越准确。保持每日打卡和记录，系统会在「成长档案」中生成更详细的趋势报告和预警。
        </p>
      </section>
    </template>
  </div>
</template>

<style scoped>
/* ── 待审批提醒横幅 ── */
.pending-banner {
  border: 2px solid #ff9800;
  background: linear-gradient(135deg, #fff8e1, #fff);
  border-radius: 24px;
  padding: 20px 24px;
  margin-bottom: 18px;
}
.pending-banner-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pending-banner-header h2 {
  font-size: 18px;
  font-weight: 800;
  color: #e65100;
}
.pending-count {
  background: #ff9800;
  color: #fff;
  font-size: 14px;
  font-weight: 800;
  border-radius: 999px;
  min-width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  padding: 0 8px;
}
.pending-desc {
  font-size: 13px;
  color: var(--muted);
  margin: 8px 0 12px;
}
.pending-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pending-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #ffe0b2;
}
.pending-item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.pending-item-info strong {
  font-size: 15px;
}
.pending-item-info .muted {
  font-size: 12px;
}
.pending-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.approve-btn {
  background: var(--primary) !important;
  color: #fff !important;
  border: none !important;
  padding: 8px 16px !important;
  font-size: 13px !important;
}
.reject-btn {
  background: #fff !important;
  color: #d32f2f !important;
  border: 2px solid #ffcdd2 !important;
  padding: 6px 14px !important;
  font-size: 13px !important;
}

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
  font-size: 22px;
  margin-bottom: 2px;
}
.mini-stat span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}
.stat-card strong {
  font-size: 28px;
}
.streak-card {
  border-color: #ffb74d;
  background: linear-gradient(135deg, #fff8e1, #fff);
}
.streak-hint {
  font-size: 11px;
  color: #e65100;
  font-weight: 700;
  margin-top: 2px;
}
.completed-row {
  transition: all .12s ease;
}
.completed-row:hover {
  border-color: var(--primary-2);
  background: #fafff5;
}
.completion-date {
  font-size: 13px;
  font-weight: 800;
  color: var(--primary);
  white-space: nowrap;
}
.completion-time {
  font-size: 11px;
  color: var(--muted);
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

/* ── 分页 ── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}
.page-btn {
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  font-weight: 800;
  font-size: 13px;
  color: var(--ink);
  cursor: pointer;
  transition: all .15s ease;
  white-space: nowrap;
}
.page-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
  background: #ecffd9;
}
.page-btn:disabled {
  opacity: .4;
  cursor: not-allowed;
}
.page-numbers {
  display: flex;
  gap: 6px;
}
.page-num {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: #fff;
  font-weight: 800;
  font-size: 14px;
  color: var(--muted);
  cursor: pointer;
  transition: all .15s ease;
  display: grid;
  place-items: center;
}
.page-num:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.page-num.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(16,110,0,.2);
}
.page-info {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted);
  font-weight: 700;
}

@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .pagination { flex-wrap: wrap; gap: 8px; }
  .page-num { width: 32px; height: 32px; font-size: 13px; }
}
</style>
