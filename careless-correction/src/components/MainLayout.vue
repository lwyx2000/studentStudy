<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores'
import { api, clearAuthToken, getAuthToken, setAuthToken } from '../utils/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isParent = computed(() => userStore.profile.role === 'parent')
const isViewingAsChild = computed(() => {
  // 当前是孩子 token，但存有家长 token（说明是切换过来的）
  return userStore.profile.role === 'child' && !!localStorage.getItem('cc-parent-token')
})

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
  { name: 'TaskHabitManager', path: '/parent/tasks', icon: '📋', label: '任务与习惯' },
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
        <template v-else>
          <button class="role-btn pwd-btn" @click="openPasswordModal">🔑 修改密码</button>
          <button class="role-btn logout-btn" @click="logout">退出登录</button>
        </template>
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
.shell { min-height: 100vh; display: grid; grid-template-columns: 260px 1fr; grid-template-rows: 76px 1fr; background: var(--bg); }
.topbar { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; padding: 0 28px; position: sticky; top: 0; z-index: 10; background: rgba(252,250,239,.9); backdrop-filter: blur(16px); border-bottom: 1px solid var(--line); }
.brand { display: inline-flex; align-items: center; gap: 12px; color: var(--primary); background: transparent; font-size: 22px; font-weight: 950; letter-spacing: -.03em; }
.brand-mark { width: 44px; height: 44px; border-radius: 16px; display: grid; place-items: center; background: var(--yellow); }
.top-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.pill, .role-btn { display: inline-flex; align-items: center; border-radius: 999px; padding: 9px 13px; background: #fff; border: 1px solid var(--line); font-weight: 800; }
.child-badge { background: #ecffd9; border-color: var(--primary); color: var(--primary); }
.role-btn { color: #fff; background: var(--primary); border-color: var(--primary); cursor: pointer; }
.back-btn { background: #e8b84b; border-color: #e8b84b; }
.pwd-btn { background: #6b8eb8; border-color: #6b8eb8; }
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

@media (max-width: 860px) { .shell { grid-template-columns: 1fr; grid-template-rows: auto auto 1fr; } .topbar { position: static; align-items: flex-start; gap: 12px; flex-direction: column; padding: 16px; } .sidebar { border-right: 0; border-bottom: 1px solid var(--line); } .tree-card { display: none; } .nav-list { margin: 0; flex-direction: row; overflow-x: auto; } .nav-item { white-space: nowrap; } .content { padding: 18px; } }
</style>
