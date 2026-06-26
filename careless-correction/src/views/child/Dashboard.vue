<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGrowthStore, useMistakeStore, useTaskStore, useUserStore } from '../../stores'

const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()
const mistakeStore = useMistakeStore()
const growthStore = useGrowthStore()
const isHighGrade = computed(() => userStore.profile.grade >= 5)
const mainTask = computed(() => taskStore.todayTasks.find(task => task.type === 'study_habit') || taskStore.todayTasks[0])
const progressPercent = computed(() => Math.round((taskStore.weeklyProgress / Math.max(taskStore.todayTasks.length, 1)) * 100))

function completeTask(id: string) {
  const points = taskStore.completeTask(id)
  if (points) {
    userStore.addSunlightPoints(points, `完成任务：${taskStore.todayTasks.find(t => t.id === id)?.title || ''}`)
    const done = taskStore.todayTasks.filter(t => t.status === 'completed').length
    growthStore.recordDataPoint({ taskCompletionRate: done / taskStore.todayTasks.length })
  }
}
</script>

<template>
  <div class="page dashboard" :class="{ mature: isHighGrade }">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">{{ isHighGrade ? '🧭 高年级自治仪表盘' : '⭐ 低年级视觉任务卡' }}</span>
        <h1>{{ isHighGrade ? '像大人一样管理今天' : '今天只做好一件小事' }}</h1>
        <p class="lead">今日任务、复习提醒和收纳状态会随完成情况即时更新，低年级只突出一个主线习惯，高年级显示时间和优先级。</p>
        <button class="btn secondary" @click="router.push('/printable')">一键打印纸质打卡单</button>
      </div>
      <div class="panel">
        <div class="card-title"><h2>{{ userStore.profile.name || 'Leo' }} 的小树苗</h2><span class="tag">☀️ {{ userStore.sunlightPoints }} 阳光值</span></div>
        <div class="growth-tree">{{ isHighGrade ? '🌳' : '🌱' }}</div>
        <div class="progress"><span :style="{ width: `${progressPercent}%` }"></span></div>
        <p class="lead">今日完成 {{ taskStore.weeklyProgress }}/{{ taskStore.todayTasks.length }} · Level {{ userStore.assessment.recommendedLevel }}</p>
      </div>
    </section>

    <template v-if="!isHighGrade">
      <section v-if="mainTask" class="focus-card" :class="{ done: mainTask.status === 'completed' }">
        <div class="big-icon">{{ mainTask.icon }}</div>
        <div>
          <span class="eyebrow">本周主线习惯</span>
          <h2>{{ mainTask.title }}</h2>
          <p class="muted">{{ mainTask.description }}</p>
        </div>
        <button class="btn" :disabled="mainTask.status === 'completed'" @click="completeTask(mainTask.id)">
          {{ mainTask.status === 'completed' ? '已完成' : `确认完成 +${mainTask.rewardPoints}` }}
        </button>
        <!-- Sub-tasks for mainTask -->
        <div v-if="mainTask.subTasks?.length" class="subtasks-inline">
          <div class="subtask-label">子任务</div>
          <div v-for="sub in mainTask.subTasks" :key="sub.id" class="subtask-chip">
            <span class="subtask-checkbox">☐</span>
            <span>{{ sub.title }}</span>
            <span v-if="sub.weekDay" class="mini-tag">{{ sub.weekDay === 'weekday' ? '平时' : sub.weekDay === 'weekend' ? '周末' : sub.weekDay }}</span>
          </div>
        </div>
      </section>
      <section class="grid-2">
        <div v-for="task in taskStore.todayTasks.filter(item => item.id !== mainTask?.id)" :key="task.id" class="soft-card action-card" :class="{ done: task.status === 'completed' }">
          <div class="icon-tile">{{ task.icon }}</div>
          <h2>{{ task.title }}</h2>
          <p class="muted">{{ task.description }}</p>
          <!-- Sub-tasks -->
          <div v-if="task.subTasks?.length" class="subtasks-inline">
            <div v-for="sub in task.subTasks" :key="sub.id" class="subtask-chip">
              <span class="subtask-checkbox">☐</span>
              <span>{{ sub.title }}</span>
              <span v-if="sub.weekDay" class="mini-tag">{{ sub.weekDay === 'weekday' ? '平时' : sub.weekDay === 'weekend' ? '周末' : sub.weekDay }}</span>
            </div>
          </div>
          <button class="btn ghost" :disabled="task.status === 'completed'" @click="completeTask(task.id)">{{ task.status === 'completed' ? '已完成' : '去完成' }}</button>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="grid-2">
        <div class="panel">
          <div class="card-title"><h2>阳光值</h2><button class="btn secondary" @click="router.push('/sunlight')">去兑换</button></div>
          <div class="kpi"><strong>☀️ {{ userStore.sunlightPoints }}</strong><span>完成任务赚阳光值，攒够了换奖励</span></div>
        </div>
        <div class="panel"><div class="card-title"><h2>今日任务优先级</h2><span class="tag">{{ taskStore.todayTasks.length }} 项</span></div><div class="list"><div v-for="task in taskStore.todayTasks" :key="task.id" class="list-row" style="flex-direction:column;align-items:stretch;gap:4px"><div style="display:flex;align-items:center;gap:8px"><span>{{ task.icon }} {{ task.title }}</span><button class="btn ghost" :disabled="task.status === 'completed'" @click="completeTask(task.id)">{{ task.status === 'completed' ? '完成' : '完成' }}</button></div><div v-if="task.subTasks?.length" style="display:flex;flex-wrap:wrap;gap:4px;padding-left:28px"><div v-for="sub in task.subTasks" :key="sub.id" class="subtask-chip" style="padding:4px 8px;font-size:12px"><span>☐ {{ sub.title }}</span><span v-if="sub.weekDay" class="mini-tag" style="margin-left:4px">{{ sub.weekDay === 'weekday' ? '平时' : '周末' }}</span></div></div></div></div></div>
        <div class="panel"><div class="card-title"><h2>错题复习提醒</h2><button class="btn ghost" @click="router.push('/mistake')">去复习</button></div><div class="kpi"><strong>{{ mistakeStore.records.length }} 题</strong><span>题库总计 · 随时查看复习</span></div></div>
        <div class="panel"><div class="card-title"><h2>空间收纳状态</h2><button class="btn ghost" @click="router.push('/tracker')">查看</button></div><div class="progress"><span :style="{ width: `${Math.min(100, progressPercent + 30)}%` }"></span></div><p class="lead">试卷归档随整理任务完成提升。</p></div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard.mature { --primary: #2e6f99; --primary-2: #92e3ff; }
.growth-tree { height: 190px; display: grid; place-items: center; border-radius: 28px; background: linear-gradient(180deg,#d9f5ff,#f6ffd8); font-size: 92px; margin-bottom: 16px; }
.focus-card { display: grid; grid-template-columns: auto 1fr auto; gap: 24px; align-items: center; padding: 30px; border-radius: 34px; background: linear-gradient(135deg,#fff,#fff4bc); border: 2px solid #fbe270; box-shadow: var(--shadow); }
.big-icon { font-size: 70px; }
.action-card { display: grid; gap: 14px; justify-items: start; }
.done { opacity: .72; }
.subtasks-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0 4px;
  border-top: 1px dashed var(--line);
  margin-top: 4px;
  width: 100%;
}
.subtask-label {
  font-size: 11px;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .5px;
  width: 100%;
}
.subtask-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: #f1f9ee;
  font-size: 13px;
  border: 1px solid #d4edc2;
}
.subtask-checkbox {
  font-size: 16px;
  color: #888;
}
button:disabled { cursor: not-allowed; opacity: .65; }
@media (max-width: 900px) { .focus-card { grid-template-columns: 1fr; } }
</style>
