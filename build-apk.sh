#!/usr/bin/env bash
# ============================================================
# 小树成长岛 - 安卓 APK 一键构建脚本
#
# 用法:
#   bash build-apk.sh                    # 构建 debug APK
#   bash build-apk.sh release            # 构建 release APK（需签名配置）
#   bash build-apk.sh --api http://1.2.3.4:8061/api/v1   # 自定义 API 地址
#
# 前置要求:
#   - Node.js >= 20
#   - Android Studio 或 Android SDK (设置 ANDROID_HOME 环境变量)
#   - Java JDK 17+
#
# 产物位置:
#   careless-correction/android/app/build/outputs/apk/debug/app-debug.apk
#   careless-correction/android/app/build/outputs/apk/release/app-release.apk
# ============================================================
set -euo pipefail

BUILD_TYPE="${1:-debug}"
API_BASE="http://192.168.3.53:8061/api/v1"

# 解析 --api 参数
while [[ $# -gt 0 ]]; do
  case "$1" in
    --api)
      API_BASE="$2"
      shift 2
      ;;
    debug|release)
      BUILD_TYPE="$1"
      shift
      ;;
    *)
      shift
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/careless-correction"
ANDROID_DIR="$FRONTEND_DIR/android"
APK_DIR="$ANDROID_DIR/app/build/outputs/apk/$BUILD_TYPE"

echo "========================================"
echo "小树成长岛 APK 构建"
echo "构建类型: $BUILD_TYPE"
echo "API 地址: $API_BASE"
echo "========================================"

# ── [1/4] 检查环境 ──
echo ""
echo ">>> [1/4] 环境检查"

if ! command -v node &> /dev/null; then
  echo "错误: 未安装 Node.js，请先安装 Node.js >= 20"
  exit 1
fi
echo "Node.js: $(node --version)"

if [ ! -d "$ANDROID_DIR" ]; then
  echo "错误: 安卓项目不存在，请先运行: cd careless-correction && npx cap add android"
  exit 1
fi

# 检查 Android SDK
if [ -z "${ANDROID_HOME:-}" ] && [ -z "${ANDROID_SDK_ROOT:-}" ]; then
  echo "警告: 未设置 ANDROID_HOME 环境变量"
  echo "  如果已安装 Android Studio，通常路径为:"
  echo "    Windows: C:\\Users\\<用户名>\\AppData\\Local\\Android\\Sdk"
  echo "    macOS:   ~/Library/Android/sdk"
  echo "    Linux:   ~/Android/Sdk"
  echo "  请设置环境变量: export ANDROID_HOME=<SDK路径>"
fi

# ── [2/4] 构建 Vue 前端（注入 API 地址）──
echo ""
echo ">>> [2/4] 构建前端 (API=$API_BASE)"
cd "$FRONTEND_DIR"

# 临时写入 .env.android
cat > .env.android << EOF
VITE_API_BASE=$API_BASE
EOF
echo "已生成 .env.android"

# 安装依赖（如果 node_modules 不存在）
if [ ! -d node_modules ]; then
  echo "安装依赖..."
  npm install
fi

# 构建
echo "构建前端..."
npx vue-tsc -b
npx vite build --mode android
echo "前端构建完成 ✓"

# ── [3/4] 同步到安卓项目 ──
echo ""
echo ">>> [3/4] 同步到安卓项目"
npx cap copy android
echo "同步完成 ✓"

# ── [4/4] 编译 APK ──
echo ""
echo ">>> [4/4] 编译 APK ($BUILD_TYPE)"
cd "$ANDROID_DIR"

# 确定 gradlew
if [ -f "./gradlew" ]; then
  GRADLE_CMD="./gradlew"
elif command -v gradle &> /dev/null; then
  GRADLE_CMD="gradle"
else
  echo "错误: 未找到 gradlew 或 gradle，请确保 Android 项目已正确初始化"
  exit 1
fi

if [ "$BUILD_TYPE" = "release" ]; then
  $GRADLE_CMD assembleRelease
else
  $GRADLE_CMD assembleDebug
fi

# ── 结果 ──
echo ""
echo "========================================"
if [ -f "$APK_DIR/app-$BUILD_TYPE.apk" ]; then
  APK_PATH="$APK_DIR/app-$BUILD_TYPE.apk"
  APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
  echo "构建成功! ✓"
  echo ""
  echo "APK 路径: $APK_PATH"
  echo "APK 大小: $APK_SIZE"
  echo ""
  echo "安装方法:"
  echo "  1. 将 APK 拷到安卓 Pad"
  echo "  2. 在 Pad 上点击 APK 文件安装"
  echo "  3. 确保 Pad 与服务器在同一局域网"
  echo "========================================"
else
  echo "构建失败! 请检查上方日志"
  echo "========================================"
  exit 1
fi
