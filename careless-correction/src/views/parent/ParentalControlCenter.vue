<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { categoryLabels, gradeLabel } from '../../utils/constants'
import { api, normalizeTask } from '../../utils/api'
import { useBadgeStore, useChildSelectStore, useMistakeStore, useParentStore, useTaskStore, useUserStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const parentStore = useParentStore()
const taskStore = useTaskStore()
const userStore = useUserStore()
const mistakeStore = useMistakeStore()
const childSelectStore = useChildSelectStore()
const badgeStore = useBadgeStore()
const selectedChild = computed(() => childSelectStore.selectedChild)

const loadingData = ref(false)

async function loadData() {
  loadingData.value = true
  const childId = childSelectStore.selectedChildId ?? undefined
  try {
    // Load ALL tasks from inventory (including completed)
    const res = await api.tasks.getInventory(childId)
    const tasks = (res.tasks ?? []).map(normalizeTask)
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
})

const displayTasks = computed(() => parentStore.parentTaskTemplates)
const completedCount = computed(() => displayTasks.value.filter(t => t.status === 'completed').length)
const progressPercent = computed(() => Math.round((completedCount.value / Math.max(displayTasks.value.length, 1)) * 100))

const expandedTaskId = ref<string | null>(null)

// ── Check-in Approval ──
const pendingCheckins = ref<any[]>([])
const loadingCheckins = ref(false)
const expandedCheckinId = ref<number | null>(null)
const checkinDetails = ref<any>(null)
const loadingDetails = ref(false)

async function loadPendingCheckins() {
  loadingCheckins.value = true
  try {
    const res = await api.checkins.getPending()
    pendingCheckins.value = res.pending ?? []
  } catch { /* offline */ }
  loadingCheckins.value = false
}

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
    pendingCheckins.value = pendingCheckins.value.filter(c => c.id !== id)
    if (expandedCheckinId.value === id) {
      expandedCheckinId.value = null
      checkinDetails.value = null
    }
    // Check for badge auto-unlocks after approval
    await badgeStore.checkAndUnlock(childSelectStore.selectedChildId ?? undefined)
  } catch { /* offline */ }
}

async function rejectCheckin(id: number) {
  try {
    await api.checkins.reject(id)
    pendingCheckins.value = pendingCheckins.value.filter(c => c.id !== id)
    if (expandedCheckinId.value === id) {
      expandedCheckinId.value = null
      checkinDetails.value = null
    }
  } catch { /* offline */ }
}

onMounted(() => {
  loadPendingCheckins()
  loadData()
})

function toggleExpandTask(id: string) {
  expandedTaskId.value = expandedTaskId.value === id ? null : id
}

function toggle(key: 'dailyReminder' | 'achievementNotification' | 'weeklyReport' | 'schoolSync') {
  parentStore.updateSettings({ [key]: !parentStore.settings[key] })
}

