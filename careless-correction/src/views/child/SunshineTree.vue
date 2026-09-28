<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { useUserStore } from '../../stores'
import { api } from '../../utils/api'
import { Typewriter, Modal } from 'animal-island-vue'


const userStore = useUserStore()

// ── DOM ref for Three.js canvas mount ──
const sceneRef = ref<HTMLDivElement>()
let renderer: THREE.WebGLRenderer | null = null
let scene3d: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let clock: THREE.Clock | null = null
let rafId = 0
let resizeObserver: ResizeObserver | null = null

// ── Scene constants ──
const SCENE_HEIGHT = 420

// ── Scene object collections（漫画式 3D：Toon 材质 + 描边壳）──
interface SunOrbObj {
  group: THREE.Group
  bodyMat: THREE.MeshToonMaterial
  outlineMat: THREE.MeshBasicMaterial
  haloMat: THREE.SpriteMaterial
  labelMat: THREE.SpriteMaterial
  pendingId: number
  amount: number
  baseX: number
  baseY: number
  phase: number
  flying: boolean
  flyT: number
  start: THREE.Vector3
}

interface ButterflyObj {
  group: THREE.Group
  flapL: THREE.Group
  flapR: THREE.Group
  phase: number
  speed: number
  centerX: number
  centerY: number
  centerZ: number
  radiusX: number
  radiusY: number
  zAmp: number
  zPhase: number
  size: number
  flapPhase: number
}

interface LeafObj {
  mesh: THREE.Mesh
  x: number
  y: number
  z: number
  vx: number
  vy: number
  rotSpeed: number
  phase: number
}

interface CloudObj {
  group: THREE.Group
  speed: number
}

interface FlowerObj {
  group: THREE.Group
  phase: number
  speed: number
}

let clouds: CloudObj[] = []
let sunOrbs: SunOrbObj[] = []
let butterflies: ButterflyObj[] = []
let leaves: LeafObj[] = []
let flowers: FlowerObj[] = []

// Tree parts
let treeGroup: THREE.Group | null = null
let canopyGlowMat: THREE.MeshBasicMaterial | null = null
let canopyGlow: THREE.Mesh | null = null
interface AppleObj { group: THREE.Group; baseY: number; phase: number; popT: number }
let treeApples: AppleObj[] = []
let sunSprite: THREE.Sprite | null = null
let sunRaySprite: THREE.Sprite | null = null
let sunGroup: THREE.Group | null = null
let shakeT = -1            // 树干剧烈摇晃剩余时间（<0 表示未在摇晃）
let glowFlashT = -1        // 树冠光晕闪烁剩余时间（收集阳光到达时触发）
const pointerNdc = { x: 0, y: 0 }   // 指针视差
const raycaster = new THREE.Raycaster()
const downPos = { x: 0, y: 0 }
let sceneWidth = 800

// ── UI state (Vue overlays) ──
const showGrowAnim = ref(false)
const growMessage = ref('')
const collectMessage = ref('')

function clickTree() {
  if (!userStore.canGrowApple) {
    triggerShake()
    growMessage.value = `还需要 ${userStore.sunlightPerApple - userStore.sunlightPoints} 阳光才能种出 1 个苹果`
    setTimeout(() => { growMessage.value = '' }, 2500)
    return
  }

  triggerShake()

  const ok = userStore.growApple()
  if (ok) {
    showGrowAnim.value = true
    growMessage.value = `🍎 种出了 1 个苹果！当前共有 ${userStore.apples} 个苹果`
    setTimeout(() => {
      showGrowAnim.value = false
      growMessage.value = ''
    }, 3000)
  }
}

// ── Apple redemption（提交申请，家长审批后扣苹果）──
const showRedeemModal = ref(false)
const redeemCount = ref(1)
const redeemReason = ref('')
const redeemSuccess = ref('')
const redeemError = ref('')
const redeemSubmitting = ref(false)

interface AppleRedemptionRequestInfo {
  id: number
  count: number
  reason: string
  status: 'pending' | 'approved' | 'rejected'
  createdAt: string | null
}
const redemptionRequests = ref<AppleRedemptionRequestInfo[]>([])
const pendingRedemption = computed(() => redemptionRequests.value.find(r => r.status === 'pending'))

async function loadRedemptionRequests() {
  try {
    const res = await api.points.getAppleRedemptionRequests()
    redemptionRequests.value = (res.requests ?? []).map((r: any) => ({
      id: r.id,
      count: r.count,
      reason: r.reason ?? '',
      status: r.status,
      createdAt: r.createdAt ?? null,
    }))
  } catch { /* offline */ }
}

function openRedeemModal() {
  redeemCount.value = 1
  redeemReason.value = ''
  redeemSuccess.value = ''
  redeemError.value = ''
  showRedeemModal.value = true
}

async function confirmRedeem() {
  if (redeemSubmitting.value) return
  if (redeemCount.value <= 0 || redeemCount.value > userStore.apples) return
  redeemSubmitting.value = true
  redeemError.value = ''
  try {
    const result = await userStore.redeemApple(redeemCount.value, redeemReason.value || `和爸爸妈妈兑换 ${redeemCount.value} 元`)
    if (result === 'busy') {
      redeemError.value = '正在提交，请稍候'
      return
    }
    if (!result) {
      redeemError.value = '苹果数量不足或数量无效'
      return
    }
    redeemSuccess.value = '📨 兑换申请已提交，等爸爸妈妈审批通过后就能兑换啦！'
    setTimeout(() => { showRedeemModal.value = false }, 2200)
    loadRedemptionRequests()
  } catch (e: any) {
    redeemError.value = e?.message || '提交失败，请重试'
  } finally {
    redeemSubmitting.value = false
  }
}

function statusLabel(s: string) {
  return s === 'pending' ? '🕐 待审批' : s === 'approved' ? '✅ 已通过' : '❌ 已驳回'
}

// ── Computed ──
const sunlightProgress = computed(() => {
  const pct = (userStore.sunlightPoints % userStore.sunlightPerApple) / userStore.sunlightPerApple * 100
  return Math.round(pct)
})

const earnHistory = computed(() =>
  userStore.appleHistory.filter(r => r.type === 'grow')
)

const redeemHistory = computed(() =>
  userStore.appleHistory.filter(r => r.type === 'redeem')
)

// ══════════════════════════════════════════════════════════════
//  Three.js 场景 — 漫画卡通渲染（MeshToonMaterial + 描边壳），全部程序化建模
// ══════════════════════════════════════════════════════════════

// ── 卡通材质工具 ──
// 天空用容器 CSS 渐变，renderer 透明；物体用 3 阶梯度 Toon 平涂 + BackSide 描边壳
const OUTLINE_CSS = '#3a3335'
let toonGradientMap: THREE.DataTexture | null = null
function getToonGradientMap() {
  if (!toonGradientMap) {
    const data = new Uint8Array([90, 0, 0, 255, 170, 0, 0, 255, 255, 0, 0, 255])
    toonGradientMap = new THREE.DataTexture(data, 3, 1, THREE.RGBAFormat)
    toonGradientMap.minFilter = THREE.NearestFilter
    toonGradientMap.magFilter = THREE.NearestFilter
    toonGradientMap.needsUpdate = true
  }
  return toonGradientMap
}
function toonMat(color: number) {
  return new THREE.MeshToonMaterial({ color, gradientMap: getToonGradientMap() })
}
function addOutline(mesh: THREE.Mesh, thickness = 1.06) {
  const outline = new THREE.Mesh(
    mesh.geometry,
    new THREE.MeshBasicMaterial({ color: 0x3a3335, side: THREE.BackSide }),
  )
  outline.scale.setScalar(thickness)
  mesh.add(outline)
  return outline
}

