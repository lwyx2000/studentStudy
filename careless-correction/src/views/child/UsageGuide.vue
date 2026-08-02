<script setup lang="ts">
const guides = [
  {
    icon: '🌳',
    title: '协同仪表盘',
    path: '/dashboard',
    purpose: '系统的核心入口页面，展示今日最需要关注的任务与即时反馈。',
    usage: [
      '查看今日任务概览，点击「去今日打卡」跳转到打卡页完成任务',
      '顶栏实时显示 ☀️ 阳光值 · 🍎 苹果，以及当前年级 Lv 等级',
      '「打卡历史」可回顾每日打卡记录并进入编辑',
      '「我的题库」概览可快速进入错题本',
      '侧栏成长树卡片提示：今天只聚焦 1 个核心习惯',
    ],
  },
  {
    icon: '✅',
    title: '每日打卡',
    path: '/habit',
    purpose: '每日微习惯的执行中心，按任务分组展示清单，打勾即打卡。',
    usage: [
      '今日清单按任务分组展示子任务，完成一项就点一下方框打 ✓',
      '全部完成后点击「提交打卡」，等待家长审批通过后获得阳光值',
      '从仪表盘「打卡历史」可查看并编辑过去日期的打卡记录',
      '提交的打卡会进入家长端「待审批打卡」等待审核',
    ],
  },
  {
    icon: '🍎',
    title: '阳光树',
    path: '/tree',
    purpose: '把阳光值可视化为苹果树，让每一点努力都看得见。',
    usage: [
      '每 100 阳光值 = 1 个苹果，苹果可兑换实物奖励',
      '查看苹果记录与兑换记录，追踪自己的成长轨迹',
      '页面内置玩法说明，帮助理解积分规则',
    ],
  },
  {
    icon: '📚',
    title: '我的题库',
    path: '/mistake',
    purpose: '集中记录和整理错题，拍照即存，按间隔重复节奏复习。',
    usage: [
      '「添加错题」：拍照上传，标记科目与 12 类粗心分类',
      '「错题列表」：按科目/状态筛选，点击进入复习',
      '「待复习错题」：到期题目集中复习，回答"能否独立做对"推进遗忘曲线',
      '「题库概览」：查看错题总量与薄弱分类分布',
    ],
  },
  {
    icon: '🎒',
    title: '物品管理',
    path: '/tracker',
    purpose: '记录丢失与收纳，用数据账单培养物品管理责任感。',
    usage: [
      '「新增丢失记录」：填写物品名、丢失地点、估计金额',
      '「添加收纳记录」：记录收纳位置，把整理变成习惯',
      '30 天内同一物品丢失满 3 次触发「高频流失急救」红光提醒',
      '查看本月流失成本与高发地点统计，直观感受代价',
    ],
  },
  {
    icon: '📈',
    title: '成长档案',
    path: '/growth',
    purpose: '把粗心变化看成发展曲线，给家长客观、无贬低的长期数据反馈。',
    usage: [
      '「长期成长趋势」：漏题率 / 丢东西频次 / 任务完成率折线图',
      '「同龄常模对比」：对照同龄儿童的参考范围',
      '智能预警卡片：用「阶段性发展发现」代替焦虑化警报',
      'LLM 驱动的综合评估报告，自动总结进步与建议',
    ],
  },
  {
    icon: '☀️',
    title: '阳光兑换',
    path: '/sunlight',
    purpose: '阳光值余额与兑换商城，把努力变成可兑现的奖励。',
    usage: [
      '查看阳光值余额与兑换记录',
      '在兑换商城用阳光值兑换家长配置的奖励（如亲子电影夜、乐高自由拼）',
      '苹果与阳光值联动：每 100 阳光值 = 1 个苹果',
    ],
  },
  {
    icon: '🏅',
    title: '勋章馆',
    path: '/badge',
    purpose: '把短期打卡变成长期的内在成就感。',
    usage: [
      '蜂巢勋章陈列架：已解锁勋章亮彩展示 + 纸屑动效，未解锁为灰色',
      '解锁条件：连续打卡天数 / 任务完成数 / 零物品丢失周期',
      '解锁新勋章可额外获得阳光值奖励',
    ],
  },
  {
    icon: '🧭',
    title: '家长控制',
    path: '/parent',
    purpose: '家长端总览仪表盘，观察孩子今日任务、习惯与错题，审批打卡。',
    usage: [
      '顶部「孩子选择器」可切换查看不同孩子',
      '查看今日任务完成率、习惯 SOP 步骤与错题积累',
      '审批孩子的打卡申请，批准后自动检查勋章解锁',
      '设置开关：每日小岛提醒 / 成就烟花 / 学校共享（只调密度，不催作业）',
      '浏览「循证资源」文章，学习科学的育儿方法',
    ],
  },
  {
    icon: '👦',
    title: '孩子管理',
    path: '/parent/children',
    purpose: '添加、编辑、删除孩子账号，并可一键切换进入孩子视角。',
    usage: [
      '「添加孩子」：填写名字与年级，自动生成孩子登录名',
      '点击「进入孩子视角」以孩子身份查看和操作（顶栏显示「👦 XX 的视角」）',
      '编辑孩子资料或删除账号（删除不可撤销，请谨慎）',
    ],
  },
  {
    icon: '📊',
    title: '进度查看',
    path: '/parent/progress',
    purpose: '孩子多维进度数据可视化看板。',
    usage: [
      '查看任务完成率、错题率、物品流失等维度的趋势图表',
      '与成长档案互补：一个看长期曲线，一个看近期完成度',
    ],
  },
  {
    icon: '📋',
    title: '任务与习惯',
    path: '/parent/tasks',
    purpose: '为孩子的每日任务与习惯 SOP 建模，布置习惯但不替孩子完成。',
    usage: [
      '创建/编辑每日任务，设置奖励阳光值与图标',
      '为任务添加子任务，并区分「平时 / 周末」适用',
      '维护习惯 SOP 步骤，孩子端自动同步展示',
      '「打印预览」可生成 A4 每日计划清单 PDF，把任务拉回物理世界',
      '遵循「只调密度，不代劳」原则——布置步骤但不替孩子执行',
    ],
  },
  {
    icon: '📦',
    title: '任务清单',
    path: '/parent/inventory',
    purpose: '查看所有（含已归档）任务与习惯的完整清单。',
    usage: [
      '浏览全部任务模板，含已完成与已归档条目',
      '用于盘点历史布置，调整未来的任务密度',
    ],
  },
  {
    icon: '🎒',
    title: '物品统计',
    path: '/parent/items',
    purpose: '物品丢失数据的统计分析。',
    usage: [
      '按物品 / 地点查看丢失频率与金额损失统计',
      '配合孩子端「物品管理」页形成完整的数据闭环',
    ],
  },
  {
    icon: '☀️',
    title: '阳光值管理',
    path: '/parent/sunlight',
    purpose: '阳光值发放与兑换管理。',
    usage: [
      '手动发放 / 调整孩子的阳光值',
      '管理兑换物品库与兑换记录',
    ],
  },
  {
    icon: '🏅',
    title: '勋章管理',
    path: '/parent/badges',
    purpose: '勋章定义与解锁配置。',
    usage: [
      '查看勋章列表与解锁条件，了解孩子成就进度',
      '设置解锁奖励的阳光值',
    ],
  },
  {
    icon: '🤖',
    title: '模型配置',
    path: '/parent/llm',
    purpose: '对接 AI 分析的模型参数配置。',
    usage: [
      '配置大模型 API 地址、Key 与模型名称',
      '设置错题分析与成长评估的 Prompt',
      '启用后，错题拍照上传可自动识别并生成分析',
    ],
  },
  {
    icon: '📖',
    title: '使用说明（本页）',
    path: '/guide',
    purpose: '当前页面，汇总系统全部页面的用途与用法。',
    usage: [
      '按模块浏览各页面说明',
      '页面链接与顶栏导航、路由一一对应',
    ],
  },
]
</script>

