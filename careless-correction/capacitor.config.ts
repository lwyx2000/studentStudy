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
  },
};

export default config;
