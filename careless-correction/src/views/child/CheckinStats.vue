<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../utils/api'

interface DayCell {
  date: string
  status: 'approved' | 'pending' | 'rejected' | 'none'
  points: number
  collected: boolean
  taskCount: number
  habitStepCount: number
}

interface StatsPayload {
  today: string
  todayStatus: DayCell['status']
  streakDays: number
  approvedStreakDays: number
  bestStreakDays: number
  totalDays: number
  submittedDays: number
  monthDays: number
  monthSubmittedDays: number
  monthSunlight: number
  totalSunlight: number
  collectedSunlight: number
  uncollectedSunlight: number
  avgSunlight: number
  daily: DayCell[]
  monthly: { month: string; days: number; sunlight: number }[]
}

const router = useRouter()
const loading = ref(true)
const stats = ref<StatsPayload | null>(null)
const rangeDays = ref(119)
const rangeOptions = [
  { label: '近 1 个月', days: 35 },
  { label: '近 3 个月', days: 91 },
  { label: '近 4 个月', days: 119 },
]

async function loadStats() {
  loading.value = true
  try {
    stats.value = await api.checkins.getStats(undefined, rangeDays.value) as StatsPayload
  } catch {
    stats.value = null
  }
  loading.value = false
}

onMounted(loadStats)
watch(rangeDays, loadStats)

const WEEK_LABELS = ['一', '二', '三', '四', '五', '六', '日']

/** 按周分列（周一为每列第一行），用于日历热力图 */
const calendarWeeks = computed<(DayCell | null)[][]>(() => {
  const daily = stats.value?.daily ?? []
  if (!daily.length) return []
  const cells: (DayCell | null)[] = []
  const first = new Date(`${daily[0].date}T00:00:00`)
  const pad = (first.getDay() + 6) % 7
  for (let i = 0; i < pad; i++) cells.push(null)
  cells.push(...daily)
  while (cells.length % 7 !== 0) cells.push(null)
  const weeks: (DayCell | null)[][] = []
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7))
  return weeks
})

/** 月份标签：每列的第一天跨月时标注 */
const monthMarks = computed(() => {
  const weeks = calendarWeeks.value
  const marks: { index: number; label: string }[] = []
  let lastMonth = ''
  weeks.forEach((week, i) => {
    const day = week.find(Boolean)
    if (!day) return
    const month = day.date.slice(0, 7)
    if (month !== lastMonth) {
      lastMonth = month
      marks.push({ index: i, label: `${Number(day.date.slice(5, 7))}月` })
    }
  })
  return marks
})

function cellLevel(day: DayCell | null): string {
  if (!day) return 'cell-empty'
  if (day.status === 'pending') return 'cell-pending'
  if (day.status === 'rejected') return 'cell-rejected'
  if (day.status !== 'approved') return 'cell-none'
  if (day.points >= 35) return 'cell-l4'
  if (day.points >= 20) return 'cell-l3'
  if (day.points >= 10) return 'cell-l2'
  return 'cell-l1'
}

function cellTitle(day: DayCell | null): string {
  if (!day) return ''
  const label = day.status === 'approved'
    ? `已通过 · +${day.points} 阳光${day.collected ? '（已收集）' : '（待收集）'}`
    : day.status === 'pending'
      ? '等待家长审批'
      : day.status === 'rejected'
        ? '已被驳回'
        : '未打卡'
  return `${fmtFull(day.date)} ${label}`
}

function fmtFull(date: string): string {
  const [y, m, d] = date.split('-')
  return `${y}年${Number(m)}月${Number(d)}日`
}

function fmtShort(date: string): string {
  const [, m, d] = date.split('-')
  return `${Number(m)}月${Number(d)}日`
}

/** 近 30 天每日获得阳光柱状图 */
const barDays = computed(() => (stats.value?.daily ?? []).slice(-30))
const maxBarPoints = computed(() =>
  Math.max(10, ...barDays.value.map(d => d.points || 0)),
)

function barHeight(d: DayCell): string {
  if (!d.points) return '3px'
  return `${Math.max(6, Math.round((d.points / maxBarPoints.value) * 100))}%`
}

function barClass(d: DayCell): string {
  if (d.status === 'approved') return 'bar-approved'
  if (d.status === 'pending') return 'bar-pending'
  if (d.status === 'rejected') return 'bar-rejected'
  return 'bar-none'
}

