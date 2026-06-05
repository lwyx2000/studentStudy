<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button, Card, Title, Divider } from 'animal-island-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const currentStepIndex = ref(0)
const parentReflectionYes = ref(false)
const weeklyProgress = ref(33)

const sopSteps = [
  { order: 1, instruction: '动笔前，用手指指着题目，逐字读题' },
  { order: 2, instruction: '用铅笔圈出每道大题的题号' },
  { order: 3, instruction: '圈完后抬头看一圈，确认没有遗漏' },
]

function handlePrint() {
  router.push('/printable')
}

function handleScanUpload() {
  alert('请拍照上传完成的纸质打卡单')
}

function nextStep() {
  if (currentStepIndex.value < sopSteps.length - 1) {
    currentStepIndex.value++
  }
}

function prevStep() {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
  }
}

const currentStep = computed(() => sopSteps[currentStepIndex.value])
</script>

<template>
  <div class="habit-center">
    <div class="progress-section">
      <Card color="app-green" type="title">
        <template #title>
          <Title size="small" color="app-green">本周习惯养成进度</Title>
        </template>
        <div class="vine-progress">
          <div class="vine-bar">
            <div class="vine-fill" :style="{ width: weeklyProgress + '%' }"></div>
          </div>
          <span class="progress-text">{{ weeklyProgress }}% - 继续加油!</span>
        </div>
      </Card>
    </div>

    <Divider type="wave-yellow" />

    <div class="sop-section">
      <div class="sop-grid">
        <div class="sop-main">
          <Card color="app-teal" type="title">
            <template #title>
              <Title size="middle" color="app-teal">习惯标准操作程序 (SOP)</Title>
            </template>
            <div class="step-display">
              <div class="step-number">第 {{ currentStep.order }} 步</div>
              <p class="step-instruction">{{ currentStep.instruction }}</p>
              <div class="step-nav">
                <Button type="dashed" @click="prevStep" :disabled="currentStepIndex === 0">上一步</Button>
                <Button type="primary" @click="nextStep" :disabled="currentStepIndex === sopSteps.length - 1">下一步</Button>
              </div>
            </div>
          </Card>
        </div>

        <div class="sop-parent-note">
          <Card color="warm-peach-pink">
            <div class="sticky-note-card">
              <Title size="small" color="warm-peach-pink">家长自查</Title>
              <p>今天您是否克制了对孩子的催促和代劳?</p>
              <div class="reflection-buttons">
                <Button type="primary" @click="parentReflectionYes = true">
                  是，我做到了
                </Button>
                <Button type="primary" danger @click="parentReflectionYes = false">
                  还需要改进
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>

    <Divider type="wave-yellow" />

    <div class="print-section">
      <Card color="app-yellow" type="title">
        <template #title>
          <Title size="middle" color="app-yellow">打印工具箱</Title>
        </template>
        <div class="print-grid">
          <div class="print-preview">
            <div class="a4-preview">
              <div class="a4-header">每日习惯打卡单</div>
              <div class="a4-body">
                <div class="a4-row">周一 ○ 周二 ○ 周三 ○</div>
                <div class="a4-row">周四 ○ 周五 ○ 周六 ○ 周日 ○</div>
              </div>
            </div>
          </div>
          <div class="print-actions">
            <Button type="primary" block @click="handlePrint">
              < name="icon-diy" /> 发送打印
            </Button>
            <Button type="dashed" block @click="handleScanUpload">
              <Icon name="icon-camera" /> 拍照回传核销
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>



<style scoped>
.habit-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vine-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.vine-bar {
  flex: 1;
  height: 16px;
  background: #e4e3d8;
  border-radius: 16px;
  overflow: hidden;
}

.vine-fill {
  height: 100%;
  background: linear-gradient(90deg, #8ac68a, #3d5a1a);
  border-radius: 16px;
  transition: width 0.5s;
}

.progress-text {
  font-weight: 700;
  color: #106e00;
}

.sop-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.step-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-number {
  font-weight: 700;
  color: #00677e;
  font-size: 18px;
}

.step-instruction {
  font-size: 16px;
  color: #725d42;
  padding: 12px;
  background: #f7f3df;
  border-radius: 12px;
}

.step-nav {
  display: flex;
  gap: 8px;
}

.sticky-note-card {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reflection-buttons {
  display: flex;
  gap: 8px;
}

.print-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 8px 0;
}

.a4-preview {
  width: 100%;
  max-width: 200px;
  padding: 12px;
  background: white;
  border: 2px solid #9a835a;
  border-radius: 4px;
  font-size: 12px;
}

.a4-header {
  text-align: center;
  font-weight: 700;
  margin-bottom: 8px;
  border-bottom: 1px dashed #9a835a;
}

.a4-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.a4-row {
  padding: 2px 0;
}

.print-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>