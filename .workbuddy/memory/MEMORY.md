# 项目长期笔记（studentStudy / 小树成长岛）

## 项目构成
- `careless-correction/`：Vue 3 + TS + Vite + Pinia 前端，Capacitor 8 打包安卓
- `careless-correction-api/`：Python FastAPI + SQLAlchemy + SQLite 后端

## 安卓打包约定
- 构建入口：`build-apk.sh` / `build-apk.bat`（debug/release，`--api` 指定后端地址）
- 默认 API 地址写在 `.env.android`：`VITE_API_BASE=http://192.168.3.53:8061/api/v1`
- 安卓工程：`careless-correction/android`，包名 `com.studentstudy.app`，应用名「小树成长岛」
- **本机构建环境**：
  - JDK 21：`D:\java\jdk-21\jdk-21.0.12.1+1`（构建时必须指定，系统 JAVA_HOME 是 JDK 8 不可用）
  - Android SDK：`F:\androidSdk`（含 platform 36、build-tools 36.0.0）
  - Gradle wrapper 8.14.3（已缓存于 ~/.gradle）
- 前端构建需加 `--emptyOutDir=false`（避免清空 dist 触发删除保护）
- `android/capacitor-cordova-android-plugins/` 需存在（模板来自 @capacitor/cli/assets 的 tar.gz，注意解压到子目录而非 android/ 根）

## 注意事项
- 后端 API 用 HTTP 明文，`capacitor.config.ts` 已开 `allowMixedContent` + `androidScheme: http`，Pad 与服务器需同局域网