// ── 装饰太阳：圆盘（固定不转）+ 光芒（单独 Sprite 旋转），挂相机右上角 ──
function createSunDiscSprite() {
  const size = 256
  const cv = document.createElement('canvas')
  cv.width = size
  cv.height = size
  const ctx = cv.getContext('2d')!
  const c = size / 2
  // 光晕
  const glow = ctx.createRadialGradient(c, c, 50, c, c, 120)
  glow.addColorStop(0, 'rgba(255,213,79,0.45)')
  glow.addColorStop(1, 'rgba(255,213,79,0)')
  ctx.fillStyle = glow
  ctx.fillRect(0, 0, size, size)
  // 圆盘 + 描边
  ctx.fillStyle = '#ffd54f'
  ctx.strokeStyle = OUTLINE_CSS
  ctx.lineWidth = 9
  ctx.beginPath()
  ctx.arc(c, c, 82, 0, Math.PI * 2)
  ctx.fill()
  ctx.stroke()
  // 高光
  ctx.fillStyle = 'rgba(255,247,189,0.75)'
  ctx.beginPath()
  ctx.arc(c - 26, c - 30, 20, 0, Math.PI * 2)
  ctx.fill()
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  const mat = new THREE.SpriteMaterial({ map: tex, transparent: false, depthTest: false, depthWrite: false })
  const sprite = new THREE.Sprite(mat)
  sprite.scale.setScalar(3.0)
  sprite.renderOrder = -9   // 背景层：最先绘制，所有场景物体叠在其上
  return sprite
}

// 光芒：8 根简洁的锥形射线（常规太阳造型），单独 Sprite 只旋转它
function createSunRaysSprite() {
  const size = 512
  const cv = document.createElement('canvas')
  cv.width = size
  cv.height = size
  const ctx = cv.getContext('2d')!
  const c = size / 2
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2
    const cos = Math.cos(a)
    const sin = Math.sin(a)
    const baseHalf = 15
    const inner = 100
    const outer = 152
    ctx.beginPath()
    ctx.moveTo(c + cos * inner - sin * baseHalf, c + sin * inner + cos * baseHalf)
    ctx.lineTo(c + cos * outer, c + sin * outer)
    ctx.lineTo(c + cos * inner + sin * baseHalf, c + sin * inner - cos * baseHalf)
    ctx.closePath()
    ctx.fillStyle = '#ffd54f'
    ctx.fill()
  }
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  const mat = new THREE.SpriteMaterial({ map: tex, transparent: false, depthTest: false, depthWrite: false })
  const sprite = new THREE.Sprite(mat)
  sprite.scale.setScalar(4.6)
  sprite.renderOrder = -10  // 光芒在圆盘之后（更靠背景）
  return sprite
}

// ── 云朵：多个白色 Toon 球叠加成 Group ──
function createCloud(scale: number) {
  const g = new THREE.Group()
  const mat = toonMat(0xffffff)
  const geo = new THREE.SphereGeometry(1, 14, 12)
  const puffs: Array<[number, number, number, number]> = [
    [0, 0.15, 0, 1], [-1.15, 0, 0, 0.72], [1.2, -0.02, 0, 0.68], [-0.5, 0.55, 0, 0.6], [0.55, 0.5, 0, 0.55],
  ]
  for (const [x, y, z, r] of puffs) {
    const m = new THREE.Mesh(geo, mat)
    m.position.set(x, y, z)
    m.scale.setScalar(r)
    g.add(m)
  }
  g.scale.setScalar(scale)
  return g
}
function buildClouds() {
  if (!scene3d) return
  const specs: Array<[number, number, number, number]> = [
    [-8, 6.4, -5, 1.1], [-2.5, 7.6, -7, 0.85], [4.5, 6.1, -6, 1.0], [8.5, 7.2, -8, 0.75],
  ]
  for (const [x, y, z, s] of specs) {
    const g = createCloud(s)
    g.position.set(x, y, z)
    scene3d.add(g)
    clouds.push({ group: g, speed: 0.3 + Math.random() * 0.45 })
  }
}

// ── 草地：扁球绿色圆丘 + 小花（微风摇摆）+ 小树苗 ──
function buildGround() {
  if (!scene3d) return
  const grass = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), toonMat(0x70c85b))
  grass.scale.set(18, 2.6, 11)
  grass.position.set(0, -2.55, 1)
  scene3d.add(grass)

  const flowerSpots: Array<[number, number]> = [[-5.2, 2.2], [-3.8, 3.1], [-6.4, 3.4], [4.6, 2.4], [6.0, 3.2], [3.4, 3.6]]
  const stemGeo = new THREE.CylinderGeometry(0.03, 0.04, 0.5, 6)
  const petalGeo = new THREE.SphereGeometry(0.11, 8, 8)
  const centerGeo = new THREE.SphereGeometry(0.1, 8, 8)
  for (let i = 0; i < flowerSpots.length; i++) {
    const g = new THREE.Group()
    const stem = new THREE.Mesh(stemGeo, toonMat(0x44934b))
    stem.position.y = 0.25
    g.add(stem)
    const petalMat = toonMat(i % 2 ? 0xff8ab0 : 0xffb74d)
    for (let p = 0; p < 5; p++) {
      const a = (p / 5) * Math.PI * 2
      const petal = new THREE.Mesh(petalGeo, petalMat)
      petal.position.set(Math.cos(a) * 0.15, 0.55, Math.sin(a) * 0.15)
      g.add(petal)
    }
    const center = new THREE.Mesh(centerGeo, toonMat(0xffd54f))
    center.position.y = 0.55
    g.add(center)
    g.position.set(flowerSpots[i][0], 0.02, flowerSpots[i][1])
    g.rotation.y = Math.random() * Math.PI * 2
    scene3d.add(g)
    flowers.push({ group: g, phase: Math.random() * Math.PI * 2, speed: 1.6 + Math.random() })
  }

  const saplingSpots: Array<[number, number]> = [[-7.6, 1.2], [7.2, 1.6]]
  for (const [x, z] of saplingSpots) {
    const g = new THREE.Group()
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.11, 1.1, 8), toonMat(0x8d5a32))
    trunk.position.y = 0.55
    g.add(trunk)
    const c1 = new THREE.Mesh(new THREE.SphereGeometry(0.42, 12, 10), toonMat(0x53ad4a))
    c1.position.set(-0.18, 1.25, 0)
    const c2 = new THREE.Mesh(new THREE.SphereGeometry(0.5, 12, 10), toonMat(0x62bc52))
    c2.position.set(0.2, 1.45, 0.05)
    const c3 = new THREE.Mesh(new THREE.SphereGeometry(0.38, 12, 10), toonMat(0x75c95e))
    c3.position.set(0, 1.8, -0.1)
    g.add(c1, c2, c3)
    g.position.set(x, 0, z)
    scene3d.add(g)
  }

  // 草丛：三叶锥形小草，散布点缀在草地上
  const tuftMat = toonMat(0x4fa552)
  const tufts: Array<[number, number, number]> = [
    [-2.6, 2.6, 0.9], [2.8, 2.4, 0.8], [-4.4, 1.7, 1.1], [4.9, 1.5, 0.9], [-1.4, 3.4, 0.65], [1.7, 3.2, 0.7],
  ]
  const bladeGeo = new THREE.ConeGeometry(0.045, 0.34, 5)
  for (const [x, z, s] of tufts) {
    const tuft = new THREE.Group()
    for (let b = -1; b <= 1; b++) {
      const blade = new THREE.Mesh(bladeGeo, tuftMat)
      blade.position.set(b * 0.07, 0.17, 0)
      blade.rotation.z = -b * 0.32
      tuft.add(blade)
    }
    tuft.position.set(x, 0.02, z)
    tuft.scale.setScalar(s)
    tuft.rotation.y = Math.random() * Math.PI * 2
    scene3d.add(tuft)
  }
}

