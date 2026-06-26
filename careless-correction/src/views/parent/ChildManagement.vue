<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore, useBadgeStore, useGrowthStore, useMistakeStore, useParentStore, useTaskStore } from '../../stores'
import { api, normalizeChild, setAuthToken, normalizeUser, type ChildProfile } from '../../utils/api'

const router = useRouter()
const userStore = useUserStore()

const children = ref<ChildProfile[]>([])
const loading = ref(false)
const adding = ref(false)
const switching = ref<string | null>(null)

// 新增表单
const newName = ref('')
const newGrade = ref(3)
const addError = ref('')

// 编辑
const editingId = ref<string | null>(null)
const editName = ref('')
const editGrade = ref(3)

async function loadChildren() {
  loading.value = true
  try {
    const res = await api.children.list()
    children.value = Array.isArray(res) ? res.map(normalizeChild) : []
  } catch {
    children.value = []
  } finally {
    loading.value = false
  }
}

async function addChild() {
  addError.value = ''
  if (!newName.value.trim()) { addError.value = '请填写孩子名字'; return }
  try {
    const res = await api.children.add({ name: newName.value.trim(), grade: newGrade.value })
    children.value.push(normalizeChild(res))
    newName.value = ''
    newGrade.value = 3
    adding.value = false
  } catch (e: any) {
    addError.value = e.message || '添加失败'
  }
}

function startEdit(child: ChildProfile) {
  editingId.value = child.id
  editName.value = child.name
  editGrade.value = child.grade
}

async function saveEdit(id: string) {
  try {
    const res = await api.children.update(id, { name: editName.value, grade: editGrade.value })
    const idx = children.value.findIndex(c => c.id === id)
    if (idx !== -1) children.value[idx] = normalizeChild(res)
    editingId.value = null
  } catch {}
}

async function removeChild(id: string) {
  if (!confirm('确认删除该孩子账号及其所有数据？此操作不可撤销。')) return
  try {
    await api.children.remove(id)
    children.value = children.value.filter(c => c.id !== id)
  } catch {}
}

async function switchToChild(child: ChildProfile) {
  switching.value = child.id
  try {
    // 保存家长 token，切换为孩子 token
    const parentToken = localStorage.getItem('cc-auth-token') ?? ''
    localStorage.setItem('cc-parent-token', parentToken)

    const res = await api.children.switchToken(child.id)
    setAuthToken(res.token)
    const childProfile = normalizeUser(res.user)
    userStore.setProfile(childProfile)

    // 重新加载孩子数据
    await Promise.allSettled([
      userStore.fetchFromApi(),
      useTaskStore().fetchFromApi(),
      useMistakeStore().fetchFromApi(),
      useBadgeStore().fetchFromApi(),
      useGrowthStore().fetchFromApi(),
    ])
    router.push('/dashboard')
  } catch {} finally {
    switching.value = null
  }
}

