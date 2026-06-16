<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '../../stores'

const userStore = useUserStore()

const redemptionHistory = computed(() =>
  userStore.sunlightHistory.filter(r => r.type === 'spend')
)
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">☀️ 阳光兑换屋</span>
        <h1>已兑换的物品</h1>
        <p class="lead">完成每日任务赚取阳光值，兑换记录会在这里展示。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">
        <span style="font-size:48px">☀️</span>
        <strong style="font-size:52px;line-height:1;margin:8px 0">{{ userStore.sunlightPoints }}</strong>
        <span class="muted" style="font-weight:700">当前阳光值</span>
      </div>
    </section>

    <section class="panel">
      <div class="card-title">
        <h2>兑换记录</h2>
        <span class="tag">共 {{ redemptionHistory.length }} 条</span>
      </div>
      <div v-if="redemptionHistory.length" class="list">
        <div
          v-for="record in redemptionHistory"
          :key="record.id"
          class="list-row"
        >
          <div style="min-width:0">
            <strong>{{ record.reason }}</strong>
            <span class="muted" style="display:block;font-size:13px">花费 {{ Math.abs(record.amount) }} 阳光值</span>
          </div>
          <span class="tag" style="flex-shrink:0;font-size:12px">
            {{ new Date(record.timestamp).toLocaleDateString() }}
          </span>
        </div>
      </div>
      <p v-else class="muted" style="text-align:center;padding:20px">还没有兑换过物品，攒够阳光值后找爸爸妈妈兑换吧！</p>
    </section>
  </div>
</template>
