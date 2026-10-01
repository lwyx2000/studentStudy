<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../../utils/api'
import { useUserStore } from '../../stores'

const userStore = useUserStore()

// Tab state
const activeTab = ref<'checkins' | 'sunlight' | 'apples'>('checkins')

function usePagination(pageSize = 15) {
  const offset = ref(0)
  const total = ref(0)
  const page = computed(() => Math.floor(offset.value / pageSize) + 1)
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
  function goToPage(p: number) {
    if (p >= 1 && p <= totalPages.value) {
      offset.value = (p - 1) * pageSize
    }
  }
  return { offset, total, page, totalPages, goToPage, pageSize }
}

// 1. Checkin records
const checkinList = ref<any[]>([])
const checkinPag = usePagination(15)
const checkinLoading = ref(false)

async function loadCheckins() {
  checkinLoading.value = true
  try {
    const res = await api.checkins.getMine(checkinPag.pageSize, checkinPag.offset.value)
    checkinList.value = res.checkins ?? []
    checkinPag.total.value = res.total ?? 0
  } catch { /* offline */ }
  checkinLoading.value = false
}
function goCheckinPage(p: number) {
  checkinPag.goToPage(p)
  loadCheckins()
}

// 2. Sunlight history
const sunHistoryList = ref<any[]>([])
const sunPag = usePagination(15)
const sunLoading = ref(false)

async function loadSunHistory() {
  sunLoading.value = true
  try {
    const res = await api.points.getHistory(undefined, sunPag.offset.value, sunPag.pageSize)
    sunHistoryList.value = (res.history ?? []).map((r: any) => ({
      id: String(r.pk_sunlight_history ?? r.id ?? ''),
      amount: r.amount ?? 0,
      reason: r.reason ?? '',
      type: r.type ?? 'earn',
      timestamp: r.created_at ?? r.timestamp ?? new Date().toISOString(),
    }))
    sunPag.total.value = res.total ?? 0
  } catch { /* offline */ }
  sunLoading.value = false
}
function goSunPage(p: number) {
  sunPag.goToPage(p)
  loadSunHistory()
}

// 3. Apple history
const appleHistoryList = ref<any[]>([])
const applePag = usePagination(15)
const appleLoading = ref(false)

async function loadAppleHistory() {
  appleLoading.value = true
  try {
    const res = await api.points.getApples(undefined, applePag.offset.value, applePag.pageSize)
    appleHistoryList.value = (res.history ?? []).map((h: any) => ({
      id: String(h.pk_apple_history ?? h.id ?? ''),
      amount: h.amount ?? 0,
      reason: h.reason ?? '',
      type: h.type ?? 'grow',
      timestamp: h.created_at ?? h.timestamp ?? new Date().toISOString(),
    }))
    applePag.total.value = res.total ?? 0
  } catch { /* offline */ }
  appleLoading.value = false
}
function goApplePage(p: number) {
  applePag.goToPage(p)
  loadAppleHistory()
}

function switchTab(tab: 'checkins' | 'sunlight' | 'apples') {
  activeTab.value = tab
  if (tab === 'checkins') loadCheckins()
  else if (tab === 'sunlight') loadSunHistory()
  else if (tab === 'apples') loadAppleHistory()
}

