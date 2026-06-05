<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'


const timerMinutes = ref(25)
const timerSeconds = ref(0)
const isRunning = ref(false)
let timerInterval: ReturnType<typeof setInterval> | null = null

const selectedDrainReason = ref<string | null>(null)
const uncertainCount = ref(0)

const drainReasons = ['读题耗时', '验算耗时', '发呆神游了']

const totalSeconds = computed(() => timerMinutes.value * 60 + timerSeconds.value)
const progressPercent = computed(() => {
  const elapsed = 25 * 60 - totalSeconds.value
  return Math.min(100, (elapsed / (25 * 60)) * 100)
})

const timelineItems = [
  { date: '6月5日', title: '数学复习', type: 'exam' },
  { date: '6月8日', title: '科学测验', type: 'quiz' },
  { date: '6月12日', title: '英语期考', type: 'exam' },
]

const subjectEstimations = [
  { subject: '数学', estimated: 30, actual: 45 },
  { subject: '历史', estimated: 20, actual: 18 },
]

function startTimer() {
  isRunning.value = true
  timerMinutes.value = 25
  timerSeconds.value = 0
  timerInterval = setInterval(() => {
    if (timerSeconds.value === 0) {
      if (timerMinutes.value === 0) {
        stopTimer()
        return
      }
      timerMinutes.value--
      timerSeconds.value = 59
    } else {
      timerSeconds.value--
    }
  }, 1000)
}

function stopTimer() {
  isRunning.value = false
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = null
}

function markUncertain() {
  uncertainCount.value++
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<template>
  <div class="time-task-cabin">
    <Title size="large" color="app-blue">时间与学习自治舱</Title>
    <p class="cabin-subtitle">5-6年级专属 - 像大人一样管理自己的生活</p>

    <div class="cabin-grid">
      <Card color="app-teal" type="title" class="timeline-card">
        <template #title>
          <Title size="middle" color="app-teal">考前复习时间流</Title>
        </template>
        <div class="timeline">
          <div v-for="item in timelineItems" :key="item.date" class="timeline-item">
            <div class="timeline-date">{{ item.date }}</div>
            <div class="timeline-task" :class="item.type">{{ item.title }}</div>
          </div>
        </div>
      </Card>

      <Card color="app-green" type="title" class="pomodoro-card">
        <template #title>
          <Title size="middle" color="app-green">番茄工作法</Title>
        </template>
        <div class="pomodoro-content">
          <div class="timer-ring">
            <svg viewBox="0 0 200 200" class="timer-svg">
              <circle cx="100" cy="100" r="90" fill="none" stroke="#e4e3d8" stroke-width="8" />
              <circle
                cx="100" cy="100" r="90" fill="none" stroke="#106e00" stroke-width="8"
                :stroke-dasharray="2 * Math.PI * 90"
                :stroke-dashoffset="2 * Math.PI * 90 * (1 - progressPercent / 100)"
                stroke-linecap="round"
                transform="rotate(-90 100 100)"
              />
            </svg>
            <div class="timer-display">
              <span class="timer-minutes">{{ String(timerMinutes).padStart(2, '0') }}</span>
              <span class="timer-colon">:</span>
              <span class="timer-seconds">{{ String(timerSeconds).padStart(2, '0') }}</span>
            </div>
          </div>
          <div class="timer-actions">
            <Button type="primary" @click="startTimer" v-if="!isRunning">启动专注</Button>
            <Button type="dashed" danger @click="stopTimer" v-if="isRunning">暂停</Button>
            <Button type="dashed" @click="markUncertain">
              < name="icon-chat" /> 我有疑问
            </Button>
          </div>
          <div v-if="uncertainCount > 0" class="uncertain-badge">
            已标记 {{ uncertainCount }} 个不确定题目
          </div>
        </div>
      </Card>

      <Card color="app-orange" type="title" class="estimation-card">
        <template #title>
          <Title size="middle" color="app-orange">时间预估 vs 实际</Title>
        </template>
        <div class="estimation-content">
          <div v-for="subj in subjectEstimations" :key="subj.subject" class="subject-bar">
            <div class="subject-name">{{ subj.subject }}</div>
            <div class="bar-group">
              <div class="bar estimated" :style="{ width: subj.estimated * 2 + 'px' }">
                预估 {{ subj.estimated }}分钟
              </div>
              <div class="bar actual" :style="{ width: subj.actual * 2 + 'px' }">
                实际 {{ subj.actual }}分钟
              </div>
            </div>
          </div>

          <Card color="app-yellow" type="dashed">
            <div class="drain-question">
              <p>多花了15分钟，主要花在了哪个环节?</p>
              <div class="drain-options">
                <Button
                  v-for="reason in drainReasons"
                  :key="reason"
                  :type="selectedDrainReason === reason ? 'primary' : 'default'"
                  size="small"
                  @click="selectedDrainReason = reason"
                >
                  {{ reason }}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.time-task-cabin {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #f0f0f5;
  min-height: 100vh;
  padding: 0;
}

.cabin-subtitle {
  color: #725d42;
  font-size: 14px;
}

.cabin-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-date {
  width: 60px;
  padding: 6px;
  background: #106e00;
  color: white;
  border-radius: 20px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
}

.timeline-task {
  padding: 8px 12px;
  background: #f7f3df;
  border-radius: 12px;
  font-weight: 500;
}

.timeline-task.exam {
  border-left: 3px solid #fc736d;
}

.timeline-task.quiz {
  border-left: 3px solid #82d5bb;
}

.pomodoro-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.timer-ring {
  position: relative;
  width: 180px;
  height: 180px;
}

.timer-svg {
  width: 100%;
  height: 100%;
}

.timer-display {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  font-size: 32px;
  font-weight: 700;
  color: #106e00;
}

.timer-colon {
  margin: 0 2px;
}

.timer-actions {
  display: flex;
  gap: 8px;
}

.uncertain-badge {
  padding: 6px 12px;
  background: #fbe270;
  border-radius: 12px;
  font-weight: 600;
  color: #6e5e00;
}

.estimation-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.subject-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.subject-name {
  width: 40px;
  font-weight: 600;
}

.bar-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.bar {
  height: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  padding-left: 8px;
  font-size: 12px;
  font-weight: 600;
}

.bar.estimated {
  background: #82d5bb;
  color: white;
}

.bar.actual {
  background: #889df0;
  color: white;
}

.drain-question {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drain-options {
  display: flex;
  gap: 8px;
}
</style>