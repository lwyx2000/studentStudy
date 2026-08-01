<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useChildSelectStore, useUserStore } from '../../stores'
import { api } from '../../utils/api'
import ChildSelector from '../../components/ChildSelector.vue'

const userStore = useUserStore()
const childSelectStore = useChildSelectStore()
const selectedChild = computed(() => childSelectStore.selectedChild)
const activeTab = ref<'history' | 'award' | 'apples' | 'redeem'>('history')

// ── Child data (loaded from API for selected child) ──
const childSunlight = ref(0)
const childApples = ref(0)
const childSunlightHistory = ref<any[]>([])
const childAppleHistory = ref<any[]>([])
const loadingData = ref(false)

async function loadChildData() {
  const childId = childSelectStore.selectedChildId
  if (!childId) return
  loadingData.value = true
  try {
    const { balance } = await api.points.getBalance(childId)
    childSunlight.value = balance
  } catch { /* offline */ }
  try {
    const res = await api.points.getHistory(childId)
    const raw: any[] = res.history ?? []
    childSunlightHistory.value = raw.map((r: any) => ({
      id: String(r.pk_sunlight_history ?? r.id ?? ''),
      amount: r.amount ?? 0,
      reason: r.reason ?? '',
      type: r.type ?? 'earn',
      timestamp: r.created_at ?? r.timestamp ?? new Date().toISOString(),
    }))
  } catch { /* offline */ }
  try {
    const res = await api.points.getApples(childId)
    childApples.value = res.apples
    childSunlight.value = res.sunlightPoints
    const rawHistory: any[] = res.history ?? []
    childAppleHistory.value = rawHistory.map((h: any) => ({
      id: String(h.pk_apple_history ?? h.id ?? ''),
      amount: h.amount ?? 0,
      reason: h.reason ?? '',
      type: h.type ?? 'grow',
      timestamp: h.created_at ?? h.timestamp ?? new Date().toISOString(),
    }))
  } catch { /* offline */ }
  try {
    await userStore.fetchFromApi(childId)
  } catch { /* offline */ }
  loadingData.value = false
}

watch(() => childSelectStore.selectedChildId, () => {
  loadChildData()
})

onMounted(() => {
  loadChildData()
})

// ── Manual award/deduct ──
const awardAmount = ref(10)
const awardReason = ref('')
const awardLoading = ref(false)
const awardSuccess = ref('')

const quickReasons = [
  { label: '👍 表现好', amount: 10 },
  { label: '📚 主动学习', amount: 20 },
  { label: '🧹 主动整理', amount: 15 },
  { label: '💪 坚持打卡', amount: 25 },
  { label: '⚠️ 撒谎', amount: -20 },
  { label: '⚠️ 打架', amount: -30 },
]

function applyQuickReason(qr: { label: string; amount: number }) {
  awardAmount.value = qr.amount
  awardReason.value = qr.label
}