const recordList = computed(() =>
  (stats.value?.daily ?? [])
    .filter(d => d.status !== 'none')
    .slice()
    .reverse()
    .slice(0, 20),
)

const nextMilestone = computed(() => {
  const streak = stats.value?.streakDays ?? 0
  const milestones = [3, 7, 14, 21, 30, 50, 100, 200, 365]
  return milestones.find(m => m > streak) ?? 365
})

const milestoneProgress = computed(() => {
  const streak = stats.value?.streakDays ?? 0
  const target = nextMilestone.value
  return Math.min(100, Math.round((streak / target) * 100))
})

const monthMaxDays = computed(() =>
  Math.max(1, ...(stats.value?.monthly ?? []).map(m => m.days)),
)

function statusLabel(status: DayCell['status']): string {
  if (status === 'approved') return '✅ 已通过'
  if (status === 'pending') return '🕐 待审批'
  if (status === 'rejected') return '❌ 已驳回'
  return '— 未打卡'
}

const todayLabel = computed(() => {
  const s = stats.value?.todayStatus
  if (s === 'approved') return '今天已打卡并通过'
  if (s === 'pending') return '今天已打卡，等待家长审批'
  if (s === 'rejected') return '今天的打卡被驳回了，可以重新提交'
  return '今天还没打卡'
})
</script>

