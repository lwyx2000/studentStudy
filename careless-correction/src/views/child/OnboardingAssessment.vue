<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores'
import { Button, Card, Title, Input } from 'animal-island-vue'

const router = useRouter()
const userStore = useUserStore()

const step = ref(1)
const childName = ref('')
const selectedGrade = ref(1)
const focusSlider = ref(3)
const orgSlider = ref(3)
const emotionSlider = ref(3)

const grades = [1, 2, 3, 4, 5, 6]

const sliderLabels: Record<number, string> = {
  1: '需要重点关注',
  2: '偶尔困难',
  3: '一般水平',
  4: '较好表现',
  5: '非常出色',
}

const focusLabel = computed(() => sliderLabels[focusSlider.value] || '')
const orgLabel = computed(() => sliderLabels[orgSlider.value] || '')
const emotionLabel = computed(() => sliderLabels[emotionSlider.value] || '')

const recommendedLevel = computed(() => {
  const avg = (focusSlider.value + orgSlider.value + emotionSlider.value) / 3
  return Math.max(1, Math.min(5, Math.round(6 - avg)))
})

function handleGenerate() {
  userStore.setProfile({
    name: childName.value,
    grade: selectedGrade.value,
    role: 'child',
  })
  userStore.setAssessment({
    focusAttention: focusSlider.value,
    organization: orgSlider.value,
    emotionalControl: emotionSlider.value,
    recommendedLevel: recommendedLevel.value,
  })
  userStore.completeOnboarding()
  router.push('/dashboard')
}
</script>

<template>
  <div class="onboarding-page">
    <div class="tree-panel">
      <div class="tree-illustration">
        <div class="sapling">
          <div class="tree-trunk"></div>
          <div class="tree-crown" :class="{ 'crown-large': recommendedLevel <= 2, 'crown-medium': recommendedLevel === 3, 'crown-small': recommendedLevel >= 4 }"></div>
        </div>
        <div class="floating-card">
          <Card color="app-green">
            <Title size="small" color="app-green">小树成长岛</Title>
            <p style="text-align: center; margin: 8px 0;">让我们一起发芽吧!</p>
          </Card>
        </div>
      </div>
    </div>

    <div class="assessment-panel">
      <Card v-if="step === 1" type="title" color="app-teal">
        <template #title>
          <Title color="app-teal">第一步: 认识小探险家</Title>
        </template>
        <div class="step-content">
          <div class="form-group">
            <label>小探险家的名字</label>
            <Input v-model="childName" placeholder="请输入孩子姓名" size="large" shadow />
          </div>
          <div class="form-group">
            <label>当前年级</label>
            <div class="grade-selector">
              <Button
                v-for="g in grades"
                :key="g"
                :type="selectedGrade === g ? 'primary' : 'default'"
                @click="selectedGrade = g"
              >
                {{ g }}年级
              </Button>
            </div>
          </div>
          <Button type="primary" block @click="step = 2">下一步</Button>
        </div>
      </Card>

      <Card v-if="step === 2" type="title" color="app-yellow">
        <template #title>
          <Title color="app-yellow">第二步: 了解成长起点</Title>
        </template>
        <div class="step-content">
          <div class="slider-group">
            <label>专注持久度</label>
            <div class="slider-row">
              <input type="range" min="1" max="5" v-model.number="focusSlider" class="custom-slider" />
              <span class="slider-value">{{ focusLabel }}</span>
            </div>
          </div>
          <div class="slider-group">
            <label>物品整洁度</label>
            <div class="slider-row">
              <input type="range" min="1" max="5" v-model.number="orgSlider" class="custom-slider" />
              <span class="slider-value">{{ orgLabel }}</span>
            </div>
          </div>
          <div class="slider-group">
            <label>情绪克制力</label>
            <div class="slider-row">
              <input type="range" min="1" max="5" v-model.number="emotionSlider" class="custom-slider" />
              <span class="slider-value">{{ emotionLabel }}</span>
            </div>
          </div>
          <div class="nav-buttons">
            <Button type="dashed" @click="step = 1">返回</Button>
            <Button type="primary" @click="step = 3">下一步</Button>
          </div>
        </div>
      </Card>

      <Card v-if="step === 3" type="title" color="app-green">
        <template #title>
          <Title color="app-green">第三步: 生成专属档案</Title>
        </template>
        <div class="step-content">
          <div class="summary-card">
            <div class="summary-row">
              <span class="summary-label">姓名:</span>
              <span class="summary-value">{{ childName }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">物理年级:</span>
              <span class="summary-value">{{ selectedGrade }}年级</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">推荐起点难度:</span>
              <span class="summary-value">Level {{ recommendedLevel }}</span>
            </div>
          </div>
          <Card type="dashed">
            <div class="ux-note">
              <p>此结果仅用于个性化定制每日任务密度，不代表智力水平，后续随打卡数据自动动态修正。</p>
            </div>
          </Card>
          <div class="nav-buttons">
            <Button type="dashed" @click="step = 2">返回</Button>
            <Button type="primary" block @click="handleGenerate">生成档案，进入小树岛!</Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.onboarding-page {
  display: grid;
  grid-template-columns: 40% 60%;
  min-height: 100vh;
  background: #fcfaef;
}

.tree-panel {
  background: linear-gradient(180deg, #d4edda 0%, #8ac68a 50%, #3d5a1a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.tree-illustration {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sapling {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.tree-trunk {
  width: 16px;
  height: 80px;
  background: #9a835a;
  border-radius: 8px;
}

.tree-crown {
  width: 100px;
  height: 80px;
  background: #8ac68a;
  border-radius: 50%;
  transition: all 0.5s;
}

.crown-large {
  width: 140px;
  height: 100px;
}

.crown-medium {
  width: 100px;
  height: 80px;
}

.crown-small {
  width: 70px;
  height: 60px;
}

.floating-card {
  margin-top: 16px;
}

.assessment-panel {
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #725d42;
}

.grade-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-group label {
  font-weight: 600;
  color: #725d42;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.custom-slider {
  flex: 1;
  accent-color: #106e00;
}

.slider-value {
  font-weight: 500;
  color: #106e00;
  min-width: 100px;
}

.nav-buttons {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.summary-card {
  padding: 16px;
  background: #e4e3d8;
  border-radius: 16px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.summary-label {
  font-weight: 600;
  color: #725d42;
}

.summary-value {
  color: #106e00;
  font-weight: 700;
}

.ux-note {
  padding: 12px;
  font-size: 14px;
  color: #6e5e00;
  background: #fbe270;
  border-radius: 8px;
}
</style>