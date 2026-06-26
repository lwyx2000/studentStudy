export const categoryLabels: Record<string, string> = {
  morning_routine: '晨间惯例',
  study_habit: '学习习惯',
  life_skill: '生活技能',
  exercise: '运动',
  reflection: '反思',
}

export const subjectOptions = ['数学', '语文', '英语', '科学', '其他']

export const timeDrainReasons = [
  { value: 'reading', label: '读题' },
  { value: 'calculation', label: '验算' },
  { value: 'daydreaming', label: '神游' },
]

export const difficultyLabels = ['阳光', '微风', '挑战']

export const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

export const weekdaysShort = ['周一', '周二', '周三', '周四', '周五']

// 12 类粗心分类（对应 t_mistake_records.category）
export const MISTAKE_CATEGORIES = [
  { value: 'symbol_error', label: '看错符号', icon: '🔣' },
  { value: 'unit_missing', label: '漏写单位', icon: '📏' },
  { value: 'misread_details', label: '读题遗漏', icon: '👁️' },
  { value: 'copying_error', label: '抄写错误', icon: '✍️' },
  { value: 'skipped_step', label: '跳步计算', icon: '🦘' },
  { value: 'rushing', label: '急于求成', icon: '⚡' },
  { value: 'lost_focus', label: '注意力涣散', icon: '🌀' },
  { value: 'messy_writing', label: '书写混乱', icon: '🌪️' },
  { value: 'format_error', label: '格式错误', icon: '📐' },
  { value: 'spelling_slip', label: '笔误/拼写', icon: '⌨️' },
  { value: 'wild_guess', label: '盲目猜测', icon: '🎲' },
  { value: 'something_else', label: '其他', icon: '❓' },
]

export function getMistakeCategoryLabel(value: string): string {
  return MISTAKE_CATEGORIES.find(c => c.value === value)?.label ?? value ?? '未知'
}

export function getMistakeCategoryIcon(value: string): string {
  return MISTAKE_CATEGORIES.find(c => c.value === value)?.icon ?? '❓'
}
