<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGrowthStore, useMistakeStore, useUserStore } from '../../stores'

const growthStore = useGrowthStore()
const mistakeStore = useMistakeStore()
const userStore = useUserStore()
const period = ref('学期')
const reportReady = ref(false)
const latest = computed(() => growthStore.trendData[growthStore.trendData.length - 1])
const maxRate = computed(() => Math.max(...growthStore.trendData.map(d => d.taskCompletionRate), 0.01))

const spiderMetrics = computed(() => [
  { label: '专注', value: 76 },
  { label: '整洁', value: Math.max(35, 90 - growthStore.highFrequencyItems.length * 18) },
  { label: '元认知', value: 68 + Math.min(20, mistakeStore.records.length * 2) },
  { label: '情绪', value: 72 },
])
const maxSpider = 100

function generateReport() {
  reportReady.value = true
  const printWin = window.open('', '_blank')
  if (!printWin) return
  const name = userStore.profile.name || 'Leo'
  const grade = userStore.profile.grade || 3
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${name} 成长报告</title>
<style>body{font-family:'Noto Sans SC',sans-serif;padding:40px;font-size:15px;color:#1f241c;max-width:800px;margin:0 auto}
h1{font-size:24px;text-align:center;color:#106e00}h2{font-size:18px;color:#106e00;margin-top:24px}
.kpi-row{display:flex;gap:16px;margin:20px 0}.kpi{flex:1;padding:16px;border-radius:16px;background:#f6ffd7;text-align:center}
.kpi strong{display:block;font-size:28px;color:#106e00}.kpi span{font-size:13px;color:#6b735f}
p{line-height:1.8}.alert{padding:14px;border-radius:14px;background:#fff8d9;margin:8px 0;color:#6e5e00}
@media print{body{padding:20px}}</style></head><body>
<h1>🌿 ${name} 的执行功能综合发展报告</h1>
<p>年级：${grade}年级 ｜ 推荐Level：${userStore.assessment.recommendedLevel} ｜ 生成时间：${new Date().toLocaleDateString()}</p>
<div class="kpi-row">
<div class="kpi"><strong>${Math.round((latest?.taskCompletionRate || 0) * 100)}%</strong><span>任务完成率</span></div>
<div class="kpi"><strong>${Math.round((latest?.mistakeRate || 0) * 100)}%</strong><span>漏题率</span></div>
<div class="kpi"><strong>${latest?.itemLossRate || 0}</strong><span>月丢失频次</span></div>
</div>
<h2>智能诊断发现</h2>
${growthStore.alerts.map(a => `<div class="alert"><strong>${a.title}</strong><p>${a.description}</p><p>建议：${a.suggestion}</p></div>`).join('')}
<h2>同龄常模对比</h2>
<p>专注 76% ｜ 整洁 ${Math.max(35, 90 - growthStore.highFrequencyItems.length * 18)}% ｜ 元认知 ${68 + Math.min(20, mistakeStore.records.length * 2)}% ｜ 情绪 72%</p>
</body></html>`
  printWin.document.write(html)
  printWin.document.close()
  setTimeout(() => printWin.print(), 300)
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📈 6 年长期成长档案与预警中心</span>
        <h1>把粗心变化看成发展曲线</h1>
        <p class="lead">长期档案汇总任务完成率、错题类型、物品流失与家庭协作状态，只呈现可行动建议，不制造焦虑。</p>
      </div>
      <div class="panel">
        <div class="card-title"><h2>最新诊断发现</h2><span class="tag">近 7 天</span></div>
        <template v-if="growthStore.alerts.length">
          <div v-for="alert in growthStore.alerts" :key="alert.id" class="alert-card" :class="alert.severity">
            <strong>{{ alert.title }}</strong>
            <p>{{ alert.description }}</p>
            <p class="suggestion">💡 {{ alert.suggestion }}</p>
          </div>
        </template>
        <p v-else class="lead">暂无预警，继续保持！</p>
      </div>
    </section>

    <section class="grid-4">
      <div class="kpi"><strong>{{ Math.round((latest?.taskCompletionRate || 0) * 100) }}%</strong><span>任务完成率</span></div>
      <div class="kpi"><strong>{{ Math.round((latest?.mistakeRate || 0) * 100) }}%</strong><span>漏题率</span></div>
      <div class="kpi"><strong>{{ latest?.itemLossRate || 0 }}</strong><span>月丢失频次</span></div>
      <div class="kpi"><strong>{{ mistakeStore.records.length }}</strong><span>错题诊断数</span></div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>长期成长趋势</h2>
          <select v-model="period" class="input compact">
            <option>学年</option><option>学期</option><option>月度</option>
          </select>
        </div>
        <div class="chart">
          <div v-for="point in growthStore.trendData" :key="point.date" class="chart-col">
            <div class="chart-bar completion" :style="{ height: Math.round(point.taskCompletionRate / maxRate * 100) + '%' }"></div>
            <div class="chart-bar mistake" :style="{ height: Math.round(point.mistakeRate * 100) + '%' }"></div>
            <span class="chart-label">{{ point.date }}</span>
          </div>
        </div>
        <div class="chart-legend">
          <span class="legend-item"><span class="dot completion"></span>完成率</span>
          <span class="legend-item"><span class="dot mistake"></span>漏题率</span>
        </div>
      </div>
      <div class="panel">
        <div class="card-title"><h2>同龄常模对比</h2><span class="tag">蜘蛛网简化图</span></div>
        <div class="spider">
          <div v-for="metric in spiderMetrics" :key="metric.label" class="metric">
            <span class="metric-label">{{ metric.label }}</span>
            <div class="progress"><span :style="{ width: `${metric.value}%` }"></span></div>
            <b>{{ metric.value }}%</b>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="card-title"><h2>PDF 成长报告</h2><span class="tag">可分享/打印</span></div>
      <p class="lead">一键生成执行功能综合发展报告，可分享给老师或打印留存。</p>
      <button class="btn" @click="generateReport">📄 生成 PDF 成长报告</button>
      <p v-if="reportReady" class="note">报告已生成并打开打印窗口，可保存为PDF或直接打印。</p>
    </section>
  </div>
</template>

<style scoped>
.alert-card { padding: 16px; border-radius: 18px; margin-bottom: 10px; }
.alert-card.info { background: #eff6ff; border: 1px solid #93c5fd; }
.alert-card.warning { background: #fff8d9; border: 1px solid #fcd34d; }
.alert-card.positive { background: #ecfdf5; border: 1px solid #86efac; }
.suggestion { font-size: 14px; color: var(--primary); font-weight: 700; margin-top: 4px; }
.chart { height: 260px; display: flex; align-items: flex-end; gap: 12px; padding: 18px; border-radius: 26px; background: #fff; border: 1px solid var(--line); }
.chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; height: 100%; justify-content: flex-end; position: relative; }
.chart-bar { width: 70%; border-radius: 8px 8px 3px 3px; min-height: 4px; transition: height .4s ease; }
.chart-bar.completion { background: linear-gradient(180deg, var(--primary-2), var(--primary)); }
.chart-bar.mistake { background: linear-gradient(180deg, #fca5a5, #f87171); width: 50%; }
.chart-label { position: absolute; bottom: -24px; font-size: 11px; color: var(--muted); white-space: nowrap; font-weight: 700; }
.chart-legend { display: flex; gap: 16px; margin-top: 32px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: var(--muted); }
.dot { width: 10px; height: 10px; border-radius: 999px; }
.dot.completion { background: var(--primary); }
.dot.mistake { background: #f87171; }
.compact { width: auto; }
.spider { display: grid; gap: 16px; }
.metric { display: grid; grid-template-columns: 70px 1fr 52px; gap: 10px; align-items: center; }
.metric-label { font-size: 13px; font-weight: 800; }
.note { padding: 14px; border-radius: 18px; background: #ecfdf5; color: #059669; margin-top: 12px; }
</style>
