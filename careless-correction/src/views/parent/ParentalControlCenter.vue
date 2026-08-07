<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, normalizeTask } from '../../utils/api'
import { useBadgeStore, useChildSelectStore, useMistakeStore, useParentStore, useTaskStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const parentStore = useParentStore()
const taskStore = useTaskStore()
const mistakeStore = useMistakeStore()
const childSelectStore = useChildSelectStore()
const badgeStore = useBadgeStore()
const selectedChild = computed(() => childSelectStore.selectedChild)

const loadingData = ref(false)

// ── 审批列表（所有孩子）──
const allCheckins = ref<any[]>([])          // 合并 pending + history
const filterStatus = ref<'all' | 'pending' | 'approved' | 'rejected'>('all')
const filterChildId = ref<string | null>(null)
const expandedCheckinId = ref<number | null>(null)
const checkinDetails = ref<any>(null)
const loadingDetails = ref(false)

async function loadAllCheckins() {
  try {
    const [pendingRes, historyRes] = await Promise.all([
      api.checkins.getPending(),
      api.checkins.getHistory(50),
    ])
    const pending = pendingRes.pending ?? []
    const history = historyRes.history ?? []
    // 合并并按时间倒序
    allCheckins.value = [...pending, ...history].sort((a, b) => {
      const da = new Date(a.createdAt || a.approvedAt || 0).getTime()
      const db = new Date(b.createdAt || b.approvedAt || 0).getTime()
      return db - da
    })
  } catch { /* offline */ }
}

const filteredCheckins = computed(() => {
  let list = allCheckins.value
  if (filterStatus.value !== 'all') {
    list = list.filter(c => c.status === filterStatus.value)
  }
  if (filterChildId.value) {
    list = list.filter(c => String(c.childId) === filterChildId.value)
  }
  return list
})

const pendingCount = computed(() => allCheckins.value.filter(c => c.status === 'pending').length)
const approvedCount = computed(() => allCheckins.value.filter(c => c.status === 'approved').length)
const rejectedCount = computed(() => allCheckins.value.filter(c => c.status === 'rejected').length)
const totalPendingPoints = computed(() =>
  allCheckins.value.filter(c => c.status === 'pending').reduce((s, c) => s + (c.totalPoints || 0), 0),
)

async function toggleCheckinDetail(ci: any) {
  if (expandedCheckinId.value === ci.id) {
    expandedCheckinId.value = null
    checkinDetails.value = null
    return
  }
  expandedCheckinId.value = ci.id
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
    // 更新本地状态：从 pending → approved
    const idx = allCheckins.value.findIndex(c => c.id === id)
    if (idx !== -1) {
      allCheckins.value[idx].status = 'approved'
      allCheckins.value[idx].approvedAt = new Date().toISOString()
    }
    if (expandedCheckinId.value === id) {
      expandedCheckinId.value = null
      checkinDetails.value = null
    }
    await badgeStore.checkAndUnlock(childSelectStore.selectedChildId ?? undefined)
  } catch { /* offline */ }
}

async function rejectCheckin(id: number) {
  try {
    await api.checkins.reject(id)
    const idx = allCheckins.value.findIndex(c => c.id === id)
    if (idx !== -1) {
      allCheckins.value[idx].status = 'rejected'
    }
    if (expandedCheckinId.value === id) {
      expandedCheckinId.value = null
      checkinDetails.value = null
    }
  } catch { /* offline */ }
}

async function approveAllPending() {
  const pending = allCheckins.value.filter(c => c.status === 'pending')
  for (const ci of pending) {
    await approveCheckin(ci.id)
  }
}

// ── 孩子数据加载 ──
async function loadData() {
  loadingData.value = true
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    const res = await api.tasks.getInventory(childId)
    const tasks = (res.tasks ?? []).map(normalizeTask)
    parentStore.parentTaskTemplates.splice(0, parentStore.parentTaskTemplates.length, ...tasks)
  } catch { /* offline */ }
  try {
    await taskStore.fetchFromApi(childId)
  } catch { /* offline */ }
  loadingData.value = false
}

watch(() => childSelectStore.selectedChildId, async () => {
  filterChildId.value = null
  await loadData()
})

