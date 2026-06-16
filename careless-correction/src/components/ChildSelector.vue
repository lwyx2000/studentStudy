<script setup lang="ts">
import { useChildSelectStore } from '../stores'

const childSelectStore = useChildSelectStore()
</script>

<template>
  <div v-if="childSelectStore.children.length > 0" class="child-selector">
    <span class="label">查看孩子：</span>
    <div class="pills">
      <button
        v-for="child in childSelectStore.children"
        :key="child.id"
        class="child-pill"
        :class="{ active: childSelectStore.selectedChildId === child.id }"
        @click="childSelectStore.selectChild(child.id)"
      >
        <span class="avatar">{{ child.name[0] }}</span>
        {{ child.name }}
        <span class="grade">{{ child.grade }}年级</span>
      </button>
    </div>
    <span v-if="!childSelectStore.selectedChild" class="muted" style="font-size:13px">
      请先在「孩子管理」中添加孩子
    </span>
  </div>
  <div v-else class="child-selector empty">
    <span class="muted">暂无孩子账号，</span>
    <router-link to="/parent/children" class="link">去添加孩子 →</router-link>
  </div>
</template>

<style scoped>
.child-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.child-selector.empty {
  background: #fff8d9;
  border-color: #f0d960;
}
.label {
  font-weight: 800;
  font-size: 14px;
  color: var(--muted);
  white-space: nowrap;
}
.pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.child-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 2px solid var(--line);
  background: #fff;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  transition: all .15s ease;
  color: var(--ink);
}
.child-pill:hover {
  border-color: var(--primary);
  background: #ecffd9;
}
.child-pill.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: 0 4px 12px rgba(16,110,0,.2);
}
.avatar {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: rgba(255,255,255,.3);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 900;
}
.child-pill.active .avatar {
  background: rgba(255,255,255,.25);
}
.grade {
  font-size: 11px;
  opacity: .8;
  font-weight: 700;
}
.link {
  color: var(--primary);
  font-weight: 800;
  font-size: 14px;
  text-decoration: none;
}
.link:hover { text-decoration: underline; }
</style>