// ── 苹果树：粗壮树干 + 球体树冠 + 可种苹果时的金色光晕壳 ──
function buildTree() {
  if (!scene3d) return
  treeGroup = new THREE.Group()

  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 0.62, 3.1, 12), toonMat(0x8d5a32))
  trunk.position.y = 1.55
  addOutline(trunk, 1.05)
  treeGroup.add(trunk)

  // 分叉树枝
  const branchGeo = new THREE.CylinderGeometry(0.09, 0.16, 1.3, 8)
  const bl = new THREE.Mesh(branchGeo, toonMat(0x8d5a32))
  bl.position.set(-0.55, 2.6, 0.1)
  bl.rotation.z = 0.7
  const br = new THREE.Mesh(branchGeo, toonMat(0x8d5a32))
  br.position.set(0.55, 2.75, -0.1)
  br.rotation.z = -0.7
  treeGroup.add(bl, br)

  // 树干上的卡通树疤（年轮圈）
  const knot = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.045, 8, 14), toonMat(0x6b4423))
  knot.position.set(0.2, 1.35, 0.56)
  knot.rotation.x = 0.25
  treeGroup.add(knot)

  // 树冠：多个绿色 Toon 球错落叠加
  const darkMat = toonMat(0x3e9e4e)
  const lightMat = toonMat(0x62bc57)
  const canopySpecs: Array<[number, number, number, number, boolean]> = [
    [0, 4.5, 0, 1.75, false], [-1.5, 3.9, 0.4, 1.25, true], [1.55, 3.95, 0.3, 1.2, false],
    [-0.8, 5.35, -0.3, 1.05, true], [0.9, 5.25, -0.4, 1.0, false], [0.1, 3.7, 1.15, 1.0, true],
  ]
  const canopyGeo = new THREE.SphereGeometry(1, 18, 14)
  for (const [x, y, z, r, light] of canopySpecs) {
    const m = new THREE.Mesh(canopyGeo, light ? lightMat : darkMat)
    m.position.set(x, y, z)
    m.scale.setScalar(r)
    addOutline(m, 1.04)
    treeGroup.add(m)
  }

  // 金色光晕壳（可种苹果时呼吸脉冲）
  canopyGlowMat = new THREE.MeshBasicMaterial({
    color: 0xffeb3b, transparent: true, opacity: 0, depthWrite: false, side: THREE.FrontSide,
  })
  canopyGlow = new THREE.Mesh(new THREE.SphereGeometry(3.05, 20, 16), canopyGlowMat)
  canopyGlow.position.set(0, 4.5, 0)
  canopyGlow.visible = false
  treeGroup.add(canopyGlow)

  treeGroup.position.set(0, 0, 0)
  scene3d.add(treeGroup)

  // 树底阴影（贴在草地上）
  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(2.3, 24),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.13, depthWrite: false }),
  )
  shadow.rotation.x = -Math.PI / 2
  shadow.position.set(0, 0.03, 0.3)
  scene3d.add(shadow)
}

// ── 树冠上的苹果（最多 8 个，红/金/青三色变体）──
const APPLE_POINTS: Array<[number, number, number]> = [
  [-1.15, 3.55, 1.15], [1.25, 3.45, 1.0], [-0.3, 4.5, 1.45], [1.7, 4.3, 0.5],
  [-1.75, 4.35, 0.45], [0.5, 5.15, 1.1], [-0.6, 3.3, 1.5], [0.95, 3.8, -1.25],
]
const APPLE_COLORS = [0xe53935, 0xf5a623, 0x5dbca9]

function buildApples() {
  if (!treeGroup) return
  // 移除旧苹果
  for (const a of treeApples) {
    treeGroup.remove(a.group)
    a.group.traverse((o) => {
      const m = o as THREE.Mesh
      if (m.isMesh) {
        m.geometry.dispose()
        const mat = m.material as THREE.Material
        mat.dispose()
      }
    })
  }
  const prevCount = treeApples.length
  treeApples = []

  const count = Math.min(userStore.apples, 8)
  if (count === 0) return

  for (let i = 0; i < count; i++) {
    const [x, y, z] = APPLE_POINTS[i]
    const g = new THREE.Group()
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.3, 14, 12), toonMat(APPLE_COLORS[i % 3]))
    body.scale.set(1, 0.92, 1)
    addOutline(body, 1.08)
    g.add(body)
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.035, 0.2, 6), toonMat(0x75451f))
    stem.position.y = 0.32
    g.add(stem)
    const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 6), toonMat(0x48a33b))
    leaf.scale.set(1.5, 0.45, 0.8)
    leaf.position.set(0.14, 0.34, 0)
    leaf.rotation.z = -0.4
    g.add(leaf)

    g.position.set(x, y, z)
    // 新种出的苹果做弹入动画（0 → 1.2 → 1 回弹）
    const isNew = i >= prevCount
    g.scale.setScalar(isNew ? 0.01 : 1)
    treeGroup.add(g)
    treeApples.push({ group: g, baseY: y, phase: i * 1.4, popT: isNew ? 0 : 1 })
  }
}

// ── 蝴蝶：纹理翅膀（上/下翅 + 斑点描边）+ 头胸腹 + 卷触角，绕树飞 8 字轨迹 ──
interface WingPalette { main: string; edge: string; spot: string }

