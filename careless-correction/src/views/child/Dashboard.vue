<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMistakeStore, useTaskStore, useUserStore } from '../../stores'

const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()
const mistakeStore = useMistakeStore()
const isHighGrade = computed(() => userStore.profile.grade >= 5)
const mainTask = computed(() => taskStore.todayTasks.find(task => task.type === 'habit') || taskStore.todayTasks[0])
const progressPercent = computed(() => Math.round((taskStore.weeklyProgress / Math.max(taskStore.todayTasks.length, 1)) * 100))

function completeTask(id: string) {
  const points = taskStore.completeTask(id)
  if (points) userStore.addSunlightPoints(points)
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
      </section>
      <section class="grid-2">
        <div v-for="task in taskStore.todayTasks.filter(item => item.id !== mainTask?.id)" :key="task.id" class="soft-card action-card" :class="{ done: task.status === 'completed' }">
          <div class="icon-tile">{{ task.icon }}</div>
          <h2>{{ task.title }}</h2>
          <p class="muted">{{ task.description }}</p>
          <button class="btn ghost" :disabled="task.status === 'completed'" @click="completeTask(task.id)">{{ task.status === 'completed' ? '已完成' : '去完成' }}</button>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="grid-2">
        <div class="panel dark-panel">
          <div class="card-title"><h2>今日时间轴</h2><button class="btn secondary" @click="router.push('/time-task')">打开番茄钟</button></div>
          <div class="timeline"><div class="timeline-row"><b>17:00</b><div class="timeline-bar"></div></div><div class="timeline-row"><b>18:20</b><div class="timeline-bar" style="width:80%"></div></div><div class="timeline-row"><b>20:00</b><div class="timeline-bar" style="width:55%"></div></div></div>
        </div>
        <div class="panel"><div class="card-title"><h2>今日任务优先级</h2><span class="tag">{{ taskStore.todayTasks.length }} 项</span></div><div class="list"><div v-for="task in taskStore.todayTasks" :key="task.id" class="list-row"><span>{{ task.icon }} {{ task.title }}</span><button class="btn ghost" :disabled="task.status === 'completed'" @click="completeTask(task.id)">{{ task.status === 'completed' ? '完成' : '完成' }}</button></div></div></div>
        <div class="panel"><div class="card-title"><h2>错题复习提醒</h2><button class="btn ghost" @click="router.push('/mistake')">去复习</button></div><div class="kpi"><strong>{{ mistakeStore.todayReviewCount }} 题</strong><span>今日待复习 · {{ Object.keys(mistakeStore.categoryStats).length }} 类错误</span></div></div>
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
button:disabled { cursor: not-allowed; opacity: .65; }
@media (max-width: 900px) { .focus-card { grid-template-columns: 1fr; } }
</style>
