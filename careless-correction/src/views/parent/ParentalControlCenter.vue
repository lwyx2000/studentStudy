<script setup lang="ts">
import { ref, computed } from 'vue'
import { useParentStore } from '../../stores'
import { Button, Card, Title, Switch, Divider, Collapse } from 'animal-island-vue'

const parentStore = useParentStore()

const difficultyLevel = ref(2)
const dailyReminder = ref(true)
const achievementNotification = ref(true)
const weeklyReport = ref(true)
const schoolSync = ref(false)

const difficultyLabels = ['阳光模式', '微风模式', '挑战模式']

const currentDifficultyLabel = computed(() => difficultyLabels[difficultyLevel.value - 1] || '微风模式')

function updateDifficulty() {
  parentStore.updateSettings({ difficultyLevel: difficultyLevel.value })
}

function updateReminder(val: boolean) {
  dailyReminder.value = val
  parentStore.updateSettings({ dailyReminder: val })
}

function updateAchievement(val: boolean) {
  achievementNotification.value = val
  parentStore.updateSettings({ achievementNotification: val })
}

function updateWeeklyReport(val: boolean) {
  weeklyReport.value = val
  parentStore.updateSettings({ weeklyReport: val })
}

function updateSchoolSync(val: boolean) {
  schoolSync.value = val
  parentStore.updateSettings({ schoolSync: val })
}
</script>

<template>
  <div class="parent-control">
    <Title size="large" color="app-teal">家长控制中心</Title>

    <div class="control-grid">
      <div class="settings-main">
        <Card color="app-teal" type="title">
          <template #title>
            <Title size="middle" color="app-teal">难度天气控制</Title>
          </template>
          <div class="difficulty-control">
            <div class="difficulty-slider">
              <input
                type="range"
                min="1"
                max="3"
                v-model.number="difficultyLevel"
                class="weather-slider"
                @change="updateDifficulty"
              />
              <div class="weather-labels">
                <span :class="{ active: difficultyLevel === 1 }">阳光</span>
                <span :class="{ active: difficultyLevel === 2 }">微风</span>
                <span :class="{ active: difficultyLevel === 3 }">挑战</span>
              </div>
            </div>
            <div class="difficulty-display">
              当前模式: <strong>{{ currentDifficultyLabel }}</strong>
            </div>
          </div>
        </Card>

        <Divider type="wave-yellow" />

        <Card color="app-yellow" type="title">
          <template #title>
            <Title size="middle" color="app-yellow">通知信号</Title>
          </template>
          <div class="notification-list">
            <div class="notification-item">
              <span>每日小岛提醒</span>
              <Switch :model-value="dailyReminder" @update:model-value="updateReminder" />
            </div>
            <div class="notification-item">
              <span>成就烟花</span>
              <Switch :model-value="achievementNotification" @update:model-value="updateAchievement" />
            </div>
            <div class="notification-item">
              <span>每周收获报告</span>
              <Switch :model-value="weeklyReport" @update:model-value="updateWeeklyReport" />
            </div>
          </div>
        </Card>

        <Divider type="wave-yellow" />

        <Card color="warm-peach-pink" type="title">
          <template #title>
            <Title size="middle" color="warm-peach-pink">账号同步</Title>
          </template>
          <div class="sync-section">
            <div class="sticky-note-card">
              <div class="sync-profiles">
                <div class="profile-item">
                  < name="icon-chat" />
                  <span>家长账号</span>
                </div>
                <Icon name="icon-helicopter" />
                <div class="profile-item">
                  <Icon name="icon-map" />
                  <span>孩子账号</span>
                </div>
              </div>
              <Button type="dashed" block>管理档案</Button>
            </div>
          </div>
        </Card>

        <Divider type="wave-yellow" />

        <Card color="app-blue" type="title">
          <template #title>
            <Title size="middle" color="app-blue">学校数据共享</Title>
          </template>
          <div class="school-sync-section">
            <div class="sync-item">
              <span>教师查看成长报告</span>
              <Switch :model-value="schoolSync" @update:model-value="updateSchoolSync" />
            </div>
            <p class="sync-note">开启后，指定老师可查看孩子的匿名化成长趋势数据</p>
          </div>
        </Card>
      </div>

      <div class="settings-side">
        <Collapse question="如何调整任务难度?" answer="通过天气控制滑块调节，阳光模式任务最少最简单，挑战模式任务最多最复杂。" />
        <Collapse question="什么是成就烟花?" answer="当孩子完成重要里程碑时，系统会推送庆祝通知到您的设备。" />
        <Collapse question="学校共享数据安全吗?" answer="所有共享数据均经过匿名化处理，不包含孩子真实姓名或具体成绩。" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.parent-control {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-grid {
  display: grid;
  grid-template-columns: 8fr 4fr;
  gap: 16px;
}

.difficulty-control {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.weather-slider {
  width: 100%;
  accent-color: #106e00;
  height: 8px;
}

.weather-labels {
  display: flex;
  justify-content: space-between;
  font-weight: 600;
}

.weather-labels span {
  color: #725d42;
  transition: all 0.2s;
}

.weather-labels span.active {
  color: #106e00;
  font-size: 16px;
}

.difficulty-display {
  text-align: center;
  font-size: 16px;
  color: #725d42;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notification-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.sync-section {
  padding: 16px;
}

.sticky-note-card {
  padding: 16px;
  background: #fbe270;
  border-radius: 12px;
}

.sync-profiles {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}

.profile-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.school-sync-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sync-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sync-note {
  font-size: 13px;
  color: #725d42;
}

.settings-side {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>