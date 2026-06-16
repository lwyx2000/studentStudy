<script setup lang="ts">
import { ref } from 'vue'
import { useChildSelectStore, useParentStore } from '../../stores'
import { api } from '../../utils/api'
import type { TaskCategory } from '../../types'
import ChildSelector from '../../components/ChildSelector.vue'

const parentStore = useParentStore()
const childSelectStore = useChildSelectStore()

const title = ref('')
const description = ref('')
const type = ref<TaskCategory>('study_habit')
const rewardPoints = ref(20)
const icon = ref('☝️')

const categoryOptions: { value: TaskCategory; label: string; icon: string }[] = [
  { value: 'morning_routine', label: '晨间惯例', icon: '🌅' },
  { value: 'study_habit', label: '学习习惯', icon: '📖' },
  { value: 'life_skill', label: '生活技能', icon: '🧹' },
  { value: 'exercise', label: '运动', icon: '⚽' },
  { value: 'reflection', label: '反思', icon: '💭' },
]

const iconOptions = ['☝️', '📖', '✏️', '🎒', '🧠', '🏃', '🧹', '💭', '🌟', '📝', '🔔', '🎯']

function createTask() {
  if (!title.value.trim()) return
  const childId = childSelectStore.selectedChildId ?? undefined
  // 调用后端直接创建任务到孩子账号
  if (childId) {
    api.tasks.create({
      title: title.value.trim(),
      type: type.value,
      description: description.value.trim(),
      rewardPoints: rewardPoints.value,
      icon: icon.value,
      childId,
    }).catch(() => {})
  }
  // 同时保存到本地模板供预览
  parentStore.addTaskTemplate({
    title: title.value.trim(),
    description: description.value.trim(),
    type: type.value,
    rewardPoints: rewardPoints.value,
    icon: icon.value,
    status: 'pending',
  })
  title.value = ''
  description.value = ''
  type.value = 'study_habit'
  rewardPoints.value = 20
  icon.value = '☝️'
}

function deleteTask(id: string) {
  parentStore.deleteTaskTemplate(id)
}
</script>

<template>
  <div class="page">
    <ChildSelector />
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📋 任务管理中心</span>
        <h1>创建和管理孩子的每日任务</h1>
        <p class="lead">自定义任务会出现在孩子的仪表盘和每日打卡页面中。按类别整理任务，帮助孩子建立结构化的日常习惯。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>任务模板库</h2>
          <span class="tag">{{ parentStore.parentTaskTemplates.length }} 个模板</span>
        </div>
        <div class="kpi">
          <strong>{{ parentStore.parentTaskTemplates.length }}</strong>
          <span>已创建任务模板</span>
        </div>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <span
            v-for="cat in categoryOptions"
            :key="cat.value"
            class="tag"
          >
            {{ cat.icon }} {{ cat.label }}
          </span>
        </div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>添加新任务</h2>
          <span class="tag">{{ categoryOptions.find(c => c.value === type)?.icon }} {{ categoryOptions.find(c => c.value === type)?.label }}</span>
        </div>
        <label style="display:block;font-weight:800;margin-bottom:6px">
          任务标题
          <input
            v-model="title"
            class="input"
            style="margin-top:6px"
            placeholder="例如：晨间朗读 10 分钟"
          />
        </label>
        <label style="display:block;font-weight:800;margin-top:14px;margin-bottom:6px">
          任务描述
          <input
            v-model="description"
            class="input"
            style="margin-top:6px"
            placeholder="具体要求和步骤说明"
          />
        </label>
        <div class="grid-2" style="margin-top:14px">
          <label style="font-weight:800">
            任务类别
            <select v-model="type" class="input" style="margin-top:6px">
              <option
                v-for="cat in categoryOptions"
                :key="cat.value"
                :value="cat.value"
              >
                {{ cat.icon }} {{ cat.label }}
              </option>
            </select>
          </label>
          <label style="font-weight:800">
            奖励阳光值
            <input
              v-model.number="rewardPoints"
              class="input"
              style="margin-top:6px"
              type="number"
              min="5"
              max="100"
              step="5"
            />
          </label>
        </div>
        <label style="display:block;font-weight:800;margin-top:14px;margin-bottom:6px">
          图标选择
          <div class="icon-picker" style="margin-top:6px">
            <button
              v-for="ico in iconOptions"
              :key="ico"
              class="icon-btn"
              :class="{ active: icon === ico }"
              @click="icon = ico"
            >
              {{ ico }}
            </button>
          </div>
        </label>
        <button
          class="btn"
          style="margin-top:20px;width:100%"
          :disabled="!title.trim()"
          @click="createTask"
        >
          ✨ 创建任务
        </button>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>已创建任务</h2>
          <span class="tag">{{ parentStore.parentTaskTemplates.length }} 项</span>
        </div>
        <div v-if="parentStore.parentTaskTemplates.length" class="list">
          <div
            v-for="template in parentStore.parentTaskTemplates"
            :key="template.id"
            class="list-row task-row"
          >
            <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
              <span style="font-size:28px;flex-shrink:0">{{ template.icon }}</span>
              <div style="min-width:0">
                <strong>{{ template.title }}</strong>
                <span class="muted" style="display:block;font-size:13px">
                  {{ template.description || '无描述' }}
                </span>
                <div style="display:flex;gap:6px;margin-top:4px">
                  <span class="mini-tag">
                    {{ categoryOptions.find(c => c.value === template.type)?.label || template.type }}
                  </span>
                  <span class="mini-tag">☀️ +{{ template.rewardPoints }}</span>
                </div>
              </div>
            </div>
            <button
              class="btn ghost"
              style="padding:6px 12px;font-size:13px;flex-shrink:0"
              @click="deleteTask(template.id)"
            >
              删除
            </button>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">
          还没有创建任务模板。在左侧表单中创建第一个任务吧 ✨
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.icon-btn {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  border: 2px solid var(--line);
  background: #fff;
  font-size: 22px;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all .12s ease;
}
.icon-btn:hover {
  border-color: var(--primary);
  background: #ecffd9;
}
.icon-btn.active {
  border-color: var(--primary);
  background: #d9f5c8;
  box-shadow: 0 4px 12px rgba(16, 110, 0, .18);
}
.mini-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
}
.task-row {
  align-items: center;
}
button:disabled {
  opacity: .5;
  cursor: not-allowed;
}
</style>