<template>
  <div class="page stats-page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📊 打卡统计</span>
        <h1>坚持的痕迹</h1>
        <p class="lead">
          这里记录你每一天的打卡与收获的阳光。连续打卡越多，小树长得越壮。
        </p>
        <div class="hero-actions">
          <button class="btn" @click="router.push('/habit')">✅ 去今日打卡</button>
          <button class="btn ghost" @click="router.push('/tree')">🌳 去收阳光</button>
        </div>
        <p class="today-hint">{{ todayLabel }}</p>
      </div>
      <div class="panel streak-panel">
        <div class="card-title">
          <h2>连续打卡</h2>
          <span class="tag">最佳 {{ stats?.bestStreakDays ?? 0 }} 天</span>
        </div>
        <div class="streak-main">
          <span class="streak-flame">🔥</span>
          <strong class="streak-big">{{ stats?.streakDays ?? 0 }}</strong>
          <span class="streak-unit">天</span>
        </div>
        <div class="milestone">
          <div class="milestone-row">
            <span>距离 {{ nextMilestone }} 天连击</span>
            <strong>{{ stats?.streakDays ?? 0 }}/{{ nextMilestone }}</strong>
          </div>
          <div class="progress"><span :style="{ width: `${milestoneProgress}%` }"></span></div>
        </div>
      </div>
    </section>

    <div v-if="loading" class="panel" style="text-align:center;padding:40px">
      <p class="muted">⏳ 正在统计打卡数据...</p>
    </div>

    <template v-else-if="stats">
      <!-- KPI -->
      <section class="kpi-grid">
        <div class="kpi-card">
          <span class="kpi-icon">🔥</span>
          <strong>{{ stats.streakDays }}</strong>
          <span class="kpi-label">当前连续（天）</span>
          <span class="kpi-sub">最佳 {{ stats.bestStreakDays }} 天</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-icon">📅</span>
          <strong>{{ stats.totalDays }}</strong>
          <span class="kpi-label">累计打卡（天）</span>
          <span class="kpi-sub">已提交 {{ stats.submittedDays }} 天</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-icon">🗓️</span>
          <strong>{{ stats.monthSubmittedDays }}</strong>
          <span class="kpi-label">本月打卡（天）</span>
          <span class="kpi-sub">已通过 {{ stats.monthDays }} 天 · +{{ stats.monthSunlight }} 阳光</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-icon">☀️</span>
          <strong>{{ stats.totalSunlight }}</strong>
          <span class="kpi-label">打卡累计阳光</span>
          <span class="kpi-sub">
            已收集 {{ stats.collectedSunlight }} · 待收集 {{ stats.uncollectedSunlight }}
          </span>
        </div>
      </section>

      <!-- 日历热力图 -->
      <section class="panel">
        <div class="card-title">
          <h2>打卡日历</h2>
          <div class="range-tabs">
            <button
              v-for="opt in rangeOptions"
              :key="opt.days"
              class="range-tab"
              :class="{ active: rangeDays === opt.days }"
              @click="rangeDays = opt.days"
            >{{ opt.label }}</button>
          </div>
        </div>

        <div class="calendar-layout">
          <div class="calendar-scroll">
            <div class="calendar">
              <div class="week-labels">
                <span v-for="w in WEEK_LABELS" :key="w">{{ w }}</span>
              </div>
              <div class="calendar-body">
                <div class="month-marks">
                  <span
                    v-for="m in monthMarks"
                    :key="m.label + m.index"
                    class="month-mark"
                    :style="{ gridColumn: m.index + 1 }"
                  >{{ m.label }}</span>
                </div>
                <div class="weeks">
                  <div v-for="(week, wi) in calendarWeeks" :key="wi" class="week-col">
                    <div
                      v-for="(day, di) in week"
                      :key="di"
                      class="day-cell"
                      :class="[cellLevel(day), { 'is-today': day?.date === stats.today }]"
                      :title="cellTitle(day)"
                    >
                      <span v-if="day && day.points" class="day-points">{{ day.points }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <aside class="calendar-summary">
            <div class="summary-row">
              <span>当前连击</span>
              <strong class="sum-hot">🔥 {{ stats.streakDays }} 天</strong>
            </div>
            <div class="summary-row">
              <span>历史最佳</span>
              <strong>{{ stats.bestStreakDays }} 天</strong>
            </div>
            <div class="summary-row">
              <span>累计打卡</span>
              <strong>{{ stats.totalDays }} 天</strong>
            </div>
            <div class="summary-row">
              <span>平均每天</span>
              <strong>+{{ stats.avgSunlight }} 阳光</strong>
            </div>
            <div class="summary-row">
              <span>待收集阳光</span>
              <strong class="sum-sun">☀️ {{ stats.uncollectedSunlight }}</strong>
            </div>
            <p class="summary-tip">点格子可看当天详情</p>
          </aside>
        </div>

        <div class="legend">
          <span class="legend-item"><i class="dot cell-none"></i>未打卡</span>
          <span class="legend-item"><i class="dot cell-l1"></i>1-9</span>
          <span class="legend-item"><i class="dot cell-l2"></i>10-19</span>
          <span class="legend-item"><i class="dot cell-l3"></i>20-34</span>
          <span class="legend-item"><i class="dot cell-l4"></i>35+</span>
          <span class="legend-item"><i class="dot cell-pending"></i>待审批</span>
          <span class="legend-item"><i class="dot cell-rejected"></i>已驳回</span>
          <span class="legend-hint">格子里的数字是当天获得的阳光</span>
        </div>
      </section>

      <!-- 每日阳光柱状图 + 月度汇总 -->
      <div class="two-col">
        <section class="panel">
          <div class="card-title">
            <h2>每日打卡获得阳光</h2>
            <span class="tag">近 30 天</span>
          </div>
          <div class="bar-chart">
            <div
              v-for="d in barDays"
              :key="d.date"
              class="bar-slot"
              :title="`${fmtFull(d.date)} · ${statusLabel(d.status)}${d.points ? ` · +${d.points}` : ''}`"
            >
              <span v-if="d.points" class="bar-value">{{ d.points }}</span>
              <div class="bar" :class="barClass(d)" :style="{ height: barHeight(d) }"></div>
              <span class="bar-date">{{ Number(d.date.slice(8, 10)) }}</span>
            </div>
          </div>
          <p class="muted chart-hint">
            平均每天 +{{ stats.avgSunlight }} 阳光 · 本月已获得 +{{ stats.monthSunlight }}
          </p>
        </section>

        <section class="panel">
          <div class="card-title">
            <h2>每月打卡</h2>
            <span class="tag">近 6 个月</span>
          </div>
          <div class="monthly-list">
            <div v-for="m in stats.monthly" :key="m.month" class="monthly-row">
              <span class="monthly-label">{{ Number(m.month.slice(5, 7)) }}月</span>
              <div class="monthly-track">
                <div class="monthly-fill" :style="{ width: `${(m.days / monthMaxDays) * 100}%` }"></div>
              </div>
              <span class="monthly-value">{{ m.days }} 天</span>
              <span class="monthly-sun">☀️ {{ m.sunlight }}</span>
            </div>
          </div>
        </section>
      </div>

      <!-- 打卡明细 -->
      <section class="panel">
        <div class="card-title">
          <h2>打卡记录</h2>
          <span class="tag">{{ recordList.length }} 条</span>
        </div>
        <div v-if="recordList.length" class="record-list">
          <div v-for="d in recordList" :key="d.date" class="record-row">
            <div class="record-date">
              <strong>{{ fmtShort(d.date) }}</strong>
              <span class="muted">{{ d.date === stats.today ? '今天' : d.date.slice(0, 4) }}</span>
            </div>
            <div class="record-meta">
              <span class="record-status" :class="`status-${d.status}`">{{ statusLabel(d.status) }}</span>
              <span v-if="d.taskCount" class="record-chip">✅ {{ d.taskCount }} 项</span>
              <span v-if="d.habitStepCount" class="record-chip">🌱 {{ d.habitStepCount }} 步</span>
            </div>
            <div class="record-sun">
              <template v-if="d.status === 'approved'">
                <strong>+{{ d.points }}</strong>
                <span class="sun-state" :class="{ collected: d.collected }">
                  {{ d.collected ? '已收集' : '待收集' }}
                </span>
              </template>
              <span v-else class="muted">—</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon">📝</div>
          <p>还没有打卡记录，今天就开始吧</p>
          <button class="btn" @click="router.push('/habit')">去今日打卡</button>
        </div>
      </section>
    </template>

    <section v-else class="panel" style="text-align:center;padding:40px">
      <p class="muted">暂时读不到统计数据，请检查网络后重试</p>
      <button class="btn ghost" style="margin-top:12px" @click="loadStats">重新加载</button>
    </section>
  </div>
</template>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  width: 100%;
}

