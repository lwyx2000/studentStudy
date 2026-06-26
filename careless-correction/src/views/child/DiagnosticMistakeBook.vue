<script setup lang="ts">
import { ref } from 'vue'
import { getMistakeCategoryIcon, getMistakeCategoryLabel, MISTAKE_CATEGORIES, subjectOptions } from '../../utils/constants'
import { useMistakeStore } from '../../stores'
import { api } from '../../utils/api'

const mistakeStore = useMistakeStore()
const subject = ref(subjectOptions[0])
const subjectTag = ref('')
const category = ref<string>('')
const imageName = ref('')
const imageFile = ref<File | null>(null)
const saved = ref(false)
const uploading = ref(false)

function handleImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    imageName.value = file.name
    imageFile.value = file
  }
}

async function saveRecord() {
  if (!imageFile.value) return
  uploading.value = true
  try {
    // 上传图片到后端，获取真实 URL
    const formData = new FormData()
    formData.append('image', imageFile.value)
    const { imageUrl } = await api.mistakes.uploadImage(formData)
    mistakeStore.addRecord({
      subject: subject.value,
      imageUrl,
      subjectTag: subjectTag.value || undefined,
      category: (category.value || undefined) as any,
      isCarelessness: !!category.value,
    })
    imageName.value = ''
    imageFile.value = null
    subjectTag.value = ''
    category.value = ''
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (e) {
    // 离线降级：用本地文件名
    mistakeStore.addRecord({
      subject: subject.value,
      imageUrl: imageName.value,
      subjectTag: subjectTag.value || undefined,
      category: (category.value || undefined) as any,
      isCarelessness: !!category.value,
    })
    imageName.value = ''
    imageFile.value = null
    subjectTag.value = ''
    category.value = ''
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } finally {
    uploading.value = false
  }
}

function removeRecord(id: string) {
  mistakeStore.removeRecord(id)
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📚 我的题库</span>
        <h1>记录和整理错题</h1>
        <p class="lead">拍照上传错题照片，添加学科标签，构建自己的专属复习题库。随时查看和回顾错题，巩固知识薄弱点。</p>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>题库概览</h2>
          <span class="tag">{{ mistakeStore.records.length }} 题</span>
        </div>
        <div class="kpi">
          <strong>{{ mistakeStore.records.length }}</strong>
          <span>已收录错题</span>
        </div>
        <div class="subject-summary" style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          <span
            v-for="sub in [...new Set(mistakeStore.records.map(r => r.subject))]"
            :key="sub"
            class="tag"
          >{{ sub }}</span>
          <span v-if="!mistakeStore.records.length" class="muted">暂无错题记录</span>
        </div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>添加错题</h2>
          <span v-if="saved" class="tag" style="background:#ecffd9;color:var(--primary)">✓ 已保存</span>
        </div>
        <label class="photo-drop">
          <span style="font-size:48px">📸</span>
          <strong>{{ imageName || '上传错题照片' }}</strong>
          <span>点击选择错题照片，支持拍照或从相册选取</span>
          <input type="file" accept="image/*" @change="handleImage" />
        </label>
        <label style="display:block;margin-top:16px;font-weight:800">
          学科
          <select v-model="subject" class="input" style="margin-top:6px">
            <option>数学</option>
            <option>语文</option>
            <option>英语</option>
            <option>科学</option>
            <option>其他</option>
          </select>
        </label>
        <label style="display:block;margin-top:12px;font-weight:800">
          粗心类型（可选）
          <div class="category-grid" style="margin-top:6px">
            <button
              v-for="cat in MISTAKE_CATEGORIES"
              :key="cat.value"
              class="cat-btn"
              :class="{ active: category === cat.value }"
              @click="category = category === cat.value ? '' : cat.value"
            >
              <span class="cat-icon">{{ cat.icon }}</span>
              <span class="cat-label">{{ cat.label }}</span>
            </button>
          </div>
        </label>
        <label style="display:block;margin-top:12px;font-weight:800">
          知识点标签（可选）
          <input
            v-model="subjectTag"
            class="input"
            style="margin-top:6px"
            placeholder="例如：分数运算、阅读细节定位"
          />
        </label>
        <button
          class="btn"
          style="margin-top:18px;width:100%"
          :disabled="!imageName || uploading"
          @click="saveRecord"
        >
          {{ uploading ? '上传中...' : '保存到题库' }}
        </button>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>错题列表</h2>
          <span class="tag">{{ mistakeStore.records.length }} 条记录</span>
        </div>
        <div v-if="mistakeStore.records.length" class="list">
          <div
            v-for="record in mistakeStore.records"
            :key="record.id"
            class="list-row"
          >
            <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
              <span style="font-size:28px;flex-shrink:0">{{ getMistakeCategoryIcon(record.category || '') }}</span>
              <div style="min-width:0">
                <strong>{{ record.subject }}</strong>
                <div v-if="record.category || record.subjectTag" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:2px">
                  <span v-if="record.category" class="mini-cat-tag">
                    {{ getMistakeCategoryLabel(record.category) }}
                  </span>
                  <span v-if="record.subjectTag" class="muted" style="font-size:13px">
                    {{ record.subjectTag }}
                  </span>
                </div>
                <span v-if="record.isCarelessness === false" class="muted" style="font-size:12px">知识漏洞</span>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
              <span class="tag" style="font-size:12px">
                {{ new Date(record.createdAt).toLocaleDateString() }}
              </span>
              <button
                class="btn ghost"
                style="padding:6px 10px;font-size:13px"
                @click="removeRecord(record.id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
        <p v-else class="muted" style="text-align:center;padding:32px">
          还没有错题记录，拍张照片开始吧 📷
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.photo-drop {
  min-height: 200px;
  border-radius: 28px;
  background: linear-gradient(180deg, #eef8ff, #fff);
  border: 2px dashed var(--blue);
  display: grid;
  place-items: center;
  text-align: center;
  font-size: 48px;
  color: var(--muted);
  padding: 24px;
  cursor: pointer;
  transition: border-color .15s ease;
}
.photo-drop:hover {
  border-color: var(--primary);
}
.photo-drop strong,
.photo-drop span {
  display: block;
  font-size: 17px;
}
.photo-drop input {
  display: none;
}
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.cat-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px;
  border-radius: 14px;
  border: 2px solid var(--line);
  background: #fff;
  cursor: pointer;
  transition: all .12s ease;
  font: inherit;
}
.cat-btn:hover {
  border-color: var(--primary-2);
  background: #f6fddc;
}
.cat-btn.active {
  border-color: var(--primary);
  background: #ecffd9;
  box-shadow: 0 2px 8px rgba(16,110,0,.15);
}
.cat-icon {
  font-size: 22px;
  line-height: 1;
}
.cat-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
  text-align: center;
}
.mini-cat-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: #d9f5c8;
  color: var(--primary);
  font-size: 12px;
  font-weight: 800;
}
button:disabled {
  opacity: .5;
  cursor: not-allowed;
}
</style>