function makeWingTexture(pal: WingPalette, lower: boolean, outlineCss: string) {
  const w = 256
  const h = 192
  const cv = document.createElement('canvas')
  cv.width = w
  cv.height = h
  const ctx = cv.getContext('2d')!
  ctx.lineJoin = 'round'
  ctx.beginPath()
  if (!lower) {
    // 上翅：大扇形，从翅根(左下)向上展开
    ctx.moveTo(20, 170)
    ctx.bezierCurveTo(30, 70, 110, 12, 216, 26)
    ctx.bezierCurveTo(248, 32, 244, 92, 196, 128)
    ctx.bezierCurveTo(140, 168, 70, 182, 20, 170)
  } else {
    // 下翅：小扇形 + 波浪尾缘
    ctx.moveTo(20, 26)
    ctx.bezierCurveTo(90, 20, 170, 48, 198, 96)
    ctx.bezierCurveTo(212, 124, 186, 150, 158, 138)
    ctx.bezierCurveTo(142, 160, 112, 154, 102, 134)
    ctx.bezierCurveTo(78, 152, 48, 142, 42, 120)
    ctx.bezierCurveTo(24, 96, 12, 56, 20, 26)
  }
  ctx.closePath()
  const grad = ctx.createLinearGradient(0, 0, w, h)
  grad.addColorStop(0, pal.edge)
  grad.addColorStop(0.55, pal.main)
  grad.addColorStop(1, pal.edge)
  ctx.fillStyle = grad
  ctx.fill()
  ctx.strokeStyle = outlineCss
  ctx.lineWidth = 12
  ctx.stroke()
  // 斑点装饰
  ctx.fillStyle = pal.spot
  if (!lower) {
    ctx.beginPath()
    ctx.arc(158, 56, 17, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(104, 96, 11, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.55)'
    ctx.lineWidth = 7
    ctx.beginPath()
    ctx.moveTo(52, 148)
    ctx.bezierCurveTo(96, 122, 148, 98, 188, 84)
    ctx.stroke()
  } else {
    ctx.beginPath()
    ctx.arc(120, 82, 13, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(70, 70, 8, 0, Math.PI * 2)
    ctx.fill()
  }
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

function buildButterflies() {
  if (!scene3d) return
  const palettes: WingPalette[] = [
    { main: '#b39ddb', edge: '#7e57c2', spot: 'rgba(255,255,255,0.92)' },
    { main: '#ffab91', edge: '#ff7043', spot: 'rgba(255,255,255,0.92)' },
    { main: '#81d4fa', edge: '#29b6f6', spot: 'rgba(255,255,255,0.92)' },
  ]
  const bodyMat = toonMat(0x5d4037)
  for (let i = 0; i < 3; i++) {
    const g = new THREE.Group()
    const pal = palettes[i]
    const upTex = makeWingTexture(pal, false, OUTLINE_CSS)
    const lowTex = makeWingTexture(pal, true, OUTLINE_CSS)

    const makeFlap = (side: 1 | -1) => {
      const flap = new THREE.Group()
      const upMat = new THREE.MeshBasicMaterial({ map: upTex, transparent: true, side: THREE.DoubleSide, depthWrite: false })
      const up = new THREE.Mesh(new THREE.PlaneGeometry(0.85, 0.64), upMat)
      up.position.set(side * 0.42, 0.24, 0)
      up.scale.x = side
      up.rotation.z = side * 0.22
      flap.add(up)
      const lowMat = new THREE.MeshBasicMaterial({ map: lowTex, transparent: true, side: THREE.DoubleSide, depthWrite: false })
      const low = new THREE.Mesh(new THREE.PlaneGeometry(0.64, 0.48), lowMat)
      low.position.set(side * 0.32, -0.2, 0)
      low.scale.x = side
      low.rotation.z = -side * 0.28
      flap.add(low)
      return flap
    }
    const flapL = makeFlap(-1)
    const flapR = makeFlap(1)
    g.add(flapL, flapR)

    // 胸 + 腹
    const chest = new THREE.Mesh(new THREE.CapsuleGeometry(0.075, 0.16, 4, 10), bodyMat)
    chest.position.set(0, 0.02, 0.02)
    g.add(chest)
    const abdomen = new THREE.Mesh(new THREE.SphereGeometry(0.085, 10, 8), bodyMat)
    abdomen.scale.set(0.85, 0.85, 1.7)
    abdomen.position.set(0, -0.04, -0.2)
    g.add(abdomen)
    // 头 + 大眼
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 10), bodyMat)
    head.position.set(0, 0.16, 0.14)
    g.add(head)
    const eyeGeo = new THREE.SphereGeometry(0.045, 8, 8)
    const eyeMat = toonMat(0x212121)
    const hlGeo = new THREE.SphereGeometry(0.016, 6, 6)
    const hlMat = toonMat(0xffffff)
    for (const ex of [-0.06, 0.06]) {
      const eye = new THREE.Mesh(eyeGeo, eyeMat)
      eye.position.set(ex, 0.19, 0.22)
      g.add(eye)
      const hl = new THREE.Mesh(hlGeo, hlMat)
      hl.position.set(ex + 0.015, 0.205, 0.255)
      g.add(hl)
    }
    // 卷触角（二次贝塞尔细管 + 端点球）
    const antMat = toonMat(0x3e2723)
    const tipGeo = new THREE.SphereGeometry(0.03, 6, 6)
    for (const side of [-1, 1]) {
      const curve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(side * 0.03, 0.25, 0.14),
        new THREE.Vector3(side * 0.14, 0.44, 0.16),
        new THREE.Vector3(side * 0.2, 0.4, 0.02),
      )
      g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 8, 0.012, 5, false), antMat))
      const tip = new THREE.Mesh(tipGeo, antMat)
      tip.position.set(side * 0.2, 0.4, 0.02)
      g.add(tip)
    }

    g.scale.setScalar(0.3)
    scene3d.add(g)
    butterflies.push({
      group: g, flapL, flapR,
      phase: Math.random() * Math.PI * 2,
      speed: 0.16 + Math.random() * 0.12,
      centerX: (Math.random() - 0.5) * 2,
      centerY: 3.4 + (Math.random() - 0.5) * 1.0,
      centerZ: 1.5,
      radiusX: 5 + Math.random() * 1.5,
      radiusY: 1.6 + Math.random() * 0.6,
      zAmp: 4.5,
      zPhase: Math.random() * Math.PI * 2,
      size: 0.3,
      flapPhase: Math.random() * Math.PI * 2,
    })
  }
}

