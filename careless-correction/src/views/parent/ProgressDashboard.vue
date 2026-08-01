<script setup lang="ts">
import { computed, ref } from 'vue'
import { categoryLabels } from '../../utils/constants'
import { useChildSelectStore, useGrowthStore, useMistakeStore, useParentStore, useTaskStore, useUserStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

type TimeRange = 'day' | 'week' | 'month' | 'half_year' | 'year'

const taskStore = useTaskStore()
const userStore = useUserStore()
const mistakeStore = useMistakeStore()
const growthStore = useGrowthStore()
const parentStore = useParentStore()
const childSelectStore = useChildSelectStore()
const selectedChild = computed(() => childSelectStore.selectedChild)

const displayTasks = computed(() => parentStore.parentTaskTemplates)

const selectedRange = ref<TimeRange>('day')
const expandedTaskId = ref<string | null>(null)
const habitExpanded = ref(false)

function toggleExpandTask(id: string) {
  expandedTaskId.value = expandedTaskId.value === id ? null : id
}

const rangeOptions: { value: TimeRange; label: string; icon: string }[] = [
  { value: 'day', label: '当日', icon: '☀️' },
  { value: 'week', label: '本周', icon: '📅' },
  { value: 'month', label: '本月', icon: '🗓️' },
  { value: 'half_year', label: '半年', icon: '📆' },
  { value: 'year', label: '一年', icon: '📈' },
]

// ---- Computed stats by time range ----

const completedToday = computed(() => displayTasks.value.filter(t => t.status === 'completed').length)
const totalToday = computed(() => displayTasks.value.length)

// Simulate weekly data: seeded defaults + current
const weeklyStats = computed(() => {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const today = new Date().getDay() || 7 // 周日=7
  const completed = completedToday.value
  const total = totalToday.value
  return days.map((day, i) => {
    const isToday = i + 1 === today
    const isPast = i + 1 < today
    return {
      day,
      done: isPast ? total : isToday ? completed : 0,
      total,
      isToday,
      isPast,
    }
  })
})

const monthlyStats = computed(() => {
  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const weekOfMonth = Math.ceil((now.getDate() + monthStart.getDay()) / 7)
  const weeks = ['第1周', '第2周', '第3周', '第4周']
  const completed = completedToday.value
  const total = totalToday.value
  return weeks.map((week, i) => {
    const weekNum = i + 1
    const isCurrent = weekNum === weekOfMonth
    const isPast = weekNum < weekOfMonth
    return {
      week,
      done: isPast ? total * 5 : isCurrent ? completed : 0,
      total: total * 5,
      isCurrent,
      isFuture: weekNum > weekOfMonth,
    }
  })
})

const halfYearStats = computed(() => {
  const months = ['1月', '2月', '3月', '4月', '5月', '6月']
  const currentMonth = new Date().getMonth() // 0-based
  return months.map((month, i) => {
    const isFuture = i > currentMonth
    const completionRate = isFuture ? 0 : Math.max(0.5, 1 - (currentMonth - i) * 0.08)
    return { month, rate: completionRate, isFuture }
  })
})

const yearlyStats = computed(() => {
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  const currentMonth = new Date().getMonth()
  return months.map((month, i) => {
    const isFuture = i > currentMonth
    const rate = isFuture ? 0 : Math.max(0.4, 1 - (currentMonth - i) * 0.05)
    return { month, rate, isFuture }
  })
})

const trendStats = computed(() => {
  if (selectedRange.value === 'week') {
    return weeklyStats.value.map(d => ({ label: d.day, done: d.done, total: d.total }))
  }
  return monthlyStats.value.slice(0, 7).map(m => ({ label: m.week, done: m.done, total: m.total }))
})

const totalMistakes = computed(() => mistakeStore.records.length)
const totalLossItems = computed(() => growthStore.itemLossRecords.reduce((s, i) => s + i.frequency, 0))
const totalStorage = computed(() => growthStore.storageRecords.length)

const summaryStats = computed(() => {
  switch (selectedRange.value) {
    case 'day':
      return {
        tasksDone: completedToday.value,
        tasksTotal: totalToday.value,
        habitsTracked: taskStore.weeklyProgress,
        mistakesAdded: 0,
        label: '今日',
      }
    case 'week':
      return {
        tasksDone: completedToday.value * 5,
        tasksTotal: totalToday.value * 7,
        habitsTracked: taskStore.weeklyProgress,
        mistakesAdded: Math.round(mistakeStore.records.length / 4),
        label: '本周预估',
      }
    case 'month':
      return {
        tasksDone: completedToday.value * 20,
        tasksTotal: totalToday.value * 30,
        habitsTracked: taskStore.weeklyProgress * 4,
        mistakesAdded: mistakeStore.records.length,
        label: '本月预估',
      }
    case 'half_year':
      return {
        tasksDone: completedToday.value * 120,
        tasksTotal: totalToday.value * 180,
        habitsTracked: taskStore.weeklyProgress * 24,
        mistakesAdded: mistakeStore.records.length,
        label: '半年累计',
      }
    case 'year':
      return {
        tasksDone: completedToday.value * 240,
        tasksTotal: totalToday.value * 365,
        habitsTracked: taskStore.weeklyProgress * 48,
        mistakesAdded: mistakeStore.records.length,
        label: '年度累计',
      }
  }
})
</script>

<template>
  <div class="page">
    <!-- Hero -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📊 进度查看</span>
        <h1>习惯与任务完成进度</h1>
        <p class="lead">按时间维度查看孩子的习惯养成和任务完成趋势，及时调整任务密度。</p>
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
            <strong>☀️ {{ userStore.sunlightPoints }}</strong>
            <span>阳光值</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 时间筛选 -->
    <ChildSelector />
    <section class="range-bar">
      <button
        v-for="opt in rangeOptions"
        :key="opt.value"
        class="btn"
        :class="selectedRange === opt.value ? '' : 'ghost'"
        @click="selectedRange = opt.value"
      >
        {{ opt.icon }} {{ opt.label }}
      </button>
    </section>

    <!-- 概览统计卡片 -->
    <section class="grid-4">
      <div class="soft-card stat-card">
        <div class="icon-tile">✅</div>
        <strong>{{ summaryStats.tasksDone }}</strong>
        <span class="muted">已完成任务</span>
        <div class="progress" style="margin-top:8px">
          <span :style="{ width: `${Math.round((summaryStats.tasksDone / Math.max(summaryStats.tasksTotal, 1)) * 100)}%` }"></span>
        </div>
      </div>
      <div class="soft-card stat-card">
        <div class="icon-tile">🎯</div>
        <strong>{{ summaryStats.habitsTracked }}</strong>
        <span class="muted">习惯打卡次数</span>
      </div>
      <div class="soft-card stat-card">
        <div class="icon-tile">📚</div>
        <strong>{{ summaryStats.mistakesAdded }}</strong>
        <span class="muted">{{ selectedRange === 'day' ? '今日错题' : '累计错题' }}</span>
      </div>
      <div class="soft-card stat-card">
        <div class="icon-tile">📋</div>
        <strong>{{ summaryStats.tasksTotal }}</strong>
        <span class="muted">{{ summaryStats.label }}总任务量</span>
      </div>
    </section>

    <!-- 任务完成详情 + 习惯进度 -->
    <section class="grid-2">
      <!-- 任务完成情况（默认展开） -->
      <div class="panel">
        <div class="card-title">
          <h2>📋 任务完成情况</h2>
          <span class="tag">{{ completedToday }}/{{ totalToday }} 今日完成</span>
        </div>

        <!-- 当日任务清单 -->
        <template v-if="selectedRange === 'day'">
          <div v-if="displayTasks.length" class="list">
            <template v-for="task in displayTasks" :key="task.id">
              <div
                class="list-row task-row"
                :class="{ 'task-row-expanded': expandedTaskId === task.id }"
                :style="task.status === 'completed' ? 'background:#ecffd9;opacity:.85' : ''"
                @click="toggleExpandTask(task.id)"
              >
                <div style="display:flex;align-items:center;gap:12px;min-width:0;flex:1">
                  <span style="font-size:22px;flex-shrink:0">{{ task.icon }}</span>
                  <div style="min-width:0">
                    <strong>{{ task.title }}</strong>
                    <span class="muted" style="display:block;font-size:13px">{{ task.description }}</span>
                  </div>
                </div>
                <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
                  <span v-if="task.subTasks?.length" class="mini-tag" style="cursor:pointer">
                    {{ expandedTaskId === task.id ? '▲' : '▼' }} {{ task.subTasks.length }}
                  </span>
                  <span
                    class="tag"
                    :style="task.status === 'completed'
                      ? 'background:#d9f5c8;color:var(--primary)'
                      : ''"
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
          <p v-else class="muted" style="text-align:center;padding:32px">暂无今日任务</p>
        </template>

        <!-- 周/月视图：分类汇总 -->
        <template v-if="selectedRange === 'week' || selectedRange === 'month'">
          <h3 style="margin-bottom:12px">按分类统计</h3>
          <div class="list">
            <div
              v-for="cat in [...new Set(displayTasks.map(t => t.type))]"
              :key="cat"
              class="list-row"
            >
              <span style="font-weight:800">{{ categoryLabels[cat] || cat }}</span>
              <div style="display:flex;align-items:center;gap:8px">
                <span class="muted">
                  {{ displayTasks.filter(t => t.type === cat && t.status === 'completed').length }}
                  /
                  {{ displayTasks.filter(t => t.type === cat).length }} 完成
                </span>
                <div class="progress" style="width:80px;height:8px">
                  <span
                    :style="{
                      width: `${Math.round((displayTasks.filter(t => t.type === cat && t.status === 'completed').length / Math.max(displayTasks.filter(t => t.type === cat).length, 1)) * 100)}%`
                    }"
                  ></span>
                </div>
              </div>
            </div>
          </div>

          <h3 style="margin-top:20px;margin-bottom:12px">每日完成趋势</h3>
          <div class="trend-mini">
            <div
              v-for="d in trendStats"
              :key="d.label"
              class="trend-dot-wrap"
            >
              <div
                class="trend-dot"
                :class="{ done: (d.done || 0) > 0, empty: !d.done }"
                :title="d.label"
              ></div>
              <span class="trend-label">{{ d.label }}</span>
            </div>
          </div>
        </template>

        <!-- 半年/年视图：长期数据 -->
        <template v-if="selectedRange === 'half_year' || selectedRange === 'year'">
          <h3 style="margin-bottom:12px">成长趋势数据</h3>
          <div v-if="growthStore.trendData.length" class="list">
            <div
              v-for="point in growthStore.trendData"
              :key="point.date"
              class="list-row"
            >
              <span style="font-weight:800">{{ point.date }}</span>
              <div style="display:flex;gap:16px;font-size:13px">
                <span>粗心率 {{ Math.round(point.mistakeRate * 100) }}%</span>
                <span>丢失率 {{ point.itemLossRate }}次</span>
                <span>完成率 {{ Math.round(point.taskCompletionRate * 100) }}%</span>
              </div>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:24px">长期数据随使用逐渐积累</p>
        </template>
      </div>

      <!-- 习惯进度（默认收起） -->
      <div class="panel">
        <div class="card-title collapsible-title" @click="habitExpanded = !habitExpanded">
          <div style="display:flex;align-items:center;gap:8px">
            <span class="collapse-arrow" :class="{ expanded: habitExpanded }">▶</span>
            <h2>🌱 习惯进度</h2>
          </div>
          <span class="tag">{{ selectedRange === 'day' ? '当日' : selectedRange === 'week' ? '本周' : selectedRange === 'month' ? '本月' : selectedRange === 'half_year' ? '半年' : '年度' }}</span>
        </div>

        <div v-show="habitExpanded" class="collapse-body">
          <!-- 日/周视图：所有习惯及步骤 -->
          <template v-if="selectedRange === 'day' || selectedRange === 'week'">
            <div v-if="taskStore.habits.length" class="habits-progress">
              <div v-for="habit in taskStore.habits" :key="habit.id" class="panel" style="margin-bottom:14px">
                <div class="card-title">
                  <h3>{{ habit.title }}</h3>
                  <span class="tag">{{ habit.steps.length }} 步 · ☀️ +{{ habit.rewardPoints }}/步</span>
                </div>
                <div class="list">
                  <div
                    v-for="step in habit.steps"
                    :key="step.order"
                    class="list-row"
                    style="justify-content:flex-start;gap:14px"
                  >
                    <b class="step-num">{{ step.order }}</b>
                    <span>{{ step.instruction }}</span>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="muted" style="text-align:center;padding:24px">暂无习惯，请在管理页面创建 ✨</p>

            <!-- 周视图：每日打卡网格 -->
            <template v-if="selectedRange === 'week'">
              <h3 style="margin-top:18px;margin-bottom:10px">每日打卡追踪</h3>
              <div class="day-grid">
                <div
                  v-for="d in weeklyStats"
                  :key="d.day"
                  class="day-cell"
                  :class="{ today: d.isToday, past: d.isPast }"
                >
                  <b>{{ d.day }}</b>
                  <span class="day-count">{{ d.done }}/{{ d.total }}</span>
                  <div class="progress" style="height:6px">
                    <span :style="{ width: `${Math.round((d.done / Math.max(d.total, 1)) * 100)}%` }"></span>
                  </div>
                </div>
              </div>
            </template>
          </template>

          <!-- 月视图：周度柱状 -->
          <template v-if="selectedRange === 'month'">
            <p class="lead" style="margin-bottom:16px">
              本月每周任务完成趋势
            </p>
            <div class="bar-chart">
              <div
                v-for="m in monthlyStats"
                :key="m.week"
                class="bar-col"
              >
                <div class="bar-label">{{ m.done }}</div>
                <div
                  class="bar-fill"
                  :class="{ current: m.isCurrent, future: m.isFuture }"
                  :style="{ height: `${Math.round((m.done / Math.max(m.total, 1)) * 100)}%` }"
                ></div>
                <span class="bar-tag">{{ m.week }}</span>
              </div>
            </div>
          </template>

          <!-- 半年/年视图：月度趋势 -->
          <template v-if="selectedRange === 'half_year' || selectedRange === 'year'">
            <p class="lead" style="margin-bottom:16px">
              月度任务完成率趋势
            </p>
            <div class="bar-chart">
              <div
                v-for="item in (selectedRange === 'half_year' ? halfYearStats : yearlyStats)"
                :key="item.month"
                class="bar-col"
              >
                <div class="bar-label">{{ Math.round(item.rate * 100) }}%</div>
                <div
                  class="bar-fill"
                  :class="{ future: item.isFuture }"
                  :style="{ height: `${Math.round(item.rate * 100)}%` }"
                ></div>
                <span class="bar-tag">{{ item.month }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </section>

    <!-- 增长趋势说明 -->
    <section class="panel" style="text-align:center">
      <p class="lead">
        💡 <strong>提示：</strong>数据随时间累积会越来越准确。保持每日打卡和记录，系统会在「成长档案」中生成更详细的趋势报告和预警。
      </p>
    </section>

  </div>
</template>

<style scoped>
.range-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
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
  gap: 8px;
}
.stat-card strong {
  font-size: 28px;
}
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
.day-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}
.day-cell {
  padding: 10px 6px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid var(--line);
  text-align: center;
}
.day-cell.today {
  border-color: var(--primary);
  background: #ecffd9;
}
.day-cell.past {
  background: #f6fddc;
  opacity: .8;
}
.day-cell b {
  display: block;
  font-size: 13px;
  margin-bottom: 4px;
}
.day-count {
  font-size: 12px;
  color: var(--muted);
  display: block;
  margin-bottom: 6px;
}
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 160px;
  padding-top: 8px;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
  justify-content: flex-end;
}
.bar-fill {
  width: 100%;
  max-width: 48px;
  border-radius: 10px 10px 4px 4px;
  background: linear-gradient(180deg, var(--primary-2), var(--primary));
  min-height: 4px;
  transition: height .4s ease;
}
.bar-fill.current {
  background: linear-gradient(180deg, var(--yellow), #d3bc4e);
}
.bar-fill.future {
  opacity: .25;
}
.bar-label {
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
}
.bar-tag {
  font-size: 11px;
  color: var(--muted);
  font-weight: 700;
  white-space: nowrap;
}
.trend-mini {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}
.trend-dot-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.trend-dot {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 2px solid var(--line);
  background: #fff;
}
.trend-dot.done {
  background: var(--primary-2);
  border-color: var(--primary);
}
.trend-dot.empty {
  background: var(--surface-2);
}
.trend-label {
  font-size: 10px;
  color: var(--muted);
  font-weight: 700;
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
.collapsible-title {
  cursor: pointer;
  user-select: none;
  transition: background .12s ease;
}
.collapsible-title:hover {
  background: #f0f7ee;
  border-radius: 12px;
}
.collapse-arrow {
  font-size: 12px;
  color: var(--muted);
  transition: transform .2s ease;
  display: inline-block;
}
.collapse-arrow.expanded {
  transform: rotate(90deg);
}
.collapse-body {
  overflow: hidden;
}
@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .day-grid { grid-template-columns: repeat(4, 1fr); }
  .bar-chart { height: 120px; }
}
</style>
