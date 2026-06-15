<script setup lang="ts">
import { computed, ref } from 'vue'
import { useQuestionBankStore } from '../../stores'
import type { QuestionSubject, QuestionType, MistakeCategory } from '../../types'

const qb = useQuestionBankStore()

const activeTab = ref<'list' | 'add' | 'print' | 'chart' | 'import'>('list')
const filterSubject = ref<QuestionSubject | 'all'>('all')
const filterResolved = ref<'all' | 'unresolved' | 'resolved'>('unresolved')

const subjectOptions: { value: QuestionSubject; label: string }[] = [
  { value: 'math', label: '数学' },
  { value: 'chinese', label: '语文' },
  { value: 'english', label: '英语' },
  { value: 'science', label: '科学' },
  { value: 'other', label: '其他' },
]
const typeOptions: { value: QuestionType; label: string }[] = [
  { value: 'choice', label: '选择题' },
  { value: 'fill', label: '填空题' },
  { value: 'calculation', label: '计算题' },
  { value: 'composition', label: '作文/应用题' },
  { value: 'other', label: '其他' },
]
const categoryOptions: { value: MistakeCategory; label: string }[] = [
  { value: 'symbol_error', label: '看错符号' },
  { value: 'unit_missing', label: '漏写单位' },
  { value: 'misread_details', label: '读题遗漏' },
  { value: 'copying_error', label: '抄写错误' },
  { value: 'skipped_step', label: '跳步计算' },
  { value: 'rushing', label: '急于求成' },
  { value: 'lost_focus', label: '注意力涣散' },
  { value: 'messy_writing', label: '书写混乱' },
  { value: 'format_error', label: '格式错误' },
  { value: 'spelling_slip', label: '笔误/拼写' },
  { value: 'wild_guess', label: '盲目猜测' },
  { value: 'something_else', label: '其他' },
]
const subjectLabels: Record<string, string> = { math: '数学', chinese: '语文', english: '英语', science: '科学', other: '其他' }
const typeLabels: Record<string, string> = { choice: '选择', fill: '填空', calculation: '计算', composition: '作文', other: '其他' }
const diffLabels = ['', '★', '★★', '★★★', '★★★★', '★★★★★']

// ---- 录入错题表单 ----
const form = ref({
  subject: 'math' as QuestionSubject,
  type: 'calculation' as QuestionType,
  content: '',
  answer: '',
  grade: 3,
  chapter: '',
  knowledgePoints: '',
  difficulty: 3 as 1 | 2 | 3 | 4 | 5,
  isCarelessness: true,
  mistakeCategory: 'symbol_error' as MistakeCategory,
  tags: '',
})
const addSuccess = ref(false)

function handleAddQuestion() {
  if (!form.value.content.trim()) return
  qb.addQuestion({
    subject: form.value.subject,
    type: form.value.type,
    content: form.value.content.trim(),
    answer: form.value.answer || undefined,
    grade: form.value.grade,
    chapter: form.value.chapter || undefined,
    knowledgePoints: form.value.knowledgePoints ? form.value.knowledgePoints.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : [],
    difficulty: form.value.difficulty,
    tags: form.value.tags ? form.value.tags.split(/[,，、]/).map(s => s.trim()).filter(Boolean) : [],
    isCarelessness: form.value.isCarelessness,
    mistakeCategory: form.value.isCarelessness ? form.value.mistakeCategory : undefined,
    source: 'manual',
  })
  form.value.content = ''
  form.value.answer = ''
  form.value.chapter = ''
  form.value.knowledgePoints = ''
  form.value.tags = ''
  addSuccess.value = true
  setTimeout(() => { addSuccess.value = false }, 2500)
}

// ---- 列表筛选 ----
const filteredQuestions = computed(() => {
  let list = qb.questions
  if (filterSubject.value !== 'all') list = list.filter(q => q.subject === filterSubject.value)
  if (filterResolved.value === 'unresolved') list = list.filter(q => !q.resolved)
  else if (filterResolved.value === 'resolved') list = list.filter(q => q.resolved)
  return list
})

