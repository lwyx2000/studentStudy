<script setup lang="ts">
import { useUserStore } from './stores'
import { computed } from 'vue'

const userStore = useUserStore()
const isOnboarded = computed(() => userStore.isOnboarded)
</script>

<template>
  <div id="app-root">
    <router-view v-if="!isOnboarded || $route.path === '/onboarding'" />
    <MainLayout v-else />
  </div>
</template>

<script lang="ts">
import MainLayout from './components/MainLayout.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app-root {
  min-height: 100vh;
  background-color: #fcfaef;
  font-family: 'Nunito', 'Noto Sans SC', sans-serif;
  color: #725d42;
}
</style>