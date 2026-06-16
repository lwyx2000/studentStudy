<script setup lang="ts">
import { ref } from 'vue'
import { useParentStore } from '../../stores'
const parentStore = useParentStore()
const title = ref('')
const content = ref('')
const tag = ref('经验')
function publish() {
  if (!title.value.trim()) return
  parentStore.createPost({ title: title.value, content: content.value || '分享经验', tags: [tag.value || '经验'] })
  title.value = ''
  content.value = ''
  tag.value = '经验'
}
</script>
<template><div class="page"><section class="page-hero"><div class="hero-card"><span class="eyebrow">🌸 社区花园</span><h1>让家长互相支持，而不是比较</h1><p class="lead">社区只展示方法和过程，不展示成绩排名；专家回答会标记“可尝试的小实验”。</p></div><div class="panel"><div class="card-title"><h2>发布经验</h2><button class="btn" @click="publish">发布</button></div><input v-model="title" class="input" placeholder="例如：三分区书包第 5 天反馈" /><input v-model="content" class="input" style="margin-top:8px" placeholder="经验内容" /><select v-model="tag" class="input" style="margin-top:8px"><option>经验</option><option>收纳</option><option>边界感</option><option>奖励系统</option></select></div></section><section class="grid-2"><div class="panel"><div class="card-title"><h2>经验帖子</h2><span class="tag">{{ parentStore.discussionPosts.length }} 条</span></div><div class="list"><div v-for="post in parentStore.discussionPosts" :key="post.id" class="list-row"><span>{{ post.title }}</span><span>{{ post.hasExpertAnswer ? '专家已答' : `${post.replyCount} 回复` }}</span></div></div></div><div class="panel"><div class="card-title"><h2>花园守则</h2><span class="tag">安全感</span></div><p class="lead">不晒分数、不贴标签、不诊断他人孩子。只讨论环境、流程和可观察行为。</p></div></section></div></template>
