<script setup lang="ts">
import { computed } from 'vue'
import { useGrowthStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const growthStore = useGrowthStore()

const totalLossItems = computed(() => growthStore.itemLossRecords.reduce((s, i) => s + i.frequency, 0))
const totalStorage = computed(() => growthStore.storageRecords.length)
</script>

<template>
  <div class="page">
    <ChildSelector />
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🎒 物品流失统计</span>
        <h1>丢失与收纳全景</h1>
        <p class="lead">查看孩子物品丢失的频次、成本与收纳记录，及时发现高频流失物品并介入引导。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>总览</h2>
          <span class="tag">累计 {{ totalLossItems }} 次丢失</span>
        </div>
        <div class="stat-row">
          <div class="mini-stat">
            <strong>{{ totalLossItems }}</strong>
            <span>累计丢失</span>
          </div>
          <div class="mini-stat">
            <strong>¥{{ growthStore.totalLossCost }}</strong>
            <span>流失成本</span>
          </div>
          <div class="mini-stat">
            <strong>{{ growthStore.highFrequencyItems.length }}</strong>
            <span>高频物品</span>
          </div>
          <div class="mini-stat">
            <strong>{{ totalStorage }}</strong>
            <span>收纳记录</span>
          </div>
        </div>
      </div>
    </section>

    <section class="grid-3">
      <div class="soft-card">
        <div class="icon-tile">📍</div>
        <h2>高发地点</h2>
        <div class="radar">
          <span
            v-for="item in growthStore.itemLossRecords"
            :key="item.id"
          >{{ item.lostLocation }} · {{ item.frequency }}次</span>
          <span v-if="!growthStore.itemLossRecords.length" class="muted" style="font-weight:400">暂无丢失记录</span>
        </div>
      </div>

      <div class="soft-card">
        <div class="icon-tile">🚑</div>
        <h2>高频流失急救</h2>
        <template v-if="growthStore.highFrequencyItems.length">
          <p
            v-for="item in growthStore.highFrequencyItems"
            :key="item.id"
            class="alert"
          >
            {{ item.itemName }} 30 天内丢失 {{ item.frequency }} 次：建议贴上荧光姓名贴，固定收纳位置。
          </p>
        </template>
        <p v-else class="lead" style="margin-top:8px">暂未触发高频流失预警。</p>
      </div>

      <div class="soft-card">
        <div class="icon-tile">🗂️</div>
        <h2>收纳概况</h2>
        <p class="lead" style="margin-top:8px">已收纳 <strong>{{ totalStorage }}</strong> 件物品</p>
        <div v-if="growthStore.storageRecords.length" class="storage-mini-list">
          <div
            v-for="record in growthStore.storageRecords.slice(0, 3)"
            :key="record.id"
            class="list-row"
            style="padding:8px 12px;font-size:14px"
          >
            <span>{{ record.itemName }}</span>
            <span class="muted">→ {{ record.storageLocation }}</span>
          </div>
          <p v-if="growthStore.storageRecords.length > 3" class="muted" style="font-size:13px">
            还有 {{ growthStore.storageRecords.length - 3 }} 条记录…
          </p>
        </div>
        <p v-else class="muted" style="text-align:center;padding:12px">暂无收纳记录</p>
      </div>
    </section>

    <section class="panel">
      <div class="card-title">
        <h2>丢失物品明细</h2>
        <span class="tag">共 {{ growthStore.itemLossRecords.length }} 件</span>
      </div>
      <div v-if="growthStore.itemLossRecords.length" class="list">
        <div
          v-for="row in growthStore.itemLossRecords"
          :key="row.id"
          class="list-row"
        >
          <span>📦 {{ row.itemName }}｜{{ row.lostLocation }}｜第{{ row.frequency }}次</span>
          <span style="font-weight:800">¥{{ row.estimatedCost * row.frequency }}</span>
        </div>
      </div>
      <p v-else class="muted" style="text-align:center;padding:20px">暂无丢失记录</p>
    </section>

    <section class="panel">
      <div class="card-title">
        <h2>收纳记录</h2>
        <span class="tag">共 {{ growthStore.storageRecords.length }} 条</span>
      </div>
      <div v-if="growthStore.storageRecords.length" class="list">
        <div
          v-for="record in growthStore.storageRecords"
          :key="record.id"
          class="list-row"
        >
          <div style="min-width:0">
            <strong>{{ record.itemName }}</strong>
            <span class="muted" style="display:block;font-size:13px">
              → {{ record.storageLocation }}
              <template v-if="record.notes"> · {{ record.notes }}</template>
            </span>
          </div>
          <span class="tag" style="flex-shrink:0;font-size:12px">
            {{ new Date(record.storageDate).toLocaleDateString() }}
          </span>
        </div>
      </div>
      <p v-else class="muted" style="text-align:center;padding:20px">暂无收纳记录</p>
    </section>
  </div>
</template>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.mini-stat {
  text-align: center;
  padding: 12px 8px;
  border-radius: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.mini-stat strong {
  display: block;
  font-size: 22px;
  margin-bottom: 2px;
}
.mini-stat span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.radar {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}
.radar span {
  padding: 10px 14px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid var(--line);
  font-weight: 800;
  font-size: 14px;
}
.alert {
  padding: 12px;
  border-radius: 18px;
  background: #ffdad6;
  color: #93000a;
  font-size: 14px;
  margin-top: 8px;
}
.storage-mini-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
</style>
