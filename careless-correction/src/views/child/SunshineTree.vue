<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import {
  Application,
  Container,
  Graphics,
  Sprite,
  Text,
  Texture,
  Assets,
  type Ticker,
} from 'pixi.js'
import { useUserStore } from '../../stores'
import { Typewriter, Modal } from 'animal-island-vue'

// ── Image assets ──
import sunImgUrl from '../../assets/img/3.png'
import cloudImgUrl from '../../assets/img/2.png'
import cloudStripImgUrl from '../../assets/img/10.png'
import treeImgUrl from '../../assets/img/9.png'
import groundImgUrl from '../../assets/img/13.png'
import appleImgUrl from '../../assets/img/1.png'
import appleRedImgUrl from '../../assets/img/7.png'
import appleGoldImgUrl from '../../assets/img/7 (2).png'
import butterflyBlueImgUrl from '../../assets/img/8.png'
import butterflyBlue2ImgUrl from '../../assets/img/8 (2).png'
import flowerImgUrl from '../../assets/img/6.png'
import saplingImgUrl from '../../assets/img/4.png'

const userStore = useUserStore()

// ── DOM ref for PixiJS canvas mount ──
const sceneRef = ref<HTMLDivElement>()
let app: Application | null = null

// ── Scene constants ──
const SCENE_HEIGHT = 420
const MAX_ORBS = 20

// ── Loaded textures ──
let textures: Record<string, Texture> = {}

// ── Scene object collections ──
interface SunOrbObj {
  sprite: Sprite
  label: Text | null
  pendingId: number
  amount: number
  baseX: number
  baseY: number
  phase: number
  flying: boolean
  flyT: number
  flyStartX: number
  flyStartY: number
  flyTargetX: number
  flyTargetY: number
}

interface BirdObj {
  container: Container
  frameA: Sprite   // 8.png  - wings up
  frameB: Sprite   // 8(2).png - wings down
  phase: number
  speed: number
  centerX: number
  centerY: number
  radiusX: number
  radiusY: number
  flapPhase: number
}

interface LeafObj {
  sprite: Sprite
  x: number
  y: number
  vx: number
  vy: number
  rot: number
  rotSpeed: number
}

interface SparkleObj {
  g: Graphics
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
}

// ── Drifting cloud cluster (multiple 2.png sprites grouped together) ──
interface CloudClusterObj {
  container: Container
  speed: number
  startX: number
}

let clouds: CloudClusterObj[] = []

let sunOrbs: SunOrbObj[] = []
let birds: BirdObj[] = []
let leaves: LeafObj[] = []
let sparkles: SparkleObj[] = []

// Flowers for swaying animation
interface FlowerObj {
  container: Container
  phase: number
  speed: number
}
let flowers: FlowerObj[] = []

// Tree parts
let treeContainer: Container | null = null
let treeGlow: Graphics | null = null
let treeApples: Sprite[] = []
let sunRayContainer: Container | null = null
let sceneWidth = 800

// ── UI state (Vue overlays) ──
const showGrowAnim = ref(false)
const growMessage = ref('')
const shakeTree = ref(false)
const collectMessage = ref('')

function clickTree() {
  if (!userStore.canGrowApple) {
    shakeTree.value = true
    setTimeout(() => { shakeTree.value = false }, 500)
    growMessage.value = `还需要 ${userStore.sunlightPerApple - userStore.sunlightPoints} 阳光才能种出 1 个苹果`
    setTimeout(() => { growMessage.value = '' }, 2500)
    return
  }

  shakeTree.value = true
  setTimeout(() => { shakeTree.value = false }, 500)

  const ok = userStore.growApple()
  if (ok) {
    showGrowAnim.value = true
    growMessage.value = `🍎 种出了 1 个苹果！当前共有 ${userStore.apples} 个苹果`
    spawnSparkles()
    setTimeout(() => {
      showGrowAnim.value = false
      growMessage.value = ''
    }, 3000)
  }
}

// ── Apple redemption ──
const showRedeemModal = ref(false)
const redeemCount = ref(1)
const redeemReason = ref('')
const redeemSuccess = ref('')

