<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loadSlim } from '@tsparticles/slim'
import type { Engine, ISourceOptions } from '@tsparticles/engine'
import { useBadgeStore, useChildSelectStore, useParentStore, useUserStore } from '../stores'
import { api, normalizeUser, setAuthToken } from '../utils/api'

const router = useRouter()
const userStore = useUserStore()

const mode = ref<'login' | 'register'>('login')
const name = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (!name.value.trim() || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  if (mode.value === 'register' && password.value !== confirmPassword.value) {
    error.value = '两次密码不一致'
    return
  }
  loading.value = true
  try {
    const res = mode.value === 'register'
      ? await api.auth.register({ name: name.value.trim(), password: password.value })
      : await api.auth.login({ name: name.value.trim(), password: password.value })

    setAuthToken(res.token)
    userStore.setProfile(normalizeUser(res.user))
    userStore.completeOnboarding()

    await Promise.allSettled([
      userStore.fetchFromApi(),
      useParentStore().fetchFromApi(),
      useBadgeStore().fetchFromApi(),
      useChildSelectStore().loadChildren(),
    ])
    router.replace('/parent')
  } catch (e: any) {
    error.value = e.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

// tsparticles 初始化 — 使用 loadSlim
async function particlesInit(engine: Engine) {
  await loadSlim(engine)
}

// 粒子配置：漂浮的 emoji + 柔和彩球
const particlesOptions: ISourceOptions = {
  fpsLimit: 60,
  background: { color: 'transparent' },
  particles: {
    number: { value: 18, density: { enable: true } },
    shape: {
      type: 'emoji',
      options: {
        emoji: {
          value: ['🌱', '⭐', '🍀', '☀️', '🌸', '🌿', '✨', '🦋', '🌈', '💫'],
          font: '16px',
        },
      },
    },
    opacity: { value: { min: 0.55, max: 0.9 }, animation: { enable: true, speed: 0.4, minimumValue: 0.4 } },
    size: { value: { min: 14, max: 26 } },
    move: {
      enable: true,
      speed: { min: 0.4, max: 1.2 },
      direction: 'none',
      random: true,
      straight: false,
      outModes: { default: 'out' },
      warp: false,
    },
    rotate: {
      value: { min: 0, max: 360 },
      animation: { enable: true, speed: 3, sync: false },
    },
  },
  interactivity: {
    events: {
      onHover: { enable: true, mode: 'bubble' },
    },
    modes: {
      bubble: { distance: 120, size: 32, duration: 0.4, opacity: 1 },
    },
  },
  detectRetina: true,
}
</script>

<template>
  <div class="login-page">

    <!-- tsparticles 全屏背景 -->
    <vue-particles
      id="login-particles"
      class="particles-bg"
      :options="particlesOptions"
      :init="particlesInit"
    />

    <!-- 渐变底色层 -->
    <div class="gradient-bg" />

    <!-- 卡片入场动画 -->
    <Transition name="card-in" appear>
      <div class="login-card">

        <!-- logo -->
        <div class="logo">
          <div class="tree-wrap">
            <span class="tree-icon">🌳</span>
            <span class="ring r1" />
            <span class="ring r2" />
          </div>
          <h1>小树成长岛</h1>
          <p class="subtitle">家长专属管理平台</p>
        </div>

        <!-- tab 切换 -->
        <div class="tab-bar">
          <button :class="{ active: mode === 'login' }" @click="mode = 'login'; error = ''">登录</button>
          <button :class="{ active: mode === 'register' }" @click="mode = 'register'; error = ''">注册</button>
          <div class="tab-slider" :class="{ right: mode === 'register' }" />
        </div>

        <!-- 表单 (带切换动画) -->
        <Transition name="form-slide" mode="out-in">
          <div :key="mode" class="form">
            <label class="field">
              <span>用户名</span>
              <div class="input-row">
                <span class="icon">👤</span>
                <input v-model="name" class="inp" placeholder="请输入用户名" autocomplete="username" @keyup.enter="submit" />
              </div>
            </label>

            <label class="field">
              <span>密码</span>
              <div class="input-row">
                <span class="icon">🔑</span>
                <input v-model="password" class="inp" type="password" placeholder="请输入密码" autocomplete="current-password" @keyup.enter="submit" />
              </div>
            </label>

            <label v-if="mode === 'register'" class="field">
              <span>确认密码</span>
              <div class="input-row">
                <span class="icon">🔒</span>
                <input v-model="confirmPassword" class="inp" type="password" placeholder="再次输入密码" @keyup.enter="submit" />
              </div>
            </label>

            <Transition name="err">
              <p v-if="error" class="error-msg">⚠️ {{ error }}</p>
            </Transition>

            <button class="submit-btn" :disabled="loading" @click="submit">
              <span v-if="!loading" class="btn-text">
                {{ mode === 'login' ? '登 录' : '注 册' }}
                <span class="arrow">→</span>
              </span>
              <span v-else class="dot-loader">
                <i /><i /><i />
              </span>
            </button>

            <p v-if="mode === 'register'" class="hint">注册后默认为家长账号，可在控制台添加孩子。</p>
          </div>
        </Transition>

      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ── 页面容器 ── */
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  position: relative;
  overflow: hidden;
}

/* ── 渐变底色 ── */
.gradient-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%, #d4f7dc 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 80% 90%, #fde68a 0%, transparent 50%),
    radial-gradient(ellipse 50% 60% at 60% 40%, #c7eafb 0%, transparent 50%),
    linear-gradient(160deg, #f0fdf4 0%, #fefce8 50%, #eff6ff 100%);
}

/* ── tsparticles ── */
.particles-bg {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

/* ── 卡片入场 ── */
.card-in-enter-active {
  transition: opacity 0.55s ease, transform 0.55s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.card-in-enter-from {
  opacity: 0;
  transform: translateY(40px) scale(0.94);
}

/* ── 登录卡片 ── */
.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 560px;
  margin: 40px;
  padding: 52px 44px 42px;
  border-radius: 36px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(32px) saturate(180%);
  -webkit-backdrop-filter: blur(32px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 16px 56px rgba(60, 130, 70, 0.18),
    0 6px 16px rgba(0, 0, 0, 0.10),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* ── Logo ── */
.logo {
  text-align: center;
  padding-bottom: 8px;
}
.tree-wrap {
  display: inline-block;
  position: relative;
  width: 92px;
  height: 92px;
  margin-bottom: 14px;
}
.tree-icon {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: 56px;
  animation: sway 4s ease-in-out infinite;
  transform-origin: bottom center;
  z-index: 2;
}
@keyframes sway {
  0%, 100% { transform: rotate(-4deg); }
  50%       { transform: rotate(4deg); }
}
.ring {
  position: absolute;
  inset: 0;
  margin: auto;
  border-radius: 50%;
  border: 2px solid rgba(76, 175, 80, 0.25);
  animation: ring-out 3s ease-out infinite;
}
.r1 { width: 72px; height: 72px; animation-delay: 0s; }
.r2 { width: 92px; height: 92px; animation-delay: 1s; }
@keyframes ring-out {
  0%   { transform: scale(0.7); opacity: 0.7; }
  100% { transform: scale(1.5); opacity: 0; }
}
.logo h1 {
  font-size: 28px;
  font-weight: 950;
  color: #2e7d32;
  letter-spacing: -0.03em;
  margin: 0 0 5px;
}
.subtitle {
  font-size: 15px;
  color: #94a3b8;
  margin: 0;
  font-weight: 600;
}

/* ── Tab ── */
.tab-bar {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #f1f5f1;
  border-radius: 18px;
  padding: 6px;
}
.tab-bar button {
  position: relative;
  z-index: 2;
  border: none;
  background: transparent;
  padding: 13px 12px;
  border-radius: 14px;
  font-weight: 800;
  font-size: 17px;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.2s;
}
.tab-bar button.active { color: #2e7d32; }
.tab-slider {
  position: absolute;
  top: 6px; left: 6px;
  bottom: 6px;
  width: calc(50% - 6px);
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tab-slider.right { transform: translateX(100%); }

/* ── 表单切换 ── */
.form-slide-enter-active,
.form-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.form-slide-enter-from { opacity: 0; transform: translateX(10px); }
.form-slide-leave-to  { opacity: 0; transform: translateX(-10px); }

/* ── 表单 ── */
.form { display: flex; flex-direction: column; gap: 18px; }

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  font-size: 15px;
  font-weight: 800;
  color: #475569;
}
.input-row {
  position: relative;
  display: flex;
  align-items: center;
}
.icon {
  position: absolute;
  left: 16px;
  font-size: 21px;
  pointer-events: none;
  z-index: 2;
}
.inp {
  width: 100%;
  padding: 15px 18px 15px 50px;
  border-radius: 16px;
  border: 2px solid #e2e8f0;
  background: rgba(255,255,255,0.9);
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}
.inp::placeholder { color: #cbd5e1; font-size: 16px; }
.inp:focus {
  border-color: #4caf50;
  box-shadow: 0 0 0 5px rgba(76,175,80,0.18);
}

/* ── 错误 ── */
.err-enter-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.err-enter-from   { opacity: 0; transform: scale(0.92) translateY(-4px); }
.err-leave-active { transition: all 0.15s ease; }
.err-leave-to     { opacity: 0; }

.error-msg {
  margin: 0;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  font-size: 15px;
  font-weight: 700;
}

/* ── 提交按钮 ── */
.submit-btn {
  margin-top: 6px;
  height: 56px;
  border-radius: 16px;
  border: none;
  background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 0.06em;
  cursor: pointer;
  display: grid;
  place-items: center;
  box-shadow: 0 6px 22px rgba(46,125,50,0.38), 0 1px 0 rgba(255,255,255,0.15) inset;
  transition: transform 0.15s, box-shadow 0.15s;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(46,125,50,0.45);
}
.submit-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 4px 14px rgba(46,125,50,0.3);
}
.submit-btn:disabled { opacity: 0.65; cursor: not-allowed; }

.btn-text {
  display: flex;
  align-items: center;
  gap: 10px;
}
.arrow {
  font-size: 22px;
  transition: transform 0.2s;
}
.submit-btn:hover:not(:disabled) .arrow { transform: translateX(5px); }

/* ── 三点加载 ── */
.dot-loader {
  display: flex;
  gap: 6px;
  align-items: center;
}
.dot-loader i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  animation: dot-bounce 1s ease-in-out infinite;
  font-style: normal;
}
.dot-loader i:nth-child(2) { animation-delay: 0.15s; }
.dot-loader i:nth-child(3) { animation-delay: 0.3s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
  40%           { transform: translateY(-8px); opacity: 1; }
}

.hint {
  font-size: 14px;
  color: #94a3b8;
  text-align: center;
  margin: 0;
  line-height: 1.6;
  padding: 0 6px;
}
</style>
