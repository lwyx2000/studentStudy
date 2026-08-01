<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { gradeLabel } from '../../utils/constants'
import { api } from '../../utils/api'
import { useBadgeStore, useGrowthStore, useMistakeStore, useParentStore, useTaskStore, useUserStore } from '../../stores'

const router = useRouter()
const userStore = useUserStore()
const name = ref(userStore.profile.name || '')
const grade = ref(userStore.profile.grade || 3)
const focus = ref(userStore.assessment.focusAttention)
const organization = ref(userStore.assessment.organization)
const emotion = ref(userStore.assessment.emotionalControl)
const planning = ref(userStore.assessment.planning)
const impulse = ref(userStore.assessment.impulseControl)
const generated = ref(false)

const sliders = computed(() => [
  { key: 'focus', label: '专注持久度', value: focus.value, update: (val: number) => (focus.value = val) },
  { key: 'organization', label: '物品整洁度', value: organization.value, update: (val: number) => (organization.value = val) },
  { key: 'emotion', label: '情绪克制力', value: emotion.value, update: (val: number) => (emotion.value = val) },
  { key: 'planning', label: '计划启动力', value: planning.value, update: (val: number) => (planning.value = val) },
  { key: 'impulse', label: '冲动抑制力', value: impulse.value, update: (val: number) => (impulse.value = val) },
])
const averageScore = computed(() => (focus.value + organization.value + emotion.value + planning.value + impulse.value) / 5)
const recommendedLevel = computed(() => Math.max(1, Math.min(5, Math.round(6 - averageScore.value))))

async function generateProfile() {
  userStore.setAssessment({
    focusAttention: focus.value,
    organization: organization.value,
    emotionalControl: emotion.value,
    planning: planning.value,
    impulseControl: impulse.value,
    recommendedLevel: recommendedLevel.value,
  })
  // 持久化到后端：保存评估并标记 onboarding 完成
  api.auth.saveAssessment({
    focusAttention: focus.value,
    organization: organization.value,
    emotionalControl: emotion.value,
    planning: planning.value,
    impulseControl: impulse.value,
    recommendedLevel: recommendedLevel.value,
    taskDensity: recommendedLevel.value >= 4 ? 'high' : recommendedLevel.value <= 2 ? 'low' : 'medium',
  }).catch(() => { /* offline 时本地保存 */ })
  userStore.completeOnboarding()
  await Promise.allSettled([
    useTaskStore().fetchFromApi(),
    useMistakeStore().fetchFromApi(),
    useBadgeStore().fetchFromApi(),
    useGrowthStore().fetchFromApi(),
    useParentStore().fetchFromApi(),
  ])
  generated.value = true
}
function enterDashboard() { router.push('/dashboard') }
function updateSlider(update: (val: number) => void, event: Event) {
  update(Number((event.target as HTMLInputElement).value))
}
</script>

<template>
  <main class="onboarding page">
    <section class="onboard-shell">
      <div class="tree-stage">
        <span class="eyebrow">🌱 注册与执行功能基线评估</span>
        <h1>{{ name || '孩子' }} 的小树正在发芽</h1>
        <p class="lead">用物理年级 + 5 项执行功能微量表建立温柔起点。结果只用于个性化任务密度，不代表智力水平。</p>
        <div class="tree-illustration" :class="`level-${recommendedLevel}`">
          <div class="sun">☀️</div>
          <div class="sprout">{{ recommendedLevel <= 2 ? '🌱' : recommendedLevel <= 4 ? '🌿' : '🌳' }}</div>
          <div class="soil">Level {{ recommendedLevel }} 推荐起点 · 平均 {{ averageScore.toFixed(1) }}</div>
        </div>
      </div>

      <div class="panel form-card">
        <div class="stepper">
          <div class="step"><b>1</b><h3>孩子资料</h3><p class="muted">称呼和物理年级</p></div>
          <div class="step"><b>2</b><h3>微型量表</h3><p class="muted">5 项执行功能</p></div>
          <div class="step"><b>3</b><h3>生成基线</h3><p class="muted">后续随数据修正</p></div>
        </div>

        <label class="field"><span>孩子称呼</span><input v-model="name" class="input" placeholder="例如 Leo" /></label>
        <label class="field"><span>物理年级：{{ gradeLabel(grade) }}</span><input v-model.number="grade" class="range" type="range" min="0" max="12" /></label>
        <label v-for="slider in sliders" :key="slider.key" class="field">
          <span>{{ slider.label }}：{{ slider.value }}</span>
          <input class="range" type="range" min="1" max="5" :value="slider.value" @input="updateSlider(slider.update, $event)" />
        </label>

        <transition name="fade-up">
          <div v-if="generated" class="result-card">
            <strong>{{ name }} 的物理年级：{{ gradeLabel(grade) }}</strong>
            <span>当前执行功能推荐起点：Level {{ recommendedLevel }} 难度</span>
          </div>
        </transition>
        <p class="note">💡 此结果仅用于定制每日任务密度；打卡、错题、物品流失数据会持续修正推荐起点。</p>
        <button class="btn" @click="generated ? enterDashboard() : generateProfile()">{{ generated ? '进入协同仪表盘' : '生成档案' }}</button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.onboarding { min-height: 100vh; padding: 28px; background: radial-gradient(circle at 20% 10%, #fff3a9, transparent 28rem), var(--bg); }
.onboard-shell { display: grid; grid-template-columns: 40% 1fr; gap: 28px; max-width: 1220px; margin: 0 auto; align-items: stretch; }
.tree-stage, .form-card { border-radius: 36px; }
.tree-stage { padding: 34px; background: linear-gradient(180deg,#fffdf7,#eef9df); border: 1px solid var(--line); box-shadow: var(--shadow); overflow: hidden; }
.tree-illustration { margin-top: 28px; min-height: 420px; border-radius: 34px; background: linear-gradient(180deg,#bdefff 0%,#efffd9 68%,#d9bb85 69%); display: grid; place-items: center; position: relative; }
.sun { position: absolute; right: 28px; top: 24px; font-size: 48px; }
.sprout { font-size: 118px; filter: drop-shadow(0 18px 20px rgba(16,110,0,.18)); }
.soil { position: absolute; bottom: 24px; background: rgba(255,255,255,.78); padding: 10px 16px; border-radius: 999px; font-weight: 900; color: var(--primary); }
.form-card { display: flex; flex-direction: column; gap: 18px; }
.field { display: grid; gap: 8px; font-weight: 900; }
.result-card { display: flex; flex-direction: column; gap: 8px; padding: 16px; border-radius: 22px; background: #ecffd9; color: var(--primary); border: 1px solid #c7edbd; }
.note { padding: 14px; border-radius: 18px; background: #fff8d9; color: #6e5e00; line-height: 1.6; }
.fade-up-enter-active, .fade-up-leave-active { transition: opacity .25s ease, transform .25s ease; }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(8px); }
@media (max-width: 900px) { .onboard-shell { grid-template-columns: 1fr; } }
</style>