function openRedeemModal() {
  redeemCount.value = 1
  redeemReason.value = ''
  redeemSuccess.value = ''
  showRedeemModal.value = true
}

function confirmRedeem() {
  if (redeemCount.value <= 0 || redeemCount.value > userStore.apples) return
  const ok = userStore.redeemApple(redeemCount.value, redeemReason.value || `和爸爸妈妈兑换 ${redeemCount.value} 元`)
  if (ok) {
    redeemSuccess.value = `成功兑换 ${redeemCount.value} 个苹果（= ${redeemCount.value} 元）`
    setTimeout(() => { showRedeemModal.value = false }, 1800)
  }
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
//  PixiJS Scene — Sprite-based rendering using image assets
// ══════════════════════════════════════════════════════════════

// ── Texture loading ──
async function loadTextures() {
  const [sun, cloud, cloudStrip, tree, ground, apple, appleRed, appleGold, butterflyBlue, butterflyBlue2, flower, sapling] = await Promise.all([
    Assets.load(sunImgUrl),
    Assets.load(cloudImgUrl),
    Assets.load(cloudStripImgUrl),
    Assets.load(treeImgUrl),
    Assets.load(groundImgUrl),
    Assets.load(appleImgUrl),
    Assets.load(appleRedImgUrl),
    Assets.load(appleGoldImgUrl),
    Assets.load(butterflyBlueImgUrl),
    Assets.load(butterflyBlue2ImgUrl),
    Assets.load(flowerImgUrl),
    Assets.load(saplingImgUrl),
  ])
  textures = { sun, cloud, cloudStrip, tree, ground, apple, appleRed, appleGold, butterflyBlue, butterflyBlue2, flower, sapling }
}

// ── Sky background (solid blue) ──
function drawSky(container: Container, w: number, h: number) {
  const g = new Graphics()
  g.rect(0, 0, w, h).fill('#5dade2')
  container.addChild(g)
}

// ── Sun (sprite from 3.png) ──
function drawSun(container: Container, w: number) {
  if (!textures.sun) return
  const sun = new Sprite(textures.sun)
  sun.anchor.set(0.5)
  sun.x = w - 70
  sun.y = 55
  sun.scale.set(0.45)
  container.addChild(sun)

  // Sun rays (Graphics, for rotation animation)
  sunRayContainer = new Container()
  sunRayContainer.x = w - 70
  sunRayContainer.y = 55
  container.addChild(sunRayContainer)

  const rayG = new Graphics()
  for (let i = 0; i < 8; i++) {
    const angle = (i / 8) * Math.PI * 2
    const x1 = Math.cos(angle) * 42
    const y1 = Math.sin(angle) * 42
    const x2 = Math.cos(angle) * 58
    const y2 = Math.sin(angle) * 58
    rayG.moveTo(x1, y1).lineTo(x2, y2).stroke({ width: 3, color: '#ffd54f', alpha: 0.6 })
  }
  sunRayContainer.addChild(rayG)
}

// ── Clouds: 2.png drifting clusters only ---
function drawClouds(container: Container, w: number, _h: number) {
  if (!textures.cloud) return
  const sunZoneX = w - 160
  const cloudScale = 0.25

  // Store clusters with their scale for sorting
  const clusters: { cluster: Container; maxScale: number }[] = []

  for (let c = 0; c < 5; c++) {
    const cluster = new Container()
    const numPuffs = 2 + Math.floor(Math.random() * 3)
    const baseY = 10 + Math.random() * 90

    let prevX = 0
    let maxScale = 0
    for (let p = 0; p < numPuffs; p++) {
      const s = new Sprite(textures.cloud)
      s.anchor.set(0.5)
      // Random scale: 0.5x to 4x base size
      const puffScaleX = cloudScale * (0.5 + Math.random() * 3.5)
      // Random stretch: 0.5x to 2x on Y axis
      const puffScaleY = puffScaleX * (0.5 + Math.random() * 1.5)
      s.scale.set(puffScaleX, puffScaleY)
      s.x = prevX + (Math.random() * 20 - 10)
      s.y = (Math.random() * 25 - 12)
      // Smaller clouds are more transparent
      const avgScale = (Math.abs(puffScaleX) + Math.abs(puffScaleY)) / 2
      s.alpha = 0.3 + (avgScale / (cloudScale * 4)) * 0.7
      cluster.addChild(s)
      prevX = s.x + s.width * 0.4
      maxScale = Math.max(maxScale, avgScale)
    }

    const startX = Math.random() * (sunZoneX + 100) - 100
    cluster.x = startX
    cluster.y = baseY

    clusters.push({
      cluster,
      maxScale,
    })
  }

  // Sort by max scale: larger clouds in front (higher z-index)
  clusters.sort((a, b) => a.maxScale - b.maxScale)

  for (const { cluster } of clusters) {
    container.addChild(cluster)
    clouds.push({
      container: cluster,
      speed: 0.15 + Math.random() * 0.25,
      startX: cluster.x,
    })
  }
}

// ── Grassland (ground strip 13.png only, no green fill) ──
function drawGrassland(container: Container, w: number, h: number) {
  if (!textures.ground) return
  const groundY = h * 0.55

  // Tile the ground strip image across the width — this IS the ground
  const groundTex = textures.ground
  // Keep original aspect ratio, scale based on width
  const scale = w / groundTex.width
  const scaledTileW = groundTex.width * scale
  let xOffset = 0
  while (xOffset < w + scaledTileW) {
    const gs = new Sprite(groundTex)
    gs.x = xOffset
    gs.y = groundY
    gs.scale.set(scale)
    container.addChild(gs)
    xOffset += scaledTileW
  }

  // Flowers (sprites from 6.png) - swaying in wind
  const flowerXs = [0.05, 0.14, 0.8, 0.9, 0.04, 0.93]
  for (let i = 0; i < flowerXs.length; i++) {
    const fc = new Container()
    const fs = new Sprite(textures.flower)
    fs.anchor.set(0.5, 1)
    fs.scale.set(0.32)
    fc.addChild(fs)
    fc.x = flowerXs[i] * w
    fc.y = h - 5 - (i % 2) * 15
    // Pivot at bottom center so flower sways from ground
    fc.pivot.set(0, 0)
    fs.x = 0
    fs.y = 0
    container.addChild(fc)
    // Store for animation
    flowers.push({ container: fc, phase: Math.random() * Math.PI * 2, speed: 0.03 + Math.random() * 0.02 })
  }

  // Saplings (sprites from 4.png) at edges
  for (const sx of [0.1, 0.88]) {
    const ss = new Sprite(textures.sapling)
    ss.anchor.set(0.5, 1)
    ss.x = sx * w
    ss.y = h - 5
    ss.scale.set(0.5)
    container.addChild(ss)
  }
}

// ── Apple Tree (sprite 9.png, large, base embedded in grass) ──
function drawTree(container: Container, w: number, h: number) {
  if (!textures.tree) return
  treeContainer = new Container()

  // Tree glow (when ready to grow apple)
  treeGlow = new Graphics()
  // 用双层圆近似径向渐变光晕：外层柔和、内层更亮
  treeGlow.circle(0, -180, 160).fill({ color: '#ffeb3b', alpha: 0.08 })
  treeGlow.circle(0, -180, 100).fill({ color: '#ffeb3b', alpha: 0.2 })
  treeGlow.visible = false
  treeContainer.addChild(treeGlow)

  // Tree sprite (9.png is 512×512, anchor bottom-center, enlarged)
  const tree = new Sprite(textures.tree)
  tree.anchor.set(0.5, 1)
  tree.scale.set(0.72)   // bigger tree
  treeContainer.addChild(tree)

  // Position: tree base embedded INTO grass
  treeContainer.x = w / 2
  treeContainer.y = h * 0.98   // tree very low, base deep in grass
  container.addChild(treeContainer)

  // Tree shadow on grass
  const shadow = new Graphics()
  shadow.ellipse(0, 10, 80, 20).fill({ color: 'rgba(0,0,0,0.15)' })
  shadow.y = 5
  treeContainer.addChildAt(shadow, 0)  // add behind tree

  // Enable tree click
  treeContainer.eventMode = 'static'
  treeContainer.cursor = 'pointer'
  treeContainer.on('pointerdown', () => clickTree())
}

// ── Apples on tree (sprites from 1.png, 7.png, 7(2).png) ──
function drawApplesOnTree() {
  if (!treeContainer || !textures.apple) return
  // Remove old apples
  for (const a of treeApples) {
    treeContainer.removeChild(a)
    a.destroy()
  }
  treeApples = []

  const count = Math.min(userStore.apples, 8)
  if (count === 0) return

  // Positions relative to tree container (tree sprite is 512×512, scale 0.72, anchored bottom-center)
  // Canopy area: roughly x: -120~120, y: -300~-150
  const positions = [
    { x: -60, y: -200 }, { x: 45, y: -180 }, { x: -20, y: -245 },
    { x: 65, y: -215 }, { x: -70, y: -230 }, { x: 20, y: -275 },
    { x: 0, y: -155 }, { x: -85, y: -180 },
  ]

  for (let i = 0; i < count; i++) {
    const pos = positions[i]
    // Cycle through apple variants
    const tex = i % 3 === 0 ? textures.apple : (i % 3 === 1 ? textures.appleRed : textures.appleGold)
    const s = new Sprite(tex)
    s.anchor.set(0.5)
    s.x = pos.x
    s.y = pos.y
    s.scale.set(0.35)
    treeContainer.addChild(s)
    treeApples.push(s)
  }
}

// ── Sun Orbs (待收集阳光，sprites from 3.png) ──
function updateOrbs() {
  if (!app || !textures.sun) return
  const pending = userStore.pendingSunlight

  // Remove orbs no longer in pending (skip flying ones)
  for (let i = sunOrbs.length - 1; i >= 0; i--) {
    const orb = sunOrbs[i]
    if (!orb.flying && !pending.some(p => p.id === orb.pendingId)) {
      app.stage.removeChild(orb.sprite)
      if (orb.label) app.stage.removeChild(orb.label)
      orb.sprite.destroy()
      if (orb.label) orb.label.destroy()
      sunOrbs.splice(i, 1)
    }
  }

  // Add orbs for new pending items
  for (const p of pending) {
    if (sunOrbs.some(o => o.pendingId === p.id)) continue
    if (sunOrbs.length >= MAX_ORBS) break
    const orb = createOrb(p.id, p.amount, sunOrbs.length)
    sunOrbs.push(orb)
    app.stage.addChild(orb.sprite)
    if (orb.label) app.stage.addChild(orb.label)
  }
}

function createOrb(pendingId: number, amount: number, index: number): SunOrbObj {
  const col = index % 5
  const row = Math.floor(index / 5)
  const baseX = sceneWidth * (0.06 + col * 0.16 + ((row % 2) * 0.08))
  const baseY = SCENE_HEIGHT * (0.08 + row * 0.12)

  const sprite = new Sprite(textures.sun)
  sprite.anchor.set(0.5)
  sprite.x = baseX
  sprite.y = baseY
  sprite.scale.set(0.2)
  sprite.eventMode = 'static'
  sprite.cursor = 'pointer'
  sprite.hitArea = { contains: (x: number, y: number) => Math.abs(x) < 30 && Math.abs(y) < 30 }

  // Amount label
  const label = new Text({
    text: `+${amount}`,
    style: {
      fontSize: 14,
      fill: '#e65100',
      fontWeight: 'bold',
      stroke: { color: '#ffffff', width: 3 },
    },
  })
  label.anchor.set(0.5)
  label.x = baseX
  label.y = baseY

  const orbObj: SunOrbObj = {
    sprite, label, pendingId, amount, baseX, baseY,
    phase: Math.random() * Math.PI * 2,
    flying: false, flyT: 0,
    flyStartX: 0, flyStartY: 0, flyTargetX: 0, flyTargetY: 0,
  }

  sprite.on('pointerdown', () => {
    if (orbObj.flying) return
    orbObj.flying = true
    orbObj.flyT = 0
    orbObj.flyStartX = sprite.x
    orbObj.flyStartY = sprite.y
    orbObj.flyTargetX = sceneWidth / 2
    orbObj.flyTargetY = SCENE_HEIGHT - 200
    sprite.eventMode = 'none'
    // 调用 store 收集阳光（乐观更新）
    userStore.collectSunlight(orbObj.pendingId)
    // 显示收集提示
    collectMessage.value = `☀️ 收集了 ${orbObj.amount} 阳光！`
    setTimeout(() => {
      collectMessage.value = ''
    }, 2500)
  })

  return orbObj
}

// ── Birds (8.png + 8(2).png as two-frame wing flap) ──
function spawnBirds(container: Container) {
  if (!textures.butterflyBlue || !textures.butterflyBlue2) return
  for (let i = 0; i < 3; i++) {
    const c = new Container()

    // Frame A: 8.png  (wings up)
    const frameA = new Sprite(textures.butterflyBlue)
    frameA.anchor.set(0.5)
    frameA.scale.set(0.38)
    frameA.visible = true
    c.addChild(frameA)

    // Frame B: 8(2).png (wings down)
    const frameB = new Sprite(textures.butterflyBlue2)
    frameB.anchor.set(0.5)
    frameB.scale.set(0.38)
    frameB.visible = false
    c.addChild(frameB)

    container.addChild(c)
    birds.push({
      container: c, frameA, frameB,
      phase: Math.random() * Math.PI * 2,
      speed: 0.3 + Math.random() * 0.3,
      centerX: sceneWidth * (0.1 + Math.random() * 0.8),
      centerY: SCENE_HEIGHT * (0.1 + Math.random() * 0.6),
      radiusX: 100 + Math.random() * 150,
      radiusY: 40 + Math.random() * 60,
      flapPhase: Math.random() * Math.PI * 2,
    })
  }
}

// ── Falling leaves (sprites from 6.png, small) ──
function spawnLeaves(container: Container) {
  if (!textures.flower) return
  for (let i = 0; i < 5; i++) {
    const s = new Sprite(textures.flower)
    s.anchor.set(0.5)
    s.scale.set(0.14)
    container.addChild(s)
    leaves.push({
      sprite: s,
      x: sceneWidth / 2 + (Math.random() - 0.5) * 120,
      y: SCENE_HEIGHT * 0.3 + Math.random() * 100,
      vx: (Math.random() - 0.5) * 0.5,
      vy: 0.3 + Math.random() * 0.4,
      rot: Math.random() * Math.PI * 2,
      rotSpeed: (Math.random() - 0.5) * 0.05,
    })
  }
}

// ── Sparkles (Graphics, for apple grow burst) ──
function spawnSparkles() {
  if (!app) return
  const cx = sceneWidth / 2
  const cy = SCENE_HEIGHT * 0.42   // tree canopy center
  for (let i = 0; i < 12; i++) {
    const g = new Graphics()
    const angle = (i / 12) * Math.PI * 2
    const size = 3 + Math.random() * 4
    g.circle(0, 0, size).fill({ color: '#fff176', alpha: 0.9 })
    g.circle(0, 0, size * 0.5).fill({ color: '#ffffff' })
    g.x = cx
    g.y = cy
    app.stage.addChild(g)
    sparkles.push({
      g, x: cx, y: cy,
      vx: Math.cos(angle) * (2 + Math.random() * 2),
      vy: Math.sin(angle) * (2 + Math.random() * 2) - 1,
      life: 0, maxLife: 60,
    })
  }
}

// ── Animation ticker ──
let elapsed = 0
function update(ticker: Ticker) {
  const dt = ticker.deltaTime
  elapsed += dt

  // Sun rays rotation
  if (sunRayContainer) {
    sunRayContainer.rotation += 0.002 * dt
  }

  // Clouds drift left→right, wrap around
  for (const c of clouds) {
    c.container.x += c.speed * dt
    // When cluster fully passes right edge, wrap to left
    if (c.container.x > sceneWidth + 100) {
      c.container.x = -200
      c.container.y = 10 + Math.random() * 90  // new random y
    }
  }

  // Sun orbs: float + fly animation
  for (let i = sunOrbs.length - 1; i >= 0; i--) {
    const orb = sunOrbs[i]
    if (orb.flying) {
      orb.flyT += dt / 60
      const t = Math.min(orb.flyT / 1.2, 1)
      const ease = 1 - Math.pow(1 - t, 3)
      orb.sprite.x = orb.flyStartX + (orb.flyTargetX - orb.flyStartX) * ease
      orb.sprite.y = orb.flyStartY + (orb.flyTargetY - orb.flyStartY) * ease
      orb.sprite.y -= Math.sin(t * Math.PI) * 40
      orb.sprite.scale.set(0.2 * (1 - t * 0.7))
      orb.sprite.alpha = 1 - t
      if (orb.label) {
        orb.label.x = orb.sprite.x
        orb.label.y = orb.sprite.y
        orb.label.alpha = orb.sprite.alpha
        orb.label.scale.set(1 - t * 0.5)
      }
      if (t >= 1) {
        // 飞行动画结束，销毁精灵
        app?.stage.removeChild(orb.sprite)
        if (orb.label) app?.stage.removeChild(orb.label)
        orb.sprite.destroy()
        if (orb.label) orb.label.destroy()
        sunOrbs.splice(i, 1)
      }
    } else {
      orb.sprite.y = orb.baseY + Math.sin(elapsed * 0.03 + orb.phase) * 8
      orb.sprite.x = orb.baseX + Math.sin(elapsed * 0.02 + orb.phase * 0.5) * 3
      if (orb.label) {
        orb.label.x = orb.sprite.x
        orb.label.y = orb.sprite.y
      }
    }
  }

  // Birds: fly in figure-8 + toggle two-frame wing flap
  for (const b of birds) {
    b.phase += b.speed * 0.01 * dt
    const px = b.centerX + Math.sin(b.phase) * b.radiusX
    const py = b.centerY + Math.sin(b.phase * 2) * b.radiusY
    b.container.x = px
    b.container.y = py
    // Face direction of travel
    const nextX = b.centerX + Math.sin(b.phase + 0.01) * b.radiusX
    b.container.scale.x = nextX > px ? 1 : -1
    // Wing flap: toggle frame A / B
    b.flapPhase += 0.18 * dt
    const showA = Math.sin(b.flapPhase) > 0
    b.frameA.visible = showA
    b.frameB.visible = !showA
  }

  // Falling leaves
  for (const leaf of leaves) {
    leaf.x += leaf.vx * dt + Math.sin(elapsed * 0.02 + leaf.rot) * 0.3
    leaf.y += leaf.vy * dt
    leaf.rot += leaf.rotSpeed * dt
    leaf.sprite.x = leaf.x
    leaf.sprite.y = leaf.y
    leaf.sprite.rotation = leaf.rot
    if (leaf.y > SCENE_HEIGHT * 0.68) {
      leaf.y = SCENE_HEIGHT * 0.25
      leaf.x = sceneWidth / 2 + (Math.random() - 0.5) * 120
      leaf.vx = (Math.random() - 0.5) * 0.5
    }
  }

  // Sparkles
  for (let i = sparkles.length - 1; i >= 0; i--) {
    const s = sparkles[i]
    s.life += dt
    s.x += s.vx * dt * 0.5
    s.y += s.vy * dt * 0.5
    s.vy += 0.08 * dt
    s.g.x = s.x
    s.g.y = s.y
    s.g.alpha = 1 - (s.life / s.maxLife)
    s.g.scale.set(1 - (s.life / s.maxLife) * 0.5)
    if (s.life >= s.maxLife) {
      app?.stage.removeChild(s.g)
      s.g.destroy()
      sparkles.splice(i, 1)
    }
  }

  // Flowers swaying in wind
  for (const f of flowers) {
    f.phase += f.speed * dt
    f.container.rotation = Math.sin(f.phase) * 0.1
  }

  // Tree shake / sway
  if (treeContainer) {
    if (shakeTree.value) {
      treeContainer.rotation = Math.sin(elapsed * 0.4) * 0.04
    } else {
      treeContainer.rotation = Math.sin(elapsed * 0.01) * 0.008
    }
  }

  // Tree glow
  if (treeGlow) {
    const shouldGlow = userStore.canGrowApple
    if (treeGlow.visible !== shouldGlow) treeGlow.visible = shouldGlow
    if (shouldGlow) {
      treeGlow.alpha = 0.5 + Math.sin(elapsed * 0.05) * 0.3
      treeGlow.scale.set(0.95 + Math.sin(elapsed * 0.05) * 0.1)
    }
  }

  // Apples bobbing
  for (let i = 0; i < treeApples.length; i++) {
    treeApples[i].y += Math.sin(elapsed * 0.03 + i) * 0.3
  }
}

// ── Scene init ──
async function initScene() {
  if (!sceneRef.value) return

  // Load textures first
  await loadTextures()

  app = new Application()
  await app.init({
    width: sceneRef.value.clientWidth,
    height: SCENE_HEIGHT,
    backgroundAlpha: 0,
    antialias: true,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
  })

  sceneRef.value.appendChild(app.canvas)
  sceneWidth = sceneRef.value.clientWidth

  // Draw all scene elements (tree BEFORE grass so grass covers trunk base)
  drawSky(app.stage, sceneWidth, SCENE_HEIGHT)
  drawSun(app.stage, sceneWidth)
  drawClouds(app.stage, sceneWidth, SCENE_HEIGHT)
  drawTree(app.stage, sceneWidth, SCENE_HEIGHT)
  drawGrassland(app.stage, sceneWidth, SCENE_HEIGHT)
  drawApplesOnTree()
  spawnBirds(app.stage)
  spawnLeaves(app.stage)
  updateOrbs()

  // Start animation
  app.ticker.add(update)

  // Resize handler
  const resizeObserver = new ResizeObserver(() => {
    if (!app || !sceneRef.value) return
    const newW = sceneRef.value.clientWidth
    if (newW > 0 && Math.abs(newW - sceneWidth) > 1) {
      sceneWidth = newW
      app.renderer.resize(newW, SCENE_HEIGHT)
      rebuildScene()
    }
  })
  resizeObserver.observe(sceneRef.value)
}

function rebuildScene() {
  if (!app) return
  for (let i = app.stage.children.length - 1; i >= 0; i--) {
    const child = app.stage.children[i]
    app.stage.removeChild(child)
    child.destroy()
  }
  sunOrbs = []
  // Labels are children of stage, destroyed above
  birds = []
  leaves = []
  sparkles = []
  clouds = []
  treeApples = []
  treeContainer = null
  treeGlow = null
  sunRayContainer = null
  flowers = []

  drawSky(app.stage, sceneWidth, SCENE_HEIGHT)
  drawSun(app.stage, sceneWidth)
  drawClouds(app.stage, sceneWidth, SCENE_HEIGHT)
  drawTree(app.stage, sceneWidth, SCENE_HEIGHT)
  drawGrassland(app.stage, sceneWidth, SCENE_HEIGHT)
  drawApplesOnTree()
  spawnBirds(app.stage)
  spawnLeaves(app.stage)
  updateOrbs()
}

// ── Watch store changes ──
watch(() => userStore.pendingSunlight, () => updateOrbs(), { deep: true })
watch(() => userStore.apples, () => drawApplesOnTree())

// ── Lifecycle ──
onMounted(() => {
  // 进入页面时重新拉取最新阳光/苹果余额，避免显示陈旧数据
  // 不 await：场景先用缓存值立即渲染，数据返回后由下方 watcher 实时刷新
  userStore.fetchFromApi()
  initScene()
})

onUnmounted(() => {
  if (app) {
    app.destroy(true)
    app = null
  }
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
          <p>1 个苹果 = 1 元钱，找爸爸妈妈兑换奖励</p>
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
          将使用 <strong>{{ redeemCount }}</strong> 个苹果（= <strong>{{ redeemCount }}</strong> 元）
        </div>

        <button
          class="btn"
          style="width:100%"
          :disabled="redeemCount <= 0 || redeemCount > userStore.apples"
          @click="confirmRedeem"
        >
          确认兑换
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
