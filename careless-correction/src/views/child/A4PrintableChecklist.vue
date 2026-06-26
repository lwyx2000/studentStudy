<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { weekdays } from '../../utils/constants'
import { useParentStore, useTaskStore, useUserStore } from '../../stores'

const userStore = useUserStore()
const taskStore = useTaskStore()
const parentStore = useParentStore()

const completionText = computed(() => `${taskStore.weeklyProgress}/${taskStore.todayTasks.length}`)

const selectedTaskIds = ref<Set<string>>(new Set(taskStore.todayTasks.map(t => t.id)))

const allTasks = computed(() => {
  const parentTasks = parentStore.parentTaskTemplates.map(t => ({
    ...t,
    status: 'pending' as const,
  }))
  const seen = new Set(taskStore.todayTasks.map(t => t.id))
  const merged = [...taskStore.todayTasks]
  for (const pt of parentTasks) {
    if (!seen.has(pt.id)) {
      merged.push(pt)
      seen.add(pt.id)
    }
  }
  return merged
})

const selectedTasks = computed(() =>
  allTasks.value.filter(t => selectedTaskIds.value.has(t.id))
)

function toggleTask(id: string) {
  if (selectedTaskIds.value.has(id)) selectedTaskIds.value.delete(id)
  else selectedTaskIds.value.add(id)
}

function selectAllTasks() {
  selectedTaskIds.value = new Set(allTasks.value.map(t => t.id))
}

function printPage() {
  window.print()
}

const router = useRouter()

const now = new Date()
const dateStr = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`

const downloading = ref(false)

async function downloadPdf() {
  if (downloading.value) return
  downloading.value = true
  try {
    const element = document.getElementById('printable-sheet')
    if (!element) return

    const html2canvas = (await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js', 'html2canvas'))
    const { jsPDF } = (await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js', 'jspdf'))

    await new Promise(r => setTimeout(r, 300))

    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width

    let srcY = 0
    let remainingHeight = pdfHeight
    const pageHeight = pdf.internal.pageSize.getHeight()

    while (remainingHeight > 0) {
      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = Math.min(canvas.width * pageHeight / pdfWidth, canvas.height - srcY)
      const ctx = pageCanvas.getContext('2d')!
      ctx.drawImage(canvas, 0, srcY, canvas.width, pageCanvas.height, 0, 0, canvas.width, pageCanvas.height)
      const pageData = pageCanvas.toDataURL('image/png')

      if (srcY > 0) pdf.addPage()
      pdf.addImage(pageData, 'PNG', 0, 0, pdfWidth, (pageCanvas.height * pdfWidth) / canvas.width)
      srcY += pageCanvas.height
      remainingHeight -= pageCanvas.height
    }

    pdf.save(`${userStore.profile.name || '我的'}的每周打卡单_第${taskStore.currentWeekHabit.weekNumber}周.pdf`)
  } catch {
    alert('下载失败，请检查网络连接后重试')
  } finally {
    downloading.value = false
  }
}

function loadScript(url: string, name: 'html2canvas' | 'jspdf'): Promise<any> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${url}"]`)
    if (existing) {
      if (name === 'jspdf') resolve({ jsPDF: (window as any).jspdf.jsPDF })
      else resolve((window as any).html2canvas)
      return
    }
    const script = document.createElement('script')
    script.src = url
    script.onload = () => {
      if (name === 'jspdf') resolve({ jsPDF: (window as any).jspdf.jsPDF })
      else resolve((window as any).html2canvas)
    }
    script.onerror = reject
    document.head.appendChild(script)
  })
}
</script>

