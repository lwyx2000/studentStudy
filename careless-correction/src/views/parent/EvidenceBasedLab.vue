<script setup lang="ts">
import { useParentStore } from '../../stores'
const parentStore = useParentStore()
</script>
<template><div class="page"><section class="page-hero"><div class="hero-card"><span class="eyebrow">🔬 循证实验室</span><h1>把每个建议都解释清楚</h1><p class="lead">家长可查看执行功能、CBT 行为链、奖励系统和家庭边界的通俗化资料，理解为什么系统不建议高压催促。</p></div><div class="panel"><div class="card-title"><h2>推荐阅读</h2><span class="tag">{{ parentStore.articles.length }} 篇</span></div><p class="lead">基于当前设置推荐“执行功能”和“非物质奖励”资料。</p></div></section><section class="grid-3"><div v-for="article in parentStore.articles" :key="article.id" class="soft-card"><div class="icon-tile">📚</div><h2>{{ article.title }}</h2><p class="lead">{{ article.summary }}</p><span class="tag">{{ article.category }} · {{ article.readingTime }} 分钟</span></div></section></div></template>