onMounted(async () => {
  await userStore.fetchFromApi()
  await loadCheckins()
})

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function statusLabel(s: string) {
  return s === 'pending' ? '🕐 待审批' : s === 'approved' ? '✅ 已通过' : '❌ 已驳回'
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📈 我的成长档案</span>
        <h1>记录成长的每一步</h1>
        <p class="lead">查看打卡记录、阳光值变动和苹果兑换记录。</p>
      </div>
      <div class="panel hero-stats">
        <div style="font-size:40px">☀️</div>
        <strong class="hero-num">{{ userStore.sunlightPoints }}</strong>
        <span class="muted" style="font-weight:700">阳光值</span>
        <div class="hero-mini-row">
          <div class="hero-mini">
            <span>🍎</span>
            <strong>{{ userStore.apples }}</strong>
            <span class="muted">苹果</span>
          </div>
          <div class="hero-mini">
            <span>✅</span>
            <strong>{{ checkinPag.total.value }}</strong>
            <span class="muted">打卡</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Tab navigation -->
    <section class="range-bar">
      <button class="btn" :class="activeTab === 'checkins' ? '' : 'ghost'" @click="switchTab('checkins')">📋 打卡记录</button>
      <button class="btn" :class="activeTab === 'sunlight' ? '' : 'ghost'" @click="switchTab('sunlight')">☀️ 阳光增减</button>
      <button class="btn" :class="activeTab === 'apples' ? '' : 'ghost'" @click="switchTab('apples')">🍎 苹果记录</button>
    </section>

    <!-- Tab: Checkin Records -->
    <template v-if="activeTab === 'checkins'">
      <section class="panel">
        <div class="card-title">
          <h2>📋 打卡记录</h2>
          <span class="tag">共 {{ checkinPag.total.value }} 条</span>
        </div>
        <div v-if="checkinLoading" style="text-align:center;padding:24px"><p class="muted">加载中...</p></div>
        <div v-else-if="checkinList.length" class="list">
          <div v-for="c in checkinList" :key="c.pk_check_ins || c.id" class="list-row">
            <div style="flex:1;min-width:0">
              <strong>📅 {{ c.check_date || c.checkDate }}</strong>
              <span class="muted" style="display:block;font-size:13px">
                ☀️ +{{ c.total_points || c.totalPoints }} 阳光 · {{ c.task_count || c.taskCount || 0 }} 任务
              </span>
            </div>
            <span class="tag" :class="{'status-pending': (c.status || 'pending') === 'pending', 'status-approved': (c.status || 'pending') === 'approved', 'status-rejected': c.status === 'rejected'}">
              {{ statusLabel(c.status || 'pending') }}
            </span>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">暂无打卡记录</p>
        <div v-if="checkinPag.totalPages.value > 1" class="pagination">
          <button class="btn ghost" :disabled="checkinPag.page.value <= 1" @click="goCheckinPage(checkinPag.page.value - 1)">上一页</button>
          <span class="page-info">第 {{ checkinPag.page.value }} / {{ checkinPag.totalPages.value }} 页</span>
          <button class="btn ghost" :disabled="checkinPag.page.value >= checkinPag.totalPages.value" @click="goCheckinPage(checkinPag.page.value + 1)">下一页</button>
        </div>
      </section>
    </template>

    <!-- Tab: Sunlight History -->
    <template v-if="activeTab === 'sunlight'">
      <section class="panel">
        <div class="card-title">
          <h2>☀️ 阳光值增减记录</h2>
          <span class="tag">共 {{ sunPag.total.value }} 条</span>
        </div>
        <div v-if="sunLoading" style="text-align:center;padding:24px"><p class="muted">加载中...</p></div>
        <div v-else-if="sunHistoryList.length" class="list">
          <div v-for="r in sunHistoryList" :key="r.id" class="list-row">
            <div style="flex:1;min-width:0">
              <span :style="r.type === 'earn' ? 'color:var(--primary);font-weight:800' : 'color:#c00;font-weight:800'">
                {{ r.type === 'earn' ? '+' : '' }}{{ r.amount }}
              </span>
              <span class="muted" style="display:block;font-size:13px">{{ r.reason }}</span>
            </div>
            <span class="tag" style="flex-shrink:0;font-size:12px">{{ formatDate(r.timestamp) }}</span>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">暂无阳光值变动记录</p>
        <div v-if="sunPag.totalPages.value > 1" class="pagination">
          <button class="btn ghost" :disabled="sunPag.page.value <= 1" @click="goSunPage(sunPag.page.value - 1)">上一页</button>
          <span class="page-info">第 {{ sunPag.page.value }} / {{ sunPag.totalPages.value }} 页</span>
          <button class="btn ghost" :disabled="sunPag.page.value >= sunPag.totalPages.value" @click="goSunPage(sunPag.page.value + 1)">下一页</button>
        </div>
      </section>
    </template>

    <!-- Tab: Apple History -->
    <template v-if="activeTab === 'apples'">
      <section class="panel">
        <div class="card-title">
          <h2>🍎 苹果兑换记录</h2>
          <span class="tag">共 {{ applePag.total.value }} 条</span>
        </div>
        <div v-if="appleLoading" style="text-align:center;padding:24px"><p class="muted">加载中...</p></div>
        <div v-else-if="appleHistoryList.length" class="list">
          <div v-for="r in appleHistoryList" :key="r.id" class="list-row">
            <div style="flex:1;min-width:0">
              <span :style="(r.amount > 0) ? 'color:var(--primary);font-weight:800' : 'color:#c00;font-weight:800'">
                {{ r.amount > 0 ? '🍎 +' : '💰 -' }} {{ Math.abs(r.amount) }} 个
              </span>
              <span class="muted" style="display:block;font-size:13px">{{ r.reason }}</span>
            </div>
            <span class="tag" style="flex-shrink:0;font-size:12px">{{ formatDate(r.timestamp) }}</span>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">暂无苹果变动记录</p>
        <div v-if="applePag.totalPages.value > 1" class="pagination">
          <button class="btn ghost" :disabled="applePag.page.value <= 1" @click="goApplePage(applePag.page.value - 1)">上一页</button>
          <span class="page-info">第 {{ applePag.page.value }} / {{ applePag.totalPages.value }} 页</span>
          <button class="btn ghost" :disabled="applePag.page.value >= applePag.totalPages.value" @click="goApplePage(applePag.page.value + 1)">下一页</button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.range-bar { display: flex; gap: 10px; flex-wrap: wrap; }
.hero-stats { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.hero-num { font-size: 48px; line-height: 1; margin: 4px 0; }
.hero-mini-row { margin-top: 12px; display: flex; gap: 20px; }
.hero-mini { text-align: center; }
.hero-mini strong { font-size: 22px; display: block; }
.hero-mini span { font-size: 24px; }
.list { display: flex; flex-direction: column; gap: 8px; }
.list-row { display: flex; align-items: center; gap: 12px; padding: 14px 18px; border-radius: 14px; border: 1px solid var(--line); background: #fff; }
.list-row:hover { border-color: var(--primary-2, #a5d6a7); }
.tag.status-pending { background: #fff3e0; color: #e65100; }
.tag.status-approved { background: #e8f5e9; color: #2e7d32; }
.tag.status-rejected { background: #ffebee; color: #c62828; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 16px 0 4px; border-top: 1px dashed #e0e0e0; margin-top: 12px; }
.page-info { font-weight: 700; font-size: 14px; color: var(--muted); white-space: nowrap; }
</style>
