#Requires -Version 5.1
<#
.SYNOPSIS
    小树成长岛 - 安卓 APK 一键构建脚本 (Windows PowerShell)

.EXAMPLE
    .\build-apk.ps1
    .\build-apk.ps1 release
    .\build-apk.ps1 -ApiBase "http://10.0.0.1:8061/api/v1"

.NOTES
    前置要求:
    - Node.js >= 20
    - Android Studio 或 Android SDK
    - Java JDK 17+
#>

param(
    [ValidateSet('debug', 'release')]
    [string]$BuildType = 'debug',

    [string]$ApiBase = 'http://192.168.3.53:8061/api/v1'
)

$ErrorActionPreference = 'Stop'
$HasError = $false

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $RootDir 'careless-correction'
$AndroidDir = Join-Path $FrontendDir 'android'
$ApkDir = Join-Path $AndroidDir "app\build\outputs\apk\$BuildType"

Write-Host '========================================' -ForegroundColor Cyan
Write-Host '小树成长岛 APK 构建' -ForegroundColor Cyan
Write-Host "构建类型: $BuildType" -ForegroundColor Cyan
Write-Host "API 地址: $ApiBase" -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan

# ── [1/5] 检查环境 ──
Write-Host ''
Write-Host '>>> [1/5] 环境检查' -ForegroundColor Yellow

# Node.js
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host '[错误] 未安装 Node.js，请先安装 Node.js 20+' -ForegroundColor Red
    Write-Host '       下载: https://nodejs.org/' -ForegroundColor Red
    $HasError = $true
    goto :end
}
$nodeVer = & node --version
Write-Host "[OK] Node.js: $nodeVer" -ForegroundColor Green

# 安卓项目存在
if (-not (Test-Path $AndroidDir)) {
    Write-Host '[错误] 安卓项目不存在' -ForegroundColor Red
    Write-Host '       请先运行: cd careless-correction ; npx cap add android' -ForegroundColor Red
    $HasError = $true
    goto :end
}
Write-Host '[OK] 安卓项目存在' -ForegroundColor Green

# Java
$java = Get-Command java -ErrorAction SilentlyContinue
if (-not $java) {
    Write-Host '[错误] 未安装 Java JDK，请安装 JDK 17+' -ForegroundColor Red
    Write-Host '       下载: https://adoptium.net/' -ForegroundColor Red
    $HasError = $true
    goto :end
}
$javaVer = (& java -version 2>&1 | Select-Object -First 1).ToString().Trim()
Write-Host "[OK] Java: $javaVer" -ForegroundColor Green

# Android SDK
$SdkFound = $false
$SdkPath = $env:ANDROID_HOME
if (-not $SdkPath) { $SdkPath = $env:ANDROID_SDK_ROOT }
if ($SdkPath -and (Test-Path $SdkPath)) {
    $SdkFound = $true
    Write-Host "[OK] Android SDK: $SdkPath" -ForegroundColor Green
}
if (-not $SdkFound) {
    $localSdk = "$env:LOCALAPPDATA\Android\Sdk"
    if (Test-Path $localSdk) {
        $SdkPath = $localSdk
        $env:ANDROID_HOME = $SdkPath
        $SdkFound = $true
        Write-Host "[OK] 自动检测到 Android SDK: $SdkPath" -ForegroundColor Green
    }
}
if (-not $SdkFound) {
    Write-Host '[错误] 未找到 Android SDK' -ForegroundColor Red
    Write-Host '       请安装 Android Studio: https://developer.android.com/studio' -ForegroundColor Red
    Write-Host '       或设置环境变量: $env:ANDROID_HOME = "SDK路径"' -ForegroundColor Red
    $HasError = $true
    goto :end
}

# gradlew
$gradlewBat = Join-Path $AndroidDir 'gradlew.bat'
if (-not (Test-Path $gradlewBat)) {
    Write-Host '[错误] 未找到 gradlew.bat，安卓项目可能不完整' -ForegroundColor Red
    $HasError = $true
    goto :end
}
Write-Host '[OK] Gradle wrapper 存在' -ForegroundColor Green

Write-Host '环境检查全部通过' -ForegroundColor Green

# ── [2/5] 构建前端 ──
Write-Host ''
Write-Host ">>> [2/5] 构建前端 (API=$ApiBase)" -ForegroundColor Yellow
Set-Location $FrontendDir

# 写入 .env.android
"VITE_API_BASE=$ApiBase" | Out-File -FilePath '.env.android' -Encoding utf8
Write-Host '[OK] 已生成 .env.android' -ForegroundColor Green

