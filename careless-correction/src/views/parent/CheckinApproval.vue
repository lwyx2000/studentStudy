<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../../utils/api'
import { useBadgeStore, useChildSelectStore } from '../../stores'

const childSelectStore = useChildSelectStore()
const badgeStore = useBadgeStore()

// ── State ──
const pendingCheckins = ref<any[]>([])
const historyCheckins = ref<any[]>([])
const loading = ref(false)
const activeTab = ref<'pending' | 'history'>('pending')

// Expanded detail
const expandedId = ref<number | null>(null)
const checkinDetails = ref<any>(null)
const loadingDetails = ref(false)

// ── Computed ──
const pendingCount = computed(() => pendingCheckins.value.length)
const totalPendingPoints = computed(() =>
  pendingCheckins.value.reduce((sum, ci) => sum + (ci.totalPoints || 0), 0),
)
const approvedCount = computed(() => historyCheckins.value.filter(h => h.status === 'approved').length)
const rejectedCount = computed(() => historyCheckins.value.filter(h => h.status === 'rejected').length)

// ── Actions ──
async function loadData() {
  loading.value = true
  await Promise.all([loadPending(), loadHistory()])
  loading.value = false
}

async function loadPending() {
  try {
    const res = await api.checkins.getPending()
    pendingCheckins.value = res.pending ?? []
  } catch { /* offline */ }
}

async function loadHistory() {
  try {
    const res = await api.checkins.getHistory(50)
    historyCheckins.value = res.history ?? []
  } catch { /* offline */ }
}

async function toggleDetail(ci: any) {
  if (expandedId.value === ci.id) {
    expandedId.value = null
    checkinDetails.value = null
    return
  }
  expandedId.value = ci.id
  checkinDetails.value = null
  loadingDetails.value = true
  try {
    const res = await api.checkins.getDetails(ci.id)
    checkinDetails.value = res
  } catch { /* offline */ }
  loadingDetails.value = false
}

async function approveCheckin(id: number) {
  try {
    await api.checkins.approve(id)
    pendingCheckins.value = pendingCheckins.value.filter(c => c.id !== id)
    if (expandedId.value === id) {
      expandedId.value = null
      checkinDetails.value = null
    }
    await badgeStore.checkAndUnlock(childSelectStore.selectedChildId ?? undefined)
    await loadHistory()
  } catch { /* offline */ }
}

async function rejectCheckin(id: number) {
  try {
    await api.checkins.reject(id)
    pendingCheckins.value = pendingCheckins.value.filter(c => c.id !== id)
    if (expandedId.value === id) {
      expandedId.value = null
      checkinDetails.value = null
    }
    await loadHistory()
  } catch { /* offline */ }
}

async function approveAll() {
  const ids = pendingCheckins.value.map(c => c.id)
  for (const id of ids) {
    await approveCheckin(id)
  }
}

onMounted(() => {
  loadData()
})

