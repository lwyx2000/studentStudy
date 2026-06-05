<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { usePomodoroStore } from '../../stores'

const pomodoroStore = usePomodoroStore()
const subject = ref('数学')
const estimate = ref(30)
const actual = ref(45)
const reason = ref('')
let timer: number | undefined
const remainingText = computed(() => {
  const minutes = Math.floor(pomodoroStore.remainingSeconds / 60).toString().padStart(2, '0')
  const seconds = (pomodoroStore.remainingSeconds % 60).toString().padStart(2, '0')
  return `${minutes}:${seconds}`
})
const diff = computed(() => actual.value - estimate.value)

watch(() => pomodoroStore.isRunning, running => {
  if (running && !timer) timer = window.setInterval(() => pomodoroStore.tick(), 1000)
  if (!running && timer) {
    window.clearInterval(timer)
    timer = undefined
  }
})
onBeforeUnmount(() => timer && window.clearInterval(timer))

function startOrPause() {
  if (!pomodoroStore.activeSessionId) pomodoroStore.startSession(estimate.value, subject.value)
  else if (pomodoroStore.isRunning) pomodoroStore.pauseSession()
  else pomodoroStore.isRunning = true
}
function finish() {
  pomodoroStore.finishSession(actual.value, reason.value)
}
</script>

<template>
  <div class="page time-cabin">
    <section class="page-hero"><div class="hero-card dark-panel"><span class="eyebrow">⏱️ 5-6 年级专属自治舱</span><h1>预估、执行、标记不确定</h1><p class="lead">冷静高信息密度界面，让高年级孩子练习考前复习规划和元认知复盘。</p></div><div class="panel dark-panel"><div class="card-title"><h2>番茄钟</h2><span class="tag">{{ remainingText }}</span></div><div class="timer">{{ remainingText }}</div><button class="btn secondary" @click="startOrPause">{{ !pomodoroStore.activeSessionId ? '启动' : pomodoroStore.isRunning ? '暂停' : '继续' }}</button><button class="btn ghost" :disabled="!pomodoroStore.activeSessionId" @click="pomodoroStore.markUncertain()">我有疑问 ?</button></div></section>
    <section class="grid-3"><div class="panel dark-panel"><div class="card-title"><h2>复习时间流</h2><span class="tag">Calendar</span></div><div class="timeline"><div class="timeline-row"><b>周一</b><div class="timeline-bar"></div></div><div class="timeline-row"><b>周三</b><div class="timeline-bar" style="width:75%"></div></div><div class="timeline-row"><b>周五</b><div class="timeline-bar" style="width:60%"></div></div></div></div><div class="panel dark-panel"><div class="card-title"><h2>预估 vs 实际</h2><span class="tag">{{ diff >= 0 ? '+' : '' }}{{ diff }} 分钟</span></div><label>科目<select v-model="subject" class="input"><option>数学</option><option>语文</option><option>英语</option></select></label><label>预估用时<input v-model.number="estimate" class="input" type="number" /></label><label>实际用时<input v-model.number="actual" class="input" type="number" /></label><p class="lead">这道题比你预估{{ diff >= 0 ? '多' : '少' }}花 {{ Math.abs(diff) }} 分钟，主要花在哪个环节？</p><div class="stepper"><button class="btn ghost" @click="reason='reading'">读题</button><button class="btn ghost" @click="reason='calculation'">验算</button><button class="btn ghost" @click="reason='daydreaming'">神游</button></div><button class="btn secondary" :disabled="!pomodoroStore.activeSessionId" @click="finish">我写完了</button></div><div class="panel dark-panel"><div class="card-title"><h2>疑问题目标记</h2><span class="tag">{{ pomodoroStore.uncertainCount }} 个 ?</span></div><div class="kpi"><strong>{{ pomodoroStore.uncertainCount }}</strong><span>已同步到本次番茄钟，完成后可转入错题本</span></div><div class="list"><div v-for="session in pomodoroStore.sessions.slice(0,3)" :key="session.id" class="list-row"><span>{{ session.subject }} · 预估{{ session.estimatedMinutes }}分</span><span>{{ session.actualMinutes || '进行中' }}</span></div></div></div></section>
  </div>
</template>
<style scoped>.time-cabin{background:#101827;margin:-28px;padding:28px;min-height:calc(100vh - 76px);border-radius:0}.timer{font-size:64px;font-weight:950;text-align:center;margin:18px 0;color:#fff}.dark-panel .input{margin:8px 0 14px;background:#22324b;color:#fff;border-color:rgba(255,255,255,.18)}button:disabled{opacity:.5;cursor:not-allowed}</style>
