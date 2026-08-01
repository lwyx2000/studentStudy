<script setup lang="ts">
import { onMounted } from 'vue'
import { useBadgeStore } from '../../stores'

const badgeStore = useBadgeStore()

function progressPercent(badge: any): number {
  if (badge.unlocked) return 100
  if (!badge.requirementValue || badge.requirementValue <= 0) return 0
  return Math.min(100, Math.round(((badge.progress ?? 0) / badge.requirementValue) * 100))
}

onMounted(() => {
  badgeStore.checkAndUnlock()
})
</script>

<template>
  <div class="page">
    <div v-if="badgeStore.confettiActive" class="confetti">🎉 🏅 ✨ 🎊</div>

    <!-- Newly unlocked notification -->
    <section v-if="badgeStore.lastNewlyUnlocked.length" class="panel unlock-notice">
      <div class="card-title">
        <h2>🎉 恭喜解锁新勋章！</h2>
      </div>
      <div class="new-unlocks">
        <div v-for="b in badgeStore.lastNewlyUnlocked" :key="b.id" class="new-unlock-item">
          <span style="font-size:32px">{{ b.icon }}</span>
          <strong>{{ b.name }}</strong>
        </div>
      </div>
    </section>

    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🏅 勋章馆</span>
        <h1>把短期打卡变成内在成就</h1>
        <p class="lead">勋章馆用明亮反馈庆祝真实努力。满足条件自动解锁，每次解锁都有阳光值奖励。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>已解锁 {{ badgeStore.unlockedCount }}/{{ badgeStore.badges.length }}</h2>
          <span class="tag">镜面空间勋章</span>
        </div>
        <div class="celebrate">🎉🏅🎉</div>
      </div>
    </section>

    <section>
      <div class="panel">
        <div class="card-title">
          <h2>蜂巢勋章陈列架</h2>
          <span class="tag">满足条件自动解锁</span>
        </div>
        <div class="honeycomb">
          <button
            v-for="badge in badgeStore.badges"
            :key="badge.id"
            class="badge-cell"
            :class="{ locked: !badge.unlocked }"
            @click="badgeStore.unlockBadge(badge.id)"
          >
            <span>{{ badge.icon }}</span>
            <small>{{ badge.name }}</small>
            <!-- Progress bar for locked badges -->
            <div v-if="!badge.unlocked && badge.requirementValue" class="badge-mini-progress">
              <div class="mini-track">
                <span class="mini-fill" :style="{ width: `${progressPercent(badge)}%` }"></span>
              </div>
              <small>{{ badge.progress ?? 0 }}/{{ badge.requirementValue }}</small>
            </div>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.celebrate {
  height: 190px;
  display: grid;
  place-items: center;
  font-size: 72px;
  border-radius: 28px;
  background: linear-gradient(135deg, #fff4bc, #dcffd5);
}
.confetti {
  position: fixed;
  inset: 0;
  z-index: 99;
  display: grid;
  place-items: center;
  font-size: 80px;
  background: rgba(255, 255, 255, .35);
  animation: pop .9s ease infinite alternate;
}
.badge-cell {
  border: 0;
  color: var(--ink);
}
.badge-cell span {
  display: block;
  font-size: 26px;
}
.badge-cell small {
  font-weight: 900;
}
.badge-mini-progress {
  width: 100%;
  margin-top: 2px;
  text-align: center;
}
.mini-track {
  height: 4px;
  border-radius: 2px;
  background: var(--surface-2, #eee);
  overflow: hidden;
}
.mini-fill {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--primary), #8bc34a);
  transition: width .3s ease;
}
.badge-mini-progress small {
  font-size: 9px;
  color: var(--muted);
}
.unlock-notice {
  border: 2px solid #4caf50;
  background: #e8f5e9;
}
.new-unlocks {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}
.new-unlock-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 18px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #c8e6c9;
}
@keyframes pop {
  from { transform: scale(.95) }
  to { transform: scale(1.02) }
}
button:disabled {
  opacity: .5;
  cursor: not-allowed;
}
</style>
