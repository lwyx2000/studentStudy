<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
const router = useRouter()
const userStore = useUserStore()
const childSelectStore = useChildSelectStore()

const isPublicPage = computed(() => route.meta.public === true)

// 家长端：当选中孩子切换时，重新加载该孩子的业务数据
watch(
  () => childSelectStore.selectedChildId,
  async (childId) => {
    if (!childId || userStore.profile.role !== 'parent') return
    await Promise.allSettled([
      useTaskStore().fetchFromApi(childId),
      useMistakeStore().fetchFromApi(childId),
      useBadgeStore().fetchFromApi(),
      useGrowthStore().fetchFromApi(childId),
    ])
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
        useTaskStore().fetchFromApi(childId),
        useMistakeStore().fetchFromApi(childId),
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
    <router-view v-if="isPublicPage" />
    <MainLayout v-else />
  </div>
</template>

<style>
#app-root {
  min-height: 100vh;
}
</style>
