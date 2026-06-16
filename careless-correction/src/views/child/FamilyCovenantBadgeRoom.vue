<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBadgeStore, useUserStore } from '../../stores'

const badgeStore = useBadgeStore()
const userStore = useUserStore()
const goal = ref('连续 5 天睡前整理书桌 3 分钟')
const reward = ref('周五亲子电影夜')
const childSignature = ref(userStore.profile.name || 'Leo')
const parentSignature = ref('')
const warning = computed(() => /钱|现金|元|红包/.test(reward.value))
function createCovenant() {
  if (warning.value) return
  badgeStore.addCovenant({ goal: goal.value, reward: reward.value, childSignature: childSignature.value, parentSignature: parentSignature.value })
}
</script>

<template>
  <div class="page">
    <div v-if="badgeStore.confettiActive" class="confetti">🎉 🏅 ✨ 🎊</div>
    <section class="page-hero"><div class="hero-card"><span class="eyebrow">🏅 成长契约与勋章馆</span><h1>把短期打卡变成内在成就</h1><p class="lead">家庭电子契约强调共同选择、非物质奖励和可完成的小目标；勋章馆用明亮反馈庆祝真实努力。</p></div><div class="panel"><div class="card-title"><h2>已解锁 {{ badgeStore.unlockedCount }}/{{ badgeStore.badges.length }}</h2><span class="tag">镜面空间勋章</span></div><div class="celebrate">🎉🏅🎉</div></div></section>
    <section class="grid-2"><div class="panel contract"><div class="card-title"><h2>家庭电子契约书</h2><span class="tag">共同签署</span></div><label>本周目标<input v-model="goal" class="input" /></label><label>奖励内容<input v-model="reward" class="input" /></label><p v-if="warning" class="warning">循证研究提示：过度物质奖励可能削弱内在驱动力，建议选择“免家务一天”“亲子电影夜”或“1 小时乐高时间”。</p><div class="signatures"><label>孩子签名<input v-model="childSignature" class="input signature" /></label><label>家长签名<input v-model="parentSignature" class="input signature" /></label></div><button class="btn" :disabled="warning" @click="createCovenant">生成家庭法案</button><div class="list"><div v-for="covenant in badgeStore.covenants" :key="covenant.id" class="list-row"><span>{{ covenant.goal }}</span><b>{{ covenant.reward }}</b></div></div></div><div class="panel"><div class="card-title"><h2>蜂巢勋章陈列架</h2><span class="tag">点击模拟解锁</span></div><div class="honeycomb"><button v-for="badge in badgeStore.badges" :key="badge.id" class="badge-cell" :class="{ locked: !badge.unlocked }" @click="badgeStore.unlockBadge(badge.id)"><span>{{ badge.icon }}</span><small>{{ badge.name }}</small></button></div></div></section>
  </div>
</template>
<style scoped>.celebrate{height:190px;display:grid;place-items:center;font-size:72px;border-radius:28px;background:linear-gradient(135deg,#fff4bc,#dcffd5)}.contract{display:grid;gap:14px}.signatures{display:grid;grid-template-columns:1fr 1fr;gap:12px}.signature{font-family:cursive;font-size:20px}.warning{padding:14px;border-radius:18px;background:#fff8d9;color:#6e5e00;line-height:1.6}.confetti{position:fixed;inset:0;z-index:99;display:grid;place-items:center;font-size:80px;background:rgba(255,255,255,.35);animation:pop .9s ease infinite alternate}.badge-cell{border:0;color:var(--ink)}.badge-cell span{display:block;font-size:26px}.badge-cell small{font-weight:900}@keyframes pop{from{transform:scale(.95)}to{transform:scale(1.02)}}button:disabled{opacity:.5;cursor:not-allowed}</style>
