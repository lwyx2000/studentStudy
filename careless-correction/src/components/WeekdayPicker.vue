<script setup lang="ts">
import { computed, ref } from 'vue'
import { DAY_LABELS, selectedToWeekDay, weekDayToSelected } from '../utils/constants'

const props = defineProps<{
  modelValue: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const visible = defineModel<boolean>('visible', { default: false })

const selected = ref<boolean[]>(weekDayToSelected(props.modelValue))
const allChecked = computed(() => selected.value.every(Boolean))

function toggleDay(index: number) {
  selected.value[index] = !selected.value[index]
}

function setAll(val: boolean) {
  selected.value = selected.value.map(() => val)
}

function setPreset(preset: 'weekday' | 'weekend') {
  if (preset === 'weekday') {
    selected.value = [true, true, true, true, true, false, false]
  } else {
    selected.value = [false, false, false, false, false, true, true]
  }
}

function confirm() {
  emit('update:modelValue', selectedToWeekDay(selected.value))
  visible.value = false
}

function cancel() {
  selected.value = weekDayToSelected(props.modelValue)
  visible.value = false
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="wkd-overlay" @click.self="cancel">
      <div class="wkd-modal">
        <h3 class="wkd-title">选择适用日期</h3>

        <div class="wkd-presets">
          <button class="wkd-preset-btn" :class="{ active: allChecked }" @click="setAll(true)">
            ✅ 每天
          </button>
          <button
            class="wkd-preset-btn"
            :class="{ active: !allChecked && selected[0] && selected[1] && selected[2] && selected[3] && selected[4] && !selected[5] && !selected[6] }"
            @click="setPreset('weekday')"
          >
            📅 平时
          </button>
          <button
            class="wkd-preset-btn"
            :class="{ active: !allChecked && !selected[0] && !selected[1] && !selected[2] && !selected[3] && !selected[4] && selected[5] && selected[6] }"
            @click="setPreset('weekend')"
          >
            🎉 周末
          </button>
        </div>

        <div class="wkd-grid">
          <label
            v-for="(label, i) in DAY_LABELS"
            :key="i"
            class="wkd-day"
            :class="{ checked: selected[i] }"
          >
            <input type="checkbox" :checked="selected[i]" @change="toggleDay(i)" />
            <span class="wkd-day-label">{{ label }}</span>
          </label>
        </div>

        <div class="wkd-actions">
          <button class="btn ghost" @click="cancel">取消</button>
          <button class="btn" @click="confirm">确定</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.wkd-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: grid;
  place-items: center;
  z-index: 9999;
  padding: 16px;
}
.wkd-modal {
  background: #fff;
  border-radius: 20px;
  padding: 28px;
  width: min(400px, 100%);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
}
.wkd-title {
  font-size: 20px;
  font-weight: 800;
  margin: 0 0 16px;
  text-align: center;
}
.wkd-presets {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.wkd-preset-btn {
  flex: 1;
  padding: 8px 4px;
  border-radius: 10px;
  border: 2px solid var(--line);
  background: #fff;
  font-weight: 800;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.12s;
}
.wkd-preset-btn:hover {
  border-color: var(--primary-2);
  background: #f6fddc;
}
.wkd-preset-btn.active {
  border-color: var(--primary);
  background: #ecffd9;
  color: var(--primary);
}
.wkd-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}
.wkd-day {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 8px;
  border-radius: 12px;
  border: 2px solid var(--line);
  background: #fff;
  cursor: pointer;
  transition: all 0.12s;
  user-select: none;
}
.wkd-day:hover {
  border-color: var(--primary-2);
  background: #f6fddc;
}
.wkd-day.checked {
  border-color: var(--primary);
  background: #ecffd9;
}
.wkd-day input {
  display: none;
}
.wkd-day-label {
  font-weight: 800;
  font-size: 15px;
}
.wkd-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.wkd-actions .btn {
  padding: 10px 24px;
  font-size: 15px;
  border-radius: 12px;
}
</style>