<template>
  <div class="page printable-page">
    <!-- Control Panel (not shown in print) -->
    <section class="panel no-print">
      <div class="card-title">
        <button class="btn ghost" style="padding:6px 14px;font-size:14px" @click="router.back()">← 返回</button>
        <h1>A4 纸质打卡单</h1>
        <div style="display:flex;gap:8px">
          <button class="btn secondary" :disabled="downloading" @click="downloadPdf">
            {{ downloading ? '⏳ 生成中...' : '📥 下载 PDF' }}
          </button>
          <button class="btn" @click="printPage">🖨️ 打印</button>
        </div>
      </div>
      <p class="lead">适合贴在书桌或冰箱上，把每日微习惯从 App 转移到真实环境。完成后拍照上传，系统将扫描勾选痕迹生成成长报告。</p>

      <div style="margin-top:12px">
        <div class="card-title">
          <h3>选择打卡任务</h3>
          <div style="display:flex;gap:8px">
            <button class="btn ghost" style="padding:4px 12px;font-size:13px" @click="selectAllTasks">全选</button>
            <button class="btn ghost" style="padding:4px 12px;font-size:13px" @click="selectedTaskIds = new Set()">取消</button>
          </div>
        </div>
        <div class="task-select-grid">
          <label v-for="task in allTasks" :key="task.id" class="task-check-card" :class="{ checked: selectedTaskIds.has(task.id) }">
            <input type="checkbox" :checked="selectedTaskIds.has(task.id)" @change="toggleTask(task.id)" />
            <span style="font-size:24px;flex-shrink:0">{{ task.icon }}</span>
            <div style="flex:1;min-width:0">
              <strong style="font-size:15px;display:block">{{ task.title }}</strong>
              <span class="muted" style="font-size:13px">{{ task.description }}</span>
            </div>
          </label>
        </div>
      </div>
    </section>

    <!-- Printable Sheet -->
    <section id="printable-sheet" class="sheet">
      <!-- Header -->
      <header class="print-header">
        <h1>小树成长岛 · 每周打卡单</h1>
        <p class="print-meta">
          <span>姓名：<strong>{{ userStore.profile.name || '______' }}</strong></span>
          <span class="sep">|</span>
          <span>年级：{{ userStore.profile.grade || '___' }} 年级</span>
          <span class="sep">|</span>
          <span>日期：{{ dateStr }}</span>
          <span class="sep">|</span>
          <span>完成：{{ completionText }}</span>
        </p>
      </header>

      <!-- ── Section 1: 本周习惯 ── -->
      <section class="print-section">
        <div class="section-header">
          <span class="section-icon">🌱</span>
          <h2>本周习惯：{{ taskStore.currentWeekHabit.title }}</h2>
          <span class="section-tag">第 {{ taskStore.currentWeekHabit.weekNumber }} 周</span>
        </div>
        <p class="section-desc">每天按步骤完成后在对应格子打 ✓，家长只观察不催促</p>
        <table class="check-table habit-table" v-if="taskStore.currentWeekHabit.steps.length">
          <thead>
            <tr>
              <th class="col-date">日期</th>
              <th v-for="step in taskStore.currentWeekHabit.steps" :key="step.order" class="col-step">
                {{ step.order }}. {{ step.instruction }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="day in weekdays" :key="day">
              <td class="col-date">{{ day }}</td>
              <td v-for="step in taskStore.currentWeekHabit.steps" :key="step.order" class="col-check">□</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="section-empty">暂未设置本周习惯步骤。</p>
      </section>

      <!-- ── Section 2: 每日任务 ── -->
      <section class="print-section">
        <div class="section-header">
          <span class="section-icon">📋</span>
          <h2>每日任务清单</h2>
          <span class="section-tag">{{ selectedTasks.length }} 项任务</span>
        </div>
        <p class="section-desc">每天完成后在对应项打 ✓，周末拍照上传</p>
        <div class="task-list" v-if="selectedTasks.length">
          <div v-for="task in selectedTasks" :key="task.id" class="task-row-item">
            <span class="task-row-check">□</span>
            <span class="task-row-icon">{{ task.icon }}</span>
            <div class="task-row-text">
              <strong>{{ task.title }}</strong>
              <span v-if="task.description" class="muted">{{ task.description }}</span>
            </div>
            <!-- Sub-tasks for print -->
            <div v-if="task.subTasks?.length" class="ptr-subtasks">
              <div v-for="sub in task.subTasks" :key="sub.id" class="ptr-subtask-item">
                <span class="ptr-sub-check">□</span>
                <span>{{ sub.title }}</span>
                <span v-if="sub.weekDay" class="ptr-sub-badge">{{ sub.weekDay === 'weekday' ? '平时' : sub.weekDay === 'weekend' ? '周末' : sub.weekDay }}</span>
              </div>
            </div>
          </div>
          <div class="task-row-item note-row">
            <span class="task-row-check">□</span>
            <span class="task-row-icon">💬</span>
            <div class="task-row-text">
              <strong>家长寄语</strong>
              <span class="muted">鼓励的话 / 注意提醒的事项</span>
            </div>
          </div>
        </div>
        <p v-else class="section-empty">请在左侧勾选要打印的任务。</p>
      </section>

      <!-- Footer -->
      <footer class="print-footer">
        <div class="footer-note">
          周末拍照上传至系统 → AI 自动识别勾选情况，生成本周成长报告。
        </div>
        <div class="footer-qr-placeholder"></div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
/* ── Page Layout ── */
.printable-page {
  align-items: center;
  display: flex;
  flex-direction: column;
}

/* ── Task Selector (Screen Only) ── */
.task-select-grid {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}
.task-check-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 2px solid var(--line);
  background: #fff;
  cursor: pointer;
  transition: all .12s ease;
}
.task-check-card:hover {
  border-color: var(--primary-2);
  background: #f6fddc;
}
.task-check-card.checked {
  border-color: var(--primary);
  background: #ecffd9;
}
.task-check-card input { display: none; }