onMounted(loadChildren)
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">👦 孩子管理</span>
        <h1>管理孩子账号</h1>
        <p class="lead">添加孩子后可切换到孩子视角查看任务、成长数据，或在各功能页面中以孩子身份操作。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center;gap:12px">
        <div class="card-title">
          <h2>账号概览</h2>
          <span class="tag">{{ children.length }} 个孩子</span>
        </div>
        <button class="btn" @click="adding = !adding">
          {{ adding ? '取消' : '＋ 添加孩子' }}
        </button>
      </div>
    </section>

    <!-- 添加孩子表单 -->
    <section v-if="adding" class="panel">
      <div class="card-title">
        <h2>添加孩子</h2>
      </div>
      <div class="add-form">
        <label>
          孩子名字
          <input v-model="newName" class="input" placeholder="例如：小明" @keyup.enter="addChild" />
        </label>
        <label>
          年级
          <select v-model.number="newGrade" class="input">
            <option v-for="g in 6" :key="g" :value="g">{{ g }} 年级</option>
          </select>
        </label>
        <button class="btn" :disabled="!newName.trim()" @click="addChild">确认添加</button>
      </div>
      <p v-if="addError" class="error-msg">{{ addError }}</p>
    </section>

    <!-- 孩子列表 -->
    <section class="panel">
      <div class="card-title">
        <h2>孩子列表</h2>
        <span v-if="loading" class="muted" style="font-size:13px">加载中...</span>
      </div>

      <div v-if="children.length" class="list">
        <div v-for="child in children" :key="child.id" class="list-row child-row">
          <!-- 编辑模式 -->
          <template v-if="editingId === child.id">
            <div class="edit-inline">
              <input v-model="editName" class="input" style="width:140px" />
              <select v-model.number="editGrade" class="input" style="width:100px">
                <option v-for="g in 6" :key="g" :value="g">{{ g }} 年级</option>
              </select>
              <button class="btn" style="padding:6px 14px;font-size:13px" @click="saveEdit(child.id)">保存</button>
              <button class="btn ghost" style="padding:6px 14px;font-size:13px" @click="editingId = null">取消</button>
            </div>
          </template>

          <!-- 展示模式 -->
          <template v-else>
            <div class="child-info">
              <span class="child-avatar">{{ child.name[0] ?? '孩' }}</span>
              <div>
                <strong>{{ child.name }}</strong>
                <span class="muted" style="display:block;font-size:13px">
                  {{ child.grade }} 年级 · ☀️ {{ child.sunlightPoints }} 阳光值
                  <span v-if="child.streakDays > 0"> · 🔥 {{ child.streakDays }} 天连续</span>
                </span>
              </div>
            </div>
            <div class="child-login-col" v-if="child.loginName">
              <span class="login-label">登录名</span>
              <span class="login-value">{{ child.loginName }}</span>
            </div>
            <div class="child-actions">
              <button
                class="btn"
                style="padding:7px 16px;font-size:13px"
                :disabled="switching === child.id"
                @click="switchToChild(child)"
              >
                {{ switching === child.id ? '切换中...' : '进入孩子视角' }}
              </button>
              <button class="btn secondary" style="padding:7px 12px;font-size:13px" @click="startEdit(child)">编辑</button>
              <button class="btn ghost" style="padding:7px 12px;font-size:13px;color:#c00" @click="removeChild(child.id)">删除</button>
            </div>
          </template>
        </div>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <span style="font-size:48px">👦</span>
        <p>还没有添加孩子，点击上方「添加孩子」开始吧。</p>
      </div>
    </section>

    <!-- 返回家长端提示（当前处于孩子视角时显示） -->
    <section v-if="userStore.profile.role === 'child'" class="panel" style="background:#fff8d9;border:1px solid #f0d960">
      <div class="card-title">
        <h2>⚠️ 当前处于孩子视角</h2>
      </div>
      <p class="lead">你正在以 <strong>{{ userStore.profile.name }}</strong> 的身份查看数据。</p>
      <button class="btn secondary" @click="$router.push('/parent/children')">返回家长端</button>
    </section>
  </div>
</template>

<style scoped>
.child-row {
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.child-info {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}
.child-avatar {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  background: linear-gradient(135deg, #fbe270, #80dc67);
  display: grid;
  place-items: center;
  font-size: 20px;
  font-weight: 900;
  flex-shrink: 0;
}
.child-login-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 16px;
  background: #e8f5e9;
  border-radius: 12px;
  flex-shrink: 0;
}
.login-label {
  font-size: 11px;
  font-weight: 700;
  color: #558b2f;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.login-value {
  font-size: 18px;
  font-weight: 900;
  color: #1b5e20;
  font-family: 'Courier New', 'SF Mono', monospace;
  letter-spacing: 1px;
}
.child-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.edit-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}
.add-form {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
  align-items: end;
}
.add-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 800;
  font-size: 14px;
}
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--muted);
}
.error-msg {
  padding: 12px;
  border-radius: 14px;
  background: #ffdad6;
  color: #93000a;
  font-weight: 700;
  font-size: 14px;
  margin-top: 8px;
}
button:disabled {
  opacity: .6;
  cursor: not-allowed;
}
@media (max-width: 700px) {
  .add-form { grid-template-columns: 1fr; }
}
</style>
