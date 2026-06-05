<script setup lang="ts">

function handlePrint() {
  window.print()
}
import { ref } from 'vue'
import { Button } from 'animal-island-vue'

const isPrintMode = ref(false)
</script>

<template>
  <div class="printable-page">
    <div class="print-helper" v-if="!isPrintMode">
      <Button type="primary" @click="handlePrint()">按 Ctrl+P 打印此页</Button>
    </div>

    <div class="a4-sheet">
      <div class="sheet-header">
        <div class="logo-area">
          <span class="logo-icon">🌿</span>
          <span class="logo-text">小树成长岛</span>
        </div>
        <div class="sheet-title">每日习惯打卡单</div>
        <div class="name-fields">
          <span>探险家名字: ____________</span>
          <span>第 ___ 周</span>
        </div>
      </div>

      <div class="habit-focus-box">
        <div class="speech-bubble-pointer"></div>
        <div class="habit-content">
          <strong>本周核心习惯聚焦</strong>
          <p>动笔前用手指着读题并圈出大题号 (Circle Question Numbers Before Writing)</p>
        </div>
      </div>

      <div class="checklist-table">
        <table>
          <thead>
            <tr>
              <th>项目</th>
              <th>周一</th>
              <th>周二</th>
              <th>周三</th>
              <th>周四</th>
              <th>周五</th>
              <th>周六</th>
              <th>周日</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="row-label main-habit">核心习惯: 指读圈号</td>
              <td v-for="d in 7" :key="d" class="check-cell">○</td>
            </tr>
            <tr>
              <td class="row-label">书包整理(3分区)</td>
              <td v-for="d in 7" :key="d" class="check-cell">□</td>
            </tr>
            <tr>
              <td class="row-label">作业时间检查</td>
              <td v-for="d in 7" :key="d" class="check-cell">□</td>
            </tr>
            <tr>
              <td class="row-label">家长签名</td>
              <td v-for="d in 7" :key="d" class="check-cell"></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="sunlight-section">
        <div class="sunlight-box">
          <strong>阳光值获得</strong>
          <div class="sun-icons">
            <span v-for="i in 7" :key="i" class="sun-icon">☀</span>
          </div>
        </div>
      </div>

      <div class="mistake-spot">
        <div class="mistake-box">
          <strong>错题收集角</strong>
          <p>把错题剪贴或抄写在这里</p>
          <div class="mistake-area"></div>
        </div>
      </div>

      <div class="sheet-footer">
        <span>小树成长岛 - 让粗心变成细心</span>
        <div class="qr-box">扫描二维码回传</div>
      </div>
    </div>
  </div>
</template>



<style scoped>
.printable-page {
  background: #fcfaef;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
}

.a4-sheet {
  width: 210mm;
  max-width: 100%;
  background: white;
  padding: 20mm 15mm;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  font-family: 'Noto Sans SC', sans-serif;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 2px solid #9a835a;
  padding-bottom: 8px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-weight: 700;
  color: #106e00;
  font-size: 18px;
}

.sheet-title {
  font-weight: 900;
  font-size: 24px;
  color: #725d42;
  text-align: center;
}

.name-fields {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #9a835a;
}

.habit-focus-box {
  background: #fbe270;
  border: 2px solid #f7cd67;
  border-radius: 12px;
  padding: 16px;
  margin: 16px 0;
  position: relative;
}

.speech-bubble-pointer {
  position: absolute;
  bottom: -10px;
  left: 30px;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid #fbe270;
}

.habit-content strong {
  color: #6e5e00;
}

.habit-content p {
  margin: 8px 0 0;
  font-size: 16px;
  color: #725d42;
}

.checklist-table {
  margin: 16px 0;
}

.checklist-table table {
  width: 100%;
  border-collapse: collapse;
}

.checklist-table th,
.checklist-table td {
  border: 1px solid #9a835a;
  padding: 8px 4px;
  text-align: center;
  font-size: 13px;
}

.row-label {
  text-align: left;
  font-weight: 600;
  color: #725d42;
  min-width: 120px;
}

.row-label.main-habit {
  background: #fbe270;
}

.check-cell {
  font-size: 16px;
  min-width: 30px;
}

.sunlight-section {
  margin: 16px 0;
}

.sunlight-box {
  border: 2px solid #f7cd67;
  border-radius: 12px;
  padding: 12px;
  background: #fef9e7;
}

.sunlight-box strong {
  color: #6e5e00;
}

.sun-icons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.sun-icon {
  font-size: 24px;
  opacity: 0.3;
}

.mistake-spot {
  margin: 16px 0;
}

.mistake-box {
  border: 2px dashed #9a835a;
  border-radius: 12px;
  padding: 12px;
}

.mistake-area {
  height: 80px;
  border: 1px dashed #e4e3d8;
  margin-top: 8px;
}

.sheet-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 8px;
  border-top: 1px solid #9a835a;
  font-size: 12px;
  color: #9a835a;
}

.qr-box {
  border: 1px solid #9a835a;
  padding: 4px 12px;
  border-radius: 4px;
}

@media print {
  .print-helper { display: none !important; }
  .a4-sheet {
    box-shadow: none;
    padding: 10mm;
  }
  .printable-page { background: white; padding: 0; }
}
</style>