<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useBadgeStore, useChildSelectStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const badgeStore = useBadgeStore()
const childSelectStore = useChildSelectStore()
const selectedChildId = computed(() => childSelectStore.selectedChildId)

async function loadBadges() {
  await badgeStore.fetchFromApi(selectedChildId.value ?? undefined)
}

watch(() => childSelectStore.selectedChildId, () => {
  loadBadges()
})

onMounted(() => {
  loadBadges()
})

function handleUnlockBadge(badgeId: string) {
  badgeStore.unlockBadge(badgeId, selectedChildId.value ?? undefined)
}

function progressPercent(badge: any): number {
  if (badge.unlocked) return 100
  if (!badge.requirementValue || badge.requirementValue <= 0) return 0
  return Math.min(100, Math.round(((badge.progress ?? 0) / badge.requirementValue) * 100))
}

function requirementLabel(type?: string): string {
  const labels: Record<string, string> = {
    streak_days: '连续打卡天数',
    total_sunlight: '累计阳光值',
    task_complete: '完成任务数',
    checkin_count: '打卡通过次数',
    mistake_count: '记录错题数',
    zero_loss_days: '零丢失天数',
    apple_count: '苹果数量',
    sunlight_earned_total: '累计获得阳光值',
  }
  return labels[type ?? ''] ?? type ?? ''
}
</script>

<template>
  <div class="page">
    <ChildSelector />
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🏅 勋章管理</span>
        <h1>查看孩子的勋章成就</h1>
        <p class="lead">孩子满足勋章解锁条件时将自动解锁。也可以手动点击未解锁的勋章来强制解锁。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center">
        <div class="card-title">
          <h2>总览</h2>
          <span class="tag">{{ badgeStore.unlockedCount }}/{{ badgeStore.badges.length }} 已解锁</span>
        </div>
        <div class="stat-row">
          <div class="mini-stat">
            <strong>{{ badgeStore.unlockedCount }}</strong>
            <span>已解锁勋章</span>
          </div>
          <div class="mini-stat">
            <strong>{{ badgeStore.badges.length - badgeStore.unlockedCount }}</strong>
            <span>未解锁勋章</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Newly unlocked notification -->
    <section v-if="badgeStore.lastNewlyUnlocked.length" class="panel" style="border:2px solid #4caf50;background:#e8f5e9">
      <div class="card-title">
        <h2>🎉 新解锁勋章！</h2>
      </div>
      <div class="new-unlocks">
        <div v-for="b in badgeStore.lastNewlyUnlocked" :key="b.id" class="new-unlock-item">
          <span style="font-size:32px">{{ b.icon }}</span>
          <strong>{{ b.name }}</strong>
          <span v-if="b.rewardPoints" class="tag">+{{ b.rewardPoints }} 阳光值</span>
        </div>
      </div>
    </section>

    <section>
      <div class="panel">
        <div class="card-title">
          <h2>🏅 勋章列表</h2>
          <span class="tag">满足条件自动解锁</span>
        </div>
        <div class="badge-grid">
          <button
            v-for="badge in badgeStore.badges"
            :key="badge.id"
            class="badge-card"
            :class="{ locked: !badge.unlocked }"
            @click="handleUnlockBadge(badge.id)"
          >
            <span class="badge-icon">{{ badge.icon }}</span>
            <strong class="badge-name">{{ badge.name }}</strong>
            <small class="badge-desc">{{ badge.description }}</small>
            <!-- Progress bar for locked badges -->
            <div v-if="!badge.unlocked && badge.requirementValue" class="badge-progress">
              <div class="progress-track">
                <span class="progress-fill" :style="{ width: `${progressPercent(badge)}%` }"></span>
              </div>
              <small class="progress-text">{{ badge.progress ?? 0 }}/{{ badge.requirementValue }} {{ requirementLabel(badge.requirementType) }}</small>
            </div>
            <span v-if="badge.unlocked" class="badge-check">✓</span>
            <span v-if="badge.rewardPoints && badge.unlocked" class="badge-reward">+{{ badge.rewardPoints }}☀️</span>
          </button>
        </div>
      </div>

    </section>
  </div>
</template>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 12px;
}
.mini-stat {
  text-align: center;
  padding: 12px 8px;
  border-radius: 20px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.mini-stat strong {
  display: block;
  font-size: 22px;
  margin-bottom: 2px;
}
.mini-stat span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.badge-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.badge-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px 14px;
  border-radius: 18px;
  border: 2px solid var(--line);
  background: #fff;
  cursor: pointer;
  transition: all .15s ease;
  position: relative;
  text-align: center;
}
.badge-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(16,110,0,.1);
}
.badge-card.locked {
  opacity: .6;
  filter: grayscale(.5);
}
.badge-icon {
  font-size: 36px;
  line-height: 1;
}
.badge-name {
  font-size: 14px;
  color: var(--ink);
}
.badge-desc {
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
  line-height: 1.3;
}
.badge-progress {
  width: 100%;
  margin-top: 4px;
}
.progress-track {
  height: 6px;
  border-radius: 3px;
  background: var(--surface-2, #eee);
  overflow: hidden;
}
.progress-fill {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--primary), #8bc34a);
  transition: width .3s ease;
}
.progress-text {
  color: var(--muted);
  font-size: 10px;
  font-weight: 700;
}
.badge-check {
  position: absolute;
  top: 8px;
  right: 10px;
  background: var(--primary);
  color: #fff;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
  display: grid;
  place-items: center;
}
.badge-reward {
  font-size: 11px;
  font-weight: 800;
  color: var(--primary);
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

@media (max-width: 900px) {
  .badge-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .badge-grid {
    grid-template-columns: 1fr;
  }
  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
