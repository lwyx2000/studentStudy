/**
 * 「保存账号密码」本地凭据管理
 * - 加密后存入 localStorage，5 天后过期
 * - 未过期：登录页自动回填账号密码；过期：自动删除存储的凭据
 * - 说明：采用 XOR + Base64 的设备级混淆（APK WebView 运行在 http 非安全上下文，
 *   无法使用 WebCrypto；本机为家庭私有 Pad，属体验性保护而非强安全加密）
 */

const STORAGE_KEY = 'cc-saved-credentials'
const VALID_DAYS = 5
const CIPHER_KEY = 'cc-island-pad-2026'

interface StoredCredentials {
  username: string
  password: string
  savedAt: number // 时间戳，用于 5 天过期判断
}

function xorTransform(text: string): string {
  const bytes = new TextEncoder().encode(text)
  const keyBytes = new TextEncoder().encode(CIPHER_KEY)
  const out = new Uint8Array(bytes.length)
  for (let i = 0; i < bytes.length; i++) out[i] = bytes[i] ^ keyBytes[i % keyBytes.length]
  let bin = ''
  out.forEach((b) => { bin += String.fromCharCode(b) })
  return bin
}

function encode(text: string): string {
  // 中文等多字节字符先转义，保证 btoa 不抛异常
  return btoa(unescape(encodeURIComponent(xorTransform(text))))
}

/** XOR 对称，加密解密走同一变换 */
function decrypt(text: string): string {
  return decodeURIComponent(escape(xorTransform(text)))
}

/** 保存凭据（用户勾选「保存账号密码」且登录成功后调用） */
export function saveCredentials(username: string, password: string) {
  const data: StoredCredentials = { username, password, savedAt: Date.now() }
  try {
    localStorage.setItem(STORAGE_KEY, encode(JSON.stringify(data)))
  } catch { /* 隐私模式等写入失败时静默忽略 */ }
}

/** 读取凭据：未过期返回明文；已过期自动删除并返回 null */
export function loadCredentials(): { username: string; password: string } | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const data = JSON.parse(decrypt(atob(raw))) as StoredCredentials
    if (!data || typeof data.username !== 'string' || typeof data.password !== 'string') {
      clearCredentials()
      return null
    }
    if (Date.now() - data.savedAt > VALID_DAYS * 24 * 60 * 60 * 1000) {
      // 超过 5 天：删除存储的账号密码，不再自动回填
      clearCredentials()
      return null
    }
    return { username: data.username, password: data.password }
  } catch {
    clearCredentials()
    return null
  }
}

/** 是否曾经勾选过「保存账号密码」（用于登录页复选框回显） */
export function hasSavedCredentials(): boolean {
  return !!localStorage.getItem(STORAGE_KEY)
}

/** 删除已存凭据（用户取消勾选时立即调用） */
export function clearCredentials() {
  localStorage.removeItem(STORAGE_KEY)
}
