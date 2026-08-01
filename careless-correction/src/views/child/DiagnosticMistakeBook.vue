<script setup lang="ts">
import { ref, computed } from 'vue'
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

// Tab state
const activeTab = ref<'list' | 'review'>('list')

// Review state
const reviewingId = ref<string | null>(null)
const reviewCanResolve = ref<boolean | null>(null)
const reviewConfidence = ref(3)
const reviewSubmitting = ref(false)

const dueReviews = computed(() => mistakeStore.dueReviews)
const dueCount = computed(() => dueReviews.value.length)

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

function startReview(id: string) {
  reviewingId.value = id
  reviewCanResolve.value = null
  reviewConfidence.value = 3
}

function cancelReview() {
  reviewingId.value = null
  reviewCanResolve.value = null
  reviewConfidence.value = 3
}

async function submitReview(id: string) {
  if (reviewCanResolve.value === null) return
  reviewSubmitting.value = true
  try {
    await mistakeStore.reviewRecord(id, reviewCanResolve.value, reviewConfidence.value)
    reviewingId.value = null
    reviewCanResolve.value = null
    reviewConfidence.value = 3
  } finally {
    reviewSubmitting.value = false
  }
}

const confidenceLabels = ['完全不会', '不太确定', '有一半把握', '比较有信心', '完全掌握了']
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
        <div style="display:flex;gap:16px;margin-top:12px">
          <div class="kpi-mini">
            <strong style="color:#e65100">{{ dueCount }}</strong>
            <span>待复习</span>
          </div>
          <div class="kpi-mini">
            <strong style="color:var(--primary)">{{ mistakeStore.records.filter(r => r.resolved).length }}</strong>
            <span>已掌握</span>
          </div>
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

    <!-- Tab Navigation -->
    <div class="tab-nav">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'list' }"
        @click="activeTab = 'list'"
      >
        📋 错题列表
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'review' }"
        @click="activeTab = 'review'"
      >
        🔄 待复习
        <span v-if="dueCount" class="badge-count">{{ dueCount }}</span>
      </button>
    </div>

    <!-- ── Tab: 错题列表 ── -->
    <template v-if="activeTab === 'list'">
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
              :class="{ 'record-resolved': record.resolved }"
            >
              <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
                <span style="font-size:28px;flex-shrink:0">{{ getMistakeCategoryIcon(record.category || '') }}</span>
                <div style="min-width:0">
                  <strong>
                    {{ record.subject }}
                    <span v-if="record.resolved" class="resolved-badge">✅ 已掌握</span>
                  </strong>
                  <div v-if="record.category || record.subjectTag" style="display:flex;gap:6px;flex-wrap:wrap;margin-top:2px">
                    <span v-if="record.category" class="mini-cat-tag">
                      {{ getMistakeCategoryLabel(record.category) }}
                    </span>
                    <span v-if="record.subjectTag" class="muted" style="font-size:13px">
                      {{ record.subjectTag }}
                    </span>
                  </div>
                  <span v-if="record.isCarelessness === false" class="muted" style="font-size:12px">知识漏洞</span>
                  <div v-if="record.nextReviewAt && !record.resolved" class="review-info">
                    <span v-if="new Date(record.nextReviewAt) <= new Date()" class="review-due">🔴 待复习</span>
                    <span v-else class="muted" style="font-size:11px">
                      下次复习：{{ new Date(record.nextReviewAt).toLocaleDateString() }}
                    </span>
                    <span v-if="record.reviewCount" class="muted" style="font-size:11px">
                      · 已复习 {{ record.reviewCount }} 次
                    </span>
                  </div>
                </div>
              </div>
              <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
                <span class="tag" style="font-size:12px">
                  {{ new Date(record.createdAt).toLocaleDateString() }}
                </span>
                <button
                  v-if="!record.resolved && record.nextReviewAt && new Date(record.nextReviewAt) <= new Date()"
                  class="btn review-btn"
                  style="padding:6px 10px;font-size:13px"
                  @click="startReview(record.id)"
                >
                  复习
                </button>
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
    </template>

    <!-- ── Tab: 待复习 ── -->
    <template v-if="activeTab === 'review'">
      <section class="review-section">
        <!-- Review modal / inline review -->
        <div v-if="reviewingId" class="panel review-panel">
          <div class="card-title">
            <h2>🔄 复习这道题</h2>
            <button class="btn ghost" style="padding:6px 14px;font-size:13px" @click="cancelReview">取消</button>
          </div>
          <p class="lead" style="font-size:14px;margin-bottom:16px">
            先看错题图片，然后回答：你现在能独立做对吗？
          </p>

          <!-- Show the mistake image -->
          <div
            v-if="mistakeStore.records.find(r => r.id === reviewingId)?.imageUrl"
            class="review-image-box"
          >
            <img
              :src="mistakeStore.records.find(r => r.id === reviewingId)!.imageUrl"
              alt="错题图片"
              class="review-image"
            />
          </div>

          <!-- Step 1: Can you resolve it? -->
          <div style="margin-top:16px">
            <label style="font-weight:800;display:block;margin-bottom:10px">
              你现在能独立做对这道题吗？
            </label>
            <div class="resolve-btns">
              <button
                class="resolve-btn"
                :class="{ active: reviewCanResolve === true, yes: reviewCanResolve === true }"
                @click="reviewCanResolve = true"
              >
                ✅ 能做对
              </button>
              <button
                class="resolve-btn"
                :class="{ active: reviewCanResolve === false, no: reviewCanResolve === false }"
                @click="reviewCanResolve = false"
              >
                ❌ 还不太会
              </button>
            </div>
          </div>

          <!-- Step 2: Confidence level (only if can resolve) -->
          <div v-if="reviewCanResolve === true" style="margin-top:16px">
            <label style="font-weight:800;display:block;margin-bottom:10px">
              你的信心等级：{{ reviewConfidence }} — {{ confidenceLabels[reviewConfidence - 1] }}
            </label>
            <input
              v-model.number="reviewConfidence"
              type="range"
              min="1"
              max="5"
              step="1"
              class="confidence-slider"
            />
            <div class="confidence-labels">
              <span v-for="(_, i) in confidenceLabels" :key="i" class="confidence-dot" :class="{ active: reviewConfidence === i + 1 }">
                {{ i + 1 }}
              </span>
            </div>
          </div>

          <button
            class="btn"
            style="margin-top:20px;width:100%"
            :disabled="reviewCanResolve === null || reviewSubmitting"
            @click="submitReview(reviewingId!)"
          >
            {{ reviewSubmitting ? '提交中...' : '提交复习结果' }}
          </button>
        </div>

        <!-- Due review list -->
        <div v-else-if="dueCount" class="panel">
          <div class="card-title">
            <h2>🔄 待复习错题</h2>
            <span class="tag" style="background:#fff3e0;color:#e65100">{{ dueCount }} 题待复习</span>
          </div>
          <p class="lead" style="font-size:14px;margin-bottom:12px">
            这些错题到了复习时间。点击「开始复习」检验自己是否已经掌握。
          </p>
          <div class="list">
            <div
              v-for="record in dueReviews"
              :key="record.id"
              class="list-row due-row"
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
                  <div style="margin-top:2px">
                    <span class="muted" style="font-size:11px">
                      已复习 {{ record.reviewCount || 0 }} 次 · 到期日 {{ new Date(record.nextReviewAt!).toLocaleDateString() }}
                    </span>
                  </div>
                </div>
              </div>
              <button
                class="btn review-btn"
                style="flex-shrink:0"
                @click="startReview(record.id)"
              >
                开始复习
              </button>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="panel" style="text-align:center;padding:48px">
          <span style="font-size:64px;display:block;margin-bottom:16px">🎉</span>
          <h2 style="margin-bottom:8px">暂无待复习错题</h2>
          <p class="lead">所有错题都复习过了！新录入的错题会在 3 天后提醒你复习。</p>
        </div>
      </section>
    </template>
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

