<script setup lang="ts">
import { ref } from 'vue'
import { useMistakeStore, useUserStore } from '../../stores'
import { Button, Card, Title, Divider, Input } from 'animal-island-vue'

const mistakeStore = useMistakeStore()
const userStore = useUserStore()
const knowledgePoint = ref('')

const uploadedImage = ref<string | null>(null)
const isCarelessness = ref<boolean | null>(null)
const selectedCategory = ref<string | null>(null)
const showDraftUpload = ref(false)
const draftImageUrl = ref<string | null>(null)

const mistakeCategories = [
  { value: 'symbol_error', label: '看错符号', icon: '+ -> -', color: 'app-red' },
  { value: 'unit_missing', label: '漏写单位', icon: '35 -> [ ]', color: 'app-orange' },
  { value: 'misread_details', label: '读题遗漏', icon: 'skip', color: 'app-pink' },
  { value: 'copying_error', label: '抄写错误', icon: 'copy', color: 'purple' },
  { value: 'skipped_step', label: '跳步计算', icon: '1->3', color: 'app-blue' },
  { value: 'rushing', label: '急于求成', icon: 'rush', color: 'app-teal' },
  { value: 'lost_focus', label: '注意力涣散', icon: 'fog', color: 'brown' },
  { value: 'messy_writing', label: '书写混乱', icon: 'mess', color: 'app-yellow' },
  { value: 'format_error', label: '格式错误', icon: 'fmt', color: 'lime-green' },
  { value: 'spelling_slip', label: '笔误/拼写', icon: 'typo', color: 'warm-peach-pink' },
  { value: 'wild_guess', label: '盲目猜测', icon: '?', color: 'yellow-green' },
  { value: 'something_else', label: '其他原因', icon: '...', color: 'default' },
]

function handleUpload() {
  uploadedImage.value = '/placeholder-mistake.png'
}

function selectCarelessness(val: boolean) {
  isCarelessness.value = val
}

function handleSave() {
  if (!uploadedImage.value || isCarelessness.value === null) return
  mistakeStore.addRecord({
    id: Date.now().toString(),
    subject: '数学',
    imageUrl: uploadedImage.value,
    isCarelessness: isCarelessness.value!,
    category: selectedCategory.value as any,
    createdAt: new Date().toISOString(),
    reviewScheduledAt: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
  })
}
</script>

<template>
  <div class="mistake-book">
    <Title size="large" color="app-teal">黄金一问智能错题本</Title>

    <Card type="dashed" class="upload-section">
      <div class="upload-zone" @click="handleUpload">
        < name="icon-camera" />
        <p>拍照上传错题 - 拍下难缠的杂草</p>
        <Button type="primary" v-if="!uploadedImage">拍照上传</Button>
        <div v-if="uploadedImage" class="uploaded-preview">
          <div class="preview-placeholder">错题图片已上传</div>
          <Button type="dashed" size="small" @click="handleUpload">重新上传</Button>
        </div>
      </div>
    </Card>

    <Divider type="wave-yellow" />

    <Card color="app-green" type="title" class="golden-question" v-if="uploadedImage">
      <template #title>
        <Title size="middle" color="app-green">黄金一问</Title>
      </template>
      <div class="question-content">
        <p class="question-text">{{ userStore.profile.name }}能重新自己立刻做对这道题吗?</p>
        <div class="answer-buttons">
          <Button
            :type="isCarelessness === true ? 'primary' : 'default'"
            size="large"
            @click="selectCarelessness(true)"
          >
            能! 只是粗心/执行功能错误
          </Button>
          <Button
            :type="isCarelessness === false ? 'primary' : 'default'"
            size="large"
            @click="selectCarelessness(false)"
          >
            不能/不确定 - 知识漏洞
          </Button>
        </div>
      </div>
    </Card>

    <Card v-if="isCarelessness === true" color="app-yellow" type="title">
      <template #title>
        <Title size="middle" color="app-yellow">选择粗心原因分类</Title>
      </template>
      <div class="category-grid">
        <div
          v-for="cat in mistakeCategories"
          :key="cat.value"
          class="category-item"
          :class="{ selected: selectedCategory === cat.value }"
          @click="selectedCategory = cat.value"
        >
          <div class="cat-icon">{{ cat.icon }}</div>
          <span class="cat-label">{{ cat.label }}</span>
        </div>
      </div>
    </Card>

    <Card v-if="isCarelessness === false" color="app-blue" type="title">
      <template #title>
        <Title size="middle" color="app-blue">标记知识漏洞</Title>
      </template>
      <p>此题不计入粗心数据统计，将归入知识漏洞档案。</p>
      <Input v-model="knowledgePoint" placeholder="输入知识点名称，如：两位数乘法" shadow />
    </Card>

    <Divider type="dashed-brown" />

    <Card type="dashed" class="draft-section">
      <div class="draft-header">
        <Title size="small" color="app-red">草稿纸痕迹分析 (可选)</Title>
        <Button type="text" @click="showDraftUpload = !showDraftUpload">
          {{ showDraftUpload ? '隐藏' : '查看草稿纸' }}
        </Button>
      </div>
      <div v-if="showDraftUpload" class="draft-upload">
        <div class="draft-upload-zone" @click="draftImageUrl = '/placeholder-draft.png'">
          <p>上传草稿纸照片，AI自动标出混乱区域</p>
        </div>
        <div v-if="draftImageUrl" class="draft-analysis">
          <div class="heatmap-overlay">
            <div class="chaos-zone" style="top: 30%; left: 20%; width: 40%; height: 25%;"></div>
            <p>红色区域为书写混乱区域，数字抄写时对位歪了</p>
          </div>
        </div>
      </div>
    </Card>

    <Button type="primary" block size="large" @click="handleSave" :disabled="!uploadedImage || isCarelessness === null">
      保存到错题本
    </Button>
  </div>
</template>



<style scoped>
.mistake-book {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px;
  border: 2px dashed #9a835a;
  border-radius: 16px;
  text-align: center;
  cursor: pointer;
}

.uploaded-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-placeholder {
  width: 200px;
  height: 150px;
  background: #e4e3d8;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #725d42;
}

.golden-question {
  margin: 8px 0;
}

.question-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-text {
  font-size: 18px;
  font-weight: 700;
  text-align: center;
  color: #725d42;
}

.answer-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 8px;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: #f7f3df;
  border: 2px solid #e4e3d8;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  transform: translateY(-2px);
  background: #e4e3d8;
}

.category-item.selected {
  border-color: #106e00;
  background: #8ac68a;
  color: white;
}

.cat-icon {
  font-size: 16px;
  font-weight: 700;
}

.cat-label {
  font-size: 12px;
}

.draft-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.draft-upload-zone {
  padding: 24px;
  border: 2px dashed #fc736d;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  color: #ba1a1a;
}

.heatmap-overlay {
  position: relative;
  padding: 16px;
  background: #f7f3df;
  border-radius: 8px;
}

.chaos-zone {
  position: absolute;
  background: rgba(252, 115, 109, 0.3);
  border: 2px solid #fc736d;
  border-radius: 4px;
}
</style>