import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.studentstudy.app',
  appName: '小树成长岛',
  webDir: 'dist',
  android: {
    // 允许混合内容（HTTP API 请求）
    allowMixedContent: true,
    // 允许 WebView 调试
    webContentsDebuggingEnabled: true,
  },
  server: {
    // Android Cleartext 支持（允许 HTTP 请求）
    androidScheme: 'http',
    // APP 直接从 nginx 服务器加载前端，改代码只重打前端包即可，无需重打 APK
    url: 'http://192.168.3.53:8061',
  },
};

export default config;
