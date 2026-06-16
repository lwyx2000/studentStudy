<script setup lang="ts">
import { useBadgeStore, useChildSelectStore } from '../../stores'
import ChildSelector from '../../components/ChildSelector.vue'

const badgeStore = useBadgeStore()
const childSelectStore = useChildSelectStore()
</script>

<template>
  <div class="page">
    <ChildSelector />
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🏅 勋章与契约</span>
        <h1>查看孩子的勋章和家庭契约</h1>
        <p class="lead">孩子端创建的契约和手动解锁的勋章都会同步显示在这里。</p>
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
          <div class="mini-stat">
            <strong>{{ badgeStore.covenants.length }}</strong>
            <span>契约总数</span>
          </div>
          <div class="mini-stat">
            <strong>{{ badgeStore.covenants.filter(c => c.status === 'active').length }}</strong>
            <span>进行中</span>
          </div>
        </div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>🏅 勋章列表</h2>
          <span class="tag">点击可解锁</span>
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
          </button>
        </div>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>📜 家庭契约</h2>
          <span class="tag">{{ badgeStore.covenants.length }} 份</span>
        </div>
        <div v-if="badgeStore.covenants.length" class="list">
          <div
            v-for="covenant in badgeStore.covenants"
            :key="covenant.id"
            class="list-row"
          >
            <div style="min-width:0">
              <strong>{{ covenant.goal }}</strong>
              <span class="muted" style="display:block;font-size:13px">奖励：{{ covenant.reward }}</span>
              <span class="muted" style="font-size:12px">
                {{ covenant.childSignature }} · {{ covenant.parentSignature }}
              </span>
            </div>
            <span class="tag" style="flex-shrink:0;font-size:12px">
              {{ covenant.status === 'active' ? '进行中' : covenant.status === 'completed' ? '已完成' : '已过期' }}
            </span>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:20px">暂无契约，让孩子在「契约勋章」页面创建。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
.honeycomb {
  display: grid;
  grid-template-columns: repeat(3, minmax(90px, 1fr));
  gap: 14px;
}
.badge-cell {
  aspect-ratio: 1;
  clip-path: polygon(25% 6%,75% 6%,100% 50%,75% 94%,25% 94%,0 50%);
  display: grid;
  place-items: center;
  text-align: center;
  padding: 18px;
  background: linear-gradient(135deg,#fbe270,#80dc67);
  font-weight: 900;
  border: 0;
  color: var(--ink);
  cursor: pointer;
}
.badge-cell.locked {
  filter: grayscale(1);
  opacity: .38;
}
.badge-cell span {
  display: block;
  font-size: 26px;
}
.badge-cell small {
  font-weight: 900;
}
</style>