<template>
  <div class="page">
    <section class="page-hero">
      <div class="hero-card">
        <span class="eyebrow">📖 使用说明</span>
        <h1>每个页面的用处与用法</h1>
        <p class="lead">本系统围绕「纠正粗心 → 陪伴成长」的理念，通过孩子端 8 个 + 家长端 9 个功能页面形成闭环干预体系（另含本使用说明页）。以下是各页面的详细说明。</p>
      </div>
      <div class="panel">
        <div class="card-title"><h2>角色切换</h2></div>
        <div class="kpi"><strong>2</strong><span>孩子视角 / 家长视角</span></div>
        <p class="lead" style="margin-top:12px">
          首次使用：家长注册 → 在「孩子管理」添加孩子 → 完成基线评估（/onboarding）→ 在「任务与习惯」布置任务。
          家长在「孩子管理」点击「进入孩子视角」可切换为孩子身份，顶栏显示「👦 名字 的视角」；点击「↩ 返回家长端」即可切回。顶栏右侧还提供「🔑 修改密码」与「退出登录」。
        </p>
      </div>
    </section>

    <section class="guide-list">
      <div v-for="g in guides" :key="g.path" class="guide-card">
        <div class="guide-header">
          <span class="guide-icon">{{ g.icon }}</span>
          <div>
            <h2>{{ g.title }}</h2>
            <span class="tag">{{ g.path }}</span>
          </div>
        </div>
        <div class="guide-purpose">
          <strong>用途：</strong>{{ g.purpose }}
        </div>
        <div class="guide-usage">
          <strong>用法：</strong>
          <ul>
            <li v-for="(tip, i) in g.usage" :key="i">{{ tip }}</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="panel" style="margin-top:8px">
      <div class="card-title"><h2>通用操作</h2></div>
      <div class="grid-3">
        <div class="kpi">
          <strong>☀️ 阳光值</strong>
          <span>完成任务、解锁勋章均可获得；每 100 阳光值 = 1 个苹果，可兑换实物奖励，顶栏实时显示</span>
        </div>
        <div class="kpi">
          <strong>🌳 成长树</strong>
          <span>侧栏成长树卡片展示（孩子端显示「我的成长树」）；「阳光树」页面把阳光值可视化为苹果树</span>
        </div>
        <div class="kpi">
          <strong>🖨️ 打印</strong>
          <span>家长在「任务与习惯」可用打印预览生成 A4 每日计划清单 PDF，把任务带回物理世界</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.guide-list { display: flex; flex-direction: column; gap: 16px; }
.guide-card { padding: 24px; border-radius: 32px; background: rgba(255,255,255,.78); border: 1px solid rgba(222,219,204,.9); box-shadow: 0 10px 28px rgba(75,63,54,.08); }
.guide-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
.guide-icon { width: 52px; height: 52px; border-radius: 18px; background: var(--yellow); display: grid; place-items: center; font-size: 28px; flex-shrink: 0; }
.guide-purpose { margin-bottom: 10px; font-size: 15px; line-height: 1.7; color: var(--ink); }
.guide-usage { font-size: 14px; line-height: 1.7; }
.guide-usage strong { display: block; margin-bottom: 4px; }
.guide-usage ul { margin: 0; padding-left: 20px; }
.guide-usage li { margin-bottom: 4px; color: var(--muted); }
.guide-usage li::marker { color: var(--primary); }
</style>