// ── 落叶：Canvas 叶片贴图（叶脉 + 描边），从树冠飘落，落地后重新生成 ──
function makeLeafTexture(color: string, vein: string, outlineCss: string) {
  const cv = document.createElement('canvas')
  cv.width = 128
  cv.height = 128
  const ctx = cv.getContext('2d')!
  ctx.lineJoin = 'round'
  // 叶柄
  ctx.strokeStyle = outlineCss
  ctx.lineWidth = 8
  ctx.beginPath()
  ctx.moveTo(64, 122)
  ctx.lineTo(64, 100)
  ctx.stroke()
  // 叶片
  ctx.beginPath()
  ctx.moveTo(64, 104)
  ctx.bezierCurveTo(14, 88, 12, 30, 64, 8)
  ctx.bezierCurveTo(116, 30, 114, 88, 64, 104)
  ctx.closePath()
  ctx.fillStyle = color
  ctx.fill()
  ctx.lineWidth = 9
  ctx.stroke()
  // 叶脉
  ctx.strokeStyle = vein
  ctx.lineWidth = 5
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.moveTo(64, 98)
  ctx.lineTo(64, 22)
  ctx.moveTo(64, 78)
  ctx.lineTo(40, 60)
  ctx.moveTo(64, 78)
  ctx.lineTo(88, 60)
  ctx.moveTo(64, 52)
  ctx.lineTo(46, 38)
  ctx.moveTo(64, 52)
  ctx.lineTo(82, 38)
  ctx.stroke()
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

function buildLeaves() {
  if (!scene3d) return
  const leafGeo = new THREE.PlaneGeometry(0.34, 0.34)
  const variants = [
    makeLeafTexture('#f2a846', '#c77f2a', OUTLINE_CSS),
    makeLeafTexture('#66bb6a', '#3e8e41', OUTLINE_CSS),
    makeLeafTexture('#e57373', '#c04f4f', OUTLINE_CSS),
  ]
  for (let i = 0; i < 4; i++) {
    const mat = new THREE.MeshBasicMaterial({
      map: variants[i % variants.length], transparent: true, side: THREE.DoubleSide, depthWrite: false,
    })
    const m = new THREE.Mesh(leafGeo, mat)
    const x = (Math.random() - 0.5) * 3
    const y = 3 + Math.random() * 2.5
    const z = 0.5 + Math.random() * 1.5
    m.position.set(x, y, z)
    scene3d.add(m)
    leaves.push({
      mesh: m, x, y, z,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -(0.35 + Math.random() * 0.3),
      rotSpeed: (Math.random() - 0.5) * 3,
      phase: Math.random() * Math.PI * 2,
    })
  }
}

// ── 可收集太阳精灵（每个 pendingSunlight 一个 3D 精灵）──
const ORB_TARGET = new THREE.Vector3(0, 4.5, 0.5)   // 树冠中心

function syncOrbs() {
  if (!scene3d) return
  const pending = userStore.pendingSunlight

  // 移除已不在 pending 中的精灵（飞行中的让它飞完）
  for (let i = sunOrbs.length - 1; i >= 0; i--) {
    const orb = sunOrbs[i]
    if (!orb.flying && !pending.some(p => p.id === orb.pendingId)) {
      disposeOrb(orb)
      sunOrbs.splice(i, 1)
    }
  }

  // 为新增 pending 项创建精灵
  for (const p of pending) {
    if (sunOrbs.some(o => o.pendingId === p.id)) continue
    if (sunOrbs.length >= 20) break
    const orb = createOrb(p.id, p.amount, sunOrbs.length)
    sunOrbs.push(orb)
    scene3d.add(orb.group)
  }
}

function createOrb(pendingId: number, amount: number, index: number): SunOrbObj {
  // 树前方空中网格布局（5 列 × 多行）
  const col = index % 5
  const row = Math.floor(index / 5)
  const baseX = -6 + col * 2.8 + (row % 2) * 1.2
  const baseY = 7.4 - row * 1.5

  const group = new THREE.Group()

  // 金色小球 + 描边
  const bodyMat = toonMat(0xffd54f)
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.38, 16, 12), bodyMat)
  const outlineMat = new THREE.MeshBasicMaterial({
    color: OUTLINE_COLOR_HEX, side: THREE.BackSide, transparent: true, opacity: 1,
  })
  const outline = new THREE.Mesh(body.geometry, outlineMat)
  outline.scale.setScalar(1.1)
  body.add(outline)
  group.add(body)

  // 柔和光晕 Sprite
  const haloMat = new THREE.SpriteMaterial({
    map: makeHaloTexture(), transparent: true, depthWrite: false, opacity: 0.9,
  })
  const halo = new THREE.Sprite(haloMat)
  halo.scale.setScalar(1.9)
  group.add(halo)

  // "+10" 文字 Sprite
  const labelMat = new THREE.SpriteMaterial({
    map: makeLabelTexture(`+${amount}`), transparent: true, depthWrite: false,
  })
  const label = new THREE.Sprite(labelMat)
  label.scale.set(1.3, 0.65, 1)
  label.position.y = -0.75
  group.add(label)

  // 环绕旋转的橙色光圈
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.035, 8, 28), toonMat(0xffb300))
  group.add(ring)
  group.userData.ring = ring

  group.position.set(baseX, baseY, 1.2)
  group.scale.setScalar(0.9)
  group.userData.pendingId = pendingId

  return {
    group, bodyMat, outlineMat, haloMat, labelMat,
    pendingId, amount, baseX, baseY,
    phase: Math.random() * Math.PI * 2,
    flying: false, flyT: 0,
    start: new THREE.Vector3(baseX, baseY, 1.2),
  }
}
const OUTLINE_COLOR_HEX = 0x3a3335

