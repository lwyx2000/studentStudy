# 应用内自动更新（APK）

App 启动时会自动检查服务器上的最新版本，发现新版本时弹窗提示，用户确认后在 App 内下载 APK 并调起系统安装器完成更新。

## 一、工作原理

```
App 启动
  → 读取本地 APK 版本号（原生插件 AppUpdater.getVersion）
  → 请求服务器 /version.json（前端静态目录，随前端部署）
  → 对比 versionCode：服务器 > 本地则弹窗
  → 用户点「立即更新」→ 后台下载 /downloads/<apk>（带进度）
  → 检查「安装未知应用」权限 → 调起系统安装器
```

涉及的关键文件：

| 文件                                                    | 作用                                        |
| ----------------------------------------------------- | ----------------------------------------- |
| `careless-correction/public/version.json`             | 版本清单，随前端打包部署到 `http://<服务器>/version.json` |
| `downloads/*.apk`                                     | 待分发的 APK，nginx 通过 `/downloads/` 对外提供      |
| `nginx/nginx.conf`                                    | 配置了 `location /downloads/` 静态目录           |
| `do【jcker-compose.yml`                                | 把宿主机 `downloads/` 挂载到 nginx 容器            |
| `careless-correction/android/app/build.gradle`        | 本地 APK 的 `versionCode` / `versionName`    |
| `careless-correction/src/utils/updater.ts`            | 前端：检查、下载、安装封装                             |
| `careless-correction/src/components/UpdateDialog.vue` | 更新提示弹窗                                    |
| `.../java/com/studentstudy/app/AppUpdaterPlugin.java` | 原生：版本读取、下载、安装                             |

## 二、version.json 字段

```json
{
  "versionCode": 2,
  "versionName": "1.1",
  "changelog": "1. 新增xxx\n2. 修复xxx",
  "downloadUrl": "/downloads/app-debug.apk",
  "force": false,
  "publishedAt": "2026-11-20"
}
```

| 字段            | 说明                                                      |
| ------------- | ------------------------------------------------------- |
| `versionCode` | **整数**，决定是否提示更新的唯一依据。必须大于旧 APK 的 versionCode            |
| `versionName` | 展示给用户看的版本号，如 `1.1`                                      |
| `changelog`   | 更新说明，支持 `\n` 换行                                         |
| `downloadUrl` | APK 下载地址，推荐用 `/downloads/` 开头的相对路径（自动拼接服务器地址）；也可写完整 URL |
| `force`       | `true` 时隐藏「暂不更新」按钮，强制更新                                 |
| `publishedAt` | 发布日期，展示用，可省略                                            |

## 三、发布新版本（完整步骤）

假设当前线上是 versionCode 2，要发布 versionCode 3：

1. **提升 APK 版本号**：编辑 `careless-correction/android/app/build.gradle`
   ```gradle
   versionCode 3
   versionName "1.2"
   ```
2. **重新打包 APK**（在项目根目录执行，需 JDK 21 + Android SDK）：
   ```bash
   cd careless-correction
   export JAVA_HOME="/d/Java/jdk-21/jdk-21.0.12.1+1"
   export ANDROID_HOME="/f/androidSdk"
   npx vue-tsc -b && npx vite build --mode android && npx cap copy android
   cd android && ./gradlew assembleDebug --no-daemon
   ```
   （Windows 可直接用项目根目录的 `build-apk.ps1` / `build-apk.bat`，注意它默认用系统 Java，需先把 `JAVA_HOME` 指向 JDK 21）
3. **把新 APK 放到下载目录**：
   ```bash
   cp careless-correction/android/app/build/outputs/apk/debug/app-debug.apk downloads/app-debug.apk
   ```
   也可以按版本命名（如 `app-1.2.apk`），此时需同步修改 `version.json` 的 `downloadUrl`。
4. **更新 version.json**：编辑 `careless-correction/public/version.json`，把 `versionCode` 改为 `3`、`versionName` 改为 `1.2`，填写本次 `changelog` 和 `publishedAt`。
5. **重新部署前端**（让新的 version.json 随前端发布到服务器）：
   ```bash
   docker compose up -d --build frontend nginx
   ```
   或按现有 `deploy.sh` / Jenkins 流程部署。
6. 完成。装有旧版本（versionCode ≤ 2）的设备打开 App 时会收到更新提示。

## 四、常见问题

- **点安装没反应 / 提示需要授权**：Android 8+ 首次安装需开启「允许安装未知应用」。点更新时若未授权，会自动跳到系统设置页，开启后返回 App 再点一次「立即更新」即可。
- **debug 包签名**：当前分发的是 `app-debug.apk`（系统 debug 签名）。同一台设备从 debug 包更新到 debug 包没问题；但如果要换成 release 签名包， Android 会因签名不同拒绝覆盖安装，需先卸载旧版。
- **更新检查失败时不提示**：设备离线、服务器未部署 version.json、或 version.json 格式错误时，更新检查会静默跳过，不影响 App 正常使用。
- **浏览器里预览**：web 环境不支持原生安装，更新检查会自动跳过，不会弹窗。
- **「暂不更新」**：仅本次会话有效，下次冷启动会再次提示（`force: true` 时无法跳过）。