/* Tab navigation */
.tab-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}
.tab-btn {
  position: relative;
  padding: 12px 24px;
  border-radius: 16px 16px 0 0;
  border: 2px solid var(--line);
  border-bottom: none;
  background: var(--surface-2);
  font: inherit;
  font-weight: 800;
  font-size: 15px;
  cursor: pointer;
  transition: all .12s ease;
  color: var(--muted);
}
.tab-btn.active {
  background: #fff;
  color: var(--ink);
  border-color: var(--primary-2);
}
.badge-count {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #e65100;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  border-radius: 999px;
  min-width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  padding: 0 6px;
}

/* KPI mini */
.kpi-mini {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.kpi-mini strong {
  font-size: 24px;
}
.kpi-mini span {
  font-size: 12px;
  color: var(--muted);
}

/* Review styles */
.record-resolved {
  opacity: .7;
  background: #f8fdf5;
}
.resolved-badge {
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  margin-left: 6px;
}
.review-info {
  margin-top: 4px;
}
.review-due {
  font-size: 11px;
  font-weight: 800;
  color: #e65100;
}
.review-btn {
  background: linear-gradient(135deg, #ff9800, #f57c00) !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(245, 124, 0, .3);
}
.review-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 124, 0, .4);
}
.due-row {
  border-left: 4px solid #ff9800;
}

/* Review panel */
.review-panel {
  border: 2px solid #ff9800;
  background: #fffbf5;
}
.review-image-box {
  border-radius: 16px;
  overflow: hidden;
  background: #f5f5f5;
  text-align: center;
  max-height: 300px;
}
.review-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
}
.resolve-btns {
  display: flex;
  gap: 12px;
}
.resolve-btn {
  flex: 1;
  padding: 16px;
  border-radius: 16px;
  border: 2px solid var(--line);
  background: #fff;
  font: inherit;
  font-weight: 800;
  font-size: 16px;
  cursor: pointer;
  transition: all .12s ease;
}
.resolve-btn:hover {
  border-color: var(--primary-2);
}
.resolve-btn.active.yes {
  border-color: var(--primary);
  background: #ecffd9;
  color: var(--primary);
}
.resolve-btn.active.no {
  border-color: #e65100;
  background: #fff3e0;
  color: #e65100;
}
.confidence-slider {
  width: 100%;
  accent-color: var(--primary);
}
.confidence-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
}
.confidence-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--line);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
  transition: all .12s ease;
}
.confidence-dot.active {
  border-color: var(--primary);
  background: var(--primary);
  color: #fff;
}
</style>
