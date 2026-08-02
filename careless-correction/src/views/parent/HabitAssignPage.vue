<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useTaskStore, useUserStore } from '../../stores'
import type { SOPStep } from '../../types'

const taskStore = useTaskStore()
const userStore = useUserStore()

onMounted(() => { taskStore.fetchHabits() })

const showForm = ref(false)
const title = ref('')
const description = ref('')
const icon = ref('✅')
const rewardPoints = ref(10)
const weekNumber = ref(1)
const stepsText = ref('')

const iconOptions = ['✅', '📚', '🎒', '🧹', '📝', '🧘', '🦷', '💤', '🍎', '🏃']

const assignedHabits = computed(() => taskStore.habitAssignments)

function openForm() {
  title.value = ''
  description.value = ''
  icon.value = '✅'
  rewardPoints.value = 10
  weekNumber.value = 1
  stepsText.value = ''
  showForm.value = true
}

function submitAssignment() {
  if (!title.value.trim()) return
  const steps: SOPStep[] = stepsText.value
    .split('\n')
    .filter(s => s.trim())
    .map((s, i) => ({ order: i + 1, instruction: s.trim() }))

  taskStore.addHabitAssignment({
    childId: userStore.profile.id,
    parentId: userStore.profile.id,
    title: title.value.trim(),
    description: description.value.trim(),
    icon: icon.value,
    rewardPoints: rewardPoints.value,
    weekNumber: weekNumber.value,
    steps,
    active: true,
  })
  showForm.value = false
}

function deactivate(id: string) {
  taskStore.deactivateHabit(id)
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📋 习惯布置中心</span>
        <h1>布置习惯，不替孩子完成</h1>
        <p class="lead">家长在此为孩子指定每周核心习惯和执行步骤，孩子端会自动同步显示。布置时请遵循"只调密度，不代劳"原则。</p>
      </div>
    </section>

    <section class="toolbar">
      <button class="btn-primary" @click="openForm">+ 布置新习惯</button>
      <span class="stat">当前活跃：{{ taskStore.activeHabits.length }} 个</span>
    </section>

    <section v-if="showForm" class="panel form-panel">
      <h2>📝 布置习惯</h2>
      <div class="form-grid">
        <label>习惯名称<input v-model="title" placeholder="如：指读圈号" /></label>
        <label>说明<input v-model="description" placeholder="简短描述这个习惯的目的" /></label>
        <label>图标
          <div class="icon-picker">
            <button v-for="ic in iconOptions" :key="ic" :class="['icon-btn', { selected: icon === ic }]" @click="icon = ic">{{ ic }}</button>
          </div>
        </label>
        <label>奖励阳光值<input v-model.number="rewardPoints" type="number" min="1" max="100" /></label>
        <label>周数<input v-model.number="weekNumber" type="number" min="1" max="52" /></label>
        <label>执行步骤（每行一步）<textarea v-model="stepsText" rows="5" placeholder="第1步：把作业本翻开&#10;第2步：用手指指着题目逐字读&#10;第3步：圈出关键词" /></label>
      </div>
      <div class="form-actions">
        <button class="btn-primary" @click="submitAssignment">确认布置</button>
        <button class="btn-soft" @click="showForm = false">取消</button>
      </div>
    </section>

    <section class="habit-list">
      <h2>已布置习惯</h2>
      <div v-if="assignedHabits.length === 0" class="empty">还没有布置任何习惯，点击上方按钮开始吧！</div>
      <div v-for="habit in assignedHabits" :key="habit.id" :class="['habit-card', { inactive: !habit.active }]">
        <div class="habit-header">
          <span class="habit-icon">{{ habit.icon }}</span>
          <div class="habit-info">
            <strong>{{ habit.title }}</strong>
            <span class="habit-meta">第{{ habit.weekNumber }}周 · {{ habit.rewardPoints }}☀️ · {{ habit.active ? '活跃' : '已停用' }}</span>
          </div>
        </div>
        <p v-if="habit.description" class="habit-desc">{{ habit.description }}</p>
        <ol v-if="habit.steps.length" class="step-list">
          <li v-for="step in habit.steps" :key="step.order">{{ step.instruction }}</li>
        </ol>
        <div class="habit-actions">
          <span class="habit-date">{{ new Date(habit.assignedAt).toLocaleDateString('zh-CN') }}</span>
          <button v-if="habit.active" class="btn-stop" @click="deactivate(habit.id)">停用</button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.stat { font-weight: 800; color: var(--muted); font-size: 14px; }
.btn-primary { display: inline-flex; align-items: center; gap: 6px; padding: 12px 20px; border-radius: 16px; background: var(--primary); color: #fff; font-weight: 850; border: none; cursor: pointer; }
.btn-primary:hover { filter: brightness(1.1); }
.btn-soft { padding: 10px 18px; border-radius: 14px; background: #f3efe2; color: var(--ink); font-weight: 800; border: none; cursor: pointer; }
.btn-stop { padding: 6px 14px; border-radius: 10px; background: #fee2e2; color: #b91c1c; font-weight: 800; font-size: 12px; border: none; cursor: pointer; }
.form-panel { background: #fff; border-radius: 22px; padding: 24px; border: 1px solid var(--line); margin-bottom: 24px; }
.form-panel h2 { margin: 0 0 16px; }
.form-grid { display: grid; gap: 16px; }
.form-grid label { display: flex; flex-direction: column; gap: 6px; font-weight: 800; font-size: 14px; }
.form-grid input, .form-grid textarea { padding: 10px 14px; border-radius: 12px; border: 1px solid var(--line); font-size: 15px; font-family: inherit; }
.icon-picker { display: flex; flex-wrap: wrap; gap: 8px; }
.icon-btn { width: 40px; height: 40px; border-radius: 12px; border: 2px solid transparent; background: #f3efe2; font-size: 20px; cursor: pointer; display: grid; place-items: center; }
.icon-btn.selected { border-color: var(--primary); background: #e6f9e2; }
.form-actions { display: flex; gap: 12px; margin-top: 20px; }
.habit-list h2 { margin-bottom: 16px; }
.empty { color: var(--muted); padding: 24px; text-align: center; }
.habit-card { background: #fff; border-radius: 18px; padding: 18px; border: 1px solid var(--line); margin-bottom: 12px; }
.habit-card.inactive { opacity: 0.55; }
.habit-header { display: flex; align-items: center; gap: 12px; }
.habit-icon { font-size: 28px; }
.habit-info { display: flex; flex-direction: column; gap: 2px; }
.habit-info strong { font-size: 16px; }
.habit-meta { font-size: 12px; color: var(--muted); font-weight: 700; }
.habit-desc { margin: 8px 0 4px; color: var(--muted); font-size: 13px; }
.step-list { margin: 8px 0 4px; padding-left: 20px; font-size: 14px; }
.step-list li { margin-bottom: 4px; }
.habit-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }
.habit-date { font-size: 12px; color: var(--muted); }
</style>
