<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores'
import { computed } from 'vue'
import { Button } from 'animal-island-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isParent = computed(() => userStore.profile.role === 'parent')

const childNavItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '🌿', label: '主页' },
  { name: 'HabitCenter', path: '/habit', icon: '✅', label: '习惯中心' },
  { name: 'MistakeBook', path: '/mistake', icon: '📖', label: '错题本' },
  { name: 'ItemTracker', path: '/tracker', icon: '🎒', label: '物品追踪' },
  { name: 'BadgeRoom', path: '/badge', icon: '🏅', label: '勋章馆' },
]

const parentNavItems = [
  { name: 'ParentControl', path: '/parent', icon: '⚙️', label: '控制中心' },
  { name: 'EvidenceLab', path: '/parent/lab', icon: '🔬', label: '循证实验室' },
  { name: 'CommunityGarden', path: '/parent/garden', icon: '🌸', label: '社区花园' },
]

const navItems = computed(() => isParent.value ? parentNavItems : childNavItems)

function switchRole() {
  userStore.setProfile({ role: userStore.profile.role === 'child' ? 'parent' : 'child' })
  if (userStore.profile.role === 'parent') {
    router.push('/parent')
  } else {
    router.push('/dashboard')
  }
}
</script>

<template>
  <div class="main-layout">
    <header class="top-bar">
      <div class="top-bar-left">
        <span class="logo-text">小树成长岛</span>
      </div>
      <div class="top-bar-right">
        <div class="sunlight-badge">
          <span class="material-icon">☀️</span>
          <span>{{ userStore.sunlightPoints }} 阳光值</span>
        </div>
        <Button type="text" size="small" @click="router.push('/badge')">🏅</Button>
        <Button type="text" size="small" @click="switchRole">👤</Button>
      </div>
    </header>
    <aside class="side-nav">
      <div class="nav-avatar">
        <div class="avatar-circle">🌿</div>
        <span class="avatar-level">Lv{{ userStore.assessment.recommendedLevel }}</span>
      </div>
      <nav class="nav-list">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.name === item.name }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="nav-footer">
        <Button type="dashed" block @click="switchRole">
          {{ isParent ? '切换到孩子视角' : '家长入口' }}
        </Button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.main-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  grid-template-rows: 56px 1fr;
  min-height: 100vh;
  background: #fcfaef;
}
.top-bar {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #f0e8d0;
  border-bottom: 2px solid #e4e3d8;
}
.logo-text {
  font-family: 'Nunito', 'Noto Sans SC', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: #106e00;
}
.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.sunlight-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #fbe270;
  border-radius: 20px;
  font-weight: 600;
  color: #6e5e00;
}
.side-nav {
  display: flex;
  flex-direction: column;
  padding: 16px 8px;
  background: #f7f3df;
  border-right: 2px solid #e4e3d8;
}
.nav-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}
.avatar-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #8ac68a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}
.avatar-level {
  margin-top: 4px;
  font-weight: 700;
  color: #106e00;
}
.nav-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  text-decoration: none;
  color: #725d42;
  transition: all 0.2s;
}
.nav-item:hover {
  background: #e4e3d8;
}
.nav-item.active {
  background: #106e00;
  color: white;
}
.nav-icon {
  font-size: 18px;
}
.nav-footer {
  margin-top: auto;
}
.main-content {
  padding: 24px;
  overflow-y: auto;
}
</style>