<script setup lang="ts">
import { ref } from 'vue'
import { useTaskStore } from '../../stores'

const taskStore = useTaskStore()

const editTitle = ref(taskStore.currentWeekHabit.title)
const editWeek = ref(taskStore.currentWeekHabit.weekNumber)
const newStep = ref('')
const newHabitTitle = ref('')

function saveHabit() {
  taskStore.updateCurrentHabit({
    title: editTitle.value.trim() || taskStore.currentWeekHabit.title,
    weekNumber: editWeek.value,
  })
}

function addStep() {
  if (!newStep.value.trim()) return
  taskStore.addStepToHabit(newStep.value.trim())
  newStep.value = ''
}

function removeStep(index: number) {
  taskStore.removeHabitStep(index)
}

function createHabit() {
  if (!newHabitTitle.value.trim()) return
  taskStore.createNewHabit(newHabitTitle.value.trim())
  editTitle.value = taskStore.currentWeekHabit.title
  editWeek.value = taskStore.currentWeekHabit.weekNumber
  newHabitTitle.value = ''
}

async function loadHistory(id: string) {
  await taskStore.loadHabitFromHistory(id)
  editTitle.value = taskStore.currentWeekHabit.title
  editWeek.value = taskStore.currentWeekHabit.weekNumber
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">✅ 习惯管理</span>
        <h1>管理每周核心习惯</h1>
        <p class="lead">设定每周主线习惯 SOP，编辑步骤，查看历史习惯记录。习惯会在孩子端「每日打卡」页面展示。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center">
        <div class="card-title">
          <h2>当前习惯</h2>
          <span class="tag">第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span>
        </div>
        <strong style="font-size:22px;margin:8px 0">{{ taskStore.currentWeekHabit.title }}</strong>
        <span class="muted" style="font-weight:700">{{ taskStore.currentWeekHabit.steps.length }} 个步骤</span>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>编辑当前习惯</h2>
          <button class="btn secondary" @click="saveHabit">保存</button>
        </div>
        <label style="font-weight:800;display:block;margin-bottom:4px">习惯名称</label>
        <input v-model="editTitle" class="input" style="margin-bottom:12px" placeholder="习惯名称" />
        <label style="font-weight:800;display:block;margin-bottom:4px">周数</label>
        <input v-model.number="editWeek" class="input" type="number" min="1" style="margin-bottom:16px;width:120px" />

        <h3 style="margin:16px 0 10px">步骤列表</h3>
        <div v-if="taskStore.currentWeekHabit.steps.length" class="list" style="margin-bottom:12px">
          <div
            v-for="(step, index) in taskStore.currentWeekHabit.steps"
            :key="index"
            class="list-row"
            style="justify-content:flex-start;gap:12px"
          >
            <b class="step-num">{{ step.order }}</b>
            <span style="flex:1">{{ step.instruction }}</span>
            <button class="btn ghost" style="padding:6px 12px;font-size:12px;color:#c00" @click="removeStep(index)">删除</button>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:12px">暂无步骤，请添加</p>

        <div style="display:flex;gap:8px">
          <input v-model="newStep" class="input" placeholder="新步骤说明" @keyup.enter="addStep" />
          <button class="btn" :disabled="!newStep.trim()" @click="addStep">添加</button>
        </div>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>创建新习惯</h2>
          <span class="tag">当前第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span>
        </div>
        <p class="lead" style="margin-bottom:12px;font-size:14px">创建后将自动归档当前习惯到历史记录。</p>
        <div style="display:flex;gap:8px">
          <input v-model="newHabitTitle" class="input" placeholder="新习惯名称（如：整理书包 SOP）" @keyup.enter="createHabit" />
          <button class="btn secondary" :disabled="!newHabitTitle.trim()" @click="createHabit">创建</button>
        </div>

        <h3 style="margin:24px 0 10px">历史习惯</h3>
        <div v-if="taskStore.habitHistory.length" class="list">
          <div
            v-for="habit in taskStore.habitHistory"
            :key="habit.id"
            class="list-row"
            :style="{ cursor: 'pointer' }"
            @click="loadHistory(habit.id)"
          >
            <div>
              <strong>{{ habit.title }}</strong>
              <span class="muted" style="display:block;font-size:13px">第 {{ habit.weekNumber }} 周 · {{ habit.steps.length }} 个步骤</span>
            </div>
            <span class="tag" style="flex-shrink:0;font-size:12px">载入</span>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:16px;font-size:14px">暂无历史习惯。创建新习惯时当前习惯会自动归档。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.step-num {
  display: inline-grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  flex-shrink: 0;
}
</style>