.hero-actions {
  display: flex;
  gap: 10px;
  margin-top: 18px;
  flex-wrap: wrap;
}
.today-hint {
  margin-top: 14px;
  font-size: 14px;
  font-weight: 800;
  color: var(--muted);
}

/* ── 连击卡 ── */
.streak-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.streak-main {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 6px 0 2px;
}
.streak-flame {
  font-size: 40px;
  line-height: 1;
  animation: flame-soft 1.8s ease-in-out infinite;
}
@keyframes flame-soft {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.14); }
}
.streak-big {
  font-size: 64px;
  line-height: 1;
  font-weight: 900;
  color: #ff8f00;
  letter-spacing: -2px;
  text-shadow: 0 3px 0 #ffe082;
}
.streak-unit {
  font-size: 18px;
  font-weight: 900;
  color: #b26a00;
}
.milestone {
  margin-top: 14px;
}
.milestone-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 800;
  color: var(--muted);
  margin-bottom: 6px;
}

/* ── KPI ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}
.kpi-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 20px;
  border-radius: 26px;
  background: rgba(255, 255, 255, .82);
  border: 1px solid var(--line);
  box-shadow: 0 10px 26px rgba(75, 63, 54, .06);
}
.kpi-icon {
  font-size: 22px;
}
.kpi-card strong {
  font-size: 34px;
  line-height: 1.1;
  font-weight: 900;
  color: var(--primary);
}
.kpi-label {
  font-size: 13px;
  font-weight: 800;
  color: var(--ink);
}
.kpi-sub {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

/* ── 日历 ── */
.range-tabs {
  display: flex;
  gap: 6px;
  background: var(--surface-2, #f3f1e6);
  padding: 4px;
  border-radius: 999px;
}
.range-tab {
  border: 0;
  background: transparent;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
  cursor: pointer;
}
.range-tab.active {
  background: #fff;
  color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, .08);
}
.calendar-layout {
  display: flex;
  align-items: flex-start;
  gap: 28px;
  justify-content: space-between;
}
.calendar-scroll {
  overflow-x: auto;
  padding-bottom: 6px;
  flex: 0 1 auto;
}
.calendar {
  display: flex;
  gap: 8px;
  min-width: max-content;
}
.week-labels {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-top: 22px;
  font-size: 11px;
  font-weight: 800;
  color: var(--muted);
}
.week-labels span {
  height: 17px;
  line-height: 17px;
}
.calendar-body {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.month-marks {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 22px;
  gap: 5px;
  height: 17px;
  font-size: 11px;
  font-weight: 800;
  color: var(--muted);
}
.month-mark {
  grid-row: 1;
  white-space: nowrap;
}
.weeks {
  display: flex;
  gap: 5px;
}
.week-col {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.day-cell {
  position: relative;
  width: 22px;
  height: 17px;
  border-radius: 5px;
  display: grid;
  place-items: center;
  font-size: 9px;
  font-weight: 900;
  color: #4a5a3f;
  transition: transform .12s ease;
}
.day-cell:hover {
  transform: scale(1.35);
  z-index: 2;
}
.day-cell.is-today {
  outline: 2px solid var(--primary);
  outline-offset: 1px;
}
.cell-empty { background: transparent; }
.cell-none { background: #eceade; }
.cell-l1 { background: #cdefbf; }
.cell-l2 { background: #94d97a; }
.cell-l3 { background: #5cb944; color: #fff; }
.cell-l4 { background: #1d7a0d; color: #fff; }
.cell-pending { background: #ffd699; }
.cell-rejected { background: #ffc4c4; }
.day-points {
  line-height: 1;
  pointer-events: none;
}
.legend {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 14px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}
.legend-hint {
  margin-left: auto;
  font-weight: 700;
  opacity: .85;
}

/* ── 日历右侧小结 ── */
.calendar-summary {
  flex: 0 0 190px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 14px 16px;
  border-radius: 20px;
  background: var(--surface-2, #f6f4e9);
  border: 1px solid var(--line);
}
.summary-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
}
.summary-row strong {
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
}
.summary-row .sum-hot { color: #d97706; }
.summary-row .sum-sun { color: #b26a00; }
.summary-tip {
  margin: 4px 0 0;
  font-size: 11px;
  font-weight: 700;
  color: #9aa38c;
}

/* ── 柱状图 ── */
.two-col {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, .75fr);
  gap: 20px;
}
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 180px;
  padding: 8px 4px 0;
  border-bottom: 1px solid var(--line);
}
.bar-slot {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 2px;
}
.bar-value {
  font-size: 9px;
  font-weight: 900;
  color: #8a6d3b;
}
.bar {
  width: 100%;
  max-width: 22px;
  border-radius: 5px 5px 2px 2px;
  transition: height .3s ease;
}
.bar-approved { background: linear-gradient(180deg, #a5e08a, #4caf50); }
.bar-pending { background: linear-gradient(180deg, #ffe0a3, #ffb74d); }
.bar-rejected { background: linear-gradient(180deg, #ffd0d0, #ef9a9a); }
.bar-none { background: #e8e6da; }
.bar-date {
  font-size: 9px;
  font-weight: 700;
  color: var(--muted);
  transform: scale(.9);
}
.chart-hint {
  margin-top: 10px;
  font-size: 12px;
  font-weight: 700;
}

/* ── 月度 ── */
.monthly-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 4px;
}
.monthly-row {
  display: grid;
  grid-template-columns: 42px 1fr 46px 62px;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
}
.monthly-label {
  color: var(--ink);
}
.monthly-track {
  height: 12px;
  border-radius: 999px;
  background: #eceade;
  overflow: hidden;
}
.monthly-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--primary-2, #80dc67), var(--primary));
  min-width: 2px;
}
.monthly-value {
  color: var(--muted);
  text-align: right;
}
.monthly-sun {
  color: #b26a00;
  text-align: right;
}

/* ── 明细 ── */
.record-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.record-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, .7);
}
.record-date {
  display: flex;
  flex-direction: column;
  min-width: 76px;
  font-size: 13px;
}
.record-date strong {
  font-size: 15px;
  font-weight: 900;
}
.record-meta {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.record-status {
  font-size: 12px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 999px;
}
.record-status.status-approved { background: #e8f5e9; color: #2e7d32; }
.record-status.status-pending { background: #fff3e0; color: #e65100; }
.record-status.status-rejected { background: #ffebee; color: #c62828; }
.record-chip {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2, #f3f1e6);
  color: var(--muted);
}
.record-sun {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: #b26a00;
}
.record-sun strong {
  font-size: 17px;
  color: #ff9800;
}
.sun-state {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #fff3e0;
  color: #b26a00;
}
.sun-state.collected {
  background: #e8f5e9;
  color: #2e7d32;
}

.empty-state {
  text-align: center;
  padding: 40px 24px;
  color: var(--muted);
}
.empty-icon {
  font-size: 44px;
  margin-bottom: 10px;
}
.empty-state p {
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 14px;
}

@media (max-width: 980px) {
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .two-col { grid-template-columns: 1fr; }
  .calendar-layout { flex-direction: column; gap: 16px; }
  .calendar-summary { flex: 1 1 auto; width: 100%; }
}
@media (max-width: 600px) {
  .streak-big { font-size: 52px; }
  .record-row { flex-wrap: wrap; gap: 8px; }
  .bar-chart { height: 150px; }
  .legend-hint { margin-left: 0; width: 100%; }
}
</style>
