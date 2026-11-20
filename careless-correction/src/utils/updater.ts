import { Capacitor, registerPlugin } from '@capacitor/core'
import type { PluginListenerHandle } from '@capacitor/core'

/**
 * 应用内更新工具
 *
 * 依赖原生插件 AppUpdater（见 android/app/src/main/java/.../AppUpdaterPlugin.java）。
 * 在浏览器/非原生环境下会安全降级：不会崩溃，也不提示更新。
 */

interface AppUpdaterPluginType {
  getVersion(): Promise<{ versionCode: number; versionName: string; packageName: string }>
  checkInstallPermission(): Promise<{ canInstall: boolean }>
  openInstallSettings(): Promise<void>
  download(options: { url: string; fileName?: string }): Promise<{ path: string; size: number }>
  getDownloadedPath(options: { fileName?: string }): Promise<{ path?: string; size?: number }>
  install(options: { path: string }): Promise<{ needPermission: boolean }>
  addListener(
    eventName: 'downloadProgress',
    listenerFunc: (data: { percent: number; loaded: number; total: number }) => void,
  ): Promise<PluginListenerHandle>
}

// 用静态导入避免 web 环境下 registerPlugin 抛错：Capacitor 会为未实现的插件生成空实现
const AppUpdater = registerPlugin<AppUpdaterPluginType>('AppUpdater')

export interface RemoteVersion {
  versionCode: number
  versionName: string
  changelog: string
  downloadUrl: string
  force?: boolean
  publishedAt?: string
}

export interface LocalVersion {
  versionCode: number
  versionName: string
  packageName: string
}

export interface UpdateCheckResult {
  hasUpdate: boolean
  local: LocalVersion | null
  remote: RemoteVersion
  /** 非原生环境（浏览器预览）时为 true，调用方应跳过提示 */
  unsupported: boolean
}

/**
 * 站点根地址：App 通过 server.url 从服务器加载前端，window.location.origin 即为服务器地址。
 * 这样 version.json / APK 下载都用相对路径配置，换服务器 IP 也不用改代码。
 */
function serverOrigin(): string {
  if (typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null') {
    return window.location.origin
  }
  return (import.meta.env.VITE_API_BASE || '/api/v1').replace(/\/api\/v1\/?$/, '')
}

/** 版本文件地址：放在服务器静态目录根下 */
const VERSION_URL = `${serverOrigin()}/version.json`

/** 把相对下载路径补全为绝对 URL（原生下载需要完整地址） */
function resolveDownloadUrl(url: string): string {
  if (/^https?:\/\//i.test(url)) return url
  return `${serverOrigin()}${url.startsWith('/') ? '' : '/'}${url}`
}

/** 仅在原生 Android 平台启用更新（浏览器预览时安全跳过） */
function isNativeAndroid(): boolean {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android'
}

/** 拉取服务器版本信息并对比本地版本 */
export async function checkForUpdate(): Promise<UpdateCheckResult> {
  const res = await fetch(`${VERSION_URL}?t=${Date.now()}`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`版本检查失败: HTTP ${res.status}`)
  const remote = (await res.json()) as RemoteVersion

  if (!isNativeAndroid()) {
    return { hasUpdate: false, local: null, remote, unsupported: true }
  }

  let local: LocalVersion
  try {
    local = await AppUpdater.getVersion()
  } catch {
    return { hasUpdate: false, local: null, remote, unsupported: true }
  }

  const hasUpdate = Number(remote.versionCode) > Number(local.versionCode)
  return { hasUpdate, local, remote, unsupported: false }
}

/** 监听下载进度，返回取消监听的函数 */
export async function onDownloadProgress(
  cb: (data: { percent: number; loaded: number; total: number }) => void,
): Promise<() => void> {
  const handle = await AppUpdater.addListener('downloadProgress', cb)
  return () => { void handle.remove() }
}

/** 下载 APK，成功返回本地路径 */
export async function downloadApk(
  url: string,
  onProgress?: (percent: number) => void,
  fileName = 'app-update.apk',
): Promise<string> {
  let remove: (() => void) | undefined
  if (onProgress) {
    remove = await onDownloadProgress((data) => onProgress(data.percent))
  }
  try {
    const result = await AppUpdater.download({ url: resolveDownloadUrl(url), fileName })
    return result.path
  } finally {
    remove?.()
  }
}

/** 检查是否允许安装未知来源应用 */
export async function canInstall(): Promise<boolean> {
  const r = await AppUpdater.checkInstallPermission()
  return r.canInstall
}

/** 打开「安装未知应用」授权页 */
export async function openInstallSettings(): Promise<void> {
  await AppUpdater.openInstallSettings()
}

/**
 * 调起系统安装器。
 * 返回 'ok' | 'need-permission'，'need-permission' 时需先 openInstallSettings。
 */
export async function installApk(path: string): Promise<'ok' | 'need-permission'> {
  const r = await AppUpdater.install({ path })
  return r.needPermission ? 'need-permission' : 'ok'
}

/** 读取已下载 APK 路径（用于断点/重复点击时避免重复下载） */
export async function getDownloadedPath(fileName = 'app-update.apk'): Promise<string | null> {
  const r = await AppUpdater.getDownloadedPath({ fileName })
  return r.path ?? null
}
