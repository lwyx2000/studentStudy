<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore, useBadgeStore } from '../../stores'
import { Button, Card, Title, Select, Divider, Input } from 'animal-island-vue'

const userStore = useUserStore()
const badgeStore = useBadgeStore()

const selectedReward = ref('family_movie')
const showConfetti = ref(false)

const rewardOptions = [
  { label: '周五亲子电影夜', value: 'family_movie' },
  { label: '免家务一天', value: 'no_chore' },
  { label: '1小时乐高组装时间', value: 'lego_hour' },
  { label: '额外游戏时间30分钟', value: 'game_30min' },
  { label: '给100元现金', value: 'cash_100' },
]

const isCashReward = computed(() => selectedReward.value === 'cash_100')

const covenantGoal = ref('连续7天完成每日习惯打卡')

const badges = [
  { id: 'streak_3', name: '3日坚持勋章', icon: 'icon-miles', color: 'app-red', unlocked: true, requirement: '连续3天完成打卡' },
  { id: 'calm_down', name: '冷静勋章', icon: 'icon-design', color: 'app-teal', unlocked: true, requirement: '情绪克制达标' },
  { id: 'helper', name: '小帮手勋章', icon: 'icon-shopping', color: 'app-orange', unlocked: true, requirement: '帮助他人3次' },
  { id: 'mirror', name: '镜面空间勋章', icon: 'icon-design', color: 'app-blue', unlocked: false, requirement: '连续7天整理书桌' },
  { id: 'focus', name: '专注达人勋章', icon: 'icon-design', color: 'purple', unlocked: false, requirement: '番茄钟完成10次' },
  { id: 'zero_loss', name: '零丢失勋章', icon: 'icon-design', color: 'app-green', unlocked: false, requirement: '30天零物品丢失' },
]

function unlockBadge(id: string) {
  const badge = badges.find(b => b.id === id)
  if (badge) {
    badge.unlocked = true
    badge.icon = badge.id === 'mirror' ? 'icon-diy' : badge.icon
    showConfetti.value = true
    setTimeout(() => { showConfetti.value = false }, 3000)
    userStore.addSunlightPoints(50)
  }
}

function createCovenant() {
  badgeStore.addCovenant({
    id: Date.now().toString(),
    goal: covenantGoal.value,
    reward: selectedReward.value,
    childSignature: userStore.profile.name,
    parentSignature: '家长',
    createdAt: new Date().toISOString(),
    status: 'active',
  })
}
</script>

