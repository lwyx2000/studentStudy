<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { LocalVersion, RemoteVersion } from '../utils/updater'

const props = defineProps<{
  visible: boolean
  remote: RemoteVersion
  local: LocalVersion | null
  /** 下载中进度 0-100，null 表示尚未开始下载 */
  progress: number | null
  /** 下载/安装过程中的错误提示 */
  error?: string
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'later'): void
}>()

const showPermissionTip = ref(false)

watch(() => props.visible, (v) => {
  if (v) showPermissionTip.value = false
})

const versionLabel = computed(() => {
  const r = props.remote.versionName || String(props.remote.versionCode)
  const l = props.local?.versionName
  return l ? `${l} → ${r}` : r
})

const isDownloading = computed(() => props.progress !== null && props.progress < 100)
const isReady = computed(() => props.progress === 100)

function onLater() {
  if (props.remote.force) return
  emit('later')
}
</script>

<template>
  <div v-if="visible" class="update-backdrop">
    <div class="update-card" role="dialog" aria-modal="true" aria-label="发现新版本">
      <div class="update-icon">🌱</div>
      <h2 class="update-title">{{ isReady ? '新版本已下载' : '发现新版本' }}</h2>

      <div class="update-version">
        <span class="update-badge">{{ versionLabel }}</span>
        <span v-if="remote.publishedAt" class="update-date">{{ remote.publishedAt }}</span>
      </div>

      <div v-if="remote.changelog" class="update-changelog">
        <div class="update-changelog-title">本次更新</div>
        <pre class="update-changelog-body">{{ remote.changelog }}</pre>
      </div>

      <div v-if="progress !== null" class="update-progress-wrap">
        <div class="progress"><span :style="{ width: `${progress}%` }"></span></div>
        <div class="update-progress-text">
          {{ isDownloading ? `正在下载 ${progress}%` : '下载完成，可以安装' }}
        </div>
      </div>

      <div v-if="error" class="update-error">{{ error }}</div>

      <div v-if="showPermissionTip" class="update-tip">
        系统需要「允许安装未知应用」权限才能更新，请在接下来的设置页中开启后返回。
      </div>

      <div class="update-actions">
        <button v-if="!remote.force" class="btn ghost" :disabled="isDownloading" @click="onLater">
          {{ isReady ? '稍后安装' : '暂不更新' }}
        </button>
        <button class="btn" :disabled="isDownloading" @click="$emit('confirm')">
          {{ isReady ? '立即安装' : isDownloading ? '下载中…' : '立即更新' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.update-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(30, 28, 20, .55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.update-card {
  width: 100%;
  max-width: 420px;
  background: #fffdf6;
  border: 1px solid var(--line, #dedbcc);
  border-radius: 32px;
  box-shadow: 0 24px 60px rgba(42, 35, 22, .28);
  padding: 30px 26px 26px;
  text-align: center;
}
.update-icon {
  width: 70px;
  height: 70px;
  margin: 0 auto 14px;
  display: grid;
  place-items: center;
  border-radius: 22px;
  background: var(--yellow, #ffe08a);
  font-size: 36px;
  box-shadow: inset 0 -4px rgba(0, 0, 0, .06);
}
.update-title {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 900;
  color: var(--ink, #2a2316);
}
.update-version {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.update-badge {
  display: inline-flex;
  padding: 5px 12px;
  border-radius: 999px;
  background: var(--primary, #106e00);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
}
.update-date { font-size: 12px; color: var(--muted, #8a8574); }
.update-changelog {
  text-align: left;
  background: var(--surface, #f6f3e6);
  border: 1px solid var(--line, #dedbcc);
  border-radius: 20px;
  padding: 14px 16px;
  margin-bottom: 18px;
}
.update-changelog-title { font-size: 13px; font-weight: 800; color: var(--primary, #106e00); margin-bottom: 6px; }
.update-changelog-body {
  margin: 0;
  font: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink, #2a2316);
  white-space: pre-wrap;
  word-break: break-word;
}
.update-progress-wrap { margin-bottom: 16px; }
.update-progress-text { margin-top: 8px; font-size: 13px; font-weight: 700; color: var(--muted, #8a8574); }
.update-error {
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #fff0ee;
  color: #b3261e;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
}
.update-tip {
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #fff8e1;
  color: #8a5a00;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
}
.update-actions { display: flex; gap: 12px; justify-content: center; }
.update-actions .btn { flex: 1; }
.update-actions .btn:disabled { opacity: .6; cursor: not-allowed; }
</style>
