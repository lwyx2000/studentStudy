<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGrowthStore, useUserStore } from '../../stores'

const growthStore = useGrowthStore()
const userStore = useUserStore()
const itemName = ref('橡皮')
const lostLocation = ref('教室')
const estimatedCost = ref(3)
const beforeName = ref('')
const afterName = ref('')
const beforeUrl = ref('')
const afterUrl = ref('')

const locationLabels: Record<string, string> = { school: '学校', bus: '公交', home: '家里', playground: '操场', other: '其他' }
const locationColors: Record<string, string> = { school: '#f87171', bus: '#60a5fa', home: '#34d399', playground: '#fbbf24', other: '#c4b5fd' }

const totalFrequency = computed(() => growthStore.itemLossRecords.reduce((sum, item) => sum + item.frequency, 0))
const locationStats = computed(() => {
  const map: Record<string, number> = {}
  for (const r of growthStore.itemLossRecords) {
    map[r.lostLocation] = (map[r.lostLocation] || 0) + r.frequency
  }
  return Object.entries(map).map(([loc, count]) => ({ location: locationLabels[loc] || loc, count, color: locationColors[loc] || '#c4b5fd' }))
})
const maxLocCount = computed(() => Math.max(...locationStats.value.map(d => d.count), 1))

const monthlyCostData = computed(() => {
  const map: Record<string, number> = {}
  for (const r of growthStore.itemLossRecords) {
    const month = r.lostDate ? r.lostDate.slice(0, 7) : '未知'
    map[month] = (map[month] || 0) + r.estimatedCost * r.frequency
  }
  return Object.entries(map).map(([month, cost]) => ({ month, cost }))
})
const maxMonthlyCost = computed(() => Math.max(...monthlyCostData.value.map(d => d.cost), 1))

function reportLoss() {
  growthStore.addItemLossRecord({ itemName: itemName.value, lostLocation: lostLocation.value, estimatedCost: estimatedCost.value })
  itemName.value = '橡皮'
  lostLocation.value = '教室'
  estimatedCost.value = 3
}