function makeHaloTexture() {
  const cv = document.createElement('canvas')
  cv.width = 128
  cv.height = 128
  const ctx = cv.getContext('2d')!
  const g = ctx.createRadialGradient(64, 64, 8, 64, 64, 62)
  g.addColorStop(0, 'rgba(255,235,130,0.85)')
  g.addColorStop(0.5, 'rgba(255,213,79,0.35)')
  g.addColorStop(1, 'rgba(255,213,79,0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, 128, 128)
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

function makeLabelTexture(text: string) {
  const cv = document.createElement('canvas')
  cv.width = 256
  cv.height = 128
  const ctx = cv.getContext('2d')!
  ctx.font = '900 76px "Comic Sans MS", "PingFang SC", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#ffffff'
  ctx.lineWidth = 16
  ctx.strokeText(text, 128, 68)
  ctx.fillStyle = '#e65100'
  ctx.fillText(text, 128, 68)
  const tex = new THREE.CanvasTexture(cv)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

function disposeOrb(orb: SunOrbObj) {
  scene3d?.remove(orb.group)
  orb.group.traverse((o) => {
    const m = o as THREE.Mesh
    if (m.isMesh) m.geometry.dispose()
  })
  orb.bodyMat.dispose()
  orb.outlineMat.dispose()
  orb.haloMat.map?.dispose()
  orb.haloMat.dispose()
  orb.labelMat.map?.dispose()
  orb.labelMat.dispose()
}

// ── 动画循环（单个 rAF + deltaTime 驱动全部动画）──
let elapsed = 0
function animate() {
  rafId = requestAnimationFrame(animate)
  if (!renderer || !scene3d || !camera || !clock) return
  const dt = Math.min(clock.getDelta(), 0.05)
  elapsed += dt

  // 太阳光芒缓慢旋转（只有光芒转，太阳脸不动）
  if (sunRaySprite) (sunRaySprite.material as THREE.SpriteMaterial).rotation += dt * 0.4
  // 太阳整体轻微浮动
  if (sunGroup) sunGroup.position.y = 2.6 + Math.sin(elapsed * 0.8) * 0.08

  // 相机视差：跟随指针轻微平移
  camera.position.x += (pointerNdc.x * 1.6 - camera.position.x) * Math.min(1, dt * 3)
  camera.position.y += (3.4 + pointerNdc.y * 0.9 - camera.position.y) * Math.min(1, dt * 3)
  camera.lookAt(0, 3.1, 0)

  // 云朵漂移：左→右，越界回绕
  for (const c of clouds) {
    c.group.position.x += c.speed * dt
    if (c.group.position.x > 14) {
      c.group.position.x = -14
      c.group.position.y = 5.8 + Math.random() * 2.2
    }
  }

  // 太阳精灵：浮动 + 收集飞行
  for (let i = sunOrbs.length - 1; i >= 0; i--) {
    const orb = sunOrbs[i]
    if (orb.flying) {
      orb.flyT += dt
      const t = Math.min(orb.flyT / 1.2, 1)
      const ease = 1 - Math.pow(1 - t, 3)
      orb.group.position.lerpVectors(orb.start, ORB_TARGET, ease)
      orb.group.position.y += Math.sin(t * Math.PI) * 1.2
      orb.group.scale.setScalar(0.9 * (1 - t))
      orb.bodyMat.opacity = 1 - t
      orb.outlineMat.opacity = 1 - t
      orb.haloMat.opacity = 0.9 * (1 - t)
      orb.labelMat.opacity = 1 - t
      const flyRing = orb.group.userData.ring as THREE.Mesh | undefined
      if (flyRing) {
        const rm = flyRing.material as THREE.MeshToonMaterial
        rm.transparent = true
        rm.opacity = 1 - t
      }
      if (t >= 1) {
        disposeOrb(orb)
        sunOrbs.splice(i, 1)
        glowFlashT = 0.45   // 树冠光晕闪一下
      }
    } else {
      orb.group.position.y = orb.baseY + Math.sin(elapsed * 2.4 + orb.phase) * 0.28
      orb.group.position.x = orb.baseX + Math.sin(elapsed * 1.3 + orb.phase * 0.5) * 0.12
      // 环绕光圈旋转
      const ring = orb.group.userData.ring as THREE.Mesh | undefined
      if (ring) {
        ring.rotation.z += dt * 1.2
        ring.rotation.x = Math.sin(elapsed * 1.5 + orb.phase) * 0.4
      }
    }
  }

  // 蝴蝶：8 字轨迹 + 快速扇翅 + 身体起伏
  for (const b of butterflies) {
    b.phase += b.speed * dt
    const px = b.centerX + Math.sin(b.phase) * b.radiusX
    const py = b.centerY + Math.sin(b.phase * 2) * b.radiusY + Math.sin(elapsed * 3 + b.flapPhase) * 0.12
    // Z 轴前后穿梭：部分轨迹绕到树后方（被树遮挡），同时产生近大远小
    const pz = b.centerZ + Math.sin(b.phase + b.zPhase) * b.zAmp
    const dir = Math.cos(b.phase) >= 0 ? 1 : -1
    b.group.position.set(px, py, pz)
    // 翻转朝向时保留基础尺寸（避免覆盖 scale 导致蝴蝶变大）
    b.group.scale.set(dir * b.size, b.size, b.size)
    b.group.rotation.z = Math.cos(b.phase) * 0.25 * dir
    b.flapPhase += dt * 7
    const flap = Math.sin(b.flapPhase) * 0.85
    b.flapL.rotation.y = flap
    b.flapR.rotation.y = -flap
  }

  // 落叶：飘落 + 摆动 + 自转，落地重生
  for (const leaf of leaves) {
    leaf.y += leaf.vy * dt
    leaf.x += (leaf.vx + Math.sin(elapsed * 2 + leaf.phase) * 0.35) * dt
    leaf.mesh.position.set(leaf.x, leaf.y, leaf.z)
    leaf.mesh.rotation.x += leaf.rotSpeed * dt
    leaf.mesh.rotation.z += leaf.rotSpeed * 0.7 * dt
    if (leaf.y < 0.12) {
      leaf.x = (Math.random() - 0.5) * 3
      leaf.y = 3.2 + Math.random() * 2.4
      leaf.z = 0.5 + Math.random() * 1.5
      leaf.vx = (Math.random() - 0.5) * 0.3
    }
  }

  // 小花微风摇摆
  for (const f of flowers) {
    f.group.rotation.z = Math.sin(elapsed * f.speed + f.phase) * 0.14
  }

  // 树干：持续微摇（0.5°），点击时剧烈摇晃（3°、0.5s 衰减）
  if (treeGroup) {
    if (shakeT >= 0) {
      shakeT = Math.min(shakeT + dt, 0.5)
      const decay = 1 - shakeT / 0.5
      treeGroup.rotation.z = Math.sin(shakeT * 38) * 0.052 * decay
      if (shakeT >= 0.5) {
        shakeT = -1
        treeGroup.rotation.z = 0
      }
    } else {
      treeGroup.rotation.z = Math.sin(elapsed * 0.9) * 0.0087
    }
  }

  // 树冠金色光晕：可种苹果时呼吸脉冲；收集到达时闪烁
  if (canopyGlow && canopyGlowMat) {
    const can = userStore.canGrowApple
    if (glowFlashT >= 0) glowFlashT -= dt
    canopyGlow.visible = can || glowFlashT >= 0
    if (canopyGlow.visible) {
      const pulse = 0.16 + Math.sin(elapsed * 2.6) * 0.08
      const flash = glowFlashT >= 0 ? (glowFlashT / 0.45) * 0.4 : 0
      canopyGlowMat.opacity = pulse + flash
      canopyGlow.scale.setScalar(1 + Math.sin(elapsed * 2.6) * 0.04)
    }
  }

  // 苹果：上下浮动 + 新种出弹入动画
  for (const apple of treeApples) {
    if (apple.popT < 1) {
      apple.popT = Math.min(apple.popT + dt / 0.4, 1)
      const p = apple.popT
      const s = p < 0.7 ? (p / 0.7) * 1.2 : 1.2 - ((p - 0.7) / 0.3) * 0.2
      apple.group.scale.setScalar(s)
    }
    apple.group.position.y = apple.baseY + Math.sin(elapsed * 2 + apple.phase) * 0.08
  }

  renderer.render(scene3d, camera)
}

function triggerShake() {
  shakeT = 0
}

// ── 指针交互：Raycaster 拾取太阳精灵 / 树干 ──
function onPointerDown(e: PointerEvent) {
  downPos.x = e.clientX
  downPos.y = e.clientY
}

function onPointerUp(e: PointerEvent) {
  if (!renderer || !scene3d || !camera || !sceneRef.value) return
  // 位移过大视为拖拽/滑动，不触发点击
  if (Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y) > 10) return
  const rect = sceneRef.value.getBoundingClientRect()
  const ndc = new THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1,
  )
  raycaster.setFromCamera(ndc, camera)

  // 1. 太阳精灵
  const orbMeshes: THREE.Object3D[] = []
  for (const orb of sunOrbs) {
    if (!orb.flying) orbMeshes.push(orb.group)
  }
  if (orbMeshes.length) {
    const hits = raycaster.intersectObjects(orbMeshes, true)
    if (hits.length) {
      let node: THREE.Object3D | null = hits[0].object
      while (node && node.userData.pendingId === undefined) node = node.parent
      const orb = sunOrbs.find(o => o.group === node)
      if (orb && !orb.flying) {
        orb.flying = true
        orb.flyT = 0
        orb.start.copy(orb.group.position)
        // 调用 store 收集阳光（乐观更新）
        userStore.collectSunlight(orb.pendingId)
        collectMessage.value = `☀️ 收集了 ${orb.amount} 阳光！`
        setTimeout(() => { collectMessage.value = '' }, 2500)
        return
      }
    }
  }

  // 2. 树干/树冠 → 种苹果
  if (treeGroup) {
    const treeHits = raycaster.intersectObject(treeGroup, true)
    if (treeHits.length) clickTree()
  }
}

function onPointerMove(e: PointerEvent) {
  if (!sceneRef.value) return
  const rect = sceneRef.value.getBoundingClientRect()
  pointerNdc.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  pointerNdc.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
}

// ── Scene init ──
function initScene() {
  const el = sceneRef.value
  if (!el) return
  const w = el.clientWidth || 800
  const h = el.clientHeight || SCENE_HEIGHT
  sceneWidth = w

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(w, h)
  el.appendChild(renderer.domElement)

  scene3d = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100)
  camera.position.set(0, 3.4, 13)
  camera.lookAt(0, 3.1, 0)
  scene3d.add(camera)   // 太阳 Sprite 挂在相机上，需要相机在场景图中

  // 光照：半球光 + 平行光（卡通风不开阴影，保低端机性能）
  scene3d.add(new THREE.HemisphereLight(0xbfe6ff, 0x8dc98f, 1.1))
  const dir = new THREE.DirectionalLight(0xfff3d6, 1.6)
  dir.position.set(6, 9, 7)   // 主光来自右上，与太阳位置一致
  scene3d.add(dir)
  scene3d.add(new THREE.AmbientLight(0xffffff, 0.35))

  sunGroup = new THREE.Group()
  sunGroup.position.set(4.4, 2.6, -10)   // 相机坐标系：右上角
  sunRaySprite = createSunRaysSprite()
  sunSprite = createSunDiscSprite()
  sunGroup.add(sunRaySprite, sunSprite)
  sunGroup.renderOrder = 5
  camera.add(sunGroup)

  buildClouds()
  buildGround()
  buildTree()
  buildApples()
  buildButterflies()
  buildLeaves()
  syncOrbs()

  el.addEventListener('pointermove', onPointerMove)
  el.addEventListener('pointerdown', onPointerDown)
  el.addEventListener('pointerup', onPointerUp)

  // Resize handler
  resizeObserver = new ResizeObserver(() => {
    if (!renderer || !camera || !sceneRef.value) return
    const newW = sceneRef.value.clientWidth
    const newH = sceneRef.value.clientHeight || SCENE_HEIGHT
    if (newW > 0 && (Math.abs(newW - sceneWidth) > 1 || Math.abs(newH - h) > 1)) {
      sceneWidth = newW
      camera.aspect = newW / newH
      camera.updateProjectionMatrix()
      renderer.setSize(newW, newH)
    }
  })
  resizeObserver.observe(el)

  clock = new THREE.Clock()
  animate()
}

