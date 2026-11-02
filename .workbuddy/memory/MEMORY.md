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

## 安全与数据一致性约定（2026-11-02 全量修复后）
- **JWT 密钥**：`app/config/settings.py` 在 `jwt_secret` 为空/示例值时自动生成随机串写入 `data/.jwt_secret`（容器内 `/app/data/.jwt_secret`，随数据卷持久化）。**严禁**在 `docker-compose.yml` / `.env.example` 中再写默认密钥。换密钥会让所有旧 token 失效。
- **注册**：首个家长可自由注册；之后必须提供 `REGISTER_INVITE_CODE`（留空即禁止新增家长）。
- **孩子账号**：初始密码随机生成，只在 `POST /children/` 响应里返回一次（`initialPassword`），前端家长页展示给家长。没有统一默认密码了。
- **打卡计分**：`POST /checkins/` 的 `total_points` 只作为上限，服务端会按 `completed_tasks` 的 title 匹配数据库子任务重新算分（必做=子任务自定义分或主任务分，可选=2/项，全完成 +10 由服务端判定），并把快照里的 `points` 覆盖成真实值。改计分口径必须同步前后端。
- **权限**：任务/子任务/习惯的写接口是 `require_parent`；孩子只能完成/打卡。
- **删除**：`DELETE /children/{id}` 靠 `_purge_owned_rows` 按外键顺序手动清理（模型没配 cascade），新增挂用户的外键表要同步加进该函数。
- **扣减**：阳光/苹果一律用 `_spend_sunlight` / `_spend_apples`（条件 UPDATE），不要再写「先 if 再 -=」。
- **SQLite**：已开 WAL + busy_timeout=5000；`GET /tasks/today` 仍会顺带重置每日任务（写库），已加异常兜底。