function handlePhoto(event: Event, target: 'before' | 'after') {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const url = URL.createObjectURL(file)
  if (target === 'before') { beforeName.value = file.name; beforeUrl.value = url }
  else {
    afterName.value = file.name; afterUrl.value = url
    if (beforeName.value) userStore.addSunlightPoints(10)
  }
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🎒 物品流失追踪与收纳实验室</span>
        <h1>让丢东西变成可观察的收纳实验</h1>
        <p class="lead">记录物品、地点、频次和成本；当 30 天内同一物品丢失满 3 次，会触发急救建议。</p>
      </div>
      <div class="panel">
        <div class="card-title"><h2>本月流失成本</h2><span class="tag">{{ totalFrequency }} 次</span></div>
        <div class="kpi"><strong>¥{{ growthStore.totalLossCost }}</strong><span>累计账单随上报自动更新</span></div>
      </div>
    </section>

    <section class="grid-3">
      <div class="soft-card">
        <div class="icon-tile">📍</div>
        <h2>高发地点雷达</h2>
        <div class="bar-chart">
          <div v-for="d in locationStats" :key="d.location" class="bar-row">
            <span class="bar-label">{{ d.location }}</span>
            <div class="bar-track"><div class="bar-fill" :style="{ width: (d.count / maxLocCount * 100) + '%', background: d.color }"></div></div>
            <span class="bar-val">{{ d.count }}</span>
          </div>
        </div>
      </div>
      <div class="soft-card">
        <div class="icon-tile">💰</div>
        <h2>累计账单折线图</h2>
        <div class="cost-chart">
          <div v-for="d in monthlyCostData" :key="d.month" class="cost-bar">
            <div class="cost-fill" :style="{ height: Math.max(8, d.cost / maxMonthlyCost * 100) + '%' }"></div>
            <span class="cost-label">{{ d.month.slice(5) }}</span>
            <span class="cost-val">¥{{ d.cost }}</span>
          </div>
        </div>
      </div>
      <div class="soft-card">
        <div class="icon-tile">🚑</div>
        <h2>高频流失急救</h2>
        <template v-if="growthStore.highFrequencyItems.length">
          <div v-for="item in growthStore.highFrequencyItems" :key="item.id" class="alert-card">
            <span class="alert-icon">🚨</span>
            <div>
              <strong>{{ item.itemName }}</strong> 30 天内丢失 {{ item.frequency }} 次
              <p class="alert-tip">贴荧光姓名贴，用完必须放回笔盒右侧。</p>
            </div>
          </div>
        </template>
        <p v-else class="lead">暂未触发高频流失（30天内≥3次）。</p>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title"><h2>新增丢失记录</h2><button class="btn" @click="reportLoss">上报</button></div>
        <div class="grid-3">
          <input v-model="itemName" class="input" placeholder="物品名称" />
          <select v-model="lostLocation" class="input">
            <option value="school">学校</option>
            <option value="bus">公交</option>
            <option value="home">家里</option>
            <option value="playground">操场</option>
            <option value="other">其他</option>
          </select>
          <input v-model.number="estimatedCost" class="input" type="number" min="0" placeholder="估计金额" />
        </div>
        <div class="list">
          <div v-for="row in growthStore.itemLossRecords" :key="row.id" class="list-row" :class="{ 'high-freq': row.frequency >= 3 }">
            <span>{{ row.itemName }} ｜ {{ locationLabels[row.lostLocation] || row.lostLocation }} ｜ 第{{ row.frequency }}次</span>
            <span>¥{{ row.estimatedCost * row.frequency }}</span>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="card-title"><h2>收纳前后对比</h2><span class="tag">上传后 +10 阳光</span></div>
        <div class="compare">
          <label class="compare-side">
            <div v-if="beforeUrl" class="photo-preview"><img :src="beforeUrl" /></div>
            <template v-else><span class="compare-icon">📷</span><span>{{ beforeName || '上传凌乱桌面' }}</span></template>
            <input type="file" accept="image/*" @change="handlePhoto($event, 'before')" />
          </label>
          <label class="compare-side">
            <div v-if="afterUrl" class="photo-preview"><img :src="afterUrl" /></div>
            <template v-else><span class="compare-icon">📷</span><span>{{ afterName || '上传整理后桌面' }}</span></template>
            <input type="file" accept="image/*" @change="handlePhoto($event, 'after')" />
          </label>
        </div>
        <p v-if="beforeName && afterName" class="note">对比照片已上传，+10 阳光值！继续保持收纳好习惯。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.bar-chart { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.bar-row { display: grid; grid-template-columns: 50px 1fr 28px; gap: 6px; align-items: center; }
.bar-label { font-size: 12px; font-weight: 800; text-align: right; }
.bar-track { height: 24px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
.bar-fill { height: 100%; border-radius: inherit; transition: width .4s ease; }
.bar-val { font-size: 13px; font-weight: 900; text-align: center; }
.cost-chart { display: flex; align-items: flex-end; gap: 10px; height: 120px; margin-top: 12px; padding-top: 8px; }
.cost-bar { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; height: 100%; justify-content: flex-end; }
.cost-fill { width: 100%; border-radius: 10px 10px 4px 4px; background: linear-gradient(180deg, var(--peach), #f87171); transition: height .4s ease; }
.cost-label { font-size: 11px; color: var(--muted); font-weight: 700; }
.cost-val { font-size: 12px; font-weight: 900; }
.alert-card { display: flex; gap: 10px; align-items: flex-start; padding: 14px; border-radius: 18px; background: #ffdad6; border: 1px solid #fca5a5; animation: pulse 1.5s ease infinite; margin-bottom: 8px; }
.alert-icon { font-size: 24px; }
.alert-tip { margin: 4px 0 0; font-size: 13px; color: #93000a; }
.high-freq { border-color: #fca5a5 !important; background: #fff5f5 !important; }
.compare { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.compare-side { min-height: 180px; border: 2px dashed var(--line); border-radius: 22px; display: grid; place-items: center; text-align: center; font-weight: 900; color: var(--muted); cursor: pointer; padding: 12px; }
.compare-side:hover { border-color: var(--primary); background: #f0fff0; }
.compare-icon { font-size: 36px; display: block; margin-bottom: 8px; }
.compare-side input { display: none; }
.photo-preview { width: 100%; height: 160px; overflow: hidden; border-radius: 16px; }
.photo-preview img { width: 100%; height: 100%; object-fit: cover; }
.note { padding: 14px; border-radius: 18px; background: #ecfdf5; color: #059669; margin-top: 12px; }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(248,113,113,0); } 50% { box-shadow: 0 0 0 8px rgba(248,113,113,.15); } }
@media (max-width: 900px) { .compare { grid-template-columns: 1fr; } }
</style>
