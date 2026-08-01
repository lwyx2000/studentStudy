<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { categoryLabels, weekDayToLabel } from '../utils/constants'

const props = defineProps<{
  visible: boolean
  type: 'subtask' | 'step'
  items: any[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', items: any[]): void
}>()

const filterText = ref('')
const selectedItems = ref<Set<string>>(new Set())

const filteredItems = ref<any[]>([])

watch([() => props.items, filterText], () => {
  let list = [...props.items]
  const q = filterText.value.toLowerCase().trim()
  if (q) {
    if (props.type === 'subtask') {
      list = list.filter(s => s.title?.toLowerCase().includes(q))
    } else {
      list = list.filter(s => s.instruction?.toLowerCase().includes(q))
    }
  }
  filteredItems.value = list
}, { immediate: true })

function toggleSelect(id: string | number) {
  const key = String(id)
  const s = selectedItems.value
  if (s.has(key)) s.delete(key)
  else s.add(key)
  selectedItems.value = new Set(s)
}

function selectAll() {
  selectedItems.value = new Set(filteredItems.value.map((_, i) => String(i)))
}

function confirmSelection() {
  const selected = filteredItems.value.filter((_, i) => selectedItems.value.has(String(i)))
  emit('select', selected)
  emit('close')
}

function onBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('modal-backdrop')) {
    emit('close')
  }
}

const title = computed(() => props.type === 'subtask' ? '📋 选择子任务' : '📝 选择步骤')
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" @click="onBackdropClick">
      <div class="modal-panel">
        <div class="modal-header">
          <h2>{{ title }}</h2>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>

        <!-- Search -->
        <div class="modal-search">
          <input
            v-model="filterText"
            class="input"
            :placeholder="type === 'subtask' ? '搜索子任务名称…' : '搜索步骤说明…'"
            autofocus
          />
        </div>

        <!-- Actions -->
        <div class="modal-actions">
          <button class="btn ghost" style="font-size:13px;padding:4px 12px" @click="selectAll">全选</button>
          <button
            class="btn"
            style="font-size:13px;padding:4px 14px"
            :disabled="selectedItems.size === 0"
            @click="confirmSelection"
          >
            添加已选 ({{ selectedItems.size }})
          </button>
        </div>

        <!-- List -->
        <div class="modal-list">
          <template v-if="type === 'subtask'">
            <div
              v-for="(s, i) in filteredItems"
              :key="s.pk_sub_tasks || i"
              class="modal-item"
              :class="{ selected: selectedItems.has(String(i)) }"
              @click="toggleSelect(i)"
            >
              <div class="checkbox" :class="{ checked: selectedItems.has(String(i)) }">
                {{ selectedItems.has(String(i)) ? '✓' : '' }}
              </div>
              <div class="modal-item-info">
                <strong>{{ s.title }}</strong>
                <div class="modal-item-meta">
                  <span class="mini-tag">{{ categoryLabels[s.type] || s.type }}</span>
                  <span v-if="s.week_day" class="mini-tag" style="background:#e3f2fd">📅 {{ weekDayToLabel(s.week_day) }}</span>
                  <span class="mini-tag" style="background:#f0fdf4;color:#166534">{{ s.task_title || '未知任务' }}</span>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div
              v-for="(s, i) in filteredItems"
              :key="s.pk_sop_steps || i"
              class="modal-item"
              :class="{ selected: selectedItems.has(String(i)) }"
              @click="toggleSelect(i)"
            >
              <div class="checkbox" :class="{ checked: selectedItems.has(String(i)) }">
                {{ selectedItems.has(String(i)) ? '✓' : '' }}
              </div>
              <div class="modal-item-info">
                <strong>{{ s.instruction }}</strong>
                <div class="modal-item-meta">
                  <span class="mini-tag" style="background:#f0fdf4;color:#166534">{{ s.habit_title || '未知习惯' }}</span>
                </div>
              </div>
            </div>
          </template>
          <div v-if="!filteredItems.length" class="modal-empty">
            <p class="muted">没有找到匹配的项目</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: grid;
  place-items: center;
  z-index: 1000;
  animation: fadeIn .15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-panel {
  background: #fff;
  border-radius: 20px;
  width: 520px;
  max-width: calc(100vw - 40px);
  max-height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  animation: slideUp .2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: none;
  background: #f1f5f1;
  font-size: 16px;
  cursor: pointer;
  display: grid;
  place-items: center;
  color: #666;
  transition: all .12s ease;
}

.modal-close:hover {
  background: #e2e8e2;
  color: #333;
}

.modal-search {
  padding: 16px 24px 8px;
}

.modal-search .input {
  width: 100%;
  padding: 12px 16px;
  border-radius: 12px;
  border: 2px solid var(--line);
  font-size: 15px;
  outline: none;
  transition: border-color .12s ease;
  box-sizing: border-box;
}

.modal-search .input:focus {
  border-color: var(--primary);
}

.modal-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 24px 12px;
}

.modal-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.modal-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  cursor: pointer;
  transition: all .12s ease;
  background: #fff;
}

.modal-item:hover {
  border-color: var(--primary);
  background: #f6fff0;
}

.modal-item.selected {
  border-color: var(--primary);
  background: #e8f5e0;
}

.checkbox {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 2px solid #ccc;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 800;
  flex-shrink: 0;
  transition: all .12s ease;
  color: transparent;
}

.checkbox.checked {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.modal-item-info {
  flex: 1;
  min-width: 0;
}

.modal-item-info strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.modal-item-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.modal-empty {
  text-align: center;
  padding: 32px;
}

.mini-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
}
</style>
