<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores'
import { api, clearAuthToken, setAuthToken } from '../utils/api'
import { gradeLabel } from '../utils/constants'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isParent = computed(() => userStore.profile.role === 'parent')
const isViewingAsChild = computed(() => {
  // 当前是孩子 token，但存有家长 token（说明是切换过来的）
  return userStore.profile.role === 'child' && !!localStorage.getItem('cc-parent-token')
})

// 侧边栏收缩/展开状态
const sidebarCollapsed = ref(localStorage.getItem('cc-sidebar-collapsed') === 'true')
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('cc-sidebar-collapsed', String(sidebarCollapsed.value))
}

// 页面切换时刷新阳光/苹果余额：顶部 pill 与各页面共享同一 store，刷新一次即全局生效
// （家长端自身顶部不显示阳光值，且切换孩子由 App.vue 统一加载，故仅孩子视角需要）
watch(
  () => route.fullPath,
  () => {
    if (isParent.value && !isViewingAsChild.value) {
      fetchPendingCount()
      return
    }
    userStore.fetchFromApi()
  },
)

// 修改密码
const showPasswordModal = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const passwordSuccess = ref(false)
const changingPassword = ref(false)

function openPasswordModal() {
  oldPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  passwordError.value = ''
  passwordSuccess.value = false
  showPasswordModal.value = true
}

async function changePassword() {
  passwordError.value = ''
  passwordSuccess.value = false
  if (!oldPassword.value) { passwordError.value = '请输入原密码'; return }
  if (!newPassword.value) { passwordError.value = '请输入新密码'; return }
  if (newPassword.value.length < 6) { passwordError.value = '新密码至少 6 位'; return }
  if (newPassword.value !== confirmPassword.value) { passwordError.value = '两次输入的新密码不一致'; return }
  changingPassword.value = true
  try {
    await api.auth.changePassword(oldPassword.value, newPassword.value)
    passwordSuccess.value = true
    setTimeout(() => { showPasswordModal.value = false }, 1500)
  } catch (e: any) {
    passwordError.value = e.message || '修改失败'
  } finally {
    changingPassword.value = false
  }
}

// 待审批数量（家长端显示徽章）
const pendingCheckinCount = ref(0)
let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchPendingCount() {
  if (!isParent.value || isViewingAsChild.value) return
  try {
    const res = await api.checkins.getPending()
    pendingCheckinCount.value = (res.pending ?? []).length
  } catch { /* offline */ }
}