const displayTasks = computed(() => parentStore.parentTaskTemplates)
const completedCount = computed(() => displayTasks.value.filter(t => t.status === 'completed').length)
const progressPercent = computed(() => Math.round((completedCount.value / Math.max(displayTasks.value.length, 1)) * 100))

// ── 打卡趋势图表数据（取近 7 次打卡）──
const recentCheckins = computed(() => {
  const childId = childSelectStore.selectedChildId
  const list = allCheckins.value
    .filter(c => c.status === 'approved' && (!childId || String(c.childId) === childId))
    .sort((a, b) => {
      const da = new Date(a.approvedAt || a.createdAt || 0).getTime()
      const db = new Date(b.approvedAt || b.createdAt || 0).getTime()
      return db - da
    })
  return list.slice(0, 7).reverse()
})

const maxPoints = computed(() => Math.max(...recentCheckins.value.map(c => c.totalPoints || 0), 1))

// ── 设置 ──
function toggle(key: 'dailyReminder' | 'achievementNotification' | 'weeklyReport' | 'schoolSync') {
  parentStore.updateSettings({ [key]: !parentStore.settings[key] })
}

function formatTime(iso?: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusLabel(status: string) {
  return status === 'pending' ? '待审批' : status === 'approved' ? '已通过' : '已驳回'
}

onMounted(() => {
  loadAllCheckins()
  loadData()
})
</script>

<template>
  <div class="page">
    <!-- ═══ Hero + KPI ═══ -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🧭 家长控制中心</span>
        <h1>家长总控台</h1>
        <p class="lead">查看所有孩子的打卡审批、任务完成情况和成长数据。审批通过后阳光会出现在阳光树上，孩子点击收集后正式变为阳光值。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>📊 全局概览</h2>
          <span class="tag">{{ childSelectStore.children.length }} 个孩子</span>
        </div>
        <div class="kpi-grid">
          <div class="kpi-item pending-kpi">
            <span class="kpi-icon">⏳</span>
            <strong>{{ pendingCount }}</strong>
            <span>待审批</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-icon">☀️</span>
            <strong>{{ totalPendingPoints }}</strong>
            <span>待发放阳光</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-icon">✅</span>
            <strong>{{ approvedCount }}</strong>
            <span>已通过</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-icon">❌</span>
            <strong>{{ rejectedCount }}</strong>
            <span>已驳回</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══ 审批列表（所有孩子）═══ -->
    <section class="panel approval-panel">
      <div class="card-title">
        <h2>📋 打卡审批列表</h2>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <span v-if="pendingCount > 0" class="tag pulse-tag">{{ pendingCount }} 条待审批</span>
          <button v-if="pendingCount > 1" class="btn batch-btn" @click="approveAllPending">⚡ 全部通过</button>
        </div>
      </div>

      <!-- 筛选条 -->
      <div class="filter-bar">
        <div class="filter-group">
          <button class="filter-btn" :class="{ active: filterStatus === 'all' }" @click="filterStatus = 'all'">全部</button>
          <button class="filter-btn" :class="{ active: filterStatus === 'pending' }" @click="filterStatus = 'pending'">待审批</button>
          <button class="filter-btn" :class="{ active: filterStatus === 'approved' }" @click="filterStatus = 'approved'">已通过</button>
          <button class="filter-btn" :class="{ active: filterStatus === 'rejected' }" @click="filterStatus = 'rejected'">已驳回</button>
        </div>
        <div class="filter-group">
          <button class="filter-btn" :class="{ active: filterChildId === null }" @click="filterChildId = null">所有孩子</button>
          <button
            v-for="child in childSelectStore.children"
            :key="child.id"
            class="filter-btn"
            :class="{ active: filterChildId === child.id }"
            @click="filterChildId = child.id"
          >{{ child.name }}</button>
        </div>
      </div>

      <!-- 审批列表 -->
      <div v-if="filteredCheckins.length" class="checkin-list">
        <div v-for="ci in filteredCheckins" :key="ci.id" class="checkin-item-wrap" :class="ci.status">
          <!-- 头部 -->
          <div
            class="list-row checkin-row"
            :class="{ 'checkin-expanded': expandedCheckinId === ci.id }"
            style="cursor:pointer"
            @click="toggleCheckinDetail(ci)"
          >
            <div style="flex:1;min-width:0">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span class="expand-arrow" :class="{ expanded: expandedCheckinId === ci.id }">▶</span>
                <strong>{{ ci.childName }}</strong>
                <span class="status-badge" :class="ci.status">{{ statusLabel(ci.status) }}</span>
                <span class="mini-tag">📅 {{ ci.checkDate }}</span>
                <span class="mini-tag" style="background:#fff3cd;color:#856404">☀️ {{ ci.totalPoints }}</span>
                <span v-if="ci.taskCount" class="mini-tag" style="background:#d4edda;color:#155724">✅ {{ ci.taskCount }} 任务</span>
                <span v-if="ci.habitStepCount" class="mini-tag" style="background:#cce5ff;color:#004085">🌱 {{ ci.habitStepCount }} 步</span>
              </div>
            </div>
            <div v-if="ci.status === 'pending'" style="display:flex;gap:8px;flex-shrink:0" @click.stop>
              <button class="btn approve-btn" @click="approveCheckin(ci.id)">✅ 通过</button>
              <button class="btn reject-btn" @click="rejectCheckin(ci.id)">❌ 驳回</button>
            </div>
            <div v-else style="flex-shrink:0">
              <span class="mini-tag" style="font-size:11px">{{ formatTime(ci.approvedAt) }}</span>
            </div>
          </div>

          <!-- 展开详情 -->
          <div v-if="expandedCheckinId === ci.id" class="checkin-detail">
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

              <!-- 已完成任务 -->
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

              <!-- 待完成任务 -->
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

              <!-- 习惯列表 -->
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

              <!-- 待审批时底部显示操作按钮 -->
              <div v-if="ci.status === 'pending'" class="detail-actions">
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
      <div v-else class="empty-state">
        <span style="font-size:48px;display:block;margin-bottom:8px">📭</span>
        <p class="muted">暂无{{ filterStatus !== 'all' ? statusLabel(filterStatus) : '' }}打卡记录</p>
      </div>
    </section>

    <!-- ═══ 孩子选择器 + 数据图表 ═══ -->
    <ChildSelector />

    <section v-if="selectedChild" class="grid-2">
      <!-- 左：打卡趋势图 + KPI -->
      <div class="panel">
        <div class="card-title">
          <h2>📈 {{ selectedChild.name }} 的打卡趋势</h2>
          <span class="tag">近 {{ recentCheckins.length }} 次</span>
        </div>

        <!-- CSS 柱状图 -->
        <div v-if="recentCheckins.length" class="bar-chart">
          <div v-for="ci in recentCheckins" :key="ci.id" class="bar-col">
            <div class="bar-value">{{ ci.totalPoints }}</div>
            <div class="bar-fill" :style="{ height: `${Math.max((ci.totalPoints / maxPoints) * 100, 8)}%` }"></div>
            <div class="bar-label">{{ ci.checkDate }}</div>
          </div>
        </div>
        <div v-else class="muted" style="text-align:center;padding:24px">暂无打卡数据</div>

        <!-- KPI 行 -->
        <div class="kpi-grid" style="margin-top:16px">
          <div class="kpi-item">
            <span class="kpi-icon">☀️</span>
            <strong>{{ selectedChild.sunlightPoints }}</strong>
            <span>阳光值</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-icon">🔥</span>
            <strong>{{ selectedChild.streakDays }}</strong>
            <span>连续天数</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-icon">✅</span>
            <strong>{{ completedCount }}/{{ displayTasks.length }}</strong>
            <span>今日任务</span>
          </div>
          <div class="kpi-item">
            <span class="kpi-icon">📚</span>
            <strong>{{ mistakeStore.records.length }}</strong>
            <span>错题数</span>
          </div>
        </div>

        <!-- 任务完成进度条 -->
        <div class="progress-section">
          <div class="progress-label">
            <span>任务完成率</span>
            <strong>{{ progressPercent }}%</strong>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
        </div>
      </div>

      <!-- 右：任务清单 + 习惯 -->
      <div class="panel">
        <div class="card-title">
          <h2>📋 今日任务清单</h2>
          <span class="tag">{{ completedCount }}/{{ displayTasks.length }} 完成</span>
        </div>
        <div v-if="displayTasks.length" class="task-list">
          <div v-for="task in displayTasks.slice(0, 8)" :key="task.id" class="task-row-mini" :class="{ done: task.status === 'completed' }">
            <span style="font-size:18px;flex-shrink:0">{{ task.icon }}</span>
            <div style="flex:1;min-width:0">
              <strong style="font-size:13px">{{ task.title }}</strong>
            </div>
            <span class="mini-tag" :style="task.status === 'completed' ? 'background:#d9f5c8;color:var(--primary)' : ''">
              {{ task.status === 'completed' ? '✓' : '○' }}
            </span>
          </div>
          <p v-if="displayTasks.length > 8" class="muted" style="font-size:12px;text-align:center;padding:4px">
            还有 {{ displayTasks.length - 8 }} 项...
          </p>
        </div>
        <p v-else class="muted" style="text-align:center;padding:16px">暂无今日任务</p>

        <!-- 习惯概览 -->
        <div class="card-title" style="margin-top:16px">
          <h2>🌱 习惯列表</h2>
          <span class="tag">{{ taskStore.habits.length }} 个</span>
        </div>
        <div v-if="taskStore.habits.length" class="habit-list">
          <div v-for="habit in taskStore.habits.slice(0, 3)" :key="habit.id" class="habit-mini">
            <strong>{{ habit.title }}</strong>
            <span class="muted" style="font-size:12px">{{ habit.steps.length }} 步 · ☀️ +{{ habit.rewardPoints }}/步</span>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:8px;font-size:13px">暂无习惯</p>

        <!-- 错题概览 -->
        <div class="card-title" style="margin-top:16px">
          <h2>📚 错题积累</h2>
          <span class="tag">{{ mistakeStore.records.length }} 题</span>
        </div>
        <div v-if="mistakeStore.records.length" class="mistake-list">
          <div v-for="record in mistakeStore.records.slice(0, 3)" :key="record.id" class="mistake-row">
            <span>📸 {{ record.subject }}</span>
            <span class="muted" style="font-size:11px">{{ new Date(record.createdAt).toLocaleDateString() }}</span>
          </div>
          <p v-if="mistakeStore.records.length > 3" class="muted" style="font-size:12px;text-align:center;padding:2px">
            还有 {{ mistakeStore.records.length - 3 }} 条记录…
          </p>
        </div>
        <p v-else class="muted" style="text-align:center;padding:8px;font-size:13px">暂无错题</p>
      </div>
    </section>

    <!-- ═══ 设置区域 ═══ -->
    <section class="grid-3">
      <button class="soft-card setting" @click="toggle('dailyReminder')">
        <div class="icon-tile">🔔</div>
        <h2>每日小岛提醒</h2>
        <p class="lead">{{ parentStore.settings.dailyReminder ? '已开启' : '已关闭' }}：只提醒环境准备，不替孩子催作业。</p>
      </button>
      <button class="soft-card setting" @click="toggle('achievementNotification')">
        <div class="icon-tile">🎆</div>
        <h2>成就烟花</h2>
        <p class="lead">{{ parentStore.settings.achievementNotification ? '已开启' : '已关闭' }}：里程碑时发送温和庆祝反馈。</p>
      </button>
      <button class="soft-card setting" @click="toggle('schoolSync')">
        <div class="icon-tile">🏫</div>
        <h2>学校共享</h2>
        <p class="lead">{{ parentStore.settings.schoolSync ? '已开启' : '已关闭' }}：仅分享匿名化成长趋势。</p>
      </button>
    </section>

    <!-- ═══ 循证资源 ═══ -->
    <section v-if="parentStore.articles.length" class="panel">
      <div class="card-title">
        <h2>📖 循证资源</h2>
        <span class="tag">{{ parentStore.articles.length }} 篇</span>
      </div>
      <div class="article-list">
        <a
          v-for="article in parentStore.articles.slice(0, 5)"
          :key="article.id"
          :href="article.contentUrl || '#'"
          target="_blank"
          rel="noopener"
          class="article-row"
        >
          <div style="min-width:0">
            <strong>{{ article.title }}</strong>
            <span class="muted" style="display:block;font-size:13px">{{ article.summary }}</span>
          </div>
          <span class="mini-tag" style="flex-shrink:0">{{ article.type === 'video' ? '🎬' : article.type === 'cbt' ? '🧩' : '📄' }} {{ article.readingTime }} 分钟</span>
        </a>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 12px;
}
.kpi-item {
  text-align: center;
  padding: 14px 8px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.kpi-item strong {
  display: block;
  font-size: 24px;
  margin: 2px 0;
}
.kpi-item span:last-child {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.kpi-icon {
  font-size: 22px;
}
.pending-kpi {
  border-color: #ff9800;
  background: #fff8e1;
}

/* ── Filter Bar ── */
.filter-bar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-btn {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  color: var(--muted);
  transition: all .12s ease;
}
.filter-btn:hover {
  border-color: var(--primary);
  background: #ecffd9;
}
.filter-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

/* ── Checkin List ── */
.checkin-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.checkin-item-wrap {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--line);
  background: #fff;
  border-left: 4px solid var(--line);
  transition: border-color .15s ease;
}
.checkin-item-wrap.pending {
  border-left-color: #ff9800;
  background: #fffbf0;
}
.checkin-item-wrap.approved {
  border-left-color: var(--primary);
  background: #f8fdf5;
}
.checkin-item-wrap.rejected {
  border-left-color: #e53935;
  background: #fef5f5;
}
.checkin-item-wrap .checkin-row {
  border: none;
  border-radius: 0;
  flex-wrap: wrap;
  gap: 8px;
}
.checkin-expanded {
  border-color: #ff9800 !important;
}
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}
.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}
.status-badge.approved {
  background: #d4edda;
  color: #155724;
}
.status-badge.rejected {
  background: #f8d7da;
  color: #721c24;
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

/* ── Checkin Detail ── */
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
.summary-item strong { font-size: 16px; }
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
.detail-section { margin-top: 14px; }
.detail-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
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
.detail-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e0e0e0;
}

