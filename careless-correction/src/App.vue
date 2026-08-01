<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from './components/MainLayout.vue'
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

const route = useRoute()
const userStore = useUserStore()
const childSelectStore = useChildSelectStore()

const isPublicPage = computed(() => route.meta.public === true)
const switchingChild = ref(false)

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
