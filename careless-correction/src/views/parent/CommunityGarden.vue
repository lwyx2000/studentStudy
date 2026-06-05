<script setup lang="ts">
import { ref } from 'vue'
import { Button, Card, Title, Input, Divider } from 'animal-island-vue'

const searchQuery = ref('')
const newPostTitle = ref('')


const sharedCovenants = [
  { id: '1', goal: '屏幕时间协议', likes: 24 },
  { id: '2', goal: '晨间流程共识', likes: 18 },
]

const discussionPosts = [
  { id: '1', title: '孩子总是丢橡皮怎么办?', tags: ['物品追踪'], preview: '我家孩子一个月丢了5块橡皮...', replyCount: 12, hasExpertAnswer: true },
  { id: '2', title: '如何避免过度催促?', tags: ['CBT'], preview: '每次看到孩子磨蹭就想喊...', replyCount: 8, hasExpertAnswer: true },
  { id: '3', title: '高年级番茄钟实践分享', tags: ['时间管理'], preview: '5年级开始用番茄钟...', replyCount: 5, hasExpertAnswer: false },
]

const peerDimensions = [
  { name: '专注', childValue: 65, avgValue: 50 },
  { name: '规律', childValue: 50, avgValue: 55 },
  { name: '同理心', childValue: 70, avgValue: 60 },
  { name: '耐心', childValue: 45, avgValue: 50 },
  { name: '分享', childValue: 60, avgValue: 55 },
  { name: '自理', childValue: 40, avgValue: 45 },
]

const expertTip = {
  author: 'Dr. Aris',
  content: '让孩子自己设定目标比家长代为设定有效3倍。本周试试让孩子自己选择一个想改进的习惯。',
}
</script>

<template>
  <div class="community-garden">
    <Title size="large" color="app-green">社区花园</Title>

    <div class="garden-grid">
      <div class="garden-main">
        <Card color="app-teal" type="title">
          <template #title>
            <Title size="middle" color="app-teal">同龄成长趋势</Title>
          </template>
          <div class="peer-radar">
            <div class="radar-bars">
              <div v-for="dim in peerDimensions" :key="dim.name" class="dim-row">
                <span class="dim-name">{{ dim.name }}</span>
                <div class="dim-bars">
                  <div class="bar child" :style="{ width: dim.childValue + '%' }">{{ dim.childValue }}</div>
                  <div class="bar avg" :style="{ width: dim.avgValue + '%' }">{{ dim.avgValue }}</div>
                </div>
              </div>
            </div>
            <div class="legend">
              <span class="legend-child">你的小树苗</span>
              <span class="legend-avg">岛上平均</span>
            </div>
          </div>
          <div class="anonymized-badge">
            < name="icon-design" /> 100% 匿名化数据
          </div>
        </Card>

        <Divider type="wave-yellow" />

        <Card color="warm-peach-pink" type="title">
          <template #title>
            <Title size="middle" color="warm-peach-pink">每周专家提示</Title>
          </template>
          <div class="sticky-note-tip">
            <div class="expert-avatar">
              <Icon name="icon-critterpedia" />
              <span>{{ expertTip.author }}</span>
            </div>
            <p>{{ expertTip.content }}</p>
            <Button type="text" size="small"><Icon name="icon-shopping" /></Button>
          </div>
        </Card>

        <Divider type="wave-yellow" />

        <Card color="app-yellow" type="title">
          <template #title>
            <Title size="middle" color="app-yellow">契约画廊</Title>
          </template>
          <div class="covenant-list">
            <div v-for="c in sharedCovenants" :key="c.id" class="shared-covenant">
              <span>{{ c.goal }}</span>
              <span class="likes"><Icon name="icon-miles" /> {{ c.likes }}</span>
            </div>
            <Button type="primary" size="small">分享一个契约</Button>
          </div>
        </Card>
      </div>

      <div class="garden-forum">
        <Card color="app-blue" type="title">
          <template #title>
            <Title size="middle" color="app-blue">家长问答板</Title>
          </template>
          <div class="forum-section">
            <Input v-model="searchQuery" placeholder="搜索讨论..." shadow>
              <template #prefix><Icon name="icon-variant" /></template>
            </Input>
            <Button type="primary" block @click="newPostTitle = ''">发新帖</Button>
            <div class="post-list">
              <Card v-for="post in discussionPosts" :key="post.id" color="default">
                <div class="post-card">
                  <Title size="small" color="app-blue">{{ post.title }}</Title>
                  <div class="post-tags">
                    <span v-for="tag in post.tags" :key="tag" class="post-tag">{{ tag }}</span>
                  </div>
                  <p class="post-preview">{{ post.preview }}</p>
                  <div class="post-footer">
                    <span>{{ post.replyCount }} 回复</span>
                    <span v-if="post.hasExpertAnswer" class="expert-badge">专家已回答!</span>
                  </div>
                </div>
              </Card>
            </div>
            <Button type="dashed" block>查看更多讨论</Button>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.community-garden {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.garden-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: 16px;
}

.peer-radar {
  padding: 8px;
}

.radar-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dim-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dim-name {
  width: 40px;
  font-weight: 600;
}

.dim-bars {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.bar {
  height: 14px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  padding-left: 8px;
  font-size: 11px;
  font-weight: 600;
}

.bar.child {
  background: #8ac68a;
  color: white;
}

.bar.avg {
  background: #e4e3d8;
  color: #725d42;
  border: 1px dashed #9a835a;
}

.legend {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.legend-child {
  color: #8ac68a;
  font-weight: 700;
}

.legend-avg {
  color: #725d42;
}

.anonymized-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #106e00;
  margin-top: 8px;
}

.sticky-note-tip {
  padding: 16px;
  background: #fbe270;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.expert-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #00677e;
}

.covenant-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shared-covenant {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f7f3df;
  border-radius: 12px;
}

.likes {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #fc736d;
}

.forum-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.post-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.post-tags {
  display: flex;
  gap: 4px;
}

.post-tag {
  padding: 2px 8px;
  background: #82d5bb;
  color: white;
  border-radius: 8px;
  font-size: 12px;
}

.post-preview {
  font-size: 14px;
  color: #725d42;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.expert-badge {
  background: #f7cd67;
  color: #725d42;
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 600;
}
</style>