function formatTime(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="page">
    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">⏳ 打卡审批</span>
        <h1>待审批打卡列表</h1>
        <p class="lead">查看孩子提交的所有打卡记录，审批通过后阳光会出现在阳光树上，孩子点击收集后才会正式变为阳光值。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>审批概览</h2>
          <span class="tag" :class="{ 'pulse-tag': pendingCount > 0 }">
            {{ pendingCount > 0 ? `${pendingCount} 条待处理` : '全部已处理' }}
          </span>
        </div>
        <div class="stat-row">
          <div class="mini-stat pending-stat">
            <strong style="color:#e65100">{{ pendingCount }}</strong>
            <span>待审批</span>
          </div>
          <div class="mini-stat">
            <strong style="color:var(--primary)">☀️ {{ totalPendingPoints }}</strong>
            <span>待发放阳光</span>
          </div>
          <div class="mini-stat">
            <strong style="color:#2e7d32">{{ approvedCount }}</strong>
            <span>已通过</span>
          </div>
          <div class="mini-stat">
            <strong style="color:#c62828">{{ rejectedCount }}</strong>
            <span>已驳回</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tab nav -->
    <div class="tab-nav">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'pending' }"
        @click="activeTab = 'pending'"
      >
        ⏳ 待审批
        <span v-if="pendingCount" class="badge-count">{{ pendingCount }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'history' }"
        @click="activeTab = 'history'"
      >
        📜 审批历史
      </button>
    </div>

    <!-- Loading -->
    <section v-if="loading" class="panel" style="text-align:center;padding:32px">
      <p class="muted">⏳ 加载数据中...</p>
    </section>

    <template v-else>
      <!-- ── Tab: 待审批 ── -->
      <template v-if="activeTab === 'pending'">
        <!-- 批量操作 -->
        <section v-if="pendingCount > 1" class="batch-bar">
          <p class="muted" style="font-size:14px">
            💡 共 {{ pendingCount }} 条待审批，合计 {{ totalPendingPoints }} 阳光值
          </p>
          <button class="btn batch-approve-btn" @click="approveAll">
            ⚡ 全部通过
          </button>
        </section>

        <!-- Pending list -->
        <section v-if="pendingCount" class="panel">
          <div class="card-title">
            <h2>⏳ 待审批打卡</h2>
            <span class="tag" style="background:#fff3e0;color:#e65100">{{ pendingCount }} 条</span>
          </div>
          <p class="lead" style="font-size:13px;margin-bottom:12px;color:#8a6d3b">
            💡 点击审批单可展开查看孩子提交的任务和习惯详情。
          </p>
          <div class="list">
            <div v-for="ci in pendingCheckins" :key="ci.id" class="checkin-item-wrap">
              <!-- Header -->
              <div
                class="list-row checkin-row"
                :class="{ 'checkin-expanded': expandedId === ci.id }"
                style="cursor:pointer"
                @click="toggleDetail(ci)"
              >
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                    <span class="expand-arrow" :class="{ expanded: expandedId === ci.id }">▶</span>
                    <strong>{{ ci.childName }}</strong>
                    <span class="mini-tag">📅 {{ ci.checkDate }}</span>
                    <span class="mini-tag" style="background:#fff3cd;color:#856404">☀️ +{{ ci.totalPoints }}</span>
                    <span v-if="ci.taskCount" class="mini-tag" style="background:#d4edda;color:#155724">✅ {{ ci.taskCount }} 项任务</span>
                    <span v-if="ci.habitStepCount" class="mini-tag" style="background:#cce5ff;color:#004085">🌱 {{ ci.habitStepCount }} 步习惯</span>
                  </div>
                </div>
                <div style="display:flex;gap:8px;flex-shrink:0" @click.stop>
                  <button class="btn approve-btn" @click="approveCheckin(ci.id)">✅ 通过</button>
                  <button class="btn reject-btn" @click="rejectCheckin(ci.id)">❌ 驳回</button>
                </div>
              </div>

              <!-- Expanded detail -->
              <div v-if="expandedId === ci.id" class="checkin-detail">
                <div v-if="loadingDetails" style="text-align:center;padding:24px">
                  <p class="muted">⏳ 加载孩子提交详情...</p>
                </div>
                <template v-else-if="checkinDetails">
                  <div class="detail-summary">
                    <div class="summary-item">
                      <strong>{{ checkinDetails.checkin.childName }}</strong>
                      <span class="muted">提交于 {{ checkinDetails.checkin.checkDate }}</span>
                    </div>
                    <div class="summary-stats">
                      <div class="summary-stat">
                        <span class="summary-num">{{ checkinDetails.checkin.taskCount }}</span>
                        <span class="muted">完成任务</span>
                      </div>
                      <div class="summary-stat">
                        <span class="summary-num">{{ checkinDetails.checkin.habitStepCount }}</span>
                        <span class="muted">习惯步骤</span>
                      </div>
                      <div class="summary-stat">
                        <span class="summary-num">+{{ checkinDetails.checkin.totalPoints }}</span>
                        <span class="muted">阳光值</span>
                      </div>
                      <div v-if="checkinDetails.checkin.streakDays" class="summary-stat">
                        <span class="summary-num">🔥 {{ checkinDetails.checkin.streakDays }}</span>
                        <span class="muted">连续天数</span>
                      </div>
                    </div>
                  </div>

                  <!-- Completed tasks -->
                  <div v-if="checkinDetails.completedTasks.length" class="detail-section">
                    <h4>✅ 已完成的任务</h4>
                    <div class="detail-list">
                      <div v-for="task in checkinDetails.completedTasks" :key="task.pk_tasks" class="detail-task-row">
                        <span style="font-size:20px;flex-shrink:0">{{ task.icon || '📋' }}</span>
                        <div style="flex:1;min-width:0">
                          <strong>{{ task.title }}</strong>
                          <span class="muted" style="display:block;font-size:12px">{{ task.description || '无描述' }}</span>
                        </div>
                        <span class="mini-tag" style="background:#d4edda;color:#155724">✓ 完成</span>
                        <span class="mini-tag">☀️ +{{ task.reward_points }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Pending tasks -->
                  <div v-if="checkinDetails.pendingTasks.length" class="detail-section">
                    <h4>⏳ 未完成的任务（{{ checkinDetails.pendingTasks.length }} 项）</h4>
                    <div class="detail-list">
                      <div v-for="task in checkinDetails.pendingTasks.slice(0, 5)" :key="task.pk_tasks" class="detail-task-row" style="opacity:.6">
                        <span style="font-size:20px;flex-shrink:0">{{ task.icon || '📋' }}</span>
                        <div style="flex:1;min-width:0">
                          <strong>{{ task.title }}</strong>
                          <span class="muted" style="display:block;font-size:12px">{{ task.description || '无描述' }}</span>
                        </div>
                        <span class="mini-tag" style="background:#f8d7da;color:#721c24">○ 未完成</span>
                      </div>
                      <p v-if="checkinDetails.pendingTasks.length > 5" class="muted" style="font-size:12px;text-align:center;padding:4px">
                        还有 {{ checkinDetails.pendingTasks.length - 5 }} 项未展示...
                      </p>
                    </div>
                  </div>

                  <!-- Habits -->
                  <div v-if="checkinDetails.habits.length" class="detail-section">
                    <h4>🌱 习惯打卡情况</h4>
                    <div class="detail-list">
                      <div v-for="habit in checkinDetails.habits" :key="habit.pk_habit_sops" class="detail-habit-row">
                        <div style="flex:1;min-width:0">
                          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                            <strong>{{ habit.title }}</strong>
                            <span class="mini-tag">☀️ +{{ habit.reward_points }}/步</span>
                            <span class="mini-tag" style="background:#cce5ff;color:#004085">{{ habit.steps.length }} 步</span>
                          </div>
                          <div v-if="habit.steps.length" class="habit-steps-mini">
                            <div v-for="step in habit.steps" :key="step.order" class="step-mini">
                              <b class="step-mini-num">{{ step.order }}</b>
                              <span>{{ step.instruction }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <p v-if="!checkinDetails.completedTasks.length && !checkinDetails.pendingTasks.length && !checkinDetails.habits.length" class="muted" style="text-align:center;padding:16px">
                    暂无任务和习惯数据
                  </p>

                  <!-- Detail-level action buttons -->
                  <div class="detail-actions">
                    <button class="btn approve-btn" style="flex:1" @click="approveCheckin(ci.id)">✅ 通过，生成 {{ ci.totalPoints }} 阳光待收集</button>
                    <button class="btn reject-btn" @click="rejectCheckin(ci.id)">❌ 驳回</button>
                  </div>
                </template>
                <div v-else style="text-align:center;padding:16px">
                  <p class="muted">加载失败，请重试</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Empty state -->
        <section v-else class="panel empty-state">
          <span style="font-size:64px;display:block;margin-bottom:16px">🎉</span>
          <h2 style="margin-bottom:8px">暂无待审批打卡</h2>
          <p class="lead">孩子提交打卡后，待审批记录会出现在这里。</p>
        </section>
      </template>

      <!-- ── Tab: 审批历史 ── -->
      <template v-if="activeTab === 'history'">
        <section v-if="historyCheckins.length" class="panel">
          <div class="card-title">
            <h2>📜 审批历史</h2>
            <span class="tag">{{ historyCheckins.length }} 条记录</span>
          </div>
          <div class="list">
            <div
              v-for="h in historyCheckins"
              :key="h.id"
              class="list-row history-row"
              :class="h.status"
            >
              <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
                <span class="status-icon">
                  {{ h.status === 'approved' ? '✅' : '❌' }}
                </span>
                <div style="min-width:0">
                  <strong>{{ h.childName }}</strong>
                  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:2px">
                    <span class="mini-tag">📅 {{ h.checkDate }}</span>
                    <span class="mini-tag">☀️ {{ h.totalPoints }}</span>
                    <span v-if="h.taskCount" class="mini-tag">📋 {{ h.taskCount }} 任务</span>
                    <span class="mini-tag" :class="h.status === 'approved' ? 'status-approved' : 'status-rejected'">
                      {{ h.status === 'approved' ? '已通过' : '已驳回' }}
                    </span>
                  </div>
                  <span class="muted" style="font-size:11px;display:block;margin-top:2px">
                    {{ formatTime(h.approvedAt) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section v-else class="panel empty-state">
          <span style="font-size:64px;display:block;margin-bottom:16px">📋</span>
          <h2 style="margin-bottom:8px">暂无审批历史</h2>
          <p class="lead">审批通过的打卡记录会在这里显示。</p>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
/* Stats */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 12px;
}
.mini-stat {
  text-align: center;
  padding: 12px 8px;
  border-radius: 16px;
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
.pending-stat {
  border-color: #ff9800;
  background: #fff8e1;
}
.pulse-tag {
  background: #ff9800 !important;
  color: #fff !important;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  50% { box-shadow: 0 0 0 6px rgba(255, 152, 0, .15); }
}

/* Tab nav */
.tab-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}
.tab-btn {
  position: relative;
  padding: 12px 24px;
  border-radius: 16px 16px 0 0;
  border: 2px solid var(--line);
  border-bottom: none;
  background: var(--surface-2);
  font: inherit;
  font-weight: 800;
  font-size: 15px;
  cursor: pointer;
  transition: all .12s ease;
  color: var(--muted);
}
.tab-btn.active {
  background: #fff;
  color: var(--ink);
  border-color: var(--primary-2);
}
.badge-count {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #e65100;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  border-radius: 999px;
  min-width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  padding: 0 6px;
}

/* Batch bar */
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff8e1, #fff);
  border: 2px solid #ffe0b2;
  margin-bottom: 14px;
}
.batch-approve-btn {
  background: var(--primary) !important;
  color: #fff !important;
  border: none !important;
  padding: 10px 24px !important;
  font-size: 15px !important;
  white-space: nowrap;
}

/* Checkin items */
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
.checkin-item-wrap {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--line);
  background: #fff;
  transition: border-color .15s ease;
}
.checkin-item-wrap + .checkin-item-wrap {
  margin-top: 8px;
}
.checkin-row {
  border: none;
  border-radius: 0;
  flex-wrap: wrap;
  gap: 8px;
}
.checkin-expanded {
  border-color: #ff9800 !important;
  background: #fffbf0;
}
.expand-arrow {
  display: inline-block;
  font-size: 11px;
  color: var(--muted);
  transition: transform .2s ease;
  flex-shrink: 0;
}
.expand-arrow.expanded {
  transform: rotate(90deg);
  color: #ff9800;
}
.checkin-detail {
  padding: 16px 18px;
  background: #fafafa;
  border-top: 1px dashed #e0e0e0;
  animation: fadeIn .2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.detail-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid var(--line);
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.summary-item strong {
  font-size: 16px;
}
.summary-stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.summary-num {
  font-size: 20px;
  font-weight: 900;
  color: var(--primary);
}
.detail-section {
  margin-top: 14px;
}
.detail-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--ink);
}
.detail-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.detail-task-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--line);
}
.detail-habit-row {
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--line);
}
.habit-steps-mini {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
  padding-left: 4px;
}
.step-mini {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #555;
}
.step-mini-num {
  display: inline-grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: var(--primary-2);
  color: #fff;
  font-size: 11px;
  flex-shrink: 0;
}

/* Action buttons */
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
.detail-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e0e0e0;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 48px 24px;
}

/* History rows */
.history-row {
  border-left: 4px solid transparent;
}
.history-row.approved {
  border-left-color: var(--primary);
  background: #f8fdf5;
}
.history-row.rejected {
  border-left-color: #e53935;
  background: #fef5f5;
}
.status-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.status-approved {
  background: #d4edda !important;
  color: #155724 !important;
}
.status-rejected {
  background: #f8d7da !important;
  color: #721c24 !important;
}

@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .batch-bar { flex-wrap: wrap; }
  .detail-summary { flex-direction: column; align-items: flex-start; }
}
</style>