/* ── Buttons ── */
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
.batch-btn {
  background: var(--primary) !important;
  color: #fff !important;
  border: none !important;
  padding: 6px 16px !important;
  font-size: 13px !important;
}
.pulse-tag {
  background: #ff9800 !important;
  color: #fff !important;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  50% { box-shadow: 0 0 0 6px rgba(255, 152, 0, .15); }
}

/* ── Bar Chart ── */
.bar-chart {
  height: 200px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 8px 28px;
  border-radius: 20px;
  background: #fafafa;
  border: 1px solid var(--line);
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  position: relative;
  justify-content: flex-end;
}
.bar-fill {
  width: 100%;
  max-width: 48px;
  border-radius: 8px 8px 4px 4px;
  background: linear-gradient(180deg, var(--primary-2), var(--primary));
  min-height: 8px;
  transition: height .3s ease;
}
.bar-value {
  position: absolute;
  top: 0;
  font-size: 12px;
  font-weight: 800;
  color: var(--primary);
}
.bar-label {
  position: absolute;
  bottom: -22px;
  font-size: 10px;
  color: var(--muted);
  white-space: nowrap;
}

/* ── Progress ── */
.progress-section {
  margin-top: 16px;
}
.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 700;
}
.progress-bar {
  height: 12px;
  border-radius: 999px;
  background: var(--surface-2);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--primary-2), var(--primary));
  transition: width .3s ease;
}

/* ── Task List Mini ── */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.task-row-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--line);
}
.task-row-mini.done {
  background: #ecffd9;
  opacity: .8;
}
.habit-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.habit-mini {
  padding: 8px 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mistake-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.mistake-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid var(--line);
  font-size: 13px;
}

/* ── Misc ── */
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
.setting {
  text-align: left;
  color: inherit;
}
.article-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.article-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #fff;
  text-decoration: none;
  color: inherit;
  transition: border-color .12s ease, box-shadow .12s ease;
}
.article-row:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(16,110,0,.08);
}
.empty-state {
  text-align: center;
  padding: 32px 16px;
}

@media (max-width: 900px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .filter-bar { flex-direction: column; }
}
</style>
