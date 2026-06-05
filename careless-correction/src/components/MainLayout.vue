<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isParent = computed(() => userStore.profile.role === 'parent')
const childNavItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '🌳', label: '协同仪表盘' },
  { name: 'HabitCenter', path: '/habit', icon: '✅', label: '习惯打印' },
  { name: 'MistakeBook', path: '/mistake', icon: '🔎', label: '黄金一问' },
  { name: 'ItemTracker', path: '/tracker', icon: '🎒', label: '物品实验室' },
  { name: 'GrowthArchive', path: '/growth', icon: '📈', label: '成长档案' },
  { name: 'TimeTaskCabin', path: '/time-task', icon: '⏱️', label: '自治舱' },
  { name: 'BadgeRoom', path: '/badge', icon: '🏅', label: '契约勋章' },
]
const parentNavItems = [
  { name: 'ParentControl', path: '/parent', icon: '🧭', label: '家长控制' },
  { name: 'EvidenceLab', path: '/parent/lab', icon: '🔬', label: '循证实验室' },
  { name: 'CommunityGarden', path: '/parent/garden', icon: '🌸', label: '社区花园' },
]
const navItems = computed(() => (isParent.value ? parentNavItems : childNavItems))

function switchRole() {
  const nextRole = userStore.profile.role === 'child' ? 'parent' : 'child'
  userStore.setProfile({ role: nextRole })
  router.push(nextRole === 'parent' ? '/parent' : '/dashboard')
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <button class="brand" @click="router.push('/dashboard')">
        <span class="brand-mark">🌿</span>
        <span>小树成长岛</span>
      </button>
      <div class="top-actions">
        <span class="pill">☀️ {{ userStore.sunlightPoints || 120 }} 阳光值</span>
        <span class="pill">Lv{{ userStore.assessment.recommendedLevel }} · {{ userStore.profile.grade || 3 }}年级</span>
        <button class="role-btn" @click="switchRole">{{ isParent ? '切到孩子视角' : '家长入口' }}</button>
      </div>
    </header>

    <aside class="sidebar">
      <div class="tree-card">
        <div class="tree-visual">🌱</div>
        <strong>{{ userStore.profile.name || 'Leo' }} 的成长树</strong>
        <span>今天只聚焦 1 个核心习惯</span>
      </div>
      <nav class="nav-list">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.name === item.name }"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.shell { min-height: 100vh; display: grid; grid-template-columns: 260px 1fr; grid-template-rows: 76px 1fr; background: var(--bg); }
.topbar { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; padding: 0 28px; position: sticky; top: 0; z-index: 10; background: rgba(252,250,239,.9); backdrop-filter: blur(16px); border-bottom: 1px solid var(--line); }
.brand { display: inline-flex; align-items: center; gap: 12px; color: var(--primary); background: transparent; font-size: 22px; font-weight: 950; letter-spacing: -.03em; }
.brand-mark { width: 44px; height: 44px; border-radius: 16px; display: grid; place-items: center; background: var(--yellow); }
.top-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.pill, .role-btn { display: inline-flex; align-items: center; border-radius: 999px; padding: 9px 13px; background: #fff; border: 1px solid var(--line); font-weight: 800; }
.role-btn { color: #fff; background: var(--primary); border-color: var(--primary); }
.sidebar { padding: 20px 14px; border-right: 1px solid var(--line); background: rgba(246,244,233,.8); }
.tree-card { padding: 18px; border-radius: 26px; background: #fff; border: 1px solid var(--line); box-shadow: 0 12px 30px rgba(75,63,54,.08); display: flex; flex-direction: column; gap: 8px; }
.tree-visual { height: 86px; display: grid; place-items: center; border-radius: 22px; background: linear-gradient(180deg, #c9f2ff, #f6ffd7); font-size: 48px; }
.tree-card span { color: var(--muted); font-size: 13px; }
.nav-list { display: flex; flex-direction: column; gap: 8px; margin-top: 18px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 13px 14px; border-radius: 18px; color: var(--muted); text-decoration: none; font-weight: 850; }
.nav-item:hover { background: rgba(255,255,255,.8); color: var(--ink); }
.nav-item.active { color: #fff; background: var(--primary); box-shadow: 0 10px 24px rgba(16,110,0,.22); }
.content { padding: 28px; overflow: auto; }
@media (max-width: 860px) { .shell { grid-template-columns: 1fr; grid-template-rows: auto auto 1fr; } .topbar { position: static; align-items: flex-start; gap: 12px; flex-direction: column; padding: 16px; } .sidebar { border-right: 0; border-bottom: 1px solid var(--line); } .tree-card { display: none; } .nav-list { margin: 0; flex-direction: row; overflow-x: auto; } .nav-item { white-space: nowrap; } .content { padding: 18px; } }
</style>
