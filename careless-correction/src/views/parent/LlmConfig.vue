<script setup lang="ts">
import { ref } from 'vue'
import { useParentStore } from '../../stores'

const parentStore = useParentStore()

const form = ref({ ...parentStore.llmConfig })
const saved = ref(false)
const testResult = ref('')

function save() {
  parentStore.updateLlmConfig(form.value)
  saved.value = true
  setTimeout(() => { saved.value = false }, 2000)
}

async function testConnection() {
  testResult.value = '测试中...'
  try {
    const res = await fetch(`${form.value.endpoint}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${form.value.apiKey}`,
      },
      body: JSON.stringify({
        model: form.value.model,
        messages: [{ role: 'user', content: '回复"连接成功"' }],
        max_tokens: 10,
      }),
    })
    if (res.ok) testResult.value = '✅ 连接成功'
    else testResult.value = `❌ ${res.status} ${res.statusText}`
  } catch {
    testResult.value = '❌ 连接失败，请检查地址和 Key'
  }
}
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">🤖 大模型配置</span>
        <h1>配置 AI 分析引擎</h1>
        <p class="lead">接入大模型用于错题分析、拍照打卡识别和成长评估。支持 OpenAI 兼容接口。</p>
      </div>
      <div class="panel" style="display:flex;flex-direction:column;justify-content:center">
        <div class="card-title">
          <h2>状态</h2>
          <span class="tag" :style="form.enabled ? 'background:#d9f5c8;color:var(--primary)' : ''">
            {{ form.enabled ? '已启用' : '已关闭' }}
          </span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;margin-top:8px">
          <span class="muted" style="font-weight:700">启用 AI</span>
          <button
            class="btn"
            :class="form.enabled ? '' : 'ghost'"
            style="padding:6px 14px;font-size:13px"
            @click="form.enabled = !form.enabled"
          >
            {{ form.enabled ? '开启' : '关闭' }}
          </button>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="card-title">
        <h2>连接配置</h2>
        <button class="btn secondary" @click="save">保存配置</button>
      </div>
      <p v-if="saved" style="color:var(--primary);font-weight:800;margin-bottom:12px">✅ 已保存</p>

      <label style="font-weight:800;display:block;margin-bottom:4px">API 地址</label>
      <input v-model="form.endpoint" class="input" style="margin-bottom:12px" placeholder="https://api.openai.com/v1" />

      <label style="font-weight:800;display:block;margin-bottom:4px">API Key</label>
      <input v-model="form.apiKey" class="input" type="password" style="margin-bottom:12px" placeholder="sk-..." />

      <label style="font-weight:800;display:block;margin-bottom:4px">模型</label>
      <select v-model="form.model" class="input" style="margin-bottom:16px">
        <option>gpt-4o-mini</option>
        <option>gpt-4o</option>
        <option>deepseek-chat</option>
        <option>qwen-plus</option>
        <option>glm-4-flash</option>
      </select>

      <div style="display:flex;gap:12px;align-items:center">
        <button class="btn ghost" @click="testConnection">测试连接</button>
        <span v-if="testResult" :style="testResult.includes('✅') ? 'color:var(--primary);font-weight:800' : 'color:#c00;font-weight:800'">{{ testResult }}</span>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="card-title">
          <h2>错题分析 Prompt</h2>
        </div>
        <textarea v-model="form.mistakePrompt" class="input" rows="8" style="resize:vertical;font-size:13px;line-height:1.6"></textarea>
      </div>

      <div class="panel">
        <div class="card-title">
          <h2>成长评估 Prompt</h2>
        </div>
        <textarea v-model="form.assessmentPrompt" class="input" rows="8" style="resize:vertical;font-size:13px;line-height:1.6"></textarea>

        <label style="font-weight:800;display:block;margin-top:16px;margin-bottom:4px">评估周期</label>
        <select v-model="form.assessmentCron" class="input">
          <option value="daily">每日</option>
          <option value="weekly">每周</option>
          <option value="monthly">每月</option>
        </select>
      </div>
    </section>
  </div>
</template>
