<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button, Card, Title, Input, Divider } from 'animal-island-vue'

const searchQuery = ref('')
const activeCategory = ref('all')

const categories = [
  { label: '全部', value: 'all' },
  { label: '执行功能', value: 'executive_function' },
  { label: '焦虑与CBT', value: 'anxiety_cbt' },
]

const suggestedArticles = [
  { id: '1', title: '为什么指读能提高解题准确率', category: '执行功能', type: 'article', readingTime: 8 },
  { id: '2', title: '暂停按钮技术: 让孩子学会自我中断', category: 'CBT', type: 'video', readingTime: 12 },
  { id: '3', title: '物品收纳与元认知发展', category: '执行功能', type: 'article', readingTime: 6 },
]

const libraryArticles = [
  { id: '4', title: '如何用番茄钟培养时间感知', category: '执行功能', type: 'article', imageUrl: '' },
  { id: '5', title: '减少催促的5个替代策略', category: 'CBT', type: 'video', imageUrl: '' },
  { id: '6', title: '草稿纸整洁与计算准确率', category: '执行功能', type: 'article', imageUrl: '' },
  { id: '7', title: '情绪温度计: 教孩子识别焦虑', category: '焦虑与CBT', type: 'cbt', imageUrl: '' },
  { id: '8', title: '家庭契约的科学依据', category: 'CBT', type: 'article', imageUrl: '' },
  { id: '9', title: '舒尔特方格训练原理', category: '执行功能', type: 'video', imageUrl: '' },
]

const filteredArticles = computed(() => {
  if (activeCategory.value === 'all') return libraryArticles
  return libraryArticles.filter(a => {
    if (activeCategory.value === 'executive_function') return a.category === '执行功能'
    if (activeCategory.value === 'anxiety_cbt') return a.category === 'CBT' || a.category === '焦虑与CBT'
    return true
  })
})
</script>

<template>
  <div class="evidence-lab">
    <Title size="large" color="purple">循证实验室</Title>

    <div class="search-bar">
      <Input v-model="searchQuery" placeholder="搜索文章、视频、CBT资源..." size="large" shadow>
        <template #prefix>< name="icon-variant" /></template>
      </Input>
    </div>

    <Divider type="wave-yellow" />

    <Card color="app-teal" type="title">
      <template #title>
        <Title size="middle" color="app-teal">为您推荐</Title>
      </template>
      <div class="suggested-carousel">
        <div class="carousel-scroll">
          <Card v-for="article in suggestedArticles" :key="article.id" :color="article.type === 'video' ? 'purple' : 'app-teal'">
            <div class="sticky-note-article">
              <Title size="small" :color="article.type === 'video' ? 'purple' : 'app-teal'">{{ article.title }}</Title>
              <div class="article-meta">
                <span class="article-tag">{{ article.category }}</span>
                <span class="reading-time">{{ article.readingTime }}分钟阅读</span>
              </div>
              <Button type="primary" size="small">阅读全文</Button>
            </div>
          </Card>
        </div>
      </div>
    </Card>

    <Divider type="dashed-brown" />

    <div class="bento-section">
      <Card color="app-green" type="title" class="bento-large">
        <template #title>
          <Title size="middle" color="app-green">习惯背后的科学</Title>
        </template>
        <div class="bento-grid">
          <Card color="app-green" class="feature-card">
            <Title size="small" color="app-green">为什么指读能提高解题准确率</Title>
            <span class="tag executive">元认知</span>
            <p>指读迫使大脑在视觉扫描时加入运动反馈回路...</p>
            <Button type="primary" size="small">深入了解</Button>
          </Card>
          <Card color="purple" class="small-card">
            <Title size="small" color="purple">暂停按钮技术</Title>
            <span class="tag cbt">CBT</span>
            <p>让孩子学会在冲动行为前按下心理暂停键</p>
            <Button type="dashed" size="small">观看视频</Button>
          </Card>
        </div>
      </Card>
    </div>

    <Divider type="wave-yellow" />

    <Card color="app-yellow" type="title">
      <template #title>
        <Title size="middle" color="app-yellow">浏览资源库</Title>
      </template>
      <div class="filter-chips">
        <Button
          v-for="cat in categories"
          :key="cat.value"
          :type="activeCategory === cat.value ? 'primary' : 'default'"
          size="small"
          @click="activeCategory = cat.value"
        >
          {{ cat.label }}
        </Button>
      </div>
      <div class="library-grid">
        <Card v-for="article in filteredArticles" :key="article.id" color="default">
          <div class="library-card-content">
            <div class="article-image-placeholder">
              <span class="emoji-icon">📄</span>
            </div>
            <Title size="small" color="default">{{ article.title }}</Title>
            <span class="article-type-tag" :class="article.type">{{ article.type === 'video' ? '视频' : article.type === 'cbt' ? 'CBT练习' : '文章' }}</span>
            <Button type="text" size="small">
              <Icon name="icon-shopping" />
            </Button>
          </div>
        </Card>
      </div>
    </Card>
  </div>
</template>

<style scoped>
.evidence-lab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-bar {
  padding: 0;
}

.suggested-carousel {
  overflow-x: auto;
}

.carousel-scroll {
  display: flex;
  gap: 16px;
  padding: 8px;
}

.sticky-note-article {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 240px;
}

.article-meta {
  display: flex;
  gap: 8px;
}

.article-tag {
  padding: 2px 8px;
  background: #8ac68a;
  color: white;
  border-radius: 8px;
  font-size: 12px;
}

.reading-time {
  font-size: 12px;
  color: #9a835a;
}

.bento-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}

.feature-card,
.small-card {
  padding: 8px;
}

.tag {
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  margin: 4px 0;
}

.tag.executive {
  background: #82d5bb;
  color: white;
}

.tag.cbt {
  background: #b77dee;
  color: white;
}

.filter-chips {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.library-card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.article-image-placeholder {
  height: 100px;
  background: #e4e3d8;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #9a835a;
}

.article-type-tag {
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
}

.article-type-tag.article {
  background: #82d5bb;
  color: white;
}

.article-type-tag.video {
  background: #b77dee;
  color: white;
}

.article-type-tag.cbt {
  background: #f7cd67;
  color: #725d42;
}
</style>