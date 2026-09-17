@echo off
chcp 65001 >nul
REM ============================================================
REM 小树成长岛 - 安卓 APK 一键构建脚本 (Windows)
REM
REM 用法:
REM   build-apk.bat                    构建默认 debug APK
REM   build-apk.bat release            构建 release APK
REM   build-apk.bat --api http://1.2.3.4:8061/api/v1   自定义 API 地址
REM
REM 前置要求:
REM   - Node.js >= 20
REM   - Android Studio 或 Android SDK
REM   - Java JDK 17+
REM ============================================================
setlocal enabledelayedexpansion

set BUILD_TYPE=debug
set API_BASE=http://192.168.3.53:8061/api/v1

REM 解析参数
:parse_args
if "%~1"=="" goto after_args
if "%~1"=="--api" (
    set API_BASE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="debug" (
    set BUILD_TYPE=debug
    shift
    goto parse_args
)
if "%~1"=="release" (
    set BUILD_TYPE=release
    shift
    goto parse_args
)
shift
goto parse_args
:after_args

set ROOT_DIR=%~dp0
set FRONTEND_DIR=%ROOT_DIR%careless-correction
set ANDROID_DIR=%FRONTEND_DIR%\android
set APK_DIR=%ANDROID_DIR%\app\build\outputs\apk\%BUILD_TYPE%
set HAS_ERROR=0

echo ========================================
echo 小树成长岛 APK 构建
echo 构建类型: %BUILD_TYPE%
echo API 地址: %API_BASE%
echo ========================================

REM ── [1/5] 检查环境 ──
echo.
echo ^>^>^> [1/5] 环境检查

where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Node.js，请先安装 Node.js 20+
    echo        下载: https://nodejs.org/
    set HAS_ERROR=1
    goto :end
)
for /f "tokens=*" %%i in ('node --version') do echo [OK] Node.js: %%i

if not exist "%ANDROID_DIR%" (
    echo [错误] 安卓项目不存在
    echo        请先运行: cd careless-correction ^&^& npx cap add android
    set HAS_ERROR=1
    goto :end
)
echo [OK] 安卓项目存在

REM 检查 Java
where java >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Java JDK，请安装 JDK 17+
    echo        下载: https://adoptium.net/
    set HAS_ERROR=1
    goto :end
)
for /f "tokens=*" %%i in ('java -version 2^>^&1 | findstr /i "version"') do echo [OK] Java: %%i

REM 检查 Android SDK
set SDK_FOUND=0
if not "%ANDROID_HOME%"=="" (
    if exist "%ANDROID_HOME%" (
        set SDK_FOUND=1
        echo [OK] ANDROID_HOME: %ANDROID_HOME%
    )
)
if "%SDK_FOUND%"=="0" if not "%ANDROID_SDK_ROOT%"=="" (
    if exist "%ANDROID_SDK_ROOT%" (
        set SDK_FOUND=1
        echo [OK] ANDROID_SDK_ROOT: %ANDROID_SDK_ROOT%
    )
)
REM 尝试常见路径
if "%SDK_FOUND%"=="0" (
    set LOCAL_SDK=%LOCALAPPDATA%\Android\Sdk
    if exist "!LOCAL_SDK!" (
        set ANDROID_HOME=!LOCAL_SDK!
        set SDK_FOUND=1
        echo [OK] 自动检测到 Android SDK: !LOCAL_SDK!
    )
)
if "%SDK_FOUND%"=="0" (
    echo [错误] 未找到 Android SDK
    echo        请安装 Android Studio: https://developer.android.com/studio
    echo        或设置环境变量: set ANDROID_HOME=SDK路径
    set HAS_ERROR=1
    goto :end
)

REM 检查 gradlew
if not exist "%ANDROID_DIR%\gradlew.bat" (
    echo [错误] 未找到 gradlew.bat，安卓项目可能不完整
    set HAS_ERROR=1
    goto :end
)
echo [OK] Gradle wrapper 存在

