<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGrowthStore, useMistakeStore } from '../../stores'

const growthStore = useGrowthStore()
const mistakeStore = useMistakeStore()
const period = ref('学年')
const reportReady = ref(false)
const latest = computed(() => growthStore.trendData[growthStore.trendData.length - 1])
const spiderMetrics = computed(() => [
  { label: '专注', value: 76 },
  { label: '整洁', value: Math.max(35, 90 - growthStore.highFrequencyItems.length * 18) },
  { label: '元认知', value: 68 + Math.min(20, mistakeStore.records.length * 2) },
  { label: '情绪', value: 72 },
])
</script>

<template>
  <div class="page">
    <section class="page-hero"><div class="hero-card"><span class="eyebrow">📈 6 年长期成长档案与预警中心</span><h1>把粗心变化看成发展曲线</h1><p class="lead">长期档案汇总任务完成率、错题类型、物品流失与家庭协作状态，只呈现可行动建议，不制造焦虑。</p></div><div class="panel"><div class="card-title"><h2>{{ growthStore.alerts[0]?.title }}</h2><span class="tag">近 7 天</span></div><p class="lead">{{ growthStore.alerts[0]?.description }} {{ growthStore.alerts[0]?.suggestion }}</p><button class="btn secondary" @click="reportReady = true">生成 PDF 成长报告</button><p v-if="reportReady" class="note">报告已生成：可打印或分享给老师。</p></div></section>
    <section class="grid-4"><div class="kpi"><strong>{{ Math.round((latest?.taskCompletionRate || 0) * 100) }}%</strong><span>任务完成率</span></div><div class="kpi"><strong>{{ Math.round((latest?.mistakeRate || 0) * 100) }}%</strong><span>漏题率</span></div><div class="kpi"><strong>{{ latest?.itemLossRate || 0 }}</strong><span>月丢失频次</span></div><div class="kpi"><strong>{{ mistakeStore.records.length }}</strong><span>错题诊断数</span></div></section>
    <section class="grid-2"><div class="panel"><div class="card-title"><h2>长期成长趋势</h2><select v-model="period" class="input compact"><option>学年</option><option>学期</option><option>月度</option></select></div><div class="chart"><span v-for="point in growthStore.trendData" :key="point.date" :style="{ height: `${Math.round(point.taskCompletionRate * 100)}%` }"><b>{{ point.date }}</b></span></div></div><div class="panel"><div class="card-title"><h2>同龄常模对比</h2><span class="tag">蜘蛛网简化图</span></div><div class="spider"><div v-for="metric in spiderMetrics" :key="metric.label" class="metric"><span>{{ metric.label }}</span><div class="progress"><span :style="{ width: `${metric.value}%` }"></span></div><b>{{ metric.value }}%</b></div></div></div></section>
  </div>
</template>
<style scoped>.chart{height:260px;display:flex;align-items:end;gap:14px;padding:18px;border-radius:26px;background:#fff;border:1px solid var(--line)}.chart span{flex:1;border-radius:999px 999px 12px 12px;background:linear-gradient(180deg,var(--primary-2),var(--primary));position:relative;min-height:36px}.chart b{position:absolute;bottom:-28px;left:50%;transform:translateX(-50%);white-space:nowrap;color:var(--muted)}.compact{width:auto}.spider{display:grid;gap:16px}.metric{display:grid;grid-template-columns:70px 1fr 52px;gap:10px;align-items:center}.note{padding:14px;border-radius:18px;background:#fff8d9;color:#6e5e00}</style>
