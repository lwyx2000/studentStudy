<script setup lang="ts">
import { computed, ref } from 'vue'
import { useChildSelectStore, useUserStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const userStore = useUserStore()
const childSelectStore = useChildSelectStore()
const selectedChild = computed(() => childSelectStore.selectedChild)
const activeTab = ref<'history' | 'redeem'>('history')

const newItemName = ref('')
const newItemDesc = ref('')
const newItemCost = ref(30)
const newItemIcon = ref('🎁')
const showAddForm = ref(false)

function handleRedeem(itemId: string) {
  const ok = userStore.redeemItem(itemId)
  if (!ok) alert('阳光值不足，无法兑换此物品')
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
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">☀️ 阳光值管理</span>
        <h1>阳光值增减与兑换</h1>
        <p class="lead">查看孩子的阳光值获取和消费记录，管理可兑换的奖励物品，引导孩子合理规划阳光值。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
        <span style="font-size:48px">☀️</span>
        <strong style="font-size:52px;line-height:1;margin:8px 0">{{ userStore.sunlightPoints }}</strong>
        <span class="muted" style="font-weight:700">当前阳光值</span>
      </div>
    </section>

    <section class="range-bar">
      <button class="btn" :class="activeTab === 'history' ? '' : 'ghost'" @click="activeTab = 'history'">📋 增减记录</button>
      <button class="btn" :class="activeTab === 'redeem' ? '' : 'ghost'" @click="activeTab = 'redeem'">🎁 兑换物品</button>
    </section>

    <template v-if="activeTab === 'history'">
      <section class="panel">
        <div class="card-title">
          <h2>阳光值增减记录</h2>
          <span class="tag">共 {{ userStore.sunlightHistory.length }} 条</span>
        </div>
        <div v-if="userStore.sunlightHistory.length" class="list">
          <div
            v-for="record in userStore.sunlightHistory"
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
              :disabled="!item.active || userStore.sunlightPoints < item.cost"
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
  </div>
</template>

<style scoped>
.range-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
