<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMistakeStore } from '../../stores'
import type { MistakeCategory } from '../../types'

const mistakeStore = useMistakeStore()
const subject = ref('数学')
const canRedo = ref<boolean | null>(null)
const category = ref<MistakeCategory>('symbol_error')
const knowledgePoint = ref('')
const imageName = ref('')
const draftName = ref('')
const diagnosisSaved = ref(false)
const categories: { value: MistakeCategory; label: string; icon: string }[] = [
  { value: 'symbol_error', label: '看错符号', icon: '+ → -' },
  { value: 'unit_missing', label: '漏写单位', icon: '35 → [ ]' },
  { value: 'misread_details', label: '读题遗漏', icon: '跳字' },
  { value: 'copying_error', label: '抄写错误', icon: '抄错' },
  { value: 'skipped_step', label: '跳步计算', icon: '1→3' },
  { value: 'rushing', label: '急于求成', icon: '快' },
  { value: 'lost_focus', label: '注意力涣散', icon: '雾' },
  { value: 'messy_writing', label: '书写混乱', icon: '乱' },
  { value: 'format_error', label: '格式错误', icon: '格' },
  { value: 'spelling_slip', label: '笔误/拼写', icon: 'typo' },
  { value: 'wild_guess', label: '盲目猜测', icon: '?' },
  { value: 'something_else', label: '其他原因', icon: '…' },
]
const reviewPlan = computed(() => canRedo.value ? ['今天：重新读题并圈符号', '3 天后：遮答案复做', '7 天后：同类题迁移'] : ['今天：标记知识点', '明天：补一个例题', '3 天后：再做同类题'])

function handleImage(event: Event, target: 'question' | 'draft') {
  const input = event.target as HTMLInputElement
  const name = input.files?.[0]?.name || ''
  if (target === 'question') imageName.value = name
  else draftName.value = name
}

function saveDiagnosis() {
  if (!imageName.value || canRedo.value === null) return
  mistakeStore.addRecord({
    subject: subject.value,
    imageUrl: imageName.value,
    isCarelessness: canRedo.value,
    category: canRedo.value ? category.value : undefined,
    knowledgePoint: canRedo.value ? undefined : knowledgePoint.value || '待补充知识点',
  })
  diagnosisSaved.value = true
}
</script>

<template>
  <div class="page">
    <section class="page-hero"><div class="hero-card"><span class="eyebrow">🔎 “黄金一问”智能错题本</span><h1>先问原因，再安排复习</h1><p class="lead">拍照录入错题后，先区分“会但做错”和“知识漏洞”，再分别进入粗心分类或知识点归档。</p></div><div class="panel"><div class="card-title"><h2>今日待复习</h2><span class="tag">{{ mistakeStore.todayReviewCount }} 题</span></div><div class="kpi"><strong>{{ Object.keys(mistakeStore.categoryStats).length }}</strong><span>已记录错误类型</span></div></div></section>
    <section class="grid-2"><div class="panel"><label class="photo-drop">📸<strong>{{ imageName || '上传错题照片' }}</strong><span>自动裁切题目区域、识别学科和题干</span><input type="file" accept="image/*" @change="handleImage($event, 'question')" /></label><label class="photo-drop draft">📝<strong>{{ draftName || '上传草稿纸痕迹' }}</strong><span>红框提示对位歪斜、跳步或书写混乱区域</span><input type="file" accept="image/*" @change="handleImage($event, 'draft')" /></label></div><div class="panel"><div class="card-title"><h2>黄金一问</h2><span class="tag">{{ canRedo === null ? '待判断' : canRedo ? '粗心/执行功能' : '知识漏洞' }}</span></div><label>学科<select v-model="subject" class="input"><option>数学</option><option>语文</option><option>英语</option></select></label><h3>Leo 能重新自己立刻做对这道题吗？</h3><div class="stepper"><button class="btn" :class="{ secondary: canRedo === true }" @click="canRedo = true">能，只是粗心</button><button class="btn ghost" :class="{ secondary: canRedo === false }" @click="canRedo = false">不能/不确定</button></div><div v-if="canRedo" class="category-grid"><button v-for="cat in categories" :key="cat.value" class="category-card" :class="{ active: category === cat.value }" @click="category = cat.value"><b>{{ cat.icon }}</b><span>{{ cat.label }}</span></button></div><label v-else-if="canRedo === false">知识点归档<input v-model="knowledgePoint" class="input" placeholder="例如：小数乘法进位" /></label><button class="btn" :disabled="!imageName || canRedo === null" @click="saveDiagnosis">保存诊断并安排复习</button><p v-if="diagnosisSaved" class="note">已保存，并纳入 {{ canRedo ? '粗心数据分析' : '知识点复习计划' }}。</p></div></section>
    <section class="panel"><div class="card-title"><h2>复习策略</h2><span class="tag">自动匹配</span></div><div class="grid-3"><div v-for="plan in reviewPlan" :key="plan" class="kpi"><strong>{{ plan.split('：')[0] }}</strong><span>{{ plan.split('：')[1] }}</span></div></div></section>
  </div>
</template>

<style scoped>
.photo-drop{min-height:220px;border-radius:28px;background:linear-gradient(180deg,#eef8ff,#fff);border:2px dashed var(--blue);display:grid;place-items:center;text-align:center;font-size:58px;color:var(--muted);margin-bottom:16px;cursor:pointer}.photo-drop.draft{background:linear-gradient(180deg,#fff8df,#fff)}.photo-drop strong,.photo-drop span{display:block;font-size:18px}.photo-drop input{display:none}.category-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:16px 0}.category-card{padding:12px;border-radius:16px;background:#fff;border:1px solid var(--line);display:grid;gap:4px;color:var(--ink)}.category-card.active{background:#ecffd9;border-color:var(--primary);color:var(--primary)}.note{padding:14px;border-radius:18px;background:#fff8d9;color:#6e5e00}button:disabled{opacity:.5;cursor:not-allowed}
</style>
