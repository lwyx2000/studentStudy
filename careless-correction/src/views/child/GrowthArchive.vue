<script setup lang="ts">
import { ref } from 'vue'
import { Button, Card, Title, Divider, Select } from 'animal-island-vue'


const selectedPeriod = ref('semester')

const periodOptions = [
  { label: '本学期', value: 'semester' },
  { label: '本学年', value: 'year' },
  { label: '全部', value: 'all' },
]

const alertItems = [
  {
    id: '1',
    title: '阶段性发展发现',
    description: '近7天看错符号错误环比上升25%，通常由近期作业量增大导致的视觉疲劳引起。',
    suggestion: '将晚上写作业的中间休息频率提高至写20分钟休息5分钟，并确保台灯亮度调高一档。',
    severity: 'warning',
  },
  {
    id: '2',
    title: '任务启动亮点',
    description: '近两周Leo的任务自主启动率提升了18%!',
    suggestion: '继续保持当前鼓励节奏，适当增加自主选择任务的机会。',
    severity: 'positive',
  },
]

const peerDimensions = [
  { name: '专注', childValue: 65, avgValue: 50 },
  { name: '整洁', childValue: 45, avgValue: 55 },
  { name: '元认知', childValue: 35, avgValue: 40 },
  { name: '情绪', childValue: 70, avgValue: 60 },
]

function generateReport() {
  alert('PDF成长报告已生成，可分享给老师')
}
</script>

<template>
  <div class="growth-archive">
    <div class="header-row">
      <Title size="large" color="app-green">6年长期成长档案与预警中心</Title>
      <Button type="primary" @click="generateReport">
        < name="icon-shopping" /> 生成PDF成长报告
      </Button>
    </div>

    <div class="trend-section">
      <Card color="app-teal" type="title" class="trend-chart-card">
        <template #title>
          <Title size="middle" color="app-teal">长期成长折线图</Title>
        </template>
        <div class="period-selector">
          <Select :options="periodOptions as any" v-model="selectedPeriod" />
        </div>
        <div class="trend-charts-grid">
          <Card color="app-green" class="mini-chart">
            <Title size="small" color="app-green">漏题率趋势</Title>
            <div class="chart-placeholder">
              <div class="trend-line down">-15% 本月!</div>
            </div>
          </Card>
          <Card color="app-red" class="mini-chart">
            <Title size="small" color="app-red">丢东西频次</Title>
            <div class="chart-placeholder">
              <div class="trend-line up">+2次/月</div>
            </div>
          </Card>
          <Card color="app-yellow" class="mini-chart">
            <Title size="small" color="app-yellow">任务完成率</Title>
            <div class="chart-placeholder">
              <div class="trend-line down">78%</div>
            </div>
          </Card>
        </div>
      </Card>

      <Card color="app-blue" type="title" class="peer-card">
        <template #title>
          <Title size="middle" color="app-blue">同龄常模对比</Title>
        </template>
        <div class="radar-chart">
          <div class="radar-web">
            <div class="radar-axis" v-for="dim in peerDimensions" :key="dim.name">
              <span class="dim-name">{{ dim.name }}</span>
              <div class="dim-bars">
                <div class="bar child" :style="{ width: dim.childValue + '%' }">{{ dim.childValue }}</div>
                <div class="bar avg" :style="{ width: dim.avgValue + '%' }">{{ dim.avgValue }}</div>
              </div>
            </div>
          </div>
          <div class="legend">
            <span class="legend-child">你的小树苗</span>
            <span class="legend-avg">岛上平均</span>
          </div>
        </div>
      </Card>
    </div>

    <Divider type="wave-yellow" />

    <Card color="default" type="title">
      <template #title>
        <Title size="middle" color="app-yellow">阶段性发展发现</Title>
      </template>
      <div class="alert-list">
        <Card v-for="alert in alertItems" :key="alert.id" :color="alert.severity === 'positive' ? 'app-green' : 'app-yellow'">
          <div class="alert-card-content">
            <Title size="small" :color="alert.severity === 'positive' ? 'app-green' : 'app-yellow'">
              {{ alert.title }}
            </Title>
            <p class="alert-desc">{{ alert.description }}</p>
            <Card type="dashed">
              <p class="alert-suggestion">建议: {{ alert.suggestion }}</p>
            </Card>
          </div>
        </Card>
      </div>
    </Card>
  </div>
</template>

<style scoped>
.growth-archive {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trend-section {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 16px;
}

.period-selector {
  margin-bottom: 12px;
}

.trend-charts-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-placeholder {
  height: 80px;
  background: #f7f3df;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.trend-line.down {
  color: #106e00;
}

.trend-line.up {
  color: #ba1a1a;
}

.radar-chart {
  padding: 8px;
}

.radar-web {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radar-axis {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dim-name {
  width: 40px;
  font-weight: 600;
  color: #725d42;
}

.dim-bars {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.bar {
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  font-size: 12px;
  font-weight: 600;
}

.bar.child {
  background: #8ac68a;
  color: white;
}

.bar.avg {
  background: #e4e3d8;
  color: #725d42;
}

.legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 14px;
}

.legend-child {
  color: #8ac68a;
  font-weight: 700;
}

.legend-avg {
  color: #725d42;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-desc {
  color: #725d42;
}

.alert-suggestion {
  color: #106e00;
  font-weight: 500;
}
</style>