echo.
echo 环境检查全部通过 ✓

REM ── [2/5] 构建前端 ──
echo.
echo ^>^>^> [2/5] 构建前端 (API=%API_BASE%)
cd /d "%FRONTEND_DIR%"

REM 写入 .env.android
echo VITE_API_BASE=%API_BASE%> .env.android
echo [OK] 已生成 .env.android

REM 安装依赖
if not exist node_modules (
    echo 安装依赖中...
    call npm install
    if errorlevel 1 (
        echo [错误] npm install 失败
        set HAS_ERROR=1
        goto :end
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] node_modules 已存在，跳过安装
)

REM TypeScript 类型检查
echo 类型检查中...
call npx vue-tsc -b 2>&1
if errorlevel 1 (
    echo [错误] TypeScript 类型检查失败，请修复代码中的类型错误
    set HAS_ERROR=1
    goto :end
)
echo [OK] 类型检查通过

REM Vite 构建
echo 前端编译中...
call npx vite build --mode android 2>&1
if errorlevel 1 (
    echo [错误] Vite 构建失败
    set HAS_ERROR=1
    goto :end
)
echo [OK] 前端构建完成

REM ── [3/5] 同步到安卓项目 ──
echo.
echo ^>^>^> [3/5] 同步到安卓项目
call npx cap copy android 2>&1
if errorlevel 1 (
    echo [错误] Capacitor 同步失败
    set HAS_ERROR=1
    goto :end
)
echo [OK] 同步完成

REM ── [4/5] 写入 local.properties ──
echo.
echo ^>^>^> [4/5] 配置 Android SDK 路径
echo sdk.dir=%ANDROID_HOME%> "%ANDROID_DIR%\local.properties"
echo [OK] local.properties 已更新

REM ── [5/5] 编译 APK ──
echo.
echo ^>^>^> [5/5] 编译 APK (%BUILD_TYPE%)
echo       首次编译可能需要 5-10 分钟，请耐心等待...
echo.
cd /d "%ANDROID_DIR%"

if "%BUILD_TYPE%"=="release" (
    call gradlew.bat assembleRelease 2>&1
) else (
    call gradlew.bat assembleDebug 2>&1
)
if errorlevel 1 (
    echo.
    echo [错误] Gradle 编译失败
    echo        常见原因:
    echo        1. SDK 版本不匹配 - 打开 Android Studio 更新 SDK
    echo        2. 网络问题 - Gradle 下载依赖失败，检查网络或配置代理
    echo        3. JDK 版本不对 - 需要 JDK 17+
    set HAS_ERROR=1
    goto :end
)

REM ── 结果 ──
echo.
echo ========================================
set APK_FILE=%APK_DIR%\app-%BUILD_TYPE%.apk
if exist "%APK_FILE%" (
    echo 构建成功! ✓
    echo.
    echo APK 路径: %APK_FILE%
    REM 拷贝到项目根目录方便查找
    copy /Y "%APK_FILE%" "%ROOT_DIR%app-%BUILD_TYPE%.apk" >nul
    echo 已拷贝到: %ROOT_DIR%app-%BUILD_TYPE%.apk
    echo.
    echo 安装方法:
    echo   1. 将 APK 拷到安卓 Pad
    echo   2. 在 Pad 上点击 APK 文件安装
    echo   3. 确保 Pad 与服务器在同一局域网
    echo ========================================
) else (
    echo [错误] APK 文件未找到: %APK_FILE%
    set HAS_ERROR=1
)

:end
echo.
if "%HAS_ERROR%"=="1" (
    echo ========================================
    echo 构建失败! 请查看上方 [错误] 提示
    echo ========================================
    echo.
    echo 提示: 如果没有 Android 开发环境，
    echo       可使用 Docker 构建: build-apk-docker.bat
    echo ========================================
    exit /b 1
) else (
    exit /b 0
)
