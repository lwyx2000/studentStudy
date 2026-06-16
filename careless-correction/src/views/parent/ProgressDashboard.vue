<script setup lang="ts">
import { computed, ref } from 'vue'
import { categoryLabels } from '../../utils/constants'
import { useChildSelectStore, useGrowthStore, useMistakeStore, useTaskStore, useUserStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

type TimeRange = 'day' | 'week' | 'month' | 'half_year' | 'year'

const taskStore = useTaskStore()
const userStore = useUserStore()
const mistakeStore = useMistakeStore()
const growthStore = useGrowthStore()
const childSelectStore = useChildSelectStore()
const selectedChild = computed(() => childSelectStore.selectedChild)

const selectedRange = ref<TimeRange>('day')

const rangeOptions: { value: TimeRange; label: string; icon: string }[] = [
  { value: 'day', label: '当日', icon: '☀️' },
  { value: 'week', label: '本周', icon: '📅' },
  { value: 'month', label: '本月', icon: '🗓️' },
  { value: 'half_year', label: '半年', icon: '📆' },
  { value: 'year', label: '一年', icon: '📈' },
]

// ---- Computed stats by time range ----

const completedToday = computed(() => taskStore.todayTasks.filter(t => t.status === 'completed').length)
const totalToday = computed(() => taskStore.todayTasks.length)

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
  const weeks = ['第1周', '第2周', '第3周', '第4周']
  const currentWeek = taskStore.currentWeekHabit.weekNumber
  const completed = completedToday.value
  const total = totalToday.value
  return weeks.map((week, i) => {
    const weekNum = i + 1
    const isCurrent = weekNum === currentWeek || (weekNum < currentWeek)
    const isFuture = weekNum > currentWeek
    return {
      week,
      done: isFuture ? 0 : isCurrent ? completed * (weekNum === currentWeek ? 1 : 5) : total * 5,
      total: total * 5,
      isCurrent: weekNum === currentWeek,
      isFuture,
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
        <p class="lead">按时间维度查看孩子的习惯养成和任务完成趋势，及时调整任务密度和难度。</p>
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

    <!-- 习惯进度 + 任务完成详情 -->
    <section class="grid-2">
      <!-- 习惯进度 -->
      <div class="panel">
        <div class="card-title">
          <h2>🌱 习惯进度</h2>
          <span class="tag">{{ selectedRange === 'day' ? '当日' : selectedRange === 'week' ? '本周' : selectedRange === 'month' ? '本月' : selectedRange === 'half_year' ? '半年' : '年度' }}</span>
        </div>

        <!-- 日/周视图：SOP 步骤 -->
        <template v-if="selectedRange === 'day' || selectedRange === 'week'">
          <p class="lead" style="margin-bottom:12px">
            主线习惯：<strong>{{ taskStore.currentWeekHabit.title }}</strong> · 第 {{ taskStore.currentWeekHabit.weekNumber }} 周
          </p>
          <div class="list">
            <div
              v-for="step in taskStore.currentWeekHabit.steps"
              :key="step.order"
              class="list-row"
              style="justify-content:flex-start;gap:14px"
            >
              <b class="step-num">{{ step.order }}</b>
              <span>{{ step.instruction }}</span>
            </div>
          </div>

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

      <!-- 任务完成情况 -->
      <div class="panel">
        <div class="card-title">
          <h2>📋 任务完成情况</h2>
          <span class="tag">{{ completedToday }}/{{ totalToday }} 今日完成</span>
        </div>

        <!-- 当日任务清单 -->
        <template v-if="selectedRange === 'day'">
          <div v-if="taskStore.todayTasks.length" class="list">
            <div
              v-for="task in taskStore.todayTasks"
              :key="task.id"
              class="list-row"
              :style="task.status === 'completed' ? 'background:#ecffd9;opacity:.85' : ''"
            >
              <div style="display:flex;align-items:center;gap:12px;min-width:0">
                <span style="font-size:22px;flex-shrink:0">{{ task.icon }}</span>
                <div style="min-width:0">
                  <strong>{{ task.title }}</strong>
                  <span class="muted" style="display:block;font-size:13px">{{ task.description }}</span>
                </div>
              </div>
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
          <p v-else class="muted" style="text-align:center;padding:32px">暂无今日任务</p>
        </template>

        <!-- 周/月视图：分类汇总 -->
        <template v-if="selectedRange === 'week' || selectedRange === 'month'">
          <h3 style="margin-bottom:12px">按分类统计</h3>
          <div class="list">
            <div
              v-for="cat in [...new Set(taskStore.todayTasks.map(t => t.type))]"
              :key="cat"
              class="list-row"
            >
              <span style="font-weight:800">{{ categoryLabels[cat] || cat }}</span>
              <div style="display:flex;align-items:center;gap:8px">
                <span class="muted">
                  {{ taskStore.todayTasks.filter(t => t.type === cat && t.status === 'completed').length }}
                  /
                  {{ taskStore.todayTasks.filter(t => t.type === cat).length }} 完成
                </span>
                <div class="progress" style="width:80px;height:8px">
                  <span
                    :style="{
                      width: `${Math.round((taskStore.todayTasks.filter(t => t.type === cat && t.status === 'completed').length / Math.max(taskStore.todayTasks.filter(t => t.type === cat).length, 1)) * 100)}%`
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
@media (max-width: 900px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .day-grid { grid-template-columns: repeat(4, 1fr); }
  .bar-chart { height: 120px; }
}
</style>
