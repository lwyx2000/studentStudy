/**
 * 「记住账号」本地存储
 *
 * 只保存登录名，**不再保存密码**。
 * 早期版本用 XOR + Base64 把密码存在 localStorage，本质上等同于明文
 * （密钥硬编码在前端代码里），设备被他人拿到即可直接读到密码。
 * 现在只保留账号名，密码每次登录由用户输入；浏览器/输入法的密码管理器
 * 才是保存密码的正确位置。
 *
 * 旧数据兼容：读到含 password 字段的历史记录时，只取用户名并立即重写存储，
 * 把已经落盘的密码抹掉。
 */

const STORAGE_KEY = 'cc-saved-credentials'
const VALID_DAYS = 30 // 记住账号的有效期
const CIPHER_KEY = 'cc-island-pad-2026'

interface StoredAccount {
  username: string
  savedAt: number
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

/** 记住账号（登录成功后调用） */
export function saveCredentials(username: string) {
  const data: StoredAccount = { username, savedAt: Date.now() }
  try {
    localStorage.setItem(STORAGE_KEY, encode(JSON.stringify(data)))
  } catch { /* 隐私模式等写入失败时静默忽略 */ }
}

/** 读取已记住的账号：未过期返回用户名；已过期自动删除并返回 null */
export function loadCredentials(): { username: string } | null {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    const data = JSON.parse(decrypt(atob(raw))) as Record<string, unknown>
    const username = typeof data?.username === 'string' ? data.username : ''
    if (!username) {
      clearCredentials()
      return null
    }
    // 历史记录里可能存过密码：立即重写，抹掉已落盘的明文密码
    if ('password' in data) {
      saveCredentials(username)
    }
    const savedAt = typeof data.savedAt === 'number' ? data.savedAt : 0
    if (!savedAt || Date.now() - savedAt > VALID_DAYS * 24 * 60 * 60 * 1000) {
      clearCredentials()
      return null
    }
    return { username }
  } catch {
    clearCredentials()
    return null
  }
}

/** 是否曾经勾选过「记住账号」（用于登录页复选框回显） */
export function hasSavedCredentials(): boolean {
  return !!localStorage.getItem(STORAGE_KEY)
}

/** 删除已存账号（用户取消勾选时立即调用） */
export function clearCredentials() {
  localStorage.removeItem(STORAGE_KEY)
}
