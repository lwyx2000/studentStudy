<script setup lang="ts">
import { computed } from 'vue'
import { categoryLabels, difficultyLabels } from '../../utils/constants'
import { useChildSelectStore, useMistakeStore, useParentStore, useTaskStore, useUserStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const parentStore = useParentStore()
const taskStore = useTaskStore()
const userStore = useUserStore()
const mistakeStore = useMistakeStore()
const childSelectStore = useChildSelectStore()
const selectedChild = computed(() => childSelectStore.selectedChild)

const difficultyLabel = computed(() => difficultyLabels[parentStore.settings.difficultyLevel - 1] || '阳光')

const completedCount = computed(() => taskStore.todayTasks.filter(t => t.status === 'completed').length)
const progressPercent = computed(() => Math.round((taskStore.weeklyProgress / Math.max(taskStore.todayTasks.length, 1)) * 100))

function toggle(key: 'dailyReminder' | 'achievementNotification' | 'weeklyReport' | 'schoolSync') {
  parentStore.updateSettings({ [key]: !parentStore.settings[key] })
}

function updateDifficulty(event: Event) {
  parentStore.updateSettings({ difficultyLevel: Number((event.target as HTMLInputElement).value) })
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🧭 家长控制中心</span>
        <h1>观察孩子，调任务密度</h1>
        <p class="lead">查看孩子今日任务完成情况、错题积累和习惯数据。在下方设置难度天气和通知边界，所有设置本地保存。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>{{ selectedChild?.name ?? userStore.profile.name ?? 'Leo' }} 的今日概览</h2>
          <span class="tag">☀️ {{ selectedChild?.sunlightPoints ?? userStore.sunlightPoints }} 阳光值</span>
        </div>
        <div class="kpi">
          <strong>{{ completedCount }}/{{ taskStore.todayTasks.length }}</strong>
          <span>今日已完成任务</span>
        </div>
        <div class="progress" style="margin-top: 12px;">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>
        <p class="lead">
          Lv{{ userStore.assessment.recommendedLevel }} · {{ userStore.profile.grade }}年级
          · 题库 {{ mistakeStore.records.length }} 题
        </p>
      </div>
    </section>

    <ChildSelector />

    <!-- 孩子任务完成情况 -->
    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>📋 今日任务清单</h2>
          <span class="tag">{{ completedCount }}/{{ taskStore.todayTasks.length }} 完成</span>
        </div>
        <div v-if="taskStore.todayTasks.length" class="list">
          <div
            v-for="task in taskStore.todayTasks"
            :key="task.id"
            class="list-row"
            :style="task.status === 'completed' ? 'opacity:.7;background:#ecffd9' : ''"
          >
            <div style="display:flex;align-items:center;gap:12px;min-width:0">
              <span style="font-size:24px;flex-shrink:0">{{ task.icon }}</span>
              <div style="min-width:0">
                <strong>{{ task.title }}</strong>
                <span class="muted" style="display:block;font-size:13px">{{ task.description }}</span>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
              <span class="mini-tag">{{ categoryLabels[task.type] || task.type }}</span>
              <span
                class="tag"
                :style="task.status === 'completed'
                  ? 'background:#d9f5c8;color:var(--primary)'
                  : 'background:var(--surface-2);color:var(--muted)'"
              >
                {{ task.status === 'completed' ? '✓ 已完成' : '○ 待完成' }}
              </span>
            </div>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:24px">
          暂无今日任务
        </p>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>📊 本周习惯进度</h2>
          <span class="tag">第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span>
        </div>
        <p class="lead" style="margin-bottom:12px">
          主线习惯：<strong>{{ taskStore.currentWeekHabit.title }}</strong>
        </p>
        <div class="progress" style="margin-bottom:16px">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>
        <div class="list">
          <div
            v-for="step in taskStore.currentWeekHabit.steps"
            :key="step.order"
            class="list-row"
            style="justify-content:flex-start;gap:12px"
          >
            <b style="display:inline-grid;place-items:center;width:28px;height:28px;border-radius:999px;background:var(--primary);color:#fff;font-size:14px;flex-shrink:0">
              {{ step.order }}
            </b>
            <span>{{ step.instruction }}</span>
          </div>
        </div>

        <!-- 错题概览 -->
        <div class="card-title" style="margin-top:20px">
          <h2>📚 错题积累</h2>
          <span class="tag">{{ mistakeStore.records.length }} 题</span>
        </div>
        <div v-if="mistakeStore.records.length" class="list">
          <div
            v-for="record in mistakeStore.records.slice(0, 3)"
            :key="record.id"
            class="list-row"
          >
            <span>📸 {{ record.subject }}</span>
            <span v-if="record.subjectTag" class="tag" style="font-size:12px">{{ record.subjectTag }}</span>
            <span class="muted" style="font-size:12px">
              {{ new Date(record.createdAt).toLocaleDateString() }}
            </span>
          </div>
          <p v-if="mistakeStore.records.length > 3" class="muted" style="text-align:center;font-size:13px">
            还有 {{ mistakeStore.records.length - 3 }} 条错题记录…
          </p>
        </div>
        <p v-else class="muted" style="text-align:center;padding:16px">暂无错题记录</p>
      </div>
    </section>

    <!-- 设置区域 -->
    <section class="grid-3">
      <button class="soft-card setting" @click="toggle('dailyReminder')">
        <div class="icon-tile">🔔</div>
        <h2>每日小岛提醒</h2>
        <p class="lead">{{ parentStore.settings.dailyReminder ? '已开启' : '已关闭' }}：只提醒环境准备，不替孩子催作业。</p>
      </button>
      <button class="soft-card setting" @click="toggle('achievementNotification')">
        <div class="icon-tile">🎆</div>
        <h2>成就烟花</h2>
        <p class="lead">{{ parentStore.settings.achievementNotification ? '已开启' : '已关闭' }}：里程碑时发送温和庆祝反馈。</p>
      </button>
      <button class="soft-card setting" @click="toggle('schoolSync')">
        <div class="icon-tile">🏫</div>
        <h2>学校共享</h2>
        <p class="lead">{{ parentStore.settings.schoolSync ? '已开启' : '已关闭' }}：仅分享匿名化成长趋势。</p>
      </button>
    </section>

    <!-- 难度 + 自查 -->
    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>难度天气</h2>
          <span class="tag">{{ difficultyLabel }} · Level {{ parentStore.settings.difficultyLevel }}</span>
        </div>
        <input
          :value="parentStore.settings.difficultyLevel"
          class="range"
          min="1"
          max="3"
          type="range"
          @input="updateDifficulty"
        />
        <p class="lead">1 阳光 · 2 微风 · 3 挑战 — 影响每日任务数量和复杂度</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>家长自查红线</h2>
          <span class="tag">非侵入提示</span>
        </div>
        <div class="list">
          <div class="list-row">
            <span>今天是否克制了催促？</span>
            <b>待勾选</b>
          </div>
          <div class="list-row">
            <span>今天是否让孩子自己收尾？</span>
            <b>待勾选</b>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.setting {
  text-align: left;
  color: inherit;
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
</style>
