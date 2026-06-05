<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from './components/MainLayout.vue'
import { useUserStore } from './stores'

const route = useRoute()
const userStore = useUserStore()
const useStandaloneOnboarding = computed(() => route.path === '/onboarding' && !userStore.isOnboarded)
</script>

<template>
  <div id="app-root">
    <router-view v-if="useStandaloneOnboarding" />
    <MainLayout v-else />
  </div>
</template>

<style>
#app-root {
  min-height: 100vh;
}
</style>