/* ── Printable Sheet ── */
.sheet {
  width: min(794px, 100%);
  min-height: 1123px;
  background: white;
  color: #111;
  padding: 50px 44px;
  border: 1px solid #ddd;
  box-shadow: var(--shadow);
  font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
}

/* ── Header ── */
.print-header {
  text-align: center;
  border-bottom: 4px solid #2e7d32;
  padding-bottom: 18px;
  margin-bottom: 28px;
}
.print-header h1 {
  font-size: 26px;
  color: #2e7d32;
  margin: 0 0 8px;
  letter-spacing: 2px;
}
.print-meta {
  font-size: 15px;
  color: #555;
  margin: 0;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
}
.print-meta .sep {
  color: #ccc;
  margin: 0 6px;
}

/* ── Section Headers ── */
.print-section {
  margin-bottom: 32px;
  page-break-inside: avoid;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.section-icon {
  font-size: 22px;
  flex-shrink: 0;
}
.section-header h2 {
  font-size: 18px;
  margin: 0;
  flex: 1;
}
.section-tag {
  font-size: 12px;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 3px 12px;
  border-radius: 999px;
  font-weight: 700;
  flex-shrink: 0;
}
.section-desc {
  font-size: 13px;
  color: #888;
  margin: 0 0 12px 32px;
}
.section-empty {
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 14px;
  border: 1px dashed #ddd;
  border-radius: 8px;
}

/* ── Check Tables ── */
.check-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
  border: 2px solid #333;
}
.check-table thead th {
  background: #e8f5e9;
  font-weight: 800;
  padding: 12px 10px;
  border: 1px solid #333;
  text-align: center;
  vertical-align: middle;
  font-size: 14px;
  color: #111;
}
.check-table tbody td {
  padding: 0;
  border: 1px solid #333;
  text-align: center;
  vertical-align: middle;
}

/* Date column */
.col-date {
  width: 64px;
  min-width: 64px;
  font-weight: 800;
  font-size: 15px !important;
  padding: 12px 8px !important;
  background: #f5f5f5;
  white-space: nowrap;
}

/* Habit step column */
.col-step {
  min-width: 100px;
  line-height: 1.4;
}

/* Checkbox cells (for habits table) */
.col-check {
  font-size: 30px !important;
  line-height: 1;
  padding: 10px 6px !important;
  color: #111;
  letter-spacing: 0;
}

/* ── Task List (simple vertical checklist) ── */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.task-row-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 2px solid #333;
}
.task-row-item:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}
.task-row-item:last-child {
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}
.task-row-check {
  font-size: 30px;
  line-height: 1;
  color: #111;
  flex-shrink: 0;
}
.task-row-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.task-row-text {
  flex: 1;
  min-width: 0;
}
.task-row-text strong {
  display: block;
  font-size: 16px;
}
.task-row-text .muted {
  display: block;
  font-size: 13px;
  color: #666;
  margin-top: 2px;
}
.note-row {
  background: #f9f9f9;
}

/* ── Sub-tasks in printable checklist ── */
.ptr-subtasks {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 0 2px 42px;
  border-top: 1px dashed #ccc;
  margin-top: 4px;
}
.ptr-subtask-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #555;
  padding: 4px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #f9f9f9;
}
.ptr-sub-check {
  font-size: 16px;
  line-height: 1;
  color: #888;
}
.ptr-sub-badge {
  font-size: 10px;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 700;
}

/* ── Footer ── */
.print-footer {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 2px solid #2e7d32;
  text-align: center;
}
.footer-note {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

/* ── Screen-only elements ── */
.no-print {
  margin-bottom: 24px;
}

/* ── Print Styles ── */
@media print {
  .no-print,
  .topbar,
  .sidebar {
    display: none !important;
  }
  .sheet {
    box-shadow: none;
    border: 0;
    width: 100%;
    min-height: auto;
    padding: 0;
    margin: 0;
  }
  body {
    margin: 0;
    padding: 0;
  }
  .printable-page {
    padding: 0;
    margin: 0;
  }
  .check-table {
    border: 2px solid #000 !important;
  }
  .check-table thead th {
    background: #e8f5e9 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    border: 1px solid #000 !important;
  }
  .check-table tbody td {
    border: 1px solid #000 !important;
  }
  .col-date {
    background: #f5f5f5 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .print-header h1 {
    font-size: 24px;
  }
  .print-header {
    border-bottom-color: #000;
  }
  .print-footer {
    border-top-color: #000;
  }
  .section-tag {
    background: #e8f5e9 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .col-check {
    font-size: 28px !important;
  }
  .task-row-item {
    border-color: #000 !important;
  }
  .task-row-check {
    color: #000 !important;
  }
  .ptr-subtasks {
    border-top-color: #999 !important;
  }
  .ptr-subtask-item {
    border-color: #999 !important;
    background: #f5f5f5 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .ptr-sub-badge {
    background: #e8f5e9 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
</style>