// ── 销毁：释放 geometry / material / texture，避免 WebGL 上下文泄漏 ──
function disposeScene() {
  if (scene3d) {
    scene3d.traverse((obj) => {
      const mesh = obj as THREE.Mesh
      if (mesh.isMesh || (obj as THREE.Sprite).isSprite) {
        mesh.geometry?.dispose()
        const mat = (mesh as any).material
        if (Array.isArray(mat)) {
          for (const m of mat) { m.map?.dispose(); m.dispose() }
        } else if (mat) {
          mat.map?.dispose()
          mat.dispose()
        }
      }
    })
  }
  toonGradientMap?.dispose()
  toonGradientMap = null
  renderer?.dispose()
  if (renderer && renderer.domElement.parentElement === sceneRef.value) {
    sceneRef.value.removeChild(renderer.domElement)
  }
  renderer = null
  scene3d = null
  camera = null
  clock = null
  sunSprite = null
  sunRaySprite = null
  sunGroup = null
  treeGroup = null
  canopyGlow = null
  canopyGlowMat = null
  clouds = []
  sunOrbs = []
  butterflies = []
  leaves = []
  flowers = []
  treeApples = []
}

// ── Watch store changes ──
watch(() => userStore.pendingSunlight, () => syncOrbs(), { deep: true })
watch(() => userStore.apples, () => buildApples())

// ── Lifecycle ──
onMounted(() => {
  // 进入页面时重新拉取最新阳光/苹果余额，避免显示陈旧数据
  // 不 await：场景先用缓存值立即渲染，数据返回后由下方 watcher 实时刷新
  userStore.fetchFromApi()
  loadRedemptionRequests()
  initScene()
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  resizeObserver = null
  const el = sceneRef.value
  if (el) {
    el.removeEventListener('pointermove', onPointerMove)
    el.removeEventListener('pointerdown', onPointerDown)
    el.removeEventListener('pointerup', onPointerUp)
  }
  disposeScene()
})
</script>

