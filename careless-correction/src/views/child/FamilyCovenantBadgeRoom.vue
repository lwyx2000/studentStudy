<script setup lang="ts">
import { computed, ref } from 'vue'
import { useBadgeStore, useUserStore } from '../../stores'

const badgeStore = useBadgeStore()
const userStore = useUserStore()
const goal = ref('连续 5 天睡前整理书桌 3 分钟')
const reward = ref('周五亲子电影夜')
const childSignature = ref('')
const parentSignature = ref('')
const childSigned = ref(false)
const parentSigned = ref(false)
const covenantCreated = ref(false)
const warning = computed(() => /钱|现金|元|红包/.test(reward.value))
const justUnlocked = ref<string | null>(null)

function signChild() { childSigned.value = true }
function signParent() { parentSigned.value = true }

function createCovenant() {
  if (warning.value) return
  badgeStore.addCovenant({
    goal: goal.value,
    reward: reward.value,
    childSignature: childSignature.value || userStore.profile.name || 'Leo',
    parentSignature: parentSignature.value || 'Mum',
  })
  covenantCreated.value = true
  setTimeout(() => { covenantCreated.value = false }, 3000)
}

function handleUnlock(id: string) {
  if (badgeStore.badges.find(b => b.id === id)?.unlocked) return
  badgeStore.unlockBadge(id)
  justUnlocked.value = id
  userStore.addSunlightPoints(50)
  setTimeout(() => { justUnlocked.value = null }, 2000)
}
</script>

<template>
  <div class="page">
    <div v-if="badgeStore.confettiActive" class="confetti-overlay">
      <div class="confetti-content">🎉 🏅 ✨ 🎊 🎉</div>
    </div>
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🏅 成长契约与勋章馆</span>
        <h1>把短期打卡变成内在成就</h1>
        <p class="lead">家庭电子契约强调共同选择、非物质奖励和可完成的小目标；勋章馆用明亮反馈庆祝真实努力。</p>
      </div>
      <div class="panel">
        <div class="card-title"><h2>已解锁 {{ badgeStore.unlockedCount }}/{{ badgeStore.badges.length }}</h2><span class="tag">+50 阳光/勋章</span></div>
        <div class="celebrate">🎉🏅🎉</div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel contract">
        <div class="card-title"><h2>家庭电子契约书</h2><span class="tag">共同签署</span></div>
        <label>本周目标<input v-model="goal" class="input" /></label>
        <label>奖励内容<input v-model="reward" class="input" /></label>
        <p v-if="warning" class="warning">循证研究提示：过度物质奖励可能削弱内在驱动力，建议选择"免家务一天""亲子电影夜"或"1 小时乐高时间"。</p>
        <div class="signatures">
          <div class="sign-box" :class="{ signed: childSigned }">
            <strong>孩子签名</strong>
            <input v-if="!childSigned" v-model="childSignature" class="input signature" :placeholder="userStore.profile.name || 'Leo'" />
            <span v-else class="signed-name">{{ childSignature || userStore.profile.name || 'Leo' }}</span>
            <button v-if="!childSigned" class="btn ghost sm-btn" @click="signChild">签署</button>
            <span v-else class="tag ok">已签署 ✓</span>
          </div>
          <div class="sign-box" :class="{ signed: parentSigned }">
            <strong>家长签名</strong>
            <input v-if="!parentSigned" v-model="parentSignature" class="input signature" placeholder="家长" />
            <span v-else class="signed-name">{{ parentSignature || 'Mum' }}</span>
            <button v-if="!parentSigned" class="btn ghost sm-btn" @click="signParent">签署</button>
            <span v-else class="tag ok">已签署 ✓</span>
          </div>
        </div>
        <button class="btn" :disabled="warning || (!childSigned && !parentSigned)" @click="createCovenant">生成家庭法案</button>
        <p v-if="covenantCreated" class="note ok">契约已生成并生效！全家一起加油！</p>
        <div class="list" v-if="badgeStore.covenants.length">
          <div v-for="covenant in badgeStore.covenants" :key="covenant.id" class="list-row">
            <span>{{ covenant.goal }}</span>
            <b>{{ covenant.reward }}</b>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="card-title"><h2>蜂巢勋章陈列架</h2><span class="tag">点击解锁</span></div>
        <div class="honeycomb">
          <button
            v-for="badge in badgeStore.badges"
            :key="badge.id"
            class="badge-cell"
            :class="{ locked: !badge.unlocked, 'just-unlocked': justUnlocked === badge.id }"
            @click="handleUnlock(badge.id)"
          >
            <span class="badge-icon">{{ badge.icon }}</span>
            <small>{{ badge.name }}</small>
            <span v-if="badge.unlocked" class="badge-check">✓</span>
          </button>
        </div>
        <p class="lead" style="margin-top:12px">解锁勋章可获得 +50 阳光值奖励，继续完成每日习惯解锁更多勋章！</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.celebrate { height: 190px; display: grid; place-items: center; font-size: 72px; border-radius: 28px; background: linear-gradient(135deg,#fff4bc,#dcffd5); }
.contract { display: grid; gap: 14px; }
.signatures { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.sign-box { padding: 14px; border-radius: 18px; background: var(--surface-2); display: flex; flex-direction: column; gap: 8px; transition: all .2s; }
.sign-box.signed { background: #ecfdf5; border: 1px solid #86efac; }
.signature { font-family: cursive; font-size: 20px; }
.signed-name { font-family: cursive; font-size: 20px; color: var(--primary); }
.sm-btn { padding: 8px 14px !important; font-size: 13px !important; }
.warning { padding: 14px; border-radius: 18px; background: #fff8d9; color: #6e5e00; line-height: 1.6; }
.note.ok { padding: 14px; border-radius: 18px; background: #ecfdf5; color: #059669; }
.tag.ok { background: #ecfdf5; color: #059669; }
.confetti-overlay { position: fixed; inset: 0; z-index: 99; display: grid; place-items: center; background: rgba(255,255,255,.5); animation: fadeOut 3s ease forwards; pointer-events: none; }
.confetti-content { font-size: 80px; animation: popBounce .6s ease; }
.honeycomb { display: grid; grid-template-columns: repeat(3, minmax(90px, 1fr)); gap: 14px; }
.badge-cell { padding: 18px; border-radius: 20px; background: linear-gradient(135deg,#fbe270,#80dc67); border: 0; color: var(--ink); display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center; transition: all .3s ease; position: relative; }
.badge-cell.locked { filter: grayscale(1); opacity: .38; }
.badge-cell.locked:hover { opacity: .6; transform: scale(1.05); }
.badge-cell.just-unlocked { animation: unlockPop .5s ease; }
.badge-icon { font-size: 32px; }
.badge-cell small { font-weight: 900; font-size: 12px; }
.badge-check { position: absolute; top: 6px; right: 8px; color: var(--primary); font-weight: 900; font-size: 14px; }
button:disabled { opacity: .5; cursor: not-allowed; }
@keyframes popBounce { 0% { transform: scale(0.3); } 50% { transform: scale(1.2); } 100% { transform: scale(1); } }
@keyframes unlockPop { 0% { transform: scale(1) rotateY(0); } 50% { transform: scale(1.15) rotateY(180deg); } 100% { transform: scale(1) rotateY(360deg); } }
@keyframes fadeOut { 0%,70% { opacity: 1; } 100% { opacity: 0; } }
</style>
