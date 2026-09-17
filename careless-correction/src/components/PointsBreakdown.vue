<script setup lang="ts">
/**
 * 打卡阳光值构成明细
 * 数据来自打卡提交时记录的 required_points / optional_bonus / all_done_bonus
 * 老打卡记录（无构成数据）自动降级为单行展示。
 */
const props = defineProps<{
  requiredPoints?: number
  optionalBonus?: number
  allDoneBonus?: number
  habitPoints?: number
  totalPoints: number
}>()

const hasBreakdown = (props.requiredPoints ?? 0) > 0
  || (props.optionalBonus ?? 0) > 0
  || (props.allDoneBonus ?? 0) > 0
  || (props.habitPoints ?? 0) > 0
</script>

<template>
  <div class="points-breakdown">
    <div class="pb-row pb-main">
      <span class="pb-label">☀️ 本次阳光值</span>
      <span class="pb-total">+{{ totalPoints }}</span>
    </div>
    <template v-if="hasBreakdown">
      <div class="pb-row">
        <span class="pb-label">├ 必做小任务</span>
        <span class="pb-value">+{{ requiredPoints ?? 0 }}</span>
      </div>
      <div v-if="(optionalBonus ?? 0) > 0" class="pb-row">
        <span class="pb-label">├ 可选 ⭐ 加分</span>
        <span class="pb-value pb-optional">+{{ optionalBonus }}</span>
      </div>
      <div v-if="(habitPoints ?? 0) > 0" class="pb-row">
        <span class="pb-label">├ 习惯打卡 🌱</span>
        <span class="pb-value pb-habit">+{{ habitPoints }}</span>
      </div>
      <div v-if="(allDoneBonus ?? 0) > 0" class="pb-row">
        <span class="pb-label">└ 全部完成奖励 🎉</span>
        <span class="pb-value pb-bonus">+{{ allDoneBonus }}</span>
      </div>
    </template>
    <p v-else class="pb-hint">本次打卡未记录构成明细</p>
  </div>
</template>

<style scoped>
.points-breakdown {
  padding: 10px 14px;
  border-radius: 12px;
  background: #fffdf2;
  border: 1px dashed #ffe082;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pb-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  gap: 12px;
}
.pb-main {
  padding-bottom: 4px;
  border-bottom: 1px solid #ffe9a8;
}
.pb-main + .pb-row {
  padding-top: 2px;
}
.pb-label {
  color: #6d5b1f;
  font-weight: 700;
}
.pb-total {
  font-size: 16px;
  font-weight: 900;
  color: #a67c00;
}
.pb-value {
  font-weight: 800;
  color: #555;
}
.pb-optional {
  color: #8a6d3b;
}
.pb-bonus {
  color: #d84315;
}
.pb-habit {
  color: #1565c0;
}
.pb-hint {
  margin: 0;
  font-size: 12px;
  color: #b8a96a;
}
</style>
