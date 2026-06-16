<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGrowthStore } from '../../stores'

const growthStore = useGrowthStore()

// Loss record form
const itemName = ref('')
const lostLocation = ref('')
const estimatedCost = ref(0)

// Storage record form
const storageItemName = ref('')
const storageLocation = ref('')
const storageNotes = ref('')

const totalFrequency = computed(() =>
  growthStore.itemLossRecords.reduce((sum, item) => sum + item.frequency, 0)
)

function reportLoss() {
  if (!itemName.value.trim()) return
  growthStore.addItemLossRecord({
    itemName: itemName.value,
    lostLocation: lostLocation.value || '未填写',
    estimatedCost: estimatedCost.value || 0,
  })
  itemName.value = ''
  lostLocation.value = ''
  estimatedCost.value = 0
}

function addStorage() {
  if (!storageItemName.value.trim()) return
  growthStore.addStorageRecord({
    itemName: storageItemName.value,
    storageLocation: storageLocation.value,
    notes: storageNotes.value || undefined,
  })
  storageItemName.value = ''
  storageLocation.value = ''
  storageNotes.value = ''
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🎒 物品管理实验室</span>
        <h1>记录丢失与收纳，减少物品流失</h1>
        <p class="lead">追踪丢失物品的频次和成本，同时记录收纳整理的好习惯。30 天内同一物品丢失满 3 次会触发急救提示。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>本月流失成本</h2>
          <span class="tag">{{ totalFrequency }} 次</span>
        </div>
        <div class="kpi">
          <strong>¥{{ growthStore.totalLossCost }}</strong>
          <span>累计账单随上报自动更新</span>
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
          <span v-if="!growthStore.itemLossRecords.length" class="muted" style="font-weight:400">
            暂无丢失记录
          </span>
        </div>
      </div>

      <div class="soft-card">
        <div class="icon-tile">🗂️</div>
        <h2>收纳记录</h2>
        <p class="lead" style="margin-top:8px">
          已收纳 <strong>{{ growthStore.storageRecords.length }}</strong> 件物品
        </p>
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
        <p v-else class="lead">暂未触发高频流失预警。</p>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>新增丢失记录</h2>
          <button class="btn" @click="reportLoss">上报</button>
        </div>
        <div class="grid-3" style="margin-bottom:16px">
          <input v-model="itemName" class="input" placeholder="物品名称" />
          <input v-model="lostLocation" class="input" placeholder="丢失地点" />
          <input
            v-model.number="estimatedCost"
            class="input"
            type="number"
            min="0"
            placeholder="估价 ¥"
          />
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
        <p v-else class="muted" style="text-align:center;padding:20px">
          暂无丢失记录
        </p>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>添加收纳记录</h2>
          <button class="btn secondary" @click="addStorage">记录</button>
        </div>
        <div class="grid-2" style="margin-bottom:16px">
          <input v-model="storageItemName" class="input" placeholder="收纳物品" />
          <input v-model="storageLocation" class="input" placeholder="收纳位置" />
        </div>
        <input
          v-model="storageNotes"
          class="input"
          style="margin-bottom:16px"
          placeholder="备注（可选）：如试卷归档、文具归位等"
        />
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
        <p v-else class="muted" style="text-align:center;padding:20px">
          暂无收纳记录
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
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
  animation: pulse 1.5s infinite;
  font-size: 14px;
  margin-top: 8px;
}
.storage-mini-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
@keyframes pulse {
  50% { box-shadow: 0 0 0 8px rgba(255, 0, 0, .08); }
}
</style>