# 安装依赖
if (-not (Test-Path 'node_modules')) {
    Write-Host '安装依赖中...' -ForegroundColor Gray
    & npm install 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[错误] npm install 失败' -ForegroundColor Red
        $HasError = $true
        goto :end
    }
    Write-Host '[OK] 依赖安装完成' -ForegroundColor Green
} else {
    Write-Host '[OK] node_modules 已存在，跳过安装' -ForegroundColor Green
}

# TypeScript 类型检查
Write-Host '类型检查中...' -ForegroundColor Gray
& npx vue-tsc -b 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host '[错误] TypeScript 类型检查失败，请修复代码中的类型错误' -ForegroundColor Red
    $HasError = $true
    goto :end
}
Write-Host '[OK] 类型检查通过' -ForegroundColor Green

# Vite 构建
Write-Host '前端编译中...' -ForegroundColor Gray
& npx vite build --mode android 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host '[错误] Vite 构建失败' -ForegroundColor Red
    $HasError = $true
    goto :end
}
Write-Host '[OK] 前端构建完成' -ForegroundColor Green

# ── [3/5] 同步到安卓项目 ──
Write-Host ''
Write-Host '>>> [3/5] 同步到安卓项目' -ForegroundColor Yellow
& npx cap copy android 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host '[错误] Capacitor 同步失败' -ForegroundColor Red
    $HasError = $true
    goto :end
}
Write-Host '[OK] 同步完成' -ForegroundColor Green

# ── [4/5] 写入 local.properties ──
Write-Host ''
Write-Host '>>> [4/5] 配置 Android SDK 路径' -ForegroundColor Yellow
"sdk.dir=$SdkPath" | Out-File -FilePath (Join-Path $AndroidDir 'local.properties') -Encoding utf8
Write-Host '[OK] local.properties 已更新' -ForegroundColor Green

# ── [5/5] 编译 APK ──
Write-Host ''
Write-Host ">>> [5/5] 编译 APK ($BuildType)" -ForegroundColor Yellow
Write-Host '       首次编译可能需要 5-10 分钟，请耐心等待...' -ForegroundColor Gray
Write-Host ''
Set-Location $AndroidDir

if ($BuildType -eq 'release') {
    & ./gradlew.bat assembleRelease 2>&1 | Out-String
} else {
    & ./gradlew.bat assembleDebug 2>&1 | Out-String
}
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '[错误] Gradle 编译失败' -ForegroundColor Red
    Write-Host '       常见原因:' -ForegroundColor Red
    Write-Host '       1. SDK 版本不匹配 - 打开 Android Studio 更新 SDK' -ForegroundColor Red
    Write-Host '       2. 网络问题 - Gradle 下载依赖失败，检查网络或配置代理' -ForegroundColor Red
    Write-Host '       3. JDK 版本不对 - 需要 JDK 17+' -ForegroundColor Red
    $HasError = $true
    goto :end
}

# ── 结果 ──
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
$ApkFile = Join-Path $ApkDir "app-$BuildType.apk"
$RootApk = Join-Path $RootDir "app-$BuildType.apk"
if (Test-Path $ApkFile) {
    Write-Host '构建成功!' -ForegroundColor Green
    Write-Host ''
    Write-Host "APK 路径: $ApkFile" -ForegroundColor White
    # 拷贝到项目根目录方便查找
    Copy-Item -Path $ApkFile -Destination $RootApk -Force
    Write-Host "已拷贝到: $RootApk" -ForegroundColor White
    Write-Host ''
    Write-Host '安装方法:' -ForegroundColor Cyan
    Write-Host '  1. 将 APK 拷到安卓 Pad' -ForegroundColor Cyan
    Write-Host '  2. 在 Pad 上点击 APK 文件安装' -ForegroundColor Cyan
    Write-Host '  3. 确保 Pad 与服务器在同一局域网' -ForegroundColor Cyan
    Write-Host '========================================' -ForegroundColor Cyan
} else {
    Write-Host "[错误] APK 文件未找到: $ApkFile" -ForegroundColor Red
    $HasError = $true
}

:end
Write-Host ''
if ($HasError) {
    Write-Host '========================================' -ForegroundColor Red
    Write-Host '构建失败! 请查看上方 [错误] 提示' -ForegroundColor Red
    Write-Host '========================================' -ForegroundColor Red
    Write-Host ''
    Write-Host '提示: 如果没有 Android 开发环境，' -ForegroundColor Yellow
    Write-Host '      可使用 Docker 构建: .\build-apk-docker.ps1' -ForegroundColor Yellow
    Write-Host '========================================' -ForegroundColor Red
    exit 1
}
exit 0