async function submitAward() {
  if (!awardAmount.value || awardAmount.value === 0 || !childSelectStore.selectedChildId) return
  awardLoading.value = true
  awardSuccess.value = ''
  try {
    const reason = awardReason.value || (awardAmount.value > 0 ? '家长手动发放' : '家长手动扣除')
    await api.points.award(awardAmount.value, reason, childSelectStore.selectedChildId)
    awardSuccess.value = `${awardAmount.value > 0 ? '发放' : '扣除'} ${Math.abs(awardAmount.value)} 阳光值成功 ✅`
    awardReason.value = ''
    await loadChildData()
    setTimeout(() => { awardSuccess.value = '' }, 3000)
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
  awardLoading.value = false
}

// ── Apple management ──
const redeemCount = ref(1)
const redeemReason = ref('')
const redeemLoading = ref(false)
const redeemSuccess = ref('')

async function redeemAppleForChild() {
  if (!childSelectStore.selectedChildId || redeemCount.value <= 0) return
  redeemLoading.value = true
  redeemSuccess.value = ''
  try {
    await api.points.redeemApple(redeemCount.value, redeemReason.value || `兑换 ${redeemCount.value} 元`, childSelectStore.selectedChildId)
    redeemSuccess.value = `成功兑换 ${redeemCount.value} 个苹果（= ${redeemCount.value} 元）✅`
    redeemReason.value = ''
    redeemCount.value = 1
    await loadChildData()
    setTimeout(() => { redeemSuccess.value = '' }, 3000)
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
  redeemLoading.value = false
}

// ── Reward items ──
const newItemName = ref('')
const newItemDesc = ref('')
const newItemCost = ref(30)
const newItemIcon = ref('🎁')
const showAddForm = ref(false)

function handleRedeem(itemId: string) {
  const ok = userStore.redeemItem(itemId)
  if (!ok) alert('阳光值不足，无法兑换此物品')
  else loadChildData()
}

function addItem() {
  if (!newItemName.value.trim() || !newItemDesc.value.trim()) return
  userStore.addRewardItem({
    name: newItemName.value,
    description: newItemDesc.value,
    cost: newItemCost.value,
    icon: newItemIcon.value,
    active: true,
  })
  newItemName.value = ''
  newItemDesc.value = ''
  newItemCost.value = 30
  newItemIcon.value = '🎁'
  showAddForm.value = false
}
</script>

<template>
  <div class="page">
    <ChildSelector />

    <section v-if="!selectedChild" class="panel" style="text-align:center;padding:40px">
      <p class="muted">请先选择一个孩子来查看阳光值数据</p>
    </section>

    <template v-else>
      <!-- Hero: child's sunlight + apples -->
      <section class="page-hero">
        <div class="hero-card">
          <span class="eyebrow">☀️ 阳光值管理</span>
          <h1>{{ selectedChild.name }} 的阳光值与苹果</h1>
          <p class="lead">查看孩子的阳光值获取和消费记录，手动发放或扣除阳光值，管理苹果兑换。</p>
        </div>
        <div class="panel" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
          <span style="font-size:48px">☀️</span>
          <strong style="font-size:52px;line-height:1;margin:8px 0">{{ childSunlight }}</strong>
          <span class="muted" style="font-weight:700">当前阳光值</span>
          <div style="margin-top:16px;display:flex;align-items:center;gap:24px">
            <div style="text-align:center">
              <div style="font-size:32px">🍎</div>
              <strong style="font-size:24px">{{ childApples }}</strong>
              <span class="muted" style="display:block;font-size:12px">苹果数</span>
            </div>
            <div style="text-align:center">
              <div style="font-size:32px">💰</div>
              <strong style="font-size:24px">{{ childApples }}</strong>
              <span class="muted" style="display:block;font-size:12px">可兑元</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Tab navigation -->
      <section class="range-bar">
        <button class="btn" :class="activeTab === 'history' ? '' : 'ghost'" @click="activeTab = 'history'">📋 增减记录</button>
        <button class="btn" :class="activeTab === 'award' ? '' : 'ghost'" @click="activeTab = 'award'">✋ 手动发放</button>
        <button class="btn" :class="activeTab === 'apples' ? '' : 'ghost'" @click="activeTab = 'apples'">🍎 苹果管理</button>
        <button class="btn" :class="activeTab === 'redeem' ? '' : 'ghost'" @click="activeTab = 'redeem'">🎁 兑换物品</button>
      </section>

      <!-- Tab: History -->
      <template v-if="activeTab === 'history'">
        <section class="panel">
          <div class="card-title">
            <h2>阳光值增减记录</h2>
            <span class="tag">共 {{ childSunlightHistory.length }} 条</span>
          </div>
          <div v-if="childSunlightHistory.length" class="list">
            <div
              v-for="record in childSunlightHistory"
              :key="record.id"
              class="list-row"
            >
              <div style="min-width:0">
                <span :style="record.type === 'earn' ? 'color:var(--primary)' : 'color:#c00'">
                  {{ record.type === 'earn' ? '+' : '' }}{{ record.amount }}
                </span>
                <span class="muted" style="display:block;font-size:13px">{{ record.reason }}</span>
              </div>
              <span class="tag" style="flex-shrink:0;font-size:12px">
                {{ new Date(record.timestamp).toLocaleDateString() }}
              </span>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:20px">暂无增减记录</p>
        </section>
      </template>

      <!-- Tab: Manual Award/Deduct -->
      <template v-if="activeTab === 'award'">
        <section class="panel">
          <div class="card-title">
            <h2>✋ 手动发放 / 扣除阳光值</h2>
            <span class="tag">家长专属</span>
          </div>
          <p class="muted" style="margin-bottom:16px;font-size:14px">
            可以给孩子手动发放阳光值作为奖励（如主动完成额外任务），也可以扣除阳光值作为惩罚（如撒谎、打架）。正数为发放，负数为扣除。
          </p>

          <div class="award-form">
            <!-- Quick reasons -->
            <div class="form-row">
              <label>快捷操作</label>
              <div class="quick-grid">
                <button
                  v-for="qr in quickReasons"
                  :key="qr.label"
                  class="btn ghost quick-btn"
                  :class="{ 'quick-negative': qr.amount < 0 }"
                  @click="applyQuickReason(qr)"
                >
                  {{ qr.label }} {{ qr.amount > 0 ? '+' : '' }}{{ qr.amount }}
                </button>
              </div>
            </div>

            <div class="form-row">
              <label>数量（正数=发放，负数=扣除）</label>
              <div class="stepper">
                <button class="step-btn" @click="awardAmount -= 5">−5</button>
                <button class="step-btn" @click="awardAmount -= 1">−1</button>
                <input v-model.number="awardAmount" type="number" class="input step-input" />
                <button class="step-btn" @click="awardAmount += 1">+1</button>
                <button class="step-btn" @click="awardAmount += 5">+5</button>
                <button class="step-btn" @click="awardAmount = 10">+10</button>
                <button class="step-btn" @click="awardAmount = 50">+50</button>
              </div>
            </div>

            <div class="form-row">
              <label>原因（可选）</label>
              <input v-model="awardReason" class="input" placeholder="例如：主动完成额外作业、今天表现很好" />
            </div>

            <div v-if="awardSuccess" class="success-banner">{{ awardSuccess }}</div>

            <button
              class="btn"
              style="width:100%;margin-top:12px"
              :disabled="!awardAmount || awardAmount === 0 || awardLoading"
              @click="submitAward"
            >
              {{ awardLoading ? '处理中...' : (awardAmount > 0 ? `发放 ${awardAmount} 阳光值` : `扣除 ${Math.abs(awardAmount)} 阳光值`) }}
            </button>
          </div>
        </section>
      </template>

      <!-- Tab: Apple Management -->
      <template v-if="activeTab === 'apples'">
        <section class="grid-2">
          <div class="panel">
            <div class="card-title">
              <h2>🍎 苹果概况</h2>
              <span class="tag">1 苹果 = 1 元</span>
            </div>
            <div class="apple-stats">
              <div class="apple-stat">
                <span style="font-size:36px">🍎</span>
                <strong>{{ childApples }}</strong>
                <span class="muted">个苹果</span>
              </div>
              <div class="apple-stat">
                <span style="font-size:36px">💰</span>
                <strong>{{ childApples }}</strong>
                <span class="muted">可兑换元</span>
              </div>
            </div>
            <p class="muted" style="font-size:14px;margin-top:12px">
              孩子每积累 100 阳光值可以在「阳光树」页面种出 1 个苹果。苹果可以兑换成现金奖励（1 苹果 = 1 元）。
            </p>
          </div>

          <div class="panel">
            <div class="card-title">
              <h2>💰 兑换苹果</h2>
              <span class="tag">家长操作</span>
            </div>
            <div v-if="redeemSuccess" class="success-banner">{{ redeemSuccess }}</div>
            <div v-if="childApples <= 0" class="muted" style="text-align:center;padding:20px">
              暂无可兑换的苹果，孩子需要先在阳光树种出苹果。
            </div>
            <template v-else>
              <div class="form-row">
                <label>兑换数量</label>
                <div class="count-stepper">
                  <button class="step-btn" @click="redeemCount = Math.max(1, redeemCount - 1)">−</button>
                  <input v-model.number="redeemCount" type="number" min="1" :max="childApples" class="input step-input" />
                  <button class="step-btn" @click="redeemCount = Math.min(childApples, redeemCount + 1)">+</button>
                </div>
              </div>
              <div class="form-row">
                <label>兑换内容（可选）</label>
                <input v-model="redeemReason" class="input" placeholder="例如：买一本漫画书" />
              </div>
              <div class="modal-summary">将使用 <strong>{{ redeemCount }}</strong> 个苹果（= <strong>{{ redeemCount }}</strong> 元）</div>
              <button
                class="btn"
                style="width:100%"
                :disabled="redeemCount <= 0 || redeemCount > childApples || redeemLoading"
                @click="redeemAppleForChild"
              >
                {{ redeemLoading ? '处理中...' : `确认兑换 ${redeemCount} 个苹果` }}
              </button>
            </template>
          </div>
        </section>

        <!-- Apple history -->
        <section class="panel" style="margin-top:18px">
          <div class="card-title">
            <h2>📋 苹果变动记录</h2>
            <span class="tag">共 {{ childAppleHistory.length }} 条</span>
          </div>
          <div v-if="childAppleHistory.length" class="list">
            <div v-for="record in childAppleHistory" :key="record.id" class="list-row">
              <div style="min-width:0">
                <span :style="record.type === 'grow' ? 'color:var(--primary)' : 'color:#c00'">
                  {{ record.type === 'grow' ? '🍎 种出' : '💰 兑换' }} {{ Math.abs(record.amount) }} 个苹果
                </span>
                <span class="muted" style="display:block;font-size:13px">{{ record.reason }}</span>
              </div>
              <span class="tag" style="flex-shrink:0;font-size:12px">
                {{ new Date(record.timestamp).toLocaleDateString() }}
              </span>
            </div>
          </div>
          <p v-else class="muted" style="text-align:center;padding:20px">暂无苹果变动记录</p>
        </section>
      </template>

      <!-- Tab: Redeem Items -->
      <template v-if="activeTab === 'redeem'">
        <section class="grid-2" style="margin-bottom:18px">
          <div v-for="item in userStore.rewardItems" :key="item.id" class="soft-card" style="position:relative">
            <div style="font-size:36px;margin-bottom:8px">{{ item.icon }}</div>
            <h3>{{ item.name }}</h3>
            <p class="muted" style="font-size:14px;margin:4px 0 12px">{{ item.description }}</p>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span class="tag">☀️ {{ item.cost }}</span>
              <button
                class="btn"
                :class="item.active ? 'secondary' : 'ghost'"
                :disabled="!item.active || childSunlight < item.cost"
                style="padding:8px 14px;font-size:13px"
                @click="handleRedeem(item.id)"
              >
                {{ item.active ? '兑换' : '已禁用' }}
              </button>
              <button class="btn ghost" style="padding:8px 14px;font-size:13px" @click="userStore.toggleRewardItem(item.id)">
                {{ item.active ? '禁用' : '启用' }}
              </button>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="card-title">
            <h2>管理可兑换物品</h2>
            <button class="btn secondary" @click="showAddForm = !showAddForm">
              {{ showAddForm ? '取消' : '添加物品' }}
            </button>
          </div>
          <template v-if="showAddForm">
            <div class="grid-2" style="margin-bottom:12px">
              <input v-model="newItemName" class="input" placeholder="物品名称" />
              <input v-model="newItemIcon" class="input" placeholder="图标 emoji" />
            </div>
            <input v-model="newItemDesc" class="input" style="margin-bottom:12px" placeholder="描述" />
            <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
              <label style="font-weight:800">阳光值 <input v-model.number="newItemCost" class="input" type="number" min="5" step="5" style="width:100px" /></label>
              <button class="btn" @click="addItem">添加</button>
            </div>
          </template>
          <p v-if="!showAddForm" class="muted" style="font-size:14px">点击「添加物品」新增可兑换的奖励，兑换后孩子阳光值相应扣除。</p>
        </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.range-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.award-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-row label {
  font-weight: 800;
  font-size: 14px;
}
.stepper {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.step-btn {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #fff;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  color: var(--ink);
  transition: background .12s ease;
}
.step-btn:hover { background: #f6fddc; }
.step-input {
  width: 80px;
  text-align: center;
  font-weight: 800;
  font-size: 18px;
}
.quick-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.quick-btn {
  font-size: 13px !important;
  padding: 8px 14px !important;
}
.quick-negative {
  border-color: #ffcdd2 !important;
  color: #c00 !important;
}
.quick-negative:hover {
  background: #fff5f5 !important;
}
.success-banner {
  text-align: center;
  padding: 14px;
  border-radius: 16px;
  background: #e8f5e9;
  color: #2e7d32;
  font-weight: 800;
  font-size: 15px;
}
.apple-stats {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-top: 16px;
}
.apple-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 24px;
  border-radius: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.apple-stat strong {
  font-size: 28px;
}
.count-stepper {
  display: flex;
  align-items: center;
  gap: 8px;
}
.modal-summary {
  text-align: center;
  font-size: 15px;
  font-weight: 700;
  color: var(--muted);
  padding: 8px;
  margin-bottom: 8px;
}
</style>