onMounted(() => {
  if (isParent.value) {
    fetchPendingCount()
    pollTimer = setInterval(fetchPendingCount, 30000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const childNavItems = [
  { name: 'Dashboard', path: '/dashboard', icon: '🌳', label: '协同仪表盘' },
  { name: 'HabitCenter', path: '/habit', icon: '✅', label: '每日打卡' },
  { name: 'SunshineTree', path: '/tree', icon: '🍎', label: '阳光树' },
  { name: 'MistakeBook', path: '/mistake', icon: '📚', label: '我的题库' },
  { name: 'ItemTracker', path: '/tracker', icon: '🎒', label: '物品管理' },
  { name: 'GrowthArchive', path: '/growth', icon: '📈', label: '成长档案' },
  { name: 'SunlightRedemption', path: '/sunlight', icon: '☀️', label: '阳光兑换' },
  { name: 'BadgeRoom', path: '/badge', icon: '🏅', label: '勋章馆' },
]
const parentNavItems = [
  { name: 'CheckinApproval', path: '/parent/checkins', icon: '⏳', label: '待审批' },
  { name: 'ParentControl', path: '/parent', icon: '🧭', label: '家长控制' },
  { name: 'ChildManagement', path: '/parent/children', icon: '👦', label: '孩子管理' },
  { name: 'ProgressDashboard', path: '/parent/progress', icon: '📊', label: '进度查看' },
  { name: 'TaskHabitManager', path: '/parent/tasks', icon: '📋', label: '任务与习惯' },
  { name: 'TaskHabitInventory', path: '/parent/inventory', icon: '📦', label: '复用库' },
  { name: 'ItemStats', path: '/parent/items', icon: '🎒', label: '物品统计' },
  { name: 'SunlightManagement', path: '/parent/sunlight', icon: '☀️', label: '阳光值' },
  { name: 'ParentBadges', path: '/parent/badges', icon: '🏅', label: '勋章管理' },
  { name: 'LlmConfig', path: '/parent/llm', icon: '🤖', label: '模型配置' },
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
  <div class="shell" :class="{ collapsed: sidebarCollapsed }">
    <header class="topbar">
      <div style="display:flex;align-items:center;gap:10px">
        <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? '展开菜单' : '收起菜单'">
          <span v-if="sidebarCollapsed">☰</span>
          <span v-else>✕</span>
        </button>
        <button class="brand" @click="router.push(isParent ? '/parent' : '/dashboard')">
          <span class="brand-mark">🌿</span>
          <span v-if="!sidebarCollapsed">小树成长岛</span>
        </button>
      </div>
      <div class="top-actions">
        <span v-if="isViewingAsChild" class="pill child-badge">
          👦 {{ userStore.profile.name }} 的视角
        </span>
        <span v-if="!isParent || isViewingAsChild" class="pill">☀️ {{ userStore.sunlightPoints || 0 }} 阳光值 · 🍎 {{ userStore.apples || 0 }} 苹果</span>
        <span v-if="!isParent" class="pill">Lv{{ userStore.assessment.recommendedLevel }} · {{ gradeLabel(userStore.profile.grade || 3) }}</span>
        <button v-if="isViewingAsChild" class="role-btn back-btn" @click="backToParent">↩ 返回家长端</button>
        <button class="role-btn guide-btn" @click="router.push('/guide')">❓ 使用说明</button>
        <button v-if="!isViewingAsChild" class="role-btn pwd-btn" @click="openPasswordModal">🔑 修改密码</button>
        <button v-if="!isViewingAsChild" class="role-btn logout-btn" @click="logout">退出登录</button>
      </div>
    </header>

    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div v-if="!sidebarCollapsed" class="tree-card clickable-card" @click="router.push(isParent ? '/parent' : '/dashboard')">
        <div class="tree-visual">{{ isParent ? '🌳' : '🌱' }}</div>
        <strong>{{ userStore.profile.name || '我的' }}{{ isParent ? ' 的管理台' : ' 的成长树' }}</strong>
        <span>{{ isParent ? '管理孩子的成长旅程' : '今天只聚焦 1 个核心习惯' }}</span>
      </div>
      <nav class="nav-list" :class="{ 'nav-collapsed': sidebarCollapsed }">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.name === item.name }"
          :title="sidebarCollapsed ? item.label : ''"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          <span v-if="item.name === 'CheckinApproval' && pendingCheckinCount > 0" class="nav-badge">{{ pendingCheckinCount }}</span>
        </router-link>
      </nav>
    </aside>

    <main class="content">
      <router-view />
    </main>

    <!-- 修改密码弹窗 -->
    <Teleport to="body">
      <div v-if="showPasswordModal" class="overlay" @click.self="showPasswordModal = false">
        <div class="pwd-modal">
          <div class="pwd-header">
            <h2>🔑 修改密码</h2>
            <button class="close-btn" @click="showPasswordModal = false">✕</button>
          </div>

          <div v-if="passwordSuccess" class="success-msg">✅ 密码修改成功！</div>

          <template v-else>
            <div class="pwd-field">
              <label>原密码</label>
              <input v-model="oldPassword" type="password" class="input" placeholder="请输入当前密码" @keyup.enter="changePassword" />
            </div>
            <div class="pwd-field">
              <label>新密码</label>
              <input v-model="newPassword" type="password" class="input" placeholder="至少 6 位" @keyup.enter="changePassword" />
            </div>
            <div class="pwd-field">
              <label>确认新密码</label>
              <input v-model="confirmPassword" type="password" class="input" placeholder="再次输入新密码" @keyup.enter="changePassword" />
            </div>
            <p v-if="passwordError" class="error-msg">{{ passwordError }}</p>
            <button class="btn" :disabled="changingPassword" @click="changePassword">
              {{ changingPassword ? '修改中...' : '确认修改' }}
            </button>
          </template>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.shell { min-height: 100vh; display: grid; grid-template-columns: 260px 1fr; grid-template-rows: 76px 1fr; background: var(--bg); transition: grid-template-columns .25s ease; }
.shell.collapsed { grid-template-columns: 64px 1fr; }
.topbar { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; padding: 0 28px; position: sticky; top: 0; z-index: 10; background: rgba(252,250,239,.9); backdrop-filter: blur(16px); border-bottom: 1px solid var(--line); }
.sidebar-toggle { width: 38px; height: 38px; border-radius: 12px; border: 1px solid var(--line); background: #fff; font-size: 18px; cursor: pointer; display: grid; place-items: center; color: var(--ink); transition: all .15s ease; flex-shrink: 0; }
.sidebar-toggle:hover { background: var(--surface); border-color: var(--primary); color: var(--primary); }
.brand { display: inline-flex; align-items: center; gap: 12px; color: var(--primary); background: transparent; font-size: 22px; font-weight: 950; letter-spacing: -.03em; }
.brand-mark { width: 44px; height: 44px; border-radius: 16px; display: grid; place-items: center; background: var(--yellow); flex-shrink: 0; }
.top-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.pill, .role-btn { display: inline-flex; align-items: center; border-radius: 999px; padding: 9px 13px; background: #fff; border: 1px solid var(--line); font-weight: 800; }
.child-badge { background: #ecffd9; border-color: var(--primary); color: var(--primary); }
.role-btn { color: #fff; background: var(--primary); border-color: var(--primary); cursor: pointer; }
.back-btn { background: #e8b84b; border-color: #e8b84b; }
.guide-btn { background: #8a5a2b; border-color: #8a5a2b; }
.pwd-btn { background: #6b8eb8; border-color: #6b8eb8; }
.logout-btn { background: #888; border-color: #888; }
.sidebar { padding: 20px 14px; border-right: 1px solid var(--line); background: rgba(246,244,233,.8); transition: padding .25s ease; overflow: hidden; }
.sidebar.collapsed { padding: 20px 8px; }
.tree-card { padding: 18px; border-radius: 26px; background: #fff; border: 1px solid var(--line); box-shadow: 0 12px 30px rgba(75,63,54,.08); display: flex; flex-direction: column; gap: 8px; }
.tree-visual { height: 86px; display: grid; place-items: center; border-radius: 22px; background: linear-gradient(180deg, #c9f2ff, #f6ffd7); font-size: 48px; }
.tree-card span { color: var(--muted); font-size: 13px; }
.clickable-card { cursor: pointer; transition: background .12s ease; }
.clickable-card:hover { background: #f7fcef; }
.nav-list { display: flex; flex-direction: column; gap: 8px; margin-top: 18px; }
.nav-list.nav-collapsed { margin-top: 18px; gap: 6px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 13px 14px; border-radius: 18px; color: var(--muted); text-decoration: none; font-weight: 850; transition: all .15s ease; position: relative; }
.nav-list.nav-collapsed .nav-item { justify-content: center; padding: 13px 0; }
.nav-icon { font-size: 20px; flex-shrink: 0; }
.nav-label { white-space: nowrap; overflow: hidden; }
.nav-item:hover { background: rgba(255,255,255,.8); color: var(--ink); }
.nav-item.active { color: #fff; background: var(--primary); box-shadow: 0 10px 24px rgba(16,110,0,.22); }
.nav-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #e65100;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  border-radius: 999px;
  min-width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  padding: 0 5px;
  animation: badgePulse 1.5s infinite;
}
@keyframes badgePulse {
  50% { box-shadow: 0 0 0 4px rgba(230, 81, 0, .2); }
}
.content { padding: 28px; overflow: auto; }
/* 修改密码弹窗 */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.32);
  display: grid;
  place-items: center;
  z-index: 999;
  padding: 20px;
}
.pwd-modal {
  background: #fff;
  border-radius: 24px;
  padding: 32px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 24px 64px rgba(0,0,0,.2);
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.pwd-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.pwd-header h2 { font-size: 20px; margin: 0; }
.close-btn {
  background: transparent;
  border: none;
  font-size: 22px;
  color: var(--muted);
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  display: grid;
  place-items: center;
}
.close-btn:hover { background: #f0f0f0; }
.pwd-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.pwd-field label {
  font-weight: 800;
  font-size: 14px;
  color: var(--ink);
}
.success-msg {
  text-align: center;
  padding: 20px;
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
}
.error-msg {
  padding: 12px;
  border-radius: 14px;
  background: #ffdad6;
  color: #93000a;
  font-weight: 700;
  font-size: 14px;
}

@media (max-width: 860px) { .shell, .shell.collapsed { grid-template-columns: 1fr; grid-template-rows: auto auto 1fr; } .topbar { position: static; align-items: flex-start; gap: 12px; flex-direction: column; padding: 16px; } .sidebar, .sidebar.collapsed { border-right: 0; border-bottom: 1px solid var(--line); padding: 12px 14px; } .tree-card { display: none; } .nav-list, .nav-list.nav-collapsed { margin: 0; flex-direction: row; overflow-x: auto; gap: 8px; } .nav-item { white-space: nowrap; } .nav-list.nav-collapsed .nav-item { padding: 13px 14px; } .content { padding: 18px; } }
</style>
