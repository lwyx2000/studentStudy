<script setup lang="ts">
import { computed, ref } from 'vue'
import { useUserStore, useTaskStore } from '../../stores'
import { Button, Card, Title, Divider } from 'animal-island-vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()
const todayReviewCount = ref(3)

const isLowGrade = computed(() => userStore.isLowGrade)
const isHighGrade = computed(() => userStore.isHighGrade)

const starTask = computed(() =>
  taskStore.todayTasks.find(t => t.type === 'habit' && t.status === 'pending')
)

const secondaryTasks = computed(() =>
  taskStore.todayTasks.filter(t => t.type !== 'habit' && t.status === 'pending')
)

function completeTask(id: string) {
  taskStore.completeTask(id)
  userStore.addSunlightPoints(10)
}
</script>

<template>
  <!-- 低年级版 (1-2年级) -->
  <div v-if="isLowGrade" class="dashboard-low">
    <div class="status-row">
      <Card color="app-green" type="title">
        <template #title>
          <Title size="small" color="app-green">{{ userStore.profile.name }}的小树苗 Lv{{ userStore.assessment.recommendedLevel }}</Title>
        </template>
        <div class="progress-bar-wrap">
          <div class="progress-bar">
            <div class="progress-fill" style="width: 33%"></div>
          </div>
        </div>
      </Card>
      <Card color="app-yellow">
        <div class="sunlight-counter">
          < name="icon-miles" />
          <span>阳光值: {{ userStore.sunlightPoints }}</span>
        </div>
      </Card>
      <Card color="app-orange" type="dashed">
        <Button type="link" @click="router.push('/badge')">
          <Icon name="icon-variant" /> 我的勋章馆
        </Button>
      </Card>
    </div>

    <div class="star-task-section" v-if="starTask">
      <Card color="app-teal" type="title">
        <template #title>
          <Title color="app-teal" size="middle">今日指读任务</Title>
        </template>
        <div class="task-detail">
          <p class="task-desc">{{ starTask.description }}</p>
          <Button type="primary" size="large" block @click="completeTask(starTask.id)">确认完成!</Button>
        </div>
      </Card>
    </div>

    <div class="secondary-tasks" v-if="secondaryTasks.length">
      <div class="task-grid">
        <Card v-for="task in secondaryTasks.slice(0, 2)" :key="task.id" color="app-blue">
          <div class="task-card-content">
            <span class="emoji-icon">📋</span>
            <h4>{{ task.title }}</h4>
            <Button type="primary" @click="completeTask(task.id)">去完成</Button>
          </div>
        </Card>
      </div>
    </div>

    <Divider type="wave-yellow" />

    <div class="bottom-actions">
      <Button type="dashed" @click="router.push('/printable')">
        <Icon name="icon-diy" /> 一键打印纸质打卡单
      </Button>
      <Card type="dashed" color="warm-peach-pink">
        <div class="sticky-note">
          <p>家长登录入口</p>
          <Button type="text" @click="router.push('/parent')">进入家长视角</Button>
        </div>
      </Card>
    </div>
  </div>

  <!-- 高年级版 (5-6年级) -->
  <div v-if="isHighGrade" class="dashboard-high">
    <div class="high-top-row">
      <Card color="app-teal" type="title" class="time-block">
        <template #title>
          <Title size="small" color="app-teal">时间管理</Title>
        </template>
        <Button type="primary" @click="router.push('/time-task')">启动番茄钟</Button>
        <div class="time-axis">
          <div class="time-slot">8:00 - 作业</div>
          <div class="time-slot">10:00 - 休息</div>
          <div class="time-slot">14:00 - 复习</div>
        </div>
      </Card>
      <Card color="app-orange" type="title" class="priority-board">
        <template #title>
          <Title size="small" color="app-orange">今日优先级</Title>
        </template>
        <div class="quadrant-grid">
          <div class="quadrant urgent-important">紧急且重要</div>
          <div class="quadrant important">重要不紧急</div>
          <div class="quadrant urgent">紧急不重要</div>
          <div class="quadrant none">不紧急不重要</div>
        </div>
      </Card>
    </div>
    <div class="high-bottom-row">
      <Card color="app-pink" type="title">
        <template #title>
          <Title size="small" color="app-pink">错题复习提醒</Title>
        </template>
        <p>今日待复习错题: {{ todayReviewCount }} 题</p>
        <Button type="primary" @click="router.push('/mistake')">开始复习</Button>
      </Card>
      <Card color="app-blue" type="title">
        <template #title>
          <Title size="small" color="app-blue">收纳状态</Title>
        </template>
        <p>试卷归档进度: 60%</p>
        <Button type="primary" @click="router.push('/tracker')">查看详情</Button>
      </Card>
    </div>
  </div>

  <!-- 中年级版 (3-4年级) -->
  <div v-if="!isLowGrade && !isHighGrade" class="dashboard-mid">
    <div class="status-row">
      <Card color="app-green" type="title">
        <template #title>
          <Title size="small" color="app-green">{{ userStore.profile.name }}的小树 Lv{{ userStore.assessment.recommendedLevel }}</Title>
        </template>
        <div class="progress-bar-wrap">
          <div class="progress-bar">
            <div class="progress-fill" style="width: 33%"></div>
          </div>
        </div>
      </Card>
      <Card color="app-yellow">
        <div class="sunlight-counter">
          <Icon name="icon-miles" />
          <span>阳光值: {{ userStore.sunlightPoints }}</span>
        </div>
      </Card>
    </div>

    <div class="star-task-section" v-if="starTask">
      <Card color="app-teal" type="title">
        <template #title>
          <Title color="app-teal" size="middle">{{ starTask.title }}</Title>
        </template>
        <p>{{ starTask.description }}</p>
        <Button type="primary" block @click="completeTask(starTask.id)">确认完成</Button>
      </Card>
    </div>

    <div class="task-grid">
      <Card v-for="task in secondaryTasks" :key="task.id" :color="task.type === 'game' ? 'app-blue' : 'app-orange'">
        <h4>{{ task.title }}</h4>
        <Button type="primary" @click="completeTask(task.id)">去完成</Button>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.dashboard-low,
.dashboard-mid,
.dashboard-high {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12px;
}

.progress-bar-wrap {
  padding: 8px 0;
}

.progress-bar {
  height: 12px;
  background: #e4e3d8;
  border-radius: 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #8ac68a;
  border-radius: 12px;
  transition: width 0.5s;
}

.sunlight-counter {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.star-task-section {
  margin: 8px 0;
}

.task-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-desc {
  font-size: 16px;
  color: #725d42;
}

.task-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.task-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.bottom-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sticky-note {
  padding: 12px;
  text-align: center;
}

.high-top-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.time-block .time-axis {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}

.time-slot {
  padding: 6px 12px;
  background: #e4e3d8;
  border-radius: 8px;
  font-size: 14px;
}

.quadrant-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 8px;
  padding: 8px;
}

.quadrant {
  padding: 8px;
  border-radius: 8px;
  text-align: center;
  font-size: 12px;
}

.urgent-important {
  background: #fc736d;
  color: white;
}

.important {
  background: #f7cd67;
  color: #725d42;
}

.urgent {
  background: #82d5bb;
  color: white;
}

.none {
  background: #e4e3d8;
  color: #725d42;
}

.high-bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
</style>