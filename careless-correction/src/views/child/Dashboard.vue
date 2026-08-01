<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMistakeCategoryIcon, getMistakeCategoryLabel } from '../../utils/constants'
import { useMistakeStore, useUserStore } from '../../stores'

const router = useRouter()
const userStore = useUserStore()
const mistakeStore = useMistakeStore()

interface ChecklistRecord {
  date: string
  checkedCount: number
  submitted: boolean
}

const records = ref<ChecklistRecord[]>([])
const loading = ref(true)

const todayStr = new Date().toLocaleDateString('zh-CN')

function loadHistory() {
  loading.value = true
  const list: ChecklistRecord[] = []
  const prefix = 'cc-checklist-'
  const submittedPrefix = 'cc-checklist-submitted-'

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (!key || !key.startsWith(prefix) || key.startsWith(submittedPrefix)) continue

    const date = key.slice(prefix.length)
    if (!date) continue

    try {
      const raw = localStorage.getItem(key)
      const state: Record<string, boolean> = raw ? JSON.parse(raw) : {}
      const checkedCount = Object.values(state).filter(Boolean).length
      const submitted = localStorage.getItem(`${submittedPrefix}${date}`) === 'true'

      // Only show records that have at least one check or are submitted
      if (checkedCount > 0 || submitted) {
        list.push({ date, checkedCount, submitted })
      }
    } catch { /* skip invalid */ }
  }

  // Sort by date descending (newest first)
  list.sort((a, b) => {
    const da = new Date(a.date.replace(/\//g, '-'))
    const db = new Date(b.date.replace(/\//g, '-'))
    return db.getTime() - da.getTime()
  })

  records.value = list
  loading.value = false
}

const hasTodayRecord = computed(() =>
  records.value.some(r => r.date === todayStr)
)

function goTodayChecklist() {
  router.push('/habit')
}

function editRecord(date: string) {
  router.push({ path: '/habit', query: { date } })
}

function deleteRecord(date: string) {
  localStorage.removeItem(`cc-checklist-${date}`)
  localStorage.removeItem(`cc-checklist-submitted-${date}`)
  loadHistory()
}

function formatDate(date: string): string {
  const isToday = date === todayStr
  const isYesterday = (() => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    return date === yesterday.toLocaleDateString('zh-CN')
  })()
  if (isToday) return '今天'
  if (isYesterday) return '昨天'
  return date
}

// ── 题库统计 ──
const mistakeCount = computed(() => mistakeStore.records.length)
const subjectStats = computed(() => {
  const map: Record<string, number> = {}
  for (const r of mistakeStore.records) {
    map[r.subject] = (map[r.subject] || 0) + 1
  }
  return Object.entries(map).map(([subject, count]) => ({ subject, count }))
})

function formatMistakeDate(iso: string): string {
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function removeMistake(id: string) {
  mistakeStore.removeRecord(id)
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="page dashboard-page">
    <!-- Header -->
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📋 打卡记录</span>
        <h1>打卡历史</h1>
        <p class="lead">查看每日打卡记录，点击编辑可修改历史打卡内容。</p>
        <button class="btn secondary" @click="goTodayChecklist">
          {{ hasTodayRecord ? '查看今日打卡' : '去今日打卡' }}
        </button>
      </div>
      <div class="panel">
        <div class="card-title">
          <h2>{{ userStore.profile.name || '我的' }}</h2>
          <span class="tag">☀️ {{ userStore.sunlightPoints }}</span>
        </div>
        <div class="kpi">
          <strong>{{ records.length }}</strong>
          <span>累计打卡天数</span>
        </div>
        <p class="lead" style="margin-top:8px">
          已提交 {{ records.filter(r => r.submitted).length }} 天
        </p>
      </div>
    </section>

    <!-- Two-column layout: History + Mistake Bank side by side -->
    <div class="lists-grid">
      <!-- History List -->
      <section class="panel">
        <div class="card-title">
          <h2>打卡历史</h2>
          <span class="tag">{{ records.length }} 条记录</span>
        </div>

        <div v-if="loading" class="empty-state">
          <p>⏳ 加载中...</p>
        </div>

        <div v-else-if="records.length" class="history-list">
          <div
            v-for="record in records"
            :key="record.date"
            class="history-row"
            :class="{ 'is-today': record.date === todayStr }"
          >
            <div class="history-date">
              <span class="date-text">{{ formatDate(record.date) }}</span>
              <span class="date-full">{{ record.date }}</span>
            </div>
            <div class="history-stats">
              <span class="stat-checked">✓ {{ record.checkedCount }} 项</span>
              <span
                class="stat-status"
                :class="record.submitted ? 'submitted' : 'pending'"
              >
                {{ record.submitted ? '已提交' : '未提交' }}
              </span>
            </div>
            <div class="history-actions">
              <button class="btn ghost edit-btn" @click="editRecord(record.date)">✏️ 编辑</button>
              <button class="btn ghost delete-btn" @click="deleteRecord(record.date)">🗑️</button>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon">📝</div>
          <p>暂无打卡记录</p>
          <button class="btn" @click="goTodayChecklist">去今日打卡</button>
        </div>
      </section>

      <!-- 题库列表 -->
      <section class="panel">
        <div class="card-title">
          <h2>📚 我的题库</h2>
          <span class="tag">{{ mistakeCount }} 题</span>
        </div>

        <!-- 学科统计 -->
        <div v-if="subjectStats.length" class="subject-stats">
          <span v-for="s in subjectStats" :key="s.subject" class="subject-tag">
            {{ s.subject }} {{ s.count }}
          </span>
        </div>

        <!-- 题库列表 -->
        <div v-if="mistakeCount" class="mistake-list">
          <div
            v-for="record in mistakeStore.records"
            :key="record.id"
            class="mistake-row"
          >
            <span class="mistake-icon">{{ getMistakeCategoryIcon(record.category || '') }}</span>
            <div class="mistake-info">
              <strong>{{ record.subject }}</strong>
              <div class="mistake-tags">
                <span v-if="record.category" class="mistake-cat-tag">
                  {{ getMistakeCategoryLabel(record.category) }}
                </span>
                <span v-if="record.subjectTag" class="mistake-sub-tag">{{ record.subjectTag }}</span>
                <span v-if="record.isCarelessness === false" class="mistake-type-tag">知识漏洞</span>
              </div>
            </div>
            <span class="mistake-date">{{ formatMistakeDate(record.createdAt) }}</span>
            <button class="btn ghost delete-mistake-btn" @click="removeMistake(record.id)">🗑️</button>
          </div>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon">📖</div>
          <p>暂无错题记录</p>
          <button class="btn" @click="router.push('/mistake')">去添加错题</button>
        </div>

        <button v-if="mistakeCount" class="btn ghost view-all-btn" @click="router.push('/mistake')">
          查看全部错题 →
        </button>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  width: 100%;
}

.lists-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.kpi {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 12px 0;
}
.kpi strong {
  font-size: 32px;
  font-weight: 900;
  color: var(--primary);
}
.kpi span {
  color: var(--muted);
  font-size: 14px;
  font-weight: 700;
}

/* ── History List ── */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.history-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #fff;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.history-row:hover {
  border-color: var(--primary-2, #a5d6a7);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.history-row.is-today {
  border-color: var(--primary);
  background: #f6fff0;
}
.history-date {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 90px;
}
.date-text {
  font-size: 18px;
  font-weight: 800;
  color: var(--ink);
}
.date-full {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
}
.history-stats {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}
.stat-checked {
  font-size: 15px;
  font-weight: 700;
  color: var(--primary);
}
.stat-status {
  font-size: 13px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}
.stat-status.submitted {
  background: #e8f5e9;
  color: #2e7d32;
}
.stat-status.pending {
  background: #fff3e0;
  color: #e65100;
}
.history-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.edit-btn {
  padding: 8px 16px;
  font-size: 14px;
}
.delete-btn {
  padding: 8px 10px;
  font-size: 14px;
}

/* ── Empty State ── */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--muted);
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.empty-state p {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}

/* ── 题库列表 ── */
.subject-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}
.subject-tag {
  padding: 4px 12px;
  border-radius: 999px;
  background: #e3f2fd;
  color: #1565c0;
  font-size: 13px;
  font-weight: 700;
}
.mistake-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mistake-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.mistake-row:hover {
  border-color: var(--primary-2, #a5d6a7);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.mistake-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.mistake-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.mistake-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.mistake-cat-tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: #d9f5c8;
  color: var(--primary);
  font-size: 12px;
  font-weight: 800;
}
.mistake-sub-tag {
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
}
.mistake-type-tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: #fff3e0;
  color: #e65100;
  font-size: 12px;
  font-weight: 700;
}
.mistake-date {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
  flex-shrink: 0;
}
.delete-mistake-btn {
  padding: 6px 10px;
  font-size: 13px;
  flex-shrink: 0;
}
.view-all-btn {
  margin-top: 14px;
  width: 100%;
}

@media (max-width: 768px) {
  .lists-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .history-row {
    flex-wrap: wrap;
    gap: 10px;
  }
  .history-date {
    min-width: 0;
  }
  .history-stats {
    width: 100%;
  }
  .mistake-row {
    flex-wrap: wrap;
  }
}
</style>
