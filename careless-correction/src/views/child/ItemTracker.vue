<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGrowthStore, useUserStore } from '../../stores'

const growthStore = useGrowthStore()
const userStore = useUserStore()
const itemName = ref('橡皮')
const lostLocation = ref('教室抽屉')
const estimatedCost = ref(3)
const beforeName = ref('')
const afterName = ref('')
const totalFrequency = computed(() => growthStore.itemLossRecords.reduce((sum, item) => sum + item.frequency, 0))

function reportLoss() {
  growthStore.addItemLossRecord({ itemName: itemName.value, lostLocation: lostLocation.value, estimatedCost: estimatedCost.value })
}
function handlePhoto(event: Event, target: 'before' | 'after') {
  const name = (event.target as HTMLInputElement).files?.[0]?.name || ''
  if (target === 'before') beforeName.value = name
  else {
    afterName.value = name
    if (beforeName.value) userStore.addSunlightPoints(10)
  }
}
</script>

<template>
  <div class="page">
    <section class="page-hero"><div class="hero-card"><span class="eyebrow">🎒 物品流失追踪与收纳实验室</span><h1>让丢东西变成可观察的收纳实验</h1><p class="lead">记录物品、地点、频次和成本；当 30 天内同一物品丢失满 3 次，会触发急救建议。</p></div><div class="panel"><div class="card-title"><h2>本月流失成本</h2><span class="tag">{{ totalFrequency }} 次</span></div><div class="kpi"><strong>¥{{ growthStore.totalLossCost }}</strong><span>累计账单会随上报自动更新</span></div></div></section>
    <section class="grid-3"><div class="soft-card"><div class="icon-tile">📍</div><h2>高发地点雷达</h2><div class="radar"><span v-for="item in growthStore.itemLossRecords" :key="item.id">{{ item.lostLocation }} · {{ item.frequency }}</span></div></div><div class="soft-card"><div class="icon-tile">🧺</div><h2>虚拟书包三分区</h2><div class="bag"><span>作业区</span><span>文具区</span><span>回执区</span></div></div><div class="soft-card"><div class="icon-tile">🚑</div><h2>高频流失急救</h2><template v-if="growthStore.highFrequencyItems.length"><p v-for="item in growthStore.highFrequencyItems" :key="item.id" class="alert">{{ item.itemName }} 30 天内 {{ item.frequency }} 次：贴荧光姓名贴，用完放回笔盒右侧。</p></template><p v-else class="lead">暂未触发高频流失。</p></div></section>
    <section class="grid-2"><div class="panel"><div class="card-title"><h2>新增丢失记录</h2><button class="btn" @click="reportLoss">上报</button></div><div class="grid-3"><input v-model="itemName" class="input" placeholder="物品"/><input v-model="lostLocation" class="input" placeholder="地点"/><input v-model.number="estimatedCost" class="input" type="number" min="0"/></div><div class="list"><div v-for="row in growthStore.itemLossRecords" :key="row.id" class="list-row"><span>{{ row.itemName }}｜{{ row.lostLocation }}｜第{{ row.frequency }}次</span><span>¥{{ row.estimatedCost * row.frequency }}</span></div></div></div><div class="panel"><div class="card-title"><h2>收纳前后对比</h2><span class="tag">上传后 +10 阳光</span></div><div class="compare"><label>Before<input type="file" accept="image/*" @change="handlePhoto($event, 'before')"/><span>{{ beforeName || '上传凌乱桌面' }}</span></label><label>After<input type="file" accept="image/*" @change="handlePhoto($event, 'after')"/><span>{{ afterName || '上传整理后桌面' }}</span></label></div></div></section>
  </div>
</template>
<style scoped>.radar,.bag{display:grid;gap:10px}.radar span,.bag span{padding:12px;border-radius:16px;background:#fff;border:1px solid var(--line);font-weight:800}.alert{padding:12px;border-radius:18px;background:#ffdad6;color:#93000a;animation:pulse 1.5s infinite}.compare{display:grid;grid-template-columns:1fr 1fr;gap:12px}.compare label{min-height:180px;border:2px dashed var(--line);border-radius:22px;display:grid;place-items:center;text-align:center;font-weight:900}.compare input{display:none}@keyframes pulse{50%{box-shadow:0 0 0 8px rgba(255,0,0,.08)}}@media(max-width:900px){.compare{grid-template-columns:1fr}}</style>