<template>
  <div class="page sunshine-tree-page">
    <!-- Scene: PixiJS Canvas -->
    <div ref="sceneRef" class="scene">
      <!-- Pending sunlight count label overlay -->
      <div v-if="userStore.pendingSunlight.length > 0" class="orb-count-label">
        {{ userStore.pendingSunlight.length }} 个待收集 ☀️
      </div>

      <!-- Collect message toast -->
      <Transition name="toast">
        <div v-if="collectMessage" class="grow-toast toast-success">
          <Typewriter :text="collectMessage" :speed="50" :auto-play="true" />
        </div>
      </Transition>

      <!-- Grow message toast (with Typewriter animation) -->
      <Transition name="toast">
        <div v-if="growMessage" class="grow-toast" :class="{ 'toast-success': showGrowAnim }">
          <Typewriter :text="growMessage" :speed="50" :auto-play="true" />
        </div>
      </Transition>
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-card sunlight-stat">
        <span class="stat-icon">☀️</span>
        <div class="stat-body">
          <strong>{{ userStore.sunlightPoints }}</strong>
          <span>阳光值</span>
          <div class="mini-progress">
            <div class="mini-progress-bar" :style="{ width: sunlightProgress + '%' }"></div>
          </div>
          <span class="stat-hint">再攒 {{ userStore.sunlightPerApple - (userStore.sunlightPoints % userStore.sunlightPerApple) }} 点可种苹果</span>
        </div>
      </div>

      <div class="stat-card apple-stat">
        <span class="stat-icon">🍎</span>
        <div class="stat-body">
          <strong>{{ userStore.apples }}</strong>
          <span>苹果数</span>
          <span class="stat-hint">= {{ userStore.appleYuanValue }} 元</span>
        </div>
      </div>

      <div class="stat-card action-stat">
        <button
          class="btn grow-btn"
          :class="{ ready: userStore.canGrowApple }"
          :disabled="!userStore.canGrowApple"
          @click="clickTree"
        >
          {{ userStore.canGrowApple ? '🍎 种出苹果' : `☀️ 还差 ${userStore.sunlightPerApple - userStore.sunlightPoints}` }}
        </button>
        <button
          v-if="userStore.apples > 0"
          class="btn ghost redeem-btn"
          @click="openRedeemModal"
        >
          💰 兑换奖励
        </button>
      </div>
    </div>

    <!-- History Section -->
    <div class="lists-grid">
      <!-- Apple Grow History -->
      <section class="panel">
        <div class="card-title">
          <h2>🍎 苹果记录</h2>
          <span class="tag">{{ earnHistory.length }} 次</span>
        </div>
        <div v-if="earnHistory.length" class="history-list">
          <div v-for="record in earnHistory.slice(0, 20)" :key="record.id" class="history-row-mini">
            <span class="row-icon">🍎</span>
            <span class="row-text">+{{ record.amount }} 苹果</span>
            <span class="row-date">{{ new Date(record.timestamp).toLocaleDateString('zh-CN') }}</span>
          </div>
        </div>
        <p v-else class="muted empty-mini">还没有种出苹果，去收集阳光吧！</p>
      </section>

      <!-- Redeem History -->
      <section class="panel">
        <div class="card-title">
          <h2>💰 兑换记录</h2>
          <span class="tag">{{ redeemHistory.length }} 次</span>
        </div>
        <div v-if="redeemHistory.length" class="history-list">
          <div v-for="record in redeemHistory.slice(0, 20)" :key="record.id" class="history-row-mini">
            <span class="row-icon">💰</span>
            <span class="row-text">{{ record.reason }}</span>
            <span class="row-date">{{ new Date(record.timestamp).toLocaleDateString('zh-CN') }}</span>
          </div>
        </div>
        <p v-else class="muted empty-mini">还没有兑换过，攒够苹果找爸爸妈妈换东西吧！</p>
      </section>
    </div>

    <!-- 兑换申请状态 -->
    <section v-if="redemptionRequests.length" class="panel redemption-panel">
      <h3>📨 我的兑换申请</h3>
      <div class="redemption-list">
        <div v-for="r in redemptionRequests.slice(0, 5)" :key="r.id" class="redemption-row" :class="r.status">
          <div style="flex:1;min-width:0">
            <strong>🍎 {{ r.count }} 个苹果（= {{ r.count }} 元）</strong>
            <p class="muted" style="font-size:12px;margin:2px 0 0">{{ r.reason }}</p>
          </div>
          <span class="redemption-status" :class="r.status">{{ statusLabel(r.status) }}</span>
        </div>
      </div>
    </section>

    <!-- Tips -->
    <section class="panel tips-panel">
      <h3>💡 玩法说明</h3>
      <div class="tips-grid">
        <div class="tip-item">
          <span class="tip-icon">☀️</span>
          <p>家长审批打卡后，阳光树上会出现待收集的太阳</p>
        </div>
        <div class="tip-item">
          <span class="tip-icon">✨</span>
          <p>点击天空中的太阳收集阳光，阳光值正式加入你的账户</p>
        </div>
        <div class="tip-item">
          <span class="tip-icon">🌳</span>
          <p>攒满 100 阳光，点击苹果树种出 1 个苹果</p>
        </div>
        <div class="tip-item">
          <span class="tip-icon">💰</span>
          <p>1 个苹果 = 1 元钱，提交兑换申请，爸爸妈妈审批通过后即可兑换</p>
        </div>
      </div>
    </section>

    <!-- Redeem Modal (using animal-island-vue Modal) -->
    <Modal
      :open="showRedeemModal"
      title="💰 苹果兑换"
      :width="440"
      :mask-closable="true"
      :show-footer="false"
      @update:open="showRedeemModal = $event"
    >
      <div v-if="redeemSuccess" class="success-banner">
        ✅ {{ redeemSuccess }}
      </div>

      <template v-else>
        <div class="modal-balance">
          <span style="font-size:40px">🍎</span>
          <strong style="font-size:28px">{{ userStore.apples }}</strong>
          <span class="muted">个苹果 = {{ userStore.apples }} 元</span>
        </div>

        <div v-if="pendingRedemption" class="pending-request-tip">
          🕐 已有申请：{{ pendingRedemption.count }} 个苹果（{{ pendingRedemption.reason }}）等待家长审批
        </div>

        <div class="modal-field">
          <label>兑换数量</label>
          <div class="count-stepper">
            <button class="step-btn" @click="redeemCount = Math.max(1, redeemCount - 1)">−</button>
            <input v-model.number="redeemCount" type="number" min="1" :max="userStore.apples" class="count-input" />
            <button class="step-btn" @click="redeemCount = Math.min(userStore.apples, redeemCount + 1)">+</button>
          </div>
        </div>

        <div class="modal-field">
          <label>兑换内容（可选）</label>
          <input v-model="redeemReason" class="input" placeholder="例如：买一本漫画书" />
        </div>

        <div class="modal-summary">
          将申请用 <strong>{{ redeemCount }}</strong> 个苹果（= <strong>{{ redeemCount }}</strong> 元），爸爸妈妈审批通过后扣除
        </div>

        <p v-if="redeemError" class="redeem-error">{{ redeemError }}</p>

        <button
          class="btn"
          style="width:100%"
          :disabled="redeemCount <= 0 || redeemCount > userStore.apples || redeemSubmitting"
          @click="confirmRedeem"
        >
          {{ redeemSubmitting ? '⏳ 提交中...' : '📨 提交兑换申请' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.sunshine-tree-page {
  width: 100%;
}

/* ── Scene ── */
.scene {
  position: relative;
  width: 100%;
  height: 420px;
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 8px 28px rgba(0,0,0,0.08);
  border: 1px solid var(--line);
  user-select: none;
  /* 天空：CSS 渐变背景（3D renderer 透明叠加在上方）+ 中心提亮四周暗角的漫画 vignette */
  background:
    radial-gradient(120% 100% at 50% 42%, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 45%, rgba(40,70,110,0.12) 100%),
    linear-gradient(180deg, #5dade2 0%, #8ecdec 46%, #cde9f8 70%, #e6f6fd 100%);
}
.scene canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

/* ── Orb count label ── */
.orb-count-label {
  position: absolute;
  top: 10px;
  left: 16px;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(255,255,255,0.85);
  font-size: 14px;
  font-weight: 800;
  color: #e65100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  z-index: 6;
}

/* ── Grow toast ── */
.grow-toast {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255,255,255,0.95);
  padding: 12px 24px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 800;
  color: var(--ink);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  z-index: 20;
  white-space: nowrap;
}
.grow-toast.toast-success {
  background: #e8f5e9;
  color: var(--primary);
  border: 2px solid var(--primary);
}
.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* ── 兑换申请 ── */
.pending-request-tip {
  padding: 10px 14px;
  border-radius: 12px;
  background: #fff8e1;
  border: 1px solid #ffe082;
  color: #b28704;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
}
.redeem-error {
  color: #c62828;
  font-size: 13px;
  font-weight: 700;
  margin: 4px 0 0;
}
.redemption-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}
.redemption-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--line);
}
.redemption-row.rejected {
  opacity: .7;
}
.redemption-status {
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}
.redemption-status.pending { color: #b28704; }
.redemption-status.approved { color: #2e7d32; }
.redemption-status.rejected { color: #c62828; }

/* ── Modal inner styles (animal-island-vue Modal) ── */
.modal-balance {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  border-radius: 16px;
  background: #fff8e1;
  border: 1px solid #ffe082;
  margin-bottom: 16px;
}
.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.modal-field label {
  font-weight: 800;
  font-size: 14px;
}
.count-stepper {
  display: flex;
  align-items: center;
  gap: 8px;
}
.step-btn {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #fff;
  font-size: 22px;
  font-weight: 800;
  color: var(--primary);
  cursor: pointer;
}
.step-btn:hover { background: #f6fddc; }
.count-input {
  flex: 1;
  text-align: center;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  font-size: 18px;
  font-weight: 800;
}
.modal-summary {
  text-align: center;
  font-size: 15px;
  font-weight: 700;
  color: var(--muted);
  padding: 8px;
  margin-bottom: 12px;
}
.success-banner {
  text-align: center;
  padding: 24px;
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  background: #e8f5e9;
  border-radius: 16px;
}

/* ── Stats Bar ── */
.stats-bar {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-top: 20px;
}
.stat-card {
  background: rgba(255,255,255,0.78);
  border: 1px solid rgba(222,219,204,0.9);
  border-radius: 24px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  font-size: 40px;
  flex-shrink: 0;
}
.stat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.stat-body strong {
  font-size: 28px;
  font-weight: 900;
  line-height: 1.1;
  color: var(--ink);
}
.stat-body > span:nth-child(2) {
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
}
.stat-hint {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--muted) !important;
}
.mini-progress {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e8e4d4;
  overflow: hidden;
  margin-top: 4px;
}
.mini-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #ffd54f, #ff9800);
  transition: width 0.4s ease;
}

.action-stat {
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}
.grow-btn {
  width: 100%;
  padding: 12px 16px;
  font-size: 15px;
}
.grow-btn.ready {
  animation: btn-ready 1.5s ease-in-out infinite;
}
@keyframes btn-ready {
  0%, 100% { box-shadow: 0 8px 0 #0a5300; }
  50% { box-shadow: 0 8px 16px rgba(16,110,0,0.3); }
}
.redeem-btn {
  width: 100%;
  padding: 8px 16px;
  font-size: 14px;
}

/* ── History Lists ── */
.lists-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.history-row-mini {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
}
.row-icon {
  font-size: 20px;
  flex-shrink: 0;
}
.row-text {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-date {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
  flex-shrink: 0;
}
.empty-mini {
  text-align: center;
  padding: 24px;
  font-size: 14px;
}

/* ── Tips ── */
.tips-panel h3 {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 14px;
}
.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}
.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px;
  border-radius: 16px;
  background: var(--surface);
  border: 1px solid var(--line);
}
.tip-icon {
  font-size: 24px;
  flex-shrink: 0;
}
.tip-item p {
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
  line-height: 1.5;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .stats-bar {
    grid-template-columns: 1fr;
  }
  .lists-grid {
    grid-template-columns: 1fr;
  }
  .scene {
    height: 340px;
  }
}
</style>
