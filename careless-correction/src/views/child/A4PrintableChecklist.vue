<script setup lang="ts">
import { computed } from 'vue'
import { weekdays } from '../../utils/constants'
import { useTaskStore, useUserStore } from '../../stores'

const userStore = useUserStore()
const taskStore = useTaskStore()
const completionText = computed(() => `${taskStore.weeklyProgress}/${taskStore.todayTasks.length}`)
function printPage() {
  window.print()
}
</script>
<template>
  <div class="page printable-page">
    <section class="panel no-print"><div class="card-title"><h1>A4 纸质打卡单</h1><button class="btn" @click="printPage">打印</button></div><p class="lead">适合贴在书桌或冰箱上，把每日微习惯从 App 转移到真实环境。</p></section>
    <section class="sheet"><header><h1>小树成长岛 · 本周打卡单</h1><p>姓名：{{ userStore.profile.name }}　年级：{{ userStore.profile.grade }} 年级　完成：{{ completionText }}</p></header><table><thead><tr><th>日期</th><th v-for="task in taskStore.todayTasks" :key="task.id">{{ task.title }}</th><th>家长只观察不催促</th></tr></thead><tbody><tr v-for="day in weekdays" :key="day"><td>{{ day }}</td><td v-for="task in taskStore.todayTasks" :key="task.id">□</td><td>□</td></tr></tbody></table><footer>周末拍照上传，系统将扫描勾选痕迹生成成长报告。</footer></section>
  </div>
</template>
<style scoped>.printable-page{align-items:center}.sheet{width:min(794px,100%);min-height:1123px;background:white;color:#222;padding:54px;border:1px solid #ddd;box-shadow:var(--shadow)}.sheet header{border-bottom:4px solid var(--primary);padding-bottom:20px;margin-bottom:28px}.sheet table{width:100%;border-collapse:collapse;font-size:16px}.sheet th,.sheet td{border:1px solid #777;padding:14px;text-align:center}.sheet footer{margin-top:28px;color:#555}@media print{.no-print,.topbar,.sidebar{display:none!important}.sheet{box-shadow:none;border:0;width:100%;min-height:auto}}</style>
