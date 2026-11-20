/**
 * 「记住账号」本地存储（含密码，用于自动登录）
 *
 * ⚠️ 安全说明：
 * - 这是家庭私有 Pad 上的局域网应用，为了让设备重启/页面刷新后免输密码，
 *   这里把账号和密码一起存到本地。密码用「设备随机盐 + 多轮变换」混淆，
 *   能防住直接翻 localStorage 看到明文，但**不是真正加密**——拿到设备的
 *   人若能读前端代码，理论上仍可还原。请勿在公共/共享设备上勾选「记住密码」。
 * - HTTP 环境下 Web Crypto 的 crypto.subtle 不可用（非安全上下文），
 *   所以这里用纯 JS 实现，不依赖 SubtleCrypto。
 *
 * 有效期 30 天，过期自动清除。用户取消勾选时立即清除。
 */

const STORAGE_KEY = 'cc-saved-credentials'
const SALT_KEY = 'cc-cred-salt'
const VALID_DAYS = 30

interface StoredAccount {
  username: string
  password: string
  savedAt: number
}

/** 设备唯一盐值：首次使用时随机生成并持久化，换设备/清数据后作废 */
function getSalt(): string {
  let salt = localStorage.getItem(SALT_KEY)
  if (!salt) {
    const arr = new Uint8Array(16)
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      crypto.getRandomValues(arr)
    } else {
      for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256)
    }
    salt = Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('')
    localStorage.setItem(SALT_KEY, salt)
  }
  return salt
}

/** 基于盐值的流式密钥：多轮混合，避免固定 key 的直接 XOR */
function deriveKey(salt: string): number[] {
  let h = 2166136261 // FNV offset basis
  const input = salt + '::studentstudy::cred-v2'
  for (let round = 0; round < 4; round++) {
    for (let i = 0; i < input.length; i++) {
      h ^= input.charCodeAt(i)
      h = Math.imul(h, 16777619) >>> 0
    }
  }
  const out: number[] = []
  let x = h || 1
  for (let i = 0; i < 32; i++) {
    x ^= x << 13; x >>>= 0
    x ^= x >> 17
    x ^= x << 5; x >>>= 0
    out.push(x & 0xff)
  }
  return out
}

/** 明文 -> 混淆串（base64 of bytes） */
function encode(text: string): string {
  const key = deriveKey(getSalt())
  const bytes = new TextEncoder().encode(text)
  const out = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) out[i] = bytes[i] ^ key[i % key.length]
  let bin = ''
  out.forEach((b) => { bin += String.fromCharCode(b) })
  return btoa(bin)
}

/** 混淆串 -> 明文 */
function decode(text: string): string {
  const key = deriveKey(getSalt())
  const bin = atob(text)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i) ^ key[i % key.length]
  return new TextDecoder().decode(out)
}

/** 记住账号和密码（登录成功后调用） */
export function saveCredentials(username: string, password: string) {
  const data: StoredAccount = { username, password, savedAt: Date.now() }
  try {
    localStorage.setItem(STORAGE_KEY, encode(JSON.stringify(data)))
  } catch { /* 隐私模式等写入失败时静默忽略 */ }
}

/** 读取已记住的账号：未过期返回账号和密码；已过期自动删除并返回 null */
export function loadCredentials(): { username: string; password: string } | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const data = JSON.parse(decode(raw)) as Record<string, unknown>
    const username = typeof data?.username === 'string' ? data.username : ''
    const password = typeof data?.password === 'string' ? data.password : ''
    if (!username || !password) {
      clearCredentials()
      return null
    }
    const savedAt = typeof data.savedAt === 'number' ? data.savedAt : 0
    if (!savedAt || Date.now() - savedAt > VALID_DAYS * 24 * 60 * 60 * 1000) {
      clearCredentials()
      return null
    }
    return { username, password }
  } catch {
    clearCredentials()
    return null
  }
}

/** 是否曾经勾选过「记住密码」（用于登录页复选框回显） */
export function hasSavedCredentials(): boolean {
  return !!localStorage.getItem(STORAGE_KEY)
}

/** 删除已存账号（用户取消勾选时立即调用） */
export function clearCredentials() {
  localStorage.removeItem(STORAGE_KEY)
}
