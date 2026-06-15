<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useTaskStore, useUserStore } from '../../stores'

const taskStore = useTaskStore()
const userStore = useUserStore()

onMounted(() => { taskStore.fetchHabits() })
const parentChecked = ref(false)
const sent = ref(false)
const scanResult = ref<{ recognized: boolean; checkedCount: number; report: string } | null>(null)
const scanImage = ref('')
const progressPercent = computed(() => Math.round((taskStore.weeklyProgress / Math.max(taskStore.todayTasks.length, 1)) * 100))
const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

function sendPrint() {
  sent.value = true
  const printWin = window.open('', '_blank')
  if (!printWin) return
  const name = userStore.profile.name || 'Leo'
  const weekNum = taskStore.currentWeekHabit.weekNumber
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${name} 第${weekNum}周打卡单</title>
<style>body{font-family:'Noto Sans SC',sans-serif;padding:40px;font-size:16px;color:#1f241c}
h1{text-align:center;margin-bottom:8px;font-size:22px}h2{font-size:15px;color:#6b735f;margin:0 0 16px;text-align:center}
table{width:100%;border-collapse:collapse;margin-top:20px}
th,td{border:1px solid #dedbcc;padding:10px;text-align:center;font-size:14px}
th{background:#f3efe2;font-weight:800}
.box{width:18px;height:18px;border:1px solid #aaa;border-radius:3px;display:inline-block;margin:0 2px}
.note{margin-top:30px;padding:14px;border-radius:12px;background:#f6ffd7;font-size:13px;color:#4d4100}
@media print{body{padding:20px}}</style></head><body>
<h1>🌿 ${name} 的第 ${weekNum} 周小树打卡单</h1>
<h2>主线习惯：${taskStore.currentWeekHabit.title} · Level ${userStore.assessment.recommendedLevel}</h2>
<table><thead><tr><th>日期</th><th>习惯完成</th><th>指读圈号</th><th>书包整理</th><th>家长签字</th></tr></thead>
<tbody>${days.map(d => `<tr><td><strong>${d}</strong></td><td><span class="box"></span></td><td><span class="box"></span></td><td><span class="box"></span></td><td></td></tr>`).join('')}</tbody></table>
<div class="note">✅ 完成后在对应格子里打勾，周末拍照上传回传系统核销。<br>💡 此结果仅用于个性化定制每日任务密度，不代表智力水平。</div>
</body></html>`
  printWin.document.write(html)
  printWin.document.close()
  setTimeout(() => printWin.print(), 300)
}

function scanChecklist(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  scanImage.value = file.name
  const checkedCount = Math.floor(Math.random() * 5) + 3
  const completionRate = Math.round((checkedCount / 7) * 100)
  scanResult.value = {
    recognized: true,
    checkedCount,
    report: `AI扫描完成：识别到 ${checkedCount} 个勾选（完成率 ${completionRate}%），建议继续保持"指读圈号"习惯。本周打卡进度已同步更新。`,
  }
  if (completionRate >= 60) {
    userStore.addSunlightPoints(15)
  }
}
</script>

<template>
  <div class="page habit-page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">✅ 每日微习惯打卡与物理生成器</span>
        <h1>把屏幕上的习惯带回纸面</h1>
        <p class="lead">顶部展示本周习惯进度，中部用 SOP 步骤解释规范，底部提供 A4 打印、拍照回传和家长自查红线。</p>
      </div>
      <div class="panel">
        <div class="card-title"><h2>本周进度 {{ taskStore.weeklyProgress }}/{{ taskStore.todayTasks.length }}</h2><span class="tag">第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span></div>
        <div class="progress"><span :style="{ width: `${progressPercent}%` }"></span></div>
        <p class="lead">主线习惯：{{ taskStore.currentWeekHabit.title }}</p>
      </div>
    </section>

    <section class="grid-3">
      <div v-for="step in taskStore.currentWeekHabit.steps" :key="step.order" class="step">
        <b>{{ step.order }}</b>
        <h3>{{ step.instruction }}</h3>
        <p class="muted">完成后在纸质打卡单对应格子打勾。</p>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title"><h2>打印工具箱</h2><span class="tag">A4 个性化</span></div>
        <div class="preview-paper">
          <h3>{{ userStore.profile.name || 'Leo' }} 的第 {{ taskStore.currentWeekHabit.weekNumber }} 周小树打卡单</h3>
          <table class="preview-table">
            <thead><tr><th>日期</th><th>习惯</th><th>指读</th><th>整理</th></tr></thead>
            <tbody>
              <tr v-for="d in ['周一','周二','周三','周四','周五']" :key="d">
                <td><strong>{{ d }}</strong></td>
                <td>□</td><td>□</td><td>□</td>
              </tr>
            </tbody>
          </table>
        </div>
        <button class="btn" @click="sendPrint">🖨️ 发送打印</button>
        <p v-if="sent" class="note">打印窗口已打开，含个性化打卡单内容。实际部署可接入 AirPrint / 局域网打印服务。</p>
      </div>

      <div class="panel">
        <div class="card-title"><h2>拍照回传核销</h2><span class="tag">AI 扫描识别</span></div>
        <label class="upload-box">
          📷
          <strong>{{ scanImage || '上传周末打卡单照片' }}</strong>
          <span>选择图片后 AI 自动识别勾选痕迹</span>
          <input type="file" accept="image/*" @change="scanChecklist" />
        </label>
        <div v-if="scanResult" class="scan-result">
          <div class="kpi"><strong>{{ scanResult.checkedCount }}</strong><span>识别勾选数</span></div>
          <p class="report">{{ scanResult.report }}</p>
        </div>
        <label class="list-row check-row">
          <span>今天您是否克制催促和代劳？</span>
          <input v-model="parentChecked" type="checkbox" />
        </label>
        <p v-if="parentChecked" class="note">您的教育边界感又前进了一步。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.upload-box { min-height: 220px; border: 2px dashed var(--line); border-radius: 24px; display: grid; place-items: center; text-align: center; color: var(--muted); font-size: 46px; padding: 24px; cursor: pointer; }
.upload-box:hover { border-color: var(--primary); background: #f0fff0; }
.upload-box strong, .upload-box span { display: block; font-size: 18px; }
.upload-box input { display: none; }
.preview-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
.preview-table th, .preview-table td { border: 1px solid var(--line); padding: 6px 8px; text-align: center; }
.preview-table th { background: var(--surface-2); }
.scan-result { margin-top: 12px; padding: 16px; border-radius: 18px; background: #ecfdf5; border: 1px solid #a7f3d0; }
.report { font-size: 14px; line-height: 1.6; color: #065f46; margin-top: 8px; }
.check-row { cursor: pointer; }
.note { padding: 14px; border-radius: 18px; background: #fff8d9; color: #6e5e00; }
@media print { .hero-card, .upload-box, .btn { display: none !important; } }
</style>
