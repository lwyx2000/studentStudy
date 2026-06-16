<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores'
import { clearAuthToken, getAuthToken, setAuthToken } from '../utils/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isParent = computed(() => userStore.profile.role === 'parent')
const isViewingAsChild = computed(() => {
  // 当前是孩子 token，但存有家长 token（说明是切换过来的）
  return userStore.profile.role === 'child' && !!localStorage.getItem('cc-parent-token')
})

const childNavItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '🌳', label: '协同仪表盘' },
  { name: 'HabitCenter', path: '/habit', icon: '✅', label: '每日打卡' },
  { name: 'MistakeBook', path: '/mistake', icon: '📚', label: '我的题库' },
  { name: 'ItemTracker', path: '/tracker', icon: '🎒', label: '物品管理' },
  { name: 'GrowthArchive', path: '/growth', icon: '📈', label: '成长档案' },
  { name: 'SunlightRedemption', path: '/sunlight', icon: '☀️', label: '阳光兑换' },
  { name: 'BadgeRoom', path: '/badge', icon: '🏅', label: '契约勋章' },
]
const parentNavItems = [
  { name: 'ParentControl', path: '/parent', icon: '🧭', label: '家长控制' },
  { name: 'ChildManagement', path: '/parent/children', icon: '👦', label: '孩子管理' },
  { name: 'ProgressDashboard', path: '/parent/progress', icon: '📊', label: '进度查看' },
  { name: 'TaskManagement', path: '/parent/tasks', icon: '📋', label: '任务管理' },
  { name: 'HabitManagement', path: '/parent/habits', icon: '✅', label: '习惯管理' },
  { name: 'ItemStats', path: '/parent/items', icon: '🎒', label: '物品统计' },
  { name: 'SunlightManagement', path: '/parent/sunlight', icon: '☀️', label: '阳光值' },
  { name: 'ParentBadges', path: '/parent/badges', icon: '🏅', label: '勋章契约' },
  { name: 'LlmConfig', path: '/parent/llm', icon: '🤖', label: '模型配置' },
  { name: 'CommunityGarden', path: '/parent/garden', icon: '🌸', label: '社区花园' },
]
const navItems = computed(() => (isParent.value ? parentNavItems : childNavItems))

async function backToParent() {
  const parentToken = localStorage.getItem('cc-parent-token')
  if (!parentToken) { router.push('/login'); return }
  setAuthToken(parentToken)
  localStorage.removeItem('cc-parent-token')
  await userStore.fetchFromApi()
  router.push('/parent/children')
}

function logout() {
  clearAuthToken()
  localStorage.removeItem('cc-parent-token')
  router.push('/login')
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <button class="brand" @click="router.push(isParent ? '/parent' : '/dashboard')">
        <span class="brand-mark">🌿</span>
        <span>小树成长岛</span>
      </button>
      <div class="top-actions">
        <span v-if="isViewingAsChild" class="pill child-badge">
          👦 {{ userStore.profile.name }} 的视角
        </span>
        <span v-else class="pill">☀️ {{ userStore.sunlightPoints || 0 }} 阳光值</span>
        <span v-if="!isParent" class="pill">Lv{{ userStore.assessment.recommendedLevel }} · {{ userStore.profile.grade || 3 }}年级</span>
        <button v-if="isViewingAsChild" class="role-btn back-btn" @click="backToParent">↩ 返回家长端</button>
        <button v-else class="role-btn logout-btn" @click="logout">退出登录</button>
      </div>
    </header>

    <aside class="sidebar">
      <div class="tree-card">
        <div class="tree-visual">{{ isParent ? '🌳' : '🌱' }}</div>
        <strong>{{ userStore.profile.name || '我的' }}{{ isParent ? ' 的管理台' : ' 的成长树' }}</strong>
        <span>{{ isParent ? '管理孩子的成长旅程' : '今天只聚焦 1 个核心习惯' }}</span>
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
.child-badge { background: #ecffd9; border-color: var(--primary); color: var(--primary); }
.role-btn { color: #fff; background: var(--primary); border-color: var(--primary); }
.back-btn { background: #e8b84b; border-color: #e8b84b; }
.logout-btn { background: #888; border-color: #888; }
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