<template>
  <div class="badge-room">
    <Title size="large" color="app-yellow">成长契约与勋章馆</Title>

    <div class="main-grid">
      <div class="covenant-section">
        <Card color="warm-peach-pink" type="title">
          <template #title>
            <Title size="middle" color="warm-peach-pink">家庭成长契约</Title>
          </template>
          <div class="covenant-document">
            <div class="covenant-paper">
              <div class="covenant-pin">📌</div>
              <h3 class="covenant-title-text">家庭法案</h3>
              <div class="covenant-body">
                <p class="covenant-goal">目标: {{ covenantGoal }}</p>
                <p class="covenant-reward">奖励: {{ rewardOptions.find(r => r.value === selectedReward)?.label }}</p>
              </div>
              <div class="covenant-signatures">
                <div class="signature">
                  <span class="sig-label">家长签名</span>
                  <span class="sig-handwriting">妈妈 & 爸爸</span>
                </div>
                <div class="signature">
                  <span class="sig-label">孩子签名</span>
                  <span class="sig-handwriting">{{ userStore.profile.name }}</span>
                </div>
              </div>
            </div>
          </div>

          <Divider type="dashed-brown" />

          <div class="covenant-generator">
            <Title size="small" color="app-orange">契约生成器</Title>
            <div class="generator-form">
              <div class="form-group">
                <label>目标描述</label>
                <Input v-model="covenantGoal" placeholder="如：连续7天完成每日习惯打卡" shadow />
              </div>
              <div class="form-group">
                <label>选择奖励</label>
                <Select :options="rewardOptions as any" v-model="selectedReward" />
              </div>
              <Card v-if="isCashReward" color="app-red" type="dashed">
                <p class="warning-nudge">循证医学表明，过度的物质奖励会削弱孩子的内在驱动力，建议选择体验类奖励如亲子电影夜或乐高时间。</p>
              </Card>
              <Button type="primary" block @click="createCovenant">拟定新契约</Button>
            </div>
          </div>
        </Card>
      </div>

      <div class="badge-section">
        <Card color="app-green" type="title">
          <template #title>
            <Title size="middle" color="app-green">勋章展览馆</Title>
          </template>
          <div class="honeycomb-grid">
            <div
              v-for="badge in badges"
              :key="badge.id"
              class="hex-badge"
              :class="{ unlocked: badge.unlocked, locked: !badge.unlocked }"
              @click="!badge.unlocked ? unlockBadge(badge.id) : null"
            >
              <div class="hex-shape">
                <span class="emoji-icon">🔒</span>
              </div>
              <span class="badge-name">{{ badge.name }}</span>
              <div v-if="!badge.unlocked" class="unlock-label">点击解锁!</div>
            </div>
          </div>
        </Card>

        <Card type="dashed">
          <p>勋章通过完成每日习惯打卡、整理书桌、情绪管理等行为解锁。每个勋章代表一个成长里程碑!</p>
        </Card>
      </div>
    </div>

    <div v-if="showConfetti" class="confetti-overlay">
      <div v-for="i in 40" :key="i" class="confetti-piece" :style="{
        left: Math.random() * 100 + '%',
        animationDelay: Math.random() * 2 + 's',
        backgroundColor: ['#fc736d', '#f7cd67', '#82d5bb', '#889df0', '#b77dee', '#8ac68a'][Math.floor(Math.random() * 6)],
        width: Math.random() * 8 + 4 + 'px',
        height: Math.random() * 8 + 4 + 'px',
        borderRadius: Math.random() > 0.5 ? '50%' : '0',
      }"></div>
    </div>
  </div>
</template>



<style scoped>
.badge-room {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

.main-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 16px;
}

.covenant-paper {
  padding: 24px;
  background: #f7f3df;
  border: 2px solid #9a835a;
  border-radius: 4px;
  position: relative;
}

.covenant-pin {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 20px;
}

.covenant-title-text {
  text-align: center;
  font-family: 'Caveat', cursive, sans-serif;
  font-size: 24px;
  color: #725d42;
}

.covenant-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 16px 0;
}

.covenant-goal,
.covenant-reward {
  font-size: 16px;
  color: #725d42;
}

.covenant-signatures {
  display: flex;
  justify-content: space-around;
  margin-top: 24px;
}

.signature {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.sig-label {
  font-size: 12px;
  color: #9a835a;
}

.sig-handwriting {
  font-family: 'Caveat', cursive, sans-serif;
  font-size: 18px;
  color: #106e00;
}

.generator-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-weight: 600;
  color: #725d42;
}

.warning-nudge {
  color: #ba1a1a;
  font-size: 14px;
  padding: 8px;
}

.honeycomb-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  padding: 16px;
}

.hex-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.hex-shape {
  width: 80px;
  height: 80px;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  transition: all 0.3s;
}

.hex-badge.unlocked .hex-shape {
  background: #8ac68a;
  color: white;
}

.hex-badge.locked .hex-shape {
  background: #e4e3d8;
  color: #9a835a;
  border: 2px dashed #9a835a;
}

.hex-badge.locked:hover .hex-shape {
  transform: scale(1.1);
  background: #fbe270;
}

.badge-name {
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  max-width: 90px;
}

.unlock-label {
  font-size: 11px;
  color: #106e00;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.confetti-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
}

.confetti-piece {
  position: absolute;
  top: -10px;
  animation: fall 3s ease-out forwards;
}

@keyframes fall {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}
</style>