function toggleSelect(id: string) {
  qb.toggleSelect(id)
}
function handleMarkResolved(id: string) {
  qb.markResolved(id)
}
function handleDelete(id: string) {
  qb.deleteQuestion(id)
}

// ---- 打印选题 ----
const printMode = ref<'manual' | 'ai'>('manual')
const printIncludeAnswer = ref(false)
const printTitle = ref('错题打印')

function handleApplyAi() {
  qb.applyAiSelection()
  printMode.value = 'ai'
}

function handlePrint() {
  const selected = qb.selectedQuestions
  if (!selected.length) return
  const printWin = window.open('', '_blank')
  if (!printWin) return
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${printTitle.value}</title>
<style>body{font-family:'Noto Sans SC',sans-serif;padding:40px;font-size:16px;color:#1f241c}
h1{text-align:center;margin-bottom:30px;font-size:24px}
.q{margin-bottom:28px;padding:16px;border:1px solid #dedbcc;border-radius:12px;page-break-inside:avoid}
.q-head{display:flex;justify-content:space-between;margin-bottom:8px;font-size:13px;color:#6b735f}
.q-content{font-size:18px;line-height:1.8;margin-bottom:8px}
.q-answer{margin-top:12px;padding:10px;border-radius:8px;background:#f6ffd7;font-size:15px;color:#4d4100}
@media print{body{padding:20px}}</style></head><body>
<h1>${printTitle.value}</h1>
${selected.map((q, i) => `<div class="q"><div class="q-head"><span>${subjectLabels[q.subject] || q.subject} · ${typeLabels[q.type] || q.type}</span><span>${diffLabels[q.difficulty]}</span></div><div class="q-content">${i + 1}. ${q.content}</div>${printIncludeAnswer.value && q.answer ? `<div class="q-answer">答案：${q.answer}</div>` : ''}</div>`).join('')}
</body></html>`
  printWin.document.write(html)
  printWin.document.close()
  setTimeout(() => printWin.print(), 300)
}

// ---- 导入题库 ----
const importResult = ref<{ success: boolean; message: string } | null>(null)
const importDragging = ref(false)

function handleImportFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) processImportFile(file)
}

function handleDrop(event: DragEvent) {
  importDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) processImportFile(file)
}

function processImportFile(file: File) {
  if (!file.name.endsWith('.json')) {
    importResult.value = { success: false, message: '仅支持 .json 格式文件导入' }
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const raw = JSON.parse(e.target?.result as string)
      const rec = qb.importQuestions(raw, file.name)
      if (rec.status === 'failed') {
        importResult.value = { success: false, message: `导入失败：${rec.errors.join('；')}` }
      } else if (rec.status === 'partial') {
        importResult.value = { success: true, message: `部分导入成功：${rec.importedCount}题导入，${rec.failedCount}题失败。原因：${rec.errors.join('；')}` }
      } else {
        importResult.value = { success: true, message: `导入成功！共导入 ${rec.importedCount} 道题目` }
      }
    } catch {
      importResult.value = { success: false, message: '文件解析失败，请确认为合法 JSON 格式' }
    }
  }
  reader.readAsText(file)
}

function handleExport() {
  const data = qb.exportQuestions()
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `treasure-bank-export-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// ---- 薄弱环节图表（纯 CSS 柱状图） ----
const chartData = computed(() => qb.weaknessChartData)
const maxSubjectCount = computed(() => Math.max(...chartData.value.bySubject.map(d => d.count), 1))
const maxCategoryCount = computed(() => Math.max(...chartData.value.byCategory.map(d => d.count), 1))
const maxKPCount = computed(() => Math.max(...chartData.value.byKnowledgePoint.map(d => d.count), 1))
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🏴‍☠️ 藏宝库（题库）</span>
        <h1>收集错题，发现宝藏</h1>
        <p class="lead">手工录入或批量导入错题，按科目、分类查看错题列表。AI智能选题打印复习，图表展示薄弱环节。</p>
      </div>
      <div class="panel stats-panel">
        <div class="card-title"><h2>题库概览</h2></div>
        <div class="grid-3">
          <div class="kpi"><strong>{{ qb.totalCount }}</strong><span>总题数</span></div>
          <div class="kpi"><strong>{{ qb.unresolvedCount }}</strong><span>未解决</span></div>
          <div class="kpi"><strong>{{ qb.todayAddedCount }}</strong><span>今日新增</span></div>
        </div>
      </div>
    </section>

    <nav class="tab-bar">
      <button :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">📋 错题列表</button>
      <button :class="{ active: activeTab === 'add' }" @click="activeTab = 'add'">✏️ 录入错题</button>
      <button :class="{ active: activeTab === 'print' }" @click="activeTab = 'print'">🖨️ 选题打印</button>
      <button :class="{ active: activeTab === 'chart' }" @click="activeTab = 'chart'">📊 薄弱分析</button>
      <button :class="{ active: activeTab === 'import' }" @click="activeTab = 'import'">📥 导入/导出</button>
    </nav>

    <!-- ====== 错题列表 ====== -->
    <section v-if="activeTab === 'list'" class="panel">
      <div class="card-title">
        <h2>错题列表</h2>
        <div class="filter-bar">
          <select v-model="filterSubject" class="input sm">
            <option value="all">全部科目</option>
            <option v-for="s in subjectOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
          <select v-model="filterResolved" class="input sm">
            <option value="unresolved">未解决</option>
            <option value="resolved">已解决</option>
            <option value="all">全部</option>
          </select>
        </div>
      </div>
      <div v-if="filteredQuestions.length === 0" class="empty-hint">暂无错题，快去录入吧！</div>
      <div class="q-list">
        <div v-for="q in filteredQuestions" :key="q.id" class="q-row" :class="{ resolved: q.resolved }">
          <div class="q-check">
            <input type="checkbox" :checked="qb.selectedIds.has(q.id)" @change="toggleSelect(q.id)" />
          </div>
          <div class="q-body">
            <div class="q-meta">
              <span class="tag" :style="{ background: subjectLabels[q.subject] === '数学' ? '#fef2f2' : subjectLabels[q.subject] === '语文' ? '#eff6ff' : subjectLabels[q.subject] === '英语' ? '#ecfdf5' : '#fefce8', color: 'inherit' }">{{ subjectLabels[q.subject] || q.subject }}</span>
              <span class="tag">{{ typeLabels[q.type] || q.type }}</span>
              <span class="tag">{{ diffLabels[q.difficulty] }}</span>
              <span v-if="q.isCarelessness && q.mistakeCategory" class="tag warn">{{ categoryOptions.find(c => c.value === q.mistakeCategory)?.label }}</span>
              <span v-if="q.resolved" class="tag ok">已解决</span>
            </div>
            <div class="q-content-text">{{ q.content }}</div>
            <div v-if="q.answer" class="q-answer-small">答案：{{ q.answer }}</div>
            <div v-if="q.knowledgePoints.length" class="q-kps">
              <span v-for="kp in q.knowledgePoints" :key="kp" class="kp-tag">{{ kp }}</span>
            </div>
          </div>
          <div class="q-actions">
            <button v-if="!q.resolved" class="btn-sm" @click="handleMarkResolved(q.id)">✓</button>
            <button class="btn-sm danger" @click="handleDelete(q.id)">✕</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 录入错题 ====== -->
    <section v-if="activeTab === 'add'" class="panel">
      <div class="card-title"><h2>手工录入错题</h2></div>
      <div class="form-grid">
        <label>科目
          <select v-model="form.subject" class="input">
            <option v-for="s in subjectOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </label>
        <label>题型
          <select v-model="form.type" class="input">
            <option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </label>
        <label>年级
          <select v-model.number="form.grade" class="input">
            <option v-for="g in 6" :key="g" :value="g">{{ g }} 年级</option>
          </select>
        </label>
        <label>难度
          <select v-model.number="form.difficulty" class="input">
            <option v-for="d in 5" :key="d" :value="d">{{ diffLabels[d] }}</option>
          </select>
        </label>
        <label class="full">题目正文 <span class="req">*</span>
          <textarea v-model="form.content" class="input" rows="3" placeholder="请输入错题的题目内容..."></textarea>
        </label>
        <label class="full">参考答案
          <input v-model="form.answer" class="input" placeholder="可选，填入正确答案" />
        </label>
        <label>教材章节
          <input v-model="form.chapter" class="input" placeholder="例如：第3单元" />
        </label>
        <label>知识点（逗号分隔）
          <input v-model="form.knowledgePoints" class="input" placeholder="例如：小数乘法，混合运算" />
        </label>
        <label class="full">标签（逗号分隔）
          <input v-model="form.tags" class="input" placeholder="例如：易错，常考" />
        </label>
        <div class="full care-section">
          <h3>是否粗心型错误？</h3>
          <div class="stepper">
            <button class="btn" :class="{ secondary: form.isCarelessness }" @click="form.isCarelessness = true">是，粗心做错</button>
            <button class="btn ghost" :class="{ secondary: !form.isCarelessness }" @click="form.isCarelessness = false">否，知识漏洞</button>
          </div>
          <div v-if="form.isCarelessness" class="category-grid">
            <button v-for="cat in categoryOptions" :key="cat.value" class="category-card" :class="{ active: form.mistakeCategory === cat.value }" @click="form.mistakeCategory = cat.value">
              <span>{{ cat.label }}</span>
            </button>
          </div>
        </div>
        <button class="btn full-width" :disabled="!form.content.trim()" @click="handleAddQuestion">💾 保存错题</button>
        <p v-if="addSuccess" class="note ok">已保存到藏宝库！</p>
      </div>
    </section>

    <!-- ====== 选题打印 ====== -->
    <section v-if="activeTab === 'print'" class="panel">
      <div class="card-title"><h2>选题打印</h2></div>
      <div class="print-mode-bar">
        <button class="btn" :class="{ secondary: printMode === 'manual' }" @click="printMode = 'manual'">🤚 手工选择</button>
        <button class="btn ghost" :class="{ secondary: printMode === 'ai' }" @click="handleApplyAi">🤖 AI智能选择</button>
        <span class="tag">已选 {{ qb.selectedQuestions.length }} 题</span>
      </div>

      <div v-if="printMode === 'manual'" class="hint-box">
        请在「错题列表」中勾选要打印的题目，然后回到此处打印。也可以直接点击下方全选未解决题目。
        <button class="btn ghost sm-btn" @click="qb.selectAll(qb.questions.filter(q => !q.resolved).map(q => q.id))">全选未解决 ({{ qb.unresolvedCount }}题)</button>
        <button class="btn ghost sm-btn" @click="qb.clearSelection()">清空选择</button>
      </div>

      <div v-if="printMode === 'ai'" class="hint-box ai-hint">
        🤖 AI已为您推荐 <strong>{{ qb.aiRecommendedIds.length }}</strong> 道重点复习题目（优先选择复习次数少、难度高的未解决题目）。
      </div>

      <div v-if="qb.selectedQuestions.length > 0" class="print-preview">
        <h3>打印预览（{{ qb.selectedQuestions.length }} 题）</h3>
        <div class="preview-list">
          <div v-for="(q, i) in qb.selectedQuestions" :key="q.id" class="preview-item">
            <span class="preview-num">{{ i + 1 }}.</span>
            <span>{{ q.content }}</span>
            <span v-if="printIncludeAnswer && q.answer" class="preview-ans">（答案：{{ q.answer }}）</span>
          </div>
        </div>
      </div>

      <div class="print-options">
        <label>打印标题
          <input v-model="printTitle" class="input" placeholder="错题打印" />
        </label>
        <label class="check-label">
          <input type="checkbox" v-model="printIncludeAnswer" />
          附带参考答案
        </label>
      </div>

      <button class="btn full-width" :disabled="qb.selectedQuestions.length === 0" @click="handlePrint">
        🖨️ 打印选中题目 ({{ qb.selectedQuestions.length }}题)
      </button>
    </section>

    <!-- ====== 薄弱环节分析图表 ====== -->
    <section v-if="activeTab === 'chart'" class="panel">
      <div class="card-title"><h2>薄弱环节分析</h2><span class="tag">基于未解决错题</span></div>

      <h3>按科目分布</h3>
      <div v-if="chartData.bySubject.length" class="bar-chart">
        <div v-for="d in chartData.bySubject" :key="d.subject" class="bar-row">
          <span class="bar-label">{{ d.subject }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: (d.count / maxSubjectCount * 100) + '%', background: d.color }"></div>
          </div>
          <span class="bar-val">{{ d.count }}</span>
        </div>
      </div>
      <p v-else class="muted">暂无数据</p>

      <h3 style="margin-top:24px">按粗心分类</h3>
      <div v-if="chartData.byCategory.length" class="bar-chart">
        <div v-for="d in chartData.byCategory" :key="d.category" class="bar-row">
          <span class="bar-label">{{ d.category }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: (d.count / maxCategoryCount * 100) + '%' }"></div>
          </div>
          <span class="bar-val">{{ d.count }}</span>
        </div>
      </div>
      <p v-else class="muted">暂无数据</p>

      <h3 style="margin-top:24px">高频知识点（Top 10）</h3>
      <div v-if="chartData.byKnowledgePoint.length" class="bar-chart">
        <div v-for="d in chartData.byKnowledgePoint" :key="d.point" class="bar-row">
          <span class="bar-label">{{ d.point }}</span>
          <div class="bar-track">
            <div class="bar-fill kp-bar" :style="{ width: (d.count / maxKPCount * 100) + '%' }"></div>
          </div>
          <span class="bar-val">{{ d.count }}</span>
        </div>
      </div>
      <p v-else class="muted">暂无数据</p>

      <h3 style="margin-top:24px">按难度分布</h3>
      <div class="diff-chart">
        <div v-for="d in chartData.byDifficulty" :key="d.level" class="diff-bar">
          <span class="diff-label">{{ d.label || '-' }}</span>
          <div class="diff-fill" :style="{ height: d.count ? Math.max(8, d.count / Math.max(...chartData.byDifficulty.map(x => x.count), 1) * 100) + '%' : '0%' }"></div>
          <span class="diff-count">{{ d.count }}</span>
        </div>
      </div>
    </section>

    <!-- ====== 导入/导出 ====== -->
    <section v-if="activeTab === 'import'" class="panel">
      <div class="card-title"><h2>导入外部题库</h2></div>

      <div class="import-drop-zone"
        :class="{ dragging: importDragging }"
        @dragover.prevent="importDragging = true"
        @dragleave="importDragging = false"
        @drop.prevent="handleDrop"
      >
        <div class="drop-content">
          <span class="drop-icon">📁</span>
          <strong>拖拽 JSON 文件到此处</strong>
          <span>或点击选择文件</span>
          <input type="file" accept=".json" class="file-input" @change="handleImportFile" />
        </div>
      </div>

      <div v-if="importResult" class="note" :class="importResult.success ? 'ok' : 'err'">
        {{ importResult.message }}
      </div>

      <div class="format-spec">
        <h3>题库导入格式说明（v1.0）</h3>
        <p>仅支持 <strong>.json</strong> 格式，文件须符合以下结构：</p>
        <pre class="code-block">{
  "version": "1.0",
  "exportedAt": "2026-06-05T10:00:00Z",
  "schoolInfo": { "name": "XX小学", "grade": 3 },
  "questions": [
    {
      "subject": "math",
      "type": "calculation",
      "content": "计算：3.25 × 4 =",
      "answer": "13",
      "grade": 3,
      "chapter": "第3单元",
      "knowledgePoints": ["小数乘法"],
      "difficulty": 2,
      "tags": ["易错"]
    }
  ]
}</pre>
        <div class="spec-table">
          <table>
            <thead><tr><th>字段</th><th>必填</th><th>说明</th></tr></thead>
            <tbody>
              <tr><td>version</td><td>是</td><td>固定 "1.0"</td></tr>
              <tr><td>questions[].subject</td><td>是</td><td>math/chinese/english/science/other</td></tr>
              <tr><td>questions[].type</td><td>是</td><td>choice/fill/calculation/composition/other</td></tr>
              <tr><td>questions[].content</td><td>是</td><td>题目正文</td></tr>
              <tr><td>questions[].answer</td><td>否</td><td>参考答案</td></tr>
              <tr><td>questions[].grade</td><td>否</td><td>1-6，缺省取 schoolInfo.grade 或 3</td></tr>
              <tr><td>questions[].chapter</td><td>否</td><td>教材章节</td></tr>
              <tr><td>questions[].knowledgePoints</td><td>否</td><td>知识点数组</td></tr>
              <tr><td>questions[].difficulty</td><td>否</td><td>1-5，缺省为 3</td></tr>
              <tr><td>questions[].tags</td><td>否</td><td>自定义标签数组</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div style="margin-top:24px">
        <button class="btn" @click="handleExport">📤 导出当前题库为 JSON</button>
      </div>

      <div v-if="qb.imports.length > 0" style="margin-top:24px">
        <h3>导入历史</h3>
        <div class="import-history">
          <div v-for="imp in qb.imports" :key="imp.id" class="imp-row">
            <span class="tag" :class="imp.status">{{ imp.status === 'success' ? '成功' : imp.status === 'partial' ? '部分' : '失败' }}</span>
            <span>{{ imp.fileName }}</span>
            <span class="muted">{{ imp.importedCount }}/{{ imp.totalCount }} 题</span>
            <span class="muted">{{ new Date(imp.importedAt).toLocaleDateString() }}</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.stats-panel { display: flex; flex-direction: column; }
.tab-bar { display: flex; gap: 6px; flex-wrap: wrap; }
.tab-bar button { padding: 10px 16px; border-radius: 999px; background: var(--surface); border: 1px solid var(--line); font-weight: 800; font-size: 14px; color: var(--muted); transition: all .15s; }
.tab-bar button.active { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 6px 0 #0a5300; }
.filter-bar { display: flex; gap: 8px; }
.input.sm { width: auto; min-width: 120px; font-size: 13px; padding: 8px 12px; }
.empty-hint { text-align: center; padding: 40px; color: var(--muted); font-size: 18px; }

.q-list { display: flex; flex-direction: column; gap: 10px; }
.q-row { display: flex; align-items: flex-start; gap: 10px; padding: 14px; border: 1px solid var(--line); background: rgba(255,255,255,.68); border-radius: 20px; transition: background .15s; }
.q-row:hover { background: rgba(255,255,255,.9); }
.q-row.resolved { opacity: .55; }
.q-check { padding-top: 4px; }
.q-body { flex: 1; min-width: 0; }
.q-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.q-content-text { font-size: 16px; line-height: 1.6; word-break: break-word; }
.q-answer-small { margin-top: 4px; font-size: 13px; color: var(--primary); font-weight: 700; }
.q-kps { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.kp-tag { display: inline-flex; padding: 2px 8px; border-radius: 999px; background: var(--surface-2); font-size: 12px; color: var(--muted); }
.tag.warn { background: #fff7ed; color: #c2410c; }
.tag.ok { background: #ecfdf5; color: #059669; }
.q-actions { display: flex; gap: 4px; }
.btn-sm { width: 32px; height: 32px; border-radius: 10px; border: 1px solid var(--line); background: #fff; font-size: 14px; display: grid; place-items: center; }
.btn-sm.danger { color: #dc2626; }
.btn-sm:hover { background: var(--surface-2); }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-grid label { display: flex; flex-direction: column; gap: 6px; font-weight: 700; font-size: 14px; }
.form-grid label.full { grid-column: 1 / -1; }
.form-grid .full-width { grid-column: 1 / -1; }
.req { color: #dc2626; }
textarea.input { resize: vertical; min-height: 80px; }
.care-section { margin-top: 8px; }
.category-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 8px; margin-top: 10px; }
.category-card { padding: 10px 8px; border-radius: 14px; background: #fff; border: 1px solid var(--line); font-size: 13px; font-weight: 700; text-align: center; color: var(--ink); transition: all .12s; }
.category-card.active { background: #ecffd9; border-color: var(--primary); color: var(--primary); }
.note { padding: 14px; border-radius: 18px; font-weight: 700; }
.note.ok { background: #ecfdf5; color: #059669; }
.note.err { background: #fef2f2; color: #dc2626; }

.print-mode-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.sm-btn { padding: 8px 14px !important; font-size: 13px !important; }
.hint-box { padding: 16px; border-radius: 18px; background: #eff6ff; color: #1e40af; margin-bottom: 16px; display: flex; flex-direction: column; gap: 10px; font-size: 14px; }
.hint-box.ai-hint { background: #fefce8; color: #854d0e; }
.print-preview { background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 20px; margin-bottom: 16px; }
.preview-list { display: flex; flex-direction: column; gap: 8px; }
.preview-item { font-size: 15px; line-height: 1.6; }
.preview-num { font-weight: 900; margin-right: 6px; }
.preview-ans { color: var(--primary); font-weight: 700; margin-left: 8px; }
.print-options { display: flex; gap: 14px; align-items: flex-end; margin-bottom: 16px; }
.print-options label { display: flex; flex-direction: column; gap: 6px; font-weight: 700; font-size: 14px; flex: 1; }
.check-label { flex-direction: row !important; align-items: center !important; gap: 8px !important; }

.bar-chart { display: flex; flex-direction: column; gap: 8px; }
.bar-row { display: grid; grid-template-columns: 80px 1fr 36px; gap: 8px; align-items: center; }
.bar-label { font-size: 13px; font-weight: 700; text-align: right; color: var(--ink); }
.bar-track { height: 28px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
.bar-fill { height: 100%; border-radius: inherit; background: var(--primary); transition: width .4s ease; }
.bar-fill.kp-bar { background: var(--blue); }
.bar-val { font-size: 14px; font-weight: 900; text-align: center; }
.diff-chart { display: flex; align-items: flex-end; gap: 14px; height: 140px; padding-top: 10px; }
.diff-bar { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; justify-content: flex-end; }
.diff-fill { width: 100%; border-radius: 12px 12px 4px 4px; background: linear-gradient(180deg, var(--primary-2), var(--primary)); transition: height .4s ease; min-height: 0; }
.diff-label { font-size: 12px; font-weight: 800; color: var(--muted); }
.diff-count { font-size: 13px; font-weight: 900; }

.import-drop-zone { border: 2px dashed var(--line); border-radius: 24px; padding: 40px; text-align: center; cursor: pointer; transition: all .15s; position: relative; }
.import-drop-zone:hover, .import-drop-zone.dragging { border-color: var(--primary); background: #f0fff0; }
.drop-content { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.drop-icon { font-size: 48px; }
.file-input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.format-spec { margin-top: 20px; padding: 18px; border-radius: 18px; background: var(--surface-2); }
.format-spec h3 { margin-bottom: 10px; }
.code-block { background: #1f241c; color: #a7f3d0; padding: 16px; border-radius: 14px; overflow-x: auto; font-size: 13px; line-height: 1.6; margin: 12px 0; }
.spec-table { overflow-x: auto; }
.spec-table table { width: 100%; border-collapse: collapse; font-size: 13px; }
.spec-table th, .spec-table td { padding: 8px 10px; border: 1px solid var(--line); text-align: left; }
.spec-table th { background: var(--surface); font-weight: 800; }
.import-history { display: flex; flex-direction: column; gap: 6px; }
.imp-row { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 14px; background: var(--surface); font-size: 13px; }
.tag.success { background: #ecfdf5; color: #059669; }
.tag.partial { background: #fefce8; color: #854d0e; }
.tag.failed { background: #fef2f2; color: #dc2626; }

@media (max-width: 700px) {
  .form-grid { grid-template-columns: 1fr; }
  .category-grid { grid-template-columns: repeat(3, minmax(0,1fr)); }
}
</style>
