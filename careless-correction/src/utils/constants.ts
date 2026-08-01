export const categoryLabels: Record<string, string> = {
  morning_routine: '晨间惯例',
  study_habit: '学习习惯',
  life_skill: '生活技能',
  exercise: '运动',
  reflection: '反思',
}

export const subjectOptions = ['数学', '语文', '英语', '科学', '其他']

export const DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
export const DAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

export const GRADE_OPTIONS = [
  { value: 0, label: '幼儿园' },
  { value: 1, label: '一年级' },
  { value: 2, label: '二年级' },
  { value: 3, label: '三年级' },
  { value: 4, label: '四年级' },
  { value: 5, label: '五年级' },
  { value: 6, label: '六年级' },
  { value: 7, label: '初一' },
  { value: 8, label: '初二' },
  { value: 9, label: '初三' },
  { value: 10, label: '高一' },
  { value: 11, label: '高二' },
  { value: 12, label: '高三' },
]

export function gradeLabel(g: number): string {
  return GRADE_OPTIONS.find(o => o.value === g)?.label ?? `${g} 年级`
}

export function weekDayToLabel(value?: string): string {
  if (!value) return '每天'
  if (value === 'weekday') return '平时'
  if (value === 'weekend') return '周末'
  const days = value.split(',')
  return days.map(d => {
    const idx = DAY_NAMES.indexOf(d)
    return idx >= 0 ? DAY_LABELS[idx] : d
  }).join('、')
}

export function weekDayToSelected(value?: string): boolean[] {
  const selected = [false, false, false, false, false, false, false]
  if (!value) return [true, true, true, true, true, true, true]
  if (value === 'weekday') return [true, true, true, true, true, false, false]
  if (value === 'weekend') return [false, false, false, false, false, true, true]
  const days = value.split(',')
  days.forEach(d => {
    const idx = DAY_NAMES.indexOf(d)
    if (idx >= 0) selected[idx] = true
  })
  return selected
}

export function selectedToWeekDay(selected: boolean[]): string {
  const allSelected = selected.every(Boolean)
  if (allSelected) return ''
  const onlyWeekday = selected[0] && selected[1] && selected[2] && selected[3] && selected[4] && !selected[5] && !selected[6]
  if (onlyWeekday) return 'weekday'
  const onlyWeekend = !selected[0] && !selected[1] && !selected[2] && !selected[3] && !selected[4] && selected[5] && selected[6]
  if (onlyWeekend) return 'weekend'
  return DAY_NAMES.filter((_, i) => selected[i]).join(',')
}

export function matchesToday(weekDay: string | undefined, date?: Date): boolean {
  if (!weekDay) return true
  const d = date || new Date()
  const today = d.getDay()
  const isWeekday = today >= 1 && today <= 5
  const isWeekend = today === 0 || today === 6

  if (weekDay === 'weekday') return isWeekday
  if (weekDay === 'weekend') return isWeekend

  const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
  const days = weekDay.split(',')
  return days.some(day => day === dayNames[today])
}

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
