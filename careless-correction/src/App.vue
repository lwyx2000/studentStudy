<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from './components/MainLayout.vue'
import UpdateDialog from './components/UpdateDialog.vue'
import {
  useBadgeStore,
  useChildSelectStore,
  useGrowthStore,
  useMistakeStore,
  useParentStore,
  useTaskStore,
  useUserStore,
} from './stores'
import { getAuthToken } from './utils/api'
import {
  canInstall,
  checkForUpdate,
  downloadApk,
  getDownloadedPath,
  installApk,
  openInstallSettings,
  type LocalVersion,
  type RemoteVersion,
} from './utils/updater'

const route = useRoute()
const userStore = useUserStore()
const childSelectStore = useChildSelectStore()

const isPublicPage = computed(() => route.meta.public === true)
const switchingChild = ref(false)

// ── 应用内更新 ──
const updateVisible = ref(false)
const updateRemote = ref<RemoteVersion | null>(null)
const updateLocal = ref<LocalVersion | null>(null)
const updateProgress = ref<number | null>(null)
const updateError = ref('')
const updateDismissed = ref(false)
const updateBusy = ref(false)

async function runUpdateCheck() {
  try {
    const result = await checkForUpdate()
    if (result.unsupported || !result.hasUpdate || updateDismissed.value) return
    updateRemote.value = result.remote
    updateLocal.value = result.local
    updateError.value = ''
    updateVisible.value = true
  } catch {
    // 版本检查失败（离线/服务器未放置 version.json）时静默跳过，不影响正常使用
  }
}

async function onUpdateConfirm() {
  if (!updateRemote.value || updateBusy.value) return
  updateBusy.value = true
  updateError.value = ''
  try {
    let path: string | null = null

    // 已下载过则直接安装，避免重复下载
    if (updateProgress.value === 100) {
      path = await getDownloadedPath()
    }
    if (!path) {
      updateProgress.value = 0
      path = await downloadApk(updateRemote.value.downloadUrl, (p) => {
        updateProgress.value = p
      })
    }
    updateProgress.value = 100

    const allowed = await canInstall()
    if (!allowed) {
      // 跳到系统设置授权，用户返回后再次点击即可安装
      await openInstallSettings()
      updateError.value = '请开启「允许安装未知应用」后返回，再点击安装'
      return
    }

    const result = await installApk(path)
    if (result === 'need-permission') {
      await openInstallSettings()
      updateError.value = '请开启「允许安装未知应用」后返回，再点击安装'
    }
  } catch (e: any) {
    updateError.value = e?.message || '更新失败，请稍后重试'
    // 下载失败时重置进度，允许重试
    updateProgress.value = null
  } finally {
    updateBusy.value = false
  }
}

function onUpdateLater() {
  updateVisible.value = false
  updateDismissed.value = true
}

// 家长端：当选中孩子切换时，重新加载该孩子的业务数据
watch(
  () => childSelectStore.selectedChildId,
  async (childId) => {
    if (!childId || userStore.profile.role !== 'parent') return
    switchingChild.value = true
    await Promise.allSettled([
      useUserStore().fetchFromApi(childId),
      useParentStore().fetchFromApi(childId),
      useTaskStore().fetchFromApi(childId),
      useMistakeStore().fetchFromApi(childId),
      useBadgeStore().fetchFromApi(childId),
      useGrowthStore().fetchFromApi(childId),
    ])
    switchingChild.value = false
  },
)

onMounted(async () => {
  // 更新检查独立于登录状态：即使未登录（含登录页）也应提示新版本
  void runUpdateCheck()

  const token = getAuthToken()
  if (!token) return

  await userStore.fetchFromApi()
  const role = userStore.profile.role

  if (role === 'parent') {
    // 家长端：先加载孩子列表，再加载第一个孩子的数据
    await Promise.allSettled([
      useParentStore().fetchFromApi(),
      useBadgeStore().fetchFromApi(),
      childSelectStore.loadChildren(),
    ])
    const childId = childSelectStore.selectedChildId ?? undefined
    if (childId) {
      await Promise.allSettled([
        useUserStore().fetchFromApi(childId),
        useParentStore().fetchFromApi(childId),
        useTaskStore().fetchFromApi(childId),
        useMistakeStore().fetchFromApi(childId),
        useBadgeStore().fetchFromApi(childId),
        useGrowthStore().fetchFromApi(childId),
      ])
    }
  } else {
    // 孩子端：加载自己的数据
    await Promise.allSettled([
      useTaskStore().fetchFromApi(),
      useMistakeStore().fetchFromApi(),
      useBadgeStore().fetchFromApi(),
      useGrowthStore().fetchFromApi(),
      useParentStore().fetchFromApi(),
    ])
  }
})
</script>

<template>
  <div id="app-root">
    <div v-if="switchingChild" class="switch-overlay">
      <div class="switch-spinner"></div>
      <span>正在切换孩子数据…</span>
    </div>
    <router-view v-if="isPublicPage" />
    <MainLayout v-else />

    <UpdateDialog
      :visible="updateVisible"
      :remote="updateRemote ?? { versionCode: 0, versionName: '', changelog: '', downloadUrl: '' }"
      :local="updateLocal"
      :progress="updateProgress"
      :error="updateError"
      @confirm="onUpdateConfirm"
      @later="onUpdateLater"
    />
  </div>
</template>

<style>
#app-root {
  min-height: 100vh;
}
.switch-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(255,255,255,.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-weight: 800;
  font-size: 15px;
  color: var(--primary, #2e7d1e);
}
.switch-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--line, #ddd);
  border-top-color: var(--primary, #2e7d1e);
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