</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🧭 家长控制中心</span>
        <h1>观察孩子，调任务密度</h1>
        <p class="lead">查看孩子今日任务完成情况、错题积累和习惯数据。在下方设置通知边界，所有设置本地保存。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>{{ selectedChild?.name ?? userStore.profile.name ?? 'Leo' }} 的今日概览</h2>
          <span class="tag">☀️ {{ selectedChild?.sunlightPoints ?? userStore.sunlightPoints }} 阳光值</span>
        </div>
        <div class="kpi">
          <strong>{{ completedCount }}/{{ displayTasks.length }}</strong>
          <span>今日已完成任务</span>
        </div>
        <div class="progress" style="margin-top: 12px;">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>
        <p class="lead">
          Lv{{ userStore.assessment.recommendedLevel }} · {{ gradeLabel(userStore.profile.grade) }}
          · 题库 {{ mistakeStore.records.length }} 题
        </p>
      </div>
    </section>

    <ChildSelector />

    <!-- ⏳ 待审批打卡 -->
    <section v-if="pendingCheckins.length" class="panel" style="border:2px solid #ff9800;background:#fffbf0">
      <div class="card-title">
        <h2>⏳ 待审批打卡</h2>
        <span class="tag" style="background:#ff9800;color:#fff">{{ pendingCheckins.length }} 条待审批</span>
      </div>
      <p class="lead" style="font-size:13px;margin-bottom:12px;color:#8a6d3b">
        💡 点击审批单可展开查看孩子提交的任务和习惯详情。
      </p>
      <div class="list">
        <div v-for="ci in pendingCheckins" :key="ci.id" class="checkin-item-wrap">
          <!-- 审批单头部（可点击展开） -->
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
                <span class="mini-tag">📅 {{ ci.checkDate }}</span>
                <span class="mini-tag" style="background:#fff3cd;color:#856404">☀️ +{{ ci.totalPoints }}</span>
                <span v-if="ci.taskCount" class="mini-tag" style="background:#d4edda;color:#155724">✅ {{ ci.taskCount }} 项任务</span>
                <span v-if="ci.habitStepCount" class="mini-tag" style="background:#cce5ff;color:#004085">🌱 {{ ci.habitStepCount }} 步习惯</span>
              </div>
            </div>
            <div style="display:flex;gap:8px;flex-shrink:0" @click.stop>
              <button class="btn secondary" style="padding:8px 16px;font-size:13px" @click="approveCheckin(ci.id)">
                ✅ 批准
              </button>
              <button class="btn ghost" style="padding:8px 16px;font-size:13px;color:#c00" @click="rejectCheckin(ci.id)">
                ❌ 驳回
              </button>
            </div>
          </div>

          <!-- 展开详情 -->
          <div v-if="expandedCheckinId === ci.id" class="checkin-detail">
            <div v-if="loadingDetails" style="text-align:center;padding:24px">
              <p class="muted">⏳ 加载孩子提交详情...</p>
            </div>
            <template v-else-if="checkinDetails">
              <!-- 提交摘要 -->
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
            </template>
            <div v-else style="text-align:center;padding:16px">
              <p class="muted">加载失败，请重试</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 加载中提示 -->
    <section v-if="loadingCheckins" class="panel" style="text-align:center;padding:24px">
      <p class="muted">⏳ 加载打卡数据...</p>
    </section>

    <!-- 孩子任务完成情况 -->
    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>📋 今日任务清单</h2>
          <span class="tag">{{ completedCount }}/{{ displayTasks.length }} 完成</span>
        </div>
        <div v-if="displayTasks.length" class="list">
          <template v-for="task in displayTasks" :key="task.id">
            <div
              class="list-row task-row"
              :class="{ 'task-row-expanded': expandedTaskId === task.id }"
              :style="task.status === 'completed' ? 'opacity:.7;background:#ecffd9' : ''"
              @click="toggleExpandTask(task.id)"
            >
              <div style="display:flex;align-items:center;gap:12px;min-width:0;flex:1">
                <span style="font-size:24px;flex-shrink:0">{{ task.icon }}</span>
                <div style="min-width:0">
                  <strong>{{ task.title }}</strong>
                  <span class="muted" style="display:block;font-size:13px">{{ task.description }}</span>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
                <span v-if="task.subTasks?.length" class="mini-tag" style="cursor:pointer">
                  {{ expandedTaskId === task.id ? '▲' : '▼' }} {{ task.subTasks.length }} 子任务
                </span>
                <span class="mini-tag">{{ categoryLabels[task.type] || task.type }}</span>
                <span
                  class="tag"
                  :style="task.status === 'completed'
                    ? 'background:#d9f5c8;color:var(--primary)'
                    : 'background:var(--surface-2);color:var(--muted)'"
                >
                  {{ task.status === 'completed' ? '✓ 已完成' : '○ 待完成' }}
                </span>
              </div>
            </div>
            <div v-if="expandedTaskId === task.id && task.subTasks?.length" class="subtask-list">
              <div v-for="sub in task.subTasks" :key="sub.id" class="subtask-row">
                <span class="subtask-dot">•</span>
                <span>{{ sub.title }}</span>
                <span v-if="sub.weekDay" class="mini-tag">{{ sub.weekDay === 'weekday' ? '📅 平时' : sub.weekDay === 'weekend' ? '🎉 周末' : sub.weekDay }}</span>
                <span v-if="sub.type" class="mini-tag">{{ categoryLabels[sub.type] || sub.type }}</span>
              </div>
            </div>
            <div v-else-if="expandedTaskId === task.id" class="subtask-list">
              <p class="muted" style="text-align:center;padding:8px;font-size:13px">暂无子任务</p>
            </div>
          </template>
        </div>
        <p v-else class="muted" style="text-align:center;padding:24px">
          暂无今日任务
        </p>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>📊 习惯列表</h2>
          <span class="tag">{{ taskStore.habits.length }} 个</span>
        </div>
        <div v-if="taskStore.habits.length" class="habits-list">
          <div v-for="habit in taskStore.habits" :key="habit.id" style="margin-bottom:16px">
            <p class="lead" style="margin-bottom:8px;font-size:15px">
              <strong>{{ habit.title }}</strong>
              <span class="muted" style="font-size:13px"> · {{ habit.steps.length }} 步 · ☀️ +{{ habit.rewardPoints }}/步</span>
            </p>
            <div class="list">
              <div
                v-for="step in habit.steps"
                :key="step.order"
                class="list-row"
                style="justify-content:flex-start;gap:12px"
              >
                <b style="display:inline-grid;place-items:center;width:28px;height:28px;border-radius:999px;background:var(--primary);color:#fff;font-size:14px;flex-shrink:0">
                  {{ step.order }}
                </b>
                <span>{{ step.instruction }}</span>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:16px">暂无习惯</p>

        <!-- 错题概览 -->
        <div class="card-title" style="margin-top:20px">
          <h2>📚 错题积累</h2>
          <span class="tag">{{ mistakeStore.records.length }} 题</span>
        </div>
        <div v-if="mistakeStore.records.length" class="list">
          <div
            v-for="record in mistakeStore.records.slice(0, 3)"
            :key="record.id"
            class="list-row"
          >
            <span>📸 {{ record.subject }}</span>
            <span v-if="record.subjectTag" class="tag" style="font-size:12px">{{ record.subjectTag }}</span>
            <span class="muted" style="font-size:12px">
              {{ new Date(record.createdAt).toLocaleDateString() }}
            </span>
          </div>
          <p v-if="mistakeStore.records.length > 3" class="muted" style="text-align:center;font-size:13px">
            还有 {{ mistakeStore.records.length - 3 }} 条错题记录…
          </p>
        </div>
        <p v-else class="muted" style="text-align:center;padding:16px">暂无错题记录</p>
      </div>
    </section>

    <!-- 设置区域 -->
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

    <!-- 循证资源 -->
    <section v-if="parentStore.articles.length" class="panel" style="margin-top:4px">
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
.setting {
  text-align: left;
  color: inherit;
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
  cursor: pointer;
  transition: background .12s ease, border-color .12s ease;
}
.task-row:hover {
  background: #f0f7ee;
}
.task-row-expanded {
  border-color: var(--primary) !important;
  background: #e8f5e0;
}
.subtask-list {
  padding: 6px 0 6px 48px;
  background: #fafff5;
  border-bottom: 1px solid var(--line);
}
.subtask-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 14px;
  color: #444;
}
.subtask-dot {
  color: var(--primary);
  font-size: 18px;
  flex-shrink: 0;
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
.checkin-row {
  flex-wrap: wrap;
  gap: 8px;
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
.checkin-item-wrap .checkin-row {
  border: none;
  border-radius: 0;
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
</style>
