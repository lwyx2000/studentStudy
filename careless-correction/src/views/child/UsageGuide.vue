<script setup lang="ts">
const guides = [
  {
    icon: '🌳',
    title: '协同仪表盘',
    path: '/dashboard',
    purpose: '系统的核心入口页面，展示今日最需要关注的任务与即时反馈。',
    usage: [
      '低年级(1-2)：大卡片单任务聚焦模式，做完解锁下一个',
      '高年级(5-6)：数据面板模式，时间轴+优先级清单+错题复习+收纳状态',
      '点击任务卡片上的"确认完成"可获得阳光值奖励',
      '顶栏显示阳光值和当前年级Level',
    ],
  },
  {
    icon: '✅',
    title: '习惯打印',
    path: '/habit',
    purpose: '提供每日习惯的详细SOP操作指引，并通过打印功能将干预拉回物理世界。',
    usage: [
      '顶部查看本周习惯养成进度',
      '中部按SOP步骤操作，配有示意图/动图',
      '点击"发送打印"可生成A4纸质打卡单PDF',
      '周末拍照上传纸质打卡单，AI自动扫描勾选痕迹并核销',
      '家长自查：勾选"今天是否克制了催促"',
    ],
  },
  {
    icon: '🏴‍☠️',
    title: '藏宝库（题库）',
    path: '/mistake',
    purpose: '集中管理所有错题，支持手工录入、批量导入、AI智能选题打印、薄弱环节图表分析。',
    usage: [
      '「录入错题」Tab：填写科目、题型、题目正文、答案，选择是否粗心+12类分类',
      '「错题列表」Tab：按科目/解决状态筛选，勾选题目用于打印',
      '「选题打印」Tab：手工选择或AI智能选择题目，预览后打印（可选附带答案）',
      '「薄弱分析」Tab：查看按科目/粗心分类/知识点/难度分布的柱状图',
      '「导入/导出」Tab：拖拽上传符合v1.0格式的JSON文件批量导入，或一键导出题库',
    ],
  },
  {
    icon: '🎒',
    title: '物品实验室',
    path: '/tracker',
    purpose: '记录物品丢失情况，形成账单反馈激发责任感，并提供收纳指导。',
    usage: [
      '虚拟书包透视图：绿色=未丢，红色=已丢失',
      '高频地点雷达图+累计账单折线图',
      '30天内丢失满3次触发呼吸红光警报+急救卡片',
      '拍摄"收纳前后对比"照片上传可赢取阳光值',
    ],
  },
  {
    icon: '📈',
    title: '成长档案',
    path: '/growth',
    purpose: '给家长提供客观无贬低的长期数据反馈，追踪习惯变化趋势与同龄对比。',
    usage: [
      '长期折线图：漏题率、丢东西频次、任务完成率，按年/学期筛选',
      '同龄常模蜘蛛网图：专注/整洁/元认知/情绪四维度',
      '智能诊断预警卡片（用"阶段性发展发现"而非"警报"）',
      '一键生成PDF成长报告，可分享给老师或打印',
    ],
  },
  {
    icon: '⏱️',
    title: '自治舱',
    path: '/time-task',
    purpose: '5-6年级专属，练习考前复习规划与元认知复盘，番茄钟+预估vs实际对照。',
    usage: [
      '启动番茄钟开始计时，可选科目和预估用时',
      '遇到不确定的题点击"我有疑问?"标记，完成后自动同步到错题本',
      '输入实际用时，系统显示与预估的差异并引导选择耗时原因',
      '复习时间流查看本周安排',
    ],
  },
  {
    icon: '🏅',
    title: '契约勋章',
    path: '/badge',
    purpose: '促成健康的亲子契约，将短期习惯打卡转化为长期内在成就感。',
    usage: [
      '创建成长契约：设定目标和奖励，双签名生效',
      '输入"钱/现金/红包"等关键词会触发防贿赂循证提示',
      '蜂巢勋章架：已解锁亮彩+纸屑动效，未解锁灰度',
      '解锁勋章获得额外阳光值奖励',
    ],
  },
  {
    icon: '🧭',
    title: '家长控制',
    path: '/parent',
    purpose: '家长端的系统设置中心，调节干预参数与通知偏好。',
    usage: [
      '难度天气滑块：1阳光(易)/2微风(中)/3挑战(难)',
      '开关：每日提醒、成就烟花、周报、学校共享',
      '家长自查红线：克制催促和代劳',
    ],
  },
  {
    icon: '📋',
    title: '习惯布置',
    path: '/parent/habit-assign',
    purpose: '家长为孩子布置每周核心习惯，包含执行步骤SOP、奖励阳光值和周数。孩子端自动同步显示活跃习惯。',
    usage: [
      '点击"布置新习惯"填写习惯名称、说明、图标、奖励阳光值、周数',
      '每行输入一个执行步骤，系统按顺序生成SOP',
      '已布置习惯以卡片列表展示，可查看步骤和布置日期',
      '点击"停用"可暂停某个习惯，孩子端将不再显示该习惯',
      '遵循"只调密度，不代劳"原则——布置步骤但不替孩子执行',
    ],
  },
  {
    icon: '🔬',
    title: '循证实验室',
    path: '/parent/lab',
    purpose: '为家长提供执行功能、CBT认知行为疗法等通俗化循证资料。',
    usage: [
      '按分类浏览文章/视频/CBT资源',
      '系统根据孩子评估结果推荐个性化阅读列表',
      '收藏感兴趣的资料方便后续查看',
    ],
  },
  {
    icon: '🌸',
    title: '社区花园',
    path: '/parent/garden',
    purpose: '家长间的匿名经验交流社区，分享心得、获取支持。',
    usage: [
      '浏览匿名帖子列表，按标签筛选',
      '发布自己的经验帖（自动匿名化）',
      '查看其他家庭分享的契约方案',
      '遵守花园守则：不晒分数、不贴标签、不诊断',
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
        <p class="lead">本系统围绕"纠正粗心→陪伴成长"的理念，通过8大功能模块形成闭环干预体系。以下是各页面的详细说明。</p>
      </div>
      <div class="panel">
        <div class="card-title"><h2>角色切换</h2></div>
        <div class="kpi"><strong>2</strong><span>孩子视角 / 家长视角</span></div>
        <p class="lead" style="margin-top:12px">点击顶栏右侧的"家长入口"按钮可在两个视角间切换。孩子视角看到的是日常打卡界面，家长视角看到的是控制中心与循证资源。</p>
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
          <span>完成任务、上传对比照片、解锁勋章均可获得，顶栏实时显示</span>
        </div>
        <div class="kpi">
          <strong>🌱 成长树</strong>
          <span>侧栏展示，随Level变化形态：🌱→🌿→🌳</span>
        </div>
        <div class="kpi">
          <strong>🖨️ 打印</strong>
          <span>习惯打卡单和错题均支持打印为A4纸质版，拍照回传可AI核销</span>
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
