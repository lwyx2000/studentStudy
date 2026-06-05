<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore, useGrowthStore } from '../../stores'
import { Button, Card, Title, Divider, Input } from 'animal-island-vue'

const userStore = useUserStore()
const growthStore = useGrowthStore()

const itemName = ref('')
const lostLocation = ref('')
const beforeImage = ref<string | null>(null)
const afterImage = ref<string | null>(null)

const locations = ['学校', '公交/地铁', '家里', '操场', '其他']

const lossStats = computed(() => {
  const records = growthStore.itemLossRecords
  const totalCost = records.reduce((sum, r) => sum + r.estimatedCost, 0)
  const highFreqItems = records.filter(r => r.frequency >= 3)
  return { totalCost, highFreqItems, totalRecords: records.length }
})

function reportLoss() {
  growthStore.itemLossRecords.push({
    id: Date.now().toString(),
    itemName: itemName.value,
    lostLocation: lostLocation.value,
    lostDate: new Date().toISOString(),
    estimatedCost: 5,
    frequency: 1,
  })
  itemName.value = ''
  lostLocation.value = ''
}

const virtualBagItems = [
  { name: '铅笔', status: 'safe', color: '#8ac68a' },
  { name: '橡皮', status: 'lost', color: '#fc736d', alert: true },
  { name: '水杯', status: 'safe', color: '#8ac68a' },
  { name: '课本', status: 'safe', color: '#8ac68a' },
  { name: '尺子', status: 'lost', color: '#fc736d' },
  { name: '文具盒', status: 'safe', color: '#8ac68a' },
]
</script>

<template>
  <div class="item-tracker">
    <Title size="large" color="app-orange">物品流失追踪与收纳实验室</Title>

    <Card color="app-teal" type="title" class="bag-section">
      <template #title>
        <Title size="middle" color="app-teal">虚拟书包透视图</Title>
      </template>
      <div class="virtual-bag">
        <div
          v-for="item in virtualBagItems"
          :key="item.name"
          class="bag-item"
          :class="{ lost: item.status === 'lost', alert: item.alert }"
          :style="{ borderColor: item.color }"
        >
          < name="icon-map" v-if="item.status === 'safe'" />
          <span v-if="item.status === 'lost'" class="lost-tag">丢失</span>
          <span class="item-name">{{ item.name }}</span>
        </div>
      </div>
      <div class="alert-cards" v-if="lossStats.highFreqItems.length">
        <Card v-for="item in lossStats.highFreqItems" :key="item.id" color="app-red">
          <div class="breathing-alert">
            <Title size="small" color="app-red">高频流失警报: {{ item.itemName }}</Title>
            <p>30天内丢失{{ item.frequency }}次! 建议立刻贴上荧光色姓名贴。</p>
          </div>
        </Card>
      </div>
    </Card>

    <Divider type="wave-yellow" />

    <div class="loss-report-section">
      <Card color="app-yellow" type="title">
        <template #title>
          <Title size="middle" color="app-yellow">报告物品丢失</Title>
        </template>
        <div class="report-form">
          <div class="form-group">
            <label>丢失物品名称</label>
            <Input v-model="itemName" placeholder="如：橡皮、水杯" shadow />
          </div>
          <div class="form-group">
            <label>丢失地点</label>
            <div class="location-selector">
              <Button
                v-for="loc in locations"
                :key="loc"
                :type="lostLocation === loc ? 'primary' : 'default'"
                size="small"
                @click="lostLocation = loc"
              >
                {{ loc }}
              </Button>
            </div>
          </div>
          <Button type="primary" block @click="reportLoss">记录丢失</Button>
        </div>
      </Card>
    </div>

    <Divider type="wave-yellow" />

    <div class="stats-section">
      <div class="stats-grid">
        <Card color="app-blue" type="title">
          <template #title>
            <Title size="small" color="app-blue">丢失地点雷达</Title>
          </template>
          <div class="radar-chart">
            <div class="radar-placeholder">地点分布图</div>
          </div>
        </Card>
        <Card color="app-orange" type="title">
          <template #title>
            <Title size="small" color="app-orange">累计损失账单</Title>
          </template>
          <div class="cost-chart">
            <p class="total-cost">累计损失: ¥{{ lossStats.totalCost }}</p>
            <div class="cost-line-placeholder">折线图</div>
          </div>
        </Card>
      </div>
    </div>

    <Divider type="dashed-brown" />

    <Card color="app-green" type="title">
      <template #title>
        <Title size="middle" color="app-green">收纳前后对比</Title>
      </template>
      <div class="before-after">
        <div class="comparison-slider">
          <div class="before-side">
            <div class="photo-placeholder" @click="beforeImage = 'uploaded'">
              <Icon name="icon-camera" />
              <p>拍摄凌乱桌面</p>
            </div>
          </div>
          <div class="after-side">
            <div class="photo-placeholder" @click="afterImage = 'uploaded'">
              <Icon name="icon-camera" />
              <p>拍摄整理后桌面</p>
            </div>
          </div>
        </div>
        <Button type="primary" @click="userStore.addSunlightPoints(15)">
          上传对比，赢取阳光值!
        </Button>
      </div>
    </Card>
  </div>
</template>



<style scoped>
.item-tracker {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.virtual-bag {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px;
}

.bag-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  border: 2px solid;
  border-radius: 12px;
  background: #f7f3df;
  transition: all 0.2s;
}

.bag-item.lost {
  background: #fce4e4;
}

.bag-item.alert {
  animation: breathing 2s ease-in-out infinite;
}

.lost-tag {
  background: #fc736d;
  color: white;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 12px;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
}

@keyframes breathing {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.breathing-alert {
  animation: breathing 2s ease-in-out infinite;
}

.report-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-weight: 600;
  color: #725d42;
}

.location-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.radar-placeholder,
.cost-line-placeholder {
  height: 200px;
  background: #e4e3d8;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #725d42;
  font-size: 14px;
}

.total-cost {
  font-size: 20px;
  font-weight: 700;
  color: #e59266;
}

.before-after {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comparison-slider {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.photo-placeholder {
  height: 160px;
  background: #f7f3df;
  border: 2px dashed #9a835a;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  color: #725d42;
}
</style>