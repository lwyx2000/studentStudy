/**
 * 页面刷新事件总线
 *
 * 下拉刷新时：MainLayout 统一刷新所有 store 后派发一个 refresh 事件，
 * 有本地数据加载逻辑的页面（不走 store 的）监听它重新加载。
 * 用事件而非强制重挂载 router-view，避免表单页丢失正在输入的内容。
 */

type RefreshHandler = () => void | Promise<void>

const handlers = new Set<RefreshHandler>()

/** 监听刷新事件，返回取消监听函数 */
export function onPageRefresh(handler: RefreshHandler): () => void {
  handlers.add(handler)
  return () => { handlers.delete(handler) }
}

/** 派发刷新事件 */
export function emitPageRefresh() {
  handlers.forEach((h) => {
    try { void h() } catch { /* 单个页面刷新失败不影响其他页面 */ }
  })
}
