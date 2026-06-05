<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTaskStore, useUserStore } from '../../stores'

const taskStore = useTaskStore()
const userStore = useUserStore()
const parentChecked = ref(false)
const sent = ref(false)
const scanResult = ref('')
const progressPercent = computed(() => Math.round((taskStore.weeklyProgress / Math.max(taskStore.todayTasks.length, 1)) * 100))

function sendPrint() {
  sent.value = true
  window.setTimeout(() => window.print(), 150)
}

function scanChecklist(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  scanResult.value = `已识别 ${input.files[0].name}：5 个勾选，建议继续保持“指读圈号”。`
}
</script>

<template>
  <div class="page habit-page">
    <section class="page-hero">
      <div class="hero-card"><span class="eyebrow">✅ 每日微习惯打卡与物理生成器</span><h1>把屏幕上的习惯带回纸面</h1><p class="lead">顶部展示本周习惯进度，中部用 SOP 步骤解释规范，底部提供 A4 打印、拍照回传和家长自查红线。</p></div>
      <div class="panel"><div class="card-title"><h2>本周进度 {{ taskStore.weeklyProgress }}/{{ taskStore.todayTasks.length }}</h2><span class="tag">第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span></div><div class="progress"><span :style="{ width: `${progressPercent}%` }"></span></div><p class="lead">主线习惯：{{ taskStore.currentWeekHabit.title }}</p></div>
    </section>
    <section class="grid-3">
      <div v-for="step in taskStore.currentWeekHabit.steps" :key="step.order" class="step"><b>{{ step.order }}</b><h3>{{ step.instruction }}</h3><p class="muted">完成后在纸质打卡单对应格子打勾。</p></div>
    </section>
    <section class="grid-2">
      <div class="panel"><div class="card-title"><h2>打印工具箱</h2><span class="tag">A4 预览</span></div><div class="preview-paper"><h3>{{ userStore.profile.name }} 的本周小树打卡单</h3><div class="list"><div v-for="day in ['周一','周二','周三','周四','周五']" :key="day" class="list-row"><span>{{ day }} 指读圈号</span><span>□ □ □</span></div></div></div><button class="btn" @click="sendPrint">发送打印</button><p v-if="sent" class="lead">已打开浏览器打印；实际部署可接入 AirPrint / 局域网打印服务。</p></div>
      <div class="panel"><div class="card-title"><h2>拍照回传核销</h2><span class="tag">本地模拟 AI 扫描</span></div><label class="upload-box">📷<strong>上传周末打卡单照片</strong><span>选择图片后生成识别结果</span><input type="file" accept="image/*" @change="scanChecklist" /></label><p v-if="scanResult" class="note">{{ scanResult }}</p><label class="list-row"><span>今天您是否克制催促和代劳？</span><input v-model="parentChecked" type="checkbox" /></label><p v-if="parentChecked" class="note">您的教育边界感又前进了一步。</p></div>
    </section>
  </div>
</template>

<style scoped>
.upload-box{min-height:220px;border:2px dashed var(--line);border-radius:24px;display:grid;place-items:center;text-align:center;color:var(--muted);font-size:46px;padding:24px;cursor:pointer}.upload-box strong,.upload-box span{display:block;font-size:18px}.upload-box input{display:none}.note{padding:14px;border-radius:18px;background:#fff8d9;color:#6e5e00}
@media print { .hero-card, .upload-box, .btn { display: none !important; } }
</style>
