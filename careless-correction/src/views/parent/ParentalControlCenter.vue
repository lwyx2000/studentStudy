<script setup lang="ts">
import { computed } from 'vue'
import { useParentStore } from '../../stores'
const parentStore = useParentStore()
const difficultyLabel = computed(() => ['阳光', '微风', '挑战'][parentStore.settings.difficultyLevel - 1])
function toggle(key: 'dailyReminder' | 'achievementNotification' | 'weeklyReport' | 'schoolSync') {
  parentStore.updateSettings({ [key]: !parentStore.settings[key] })
}
function updateDifficulty(event: Event) {
  parentStore.updateSettings({ difficultyLevel: Number((event.target as HTMLInputElement).value) })
}
</script>
<template><div class="page"><section class="page-hero"><div class="hero-card"><span class="eyebrow">🧭 家长控制中心</span><h1>调任务密度，不替孩子完成</h1><p class="lead">家长端用于设置难度天气、通知边界和学校共享。所有设置会本地保存，后续可对接后端 parent settings API。</p></div><div class="panel"><div class="card-title"><h2>难度天气</h2><span class="tag">{{ difficultyLabel }} · Level {{ parentStore.settings.difficultyLevel }}</span></div><input :value="parentStore.settings.difficultyLevel" class="range" min="1" max="3" type="range" @input="updateDifficulty"/><p class="lead">1 阳光 · 2 微风 · 3 挑战</p></div></section><section class="grid-3"><button class="soft-card setting" @click="toggle('dailyReminder')"><div class="icon-tile">🔔</div><h2>每日小岛提醒</h2><p class="lead">{{ parentStore.settings.dailyReminder ? '已开启' : '已关闭' }}：只提醒环境准备，不替孩子催作业。</p></button><button class="soft-card setting" @click="toggle('achievementNotification')"><div class="icon-tile">🎆</div><h2>成就烟花</h2><p class="lead">{{ parentStore.settings.achievementNotification ? '已开启' : '已关闭' }}：里程碑时发送温和庆祝反馈。</p></button><button class="soft-card setting" @click="toggle('schoolSync')"><div class="icon-tile">🏫</div><h2>学校共享</h2><p class="lead">{{ parentStore.settings.schoolSync ? '已开启' : '已关闭' }}：仅分享匿名化成长趋势。</p></button></section><section class="panel"><div class="card-title"><h2>家长自查红线</h2><span class="tag">非侵入提示</span></div><div class="list"><div class="list-row"><span>今天是否克制了催促？</span><b>待勾选</b></div><div class="list-row"><span>今天是否让孩子自己收尾？</span><b>待勾选</b></div></div></section></div></template>
<style scoped>.setting{text-align:left;color:inherit}</style>
