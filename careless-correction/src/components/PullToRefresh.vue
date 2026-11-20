<script setup lang="ts">
import { ref } from 'vue'

/**
 * 通用下拉刷新容器（移动端触摸手势）
 *
 * - 仅在页面滚动到顶部时检测下拉
 * - 下拉超过阈值（60px，带阻尼）松手触发 refresh 事件
 * - 刷新中显示旋转指示器，完成后自动收起
 */
const emit = defineEmits<{ (e: 'refresh'): void }>()

const THRESHOLD = 60
const DAMPING = 0.5

const pull = ref(0)
const refreshing = ref(false)
let startY = 0
let dragging = false

function atTop(): boolean {
  const content = document.querySelector('.content')
  const contentTop = content?.scrollTop ?? 0
  return contentTop <= 0 && window.scrollY <= 0
}

function onTouchStart(e: TouchEvent) {
  if (refreshing.value || !atTop()) return
  startY = e.touches[0]?.clientY ?? 0
  dragging = true
}

function onTouchMove(e: TouchEvent) {
  if (!dragging || refreshing.value) return
  const y = e.touches[0]?.clientY ?? 0
  const dy = y - startY
  if (dy <= 0 || !atTop()) {
    pull.value = 0
    return
  }
  // 阻止原生 overscroll，让下拉指示器可见
  if (e.cancelable) e.preventDefault()
  pull.value = Math.min(90, dy * DAMPING)
}

async function onTouchEnd() {
  if (!dragging) return
  dragging = false
  if (pull.value >= THRESHOLD) {
    refreshing.value = true
    pull.value = THRESHOLD
    try {
      await Promise.resolve(emit('refresh'))
    } finally {
      refreshing.value = false
      pull.value = 0
    }
  } else {
    pull.value = 0
  }
}
</script>

<template>
  <div class="ptr" @touchstart.passive="onTouchStart" @touchmove="onTouchMove" @touchend.passive="onTouchEnd" @touchcancel.passive="onTouchEnd">
    <div class="ptr-indicator" :class="{ active: refreshing }" :style="{ height: `${pull}px` }">
      <span v-if="refreshing" class="ptr-spinner"></span>
      <span v-else-if="pull > 0">{{ pull >= THRESHOLD ? '↑ 松开刷新' : '↓ 下拉刷新' }}</span>
    </div>
    <slot />
  </div>
</template>

<style scoped>
.ptr { overscroll-behavior-y: contain; }
.ptr-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: var(--muted, #8a8574);
  font-size: 13px;
  font-weight: 700;
  transition: height .18s ease;
  height: 0;
}
.ptr-indicator.active { height: 44px !important; }
.ptr-spinner {
  width: 22px;
  height: 22px;
  border: 3px solid var(--line, #dedbcc);
  border-top-color: var(--primary, #106e00);
  border-radius: 50%;
  animation: ptr-spin .7s linear infinite;
}
@keyframes ptr-spin { to { transform: rotate(360deg); } }
</style>
