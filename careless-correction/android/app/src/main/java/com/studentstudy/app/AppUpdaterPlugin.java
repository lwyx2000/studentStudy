package com.studentstudy.app;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.Settings;
import android.util.Log;

import androidx.core.content.FileProvider;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 应用内更新插件
 *
 * - getVersion()         读取当前已安装 APK 的版本号
 * - download()           后台下载新 APK，并通过 "downloadProgress" 事件推送进度
 * - checkInstallPermission() 是否允许安装未知来源应用（Android 8+）
 * - openInstallSettings()    跳转「安装未知应用」授权页
 * - install()            通过 FileProvider 调用系统安装器
 * - getDownloadedPath()  获取已下载 APK 的本地路径
 */
@CapacitorPlugin(name = "AppUpdater")
public class AppUpdaterPlugin extends Plugin {

    private static final String TAG = "AppUpdater";
    private static final String EVENT_PROGRESS = "downloadProgress";
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    /** 返回当前 APK 版本信息 */
    @PluginMethod
    public void getVersion(PluginCall call) {
        JSObject ret = new JSObject();
        try {
            Context ctx = getContext();
            PackageManager pm = ctx.getPackageManager();
            PackageInfo pi = pm.getPackageInfo(ctx.getPackageName(), 0);
            long versionCode;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                versionCode = pi.getLongVersionCode();
            } else {
                versionCode = pi.versionCode;
            }
            ret.put("versionCode", versionCode);
            ret.put("versionName", pi.versionName == null ? "" : pi.versionName);
            ret.put("packageName", ctx.getPackageName());
            call.resolve(ret);
        } catch (Exception e) {
            Log.e(TAG, "getVersion failed", e);
            call.reject("读取版本信息失败: " + e.getMessage());
        }
    }

    /** 是否允许安装未知来源应用 */
    @PluginMethod
    public void checkInstallPermission(PluginCall call) {
        JSObject ret = new JSObject();
        boolean canInstall;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            canInstall = getContext().getPackageManager().canRequestPackageInstalls();
        } else {
            canInstall = true;
        }
        ret.put("canInstall", canInstall);
        call.resolve(ret);
    }

    /** 跳转到「安装未知应用」授权设置页 */
    @PluginMethod
    public void openInstallSettings(PluginCall call) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                Intent intent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES);
                intent.setData(Uri.parse("package:" + getContext().getPackageName()));
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
            } else {
                Intent intent = new Intent(Settings.ACTION_SECURITY_SETTINGS);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
            }
            call.resolve();
        } catch (Exception e) {
            Log.e(TAG, "openInstallSettings failed", e);
            call.reject("打开设置失败: " + e.getMessage());
        }
    }

    /** 后台下载 APK，进度通过 downloadProgress 事件推送 */
    @PluginMethod
    public void download(PluginCall call) {
        final String urlStr = call.getString("url");
        if (urlStr == null || urlStr.trim().isEmpty()) {
            call.reject("下载地址不能为空");
            return;
        }
        String rawName = call.getString("fileName", "app-update.apk");
        final String fileName = rawName.replaceAll("[^a-zA-Z0-9._-]", "_");
        call.setKeepAlive(true);

        executor.execute(() -> {
            HttpURLConnection conn = null;
            try {
                File dir = new File(getContext().getCacheDir(), "updater");
                if (!dir.exists() && !dir.mkdirs()) {
                    throw new IOException("无法创建下载目录");
                }
                File target = new File(dir, fileName);
                File tmp = new File(dir, fileName + ".part");
                if (tmp.exists()) {
                    //noinspection ResultOfMethodCallIgnored
                    tmp.delete();
                }

                URL url = new URL(urlStr);
                conn = (HttpURLConnection) url.openConnection();
                conn.setInstanceFollowRedirects(true);
                conn.setConnectTimeout(20000);
                conn.setReadTimeout(30000);
                conn.setRequestMethod("GET");
                int status = conn.getResponseCode();
                if (status < 200 || status >= 300) {
                    throw new IOException("HTTP " + status);
                }

                long total = conn.getContentLengthLong();
                long loaded = 0;
                int lastPercent = -1;
                byte[] buffer = new byte[16 * 1024];

                try (InputStream in = new BufferedInputStream(conn.getInputStream());
                     FileOutputStream out = new FileOutputStream(tmp)) {
                    int read;
                    while ((read = in.read(buffer)) != -1) {
                        out.write(buffer, 0, read);
                        loaded += read;
                        if (total > 0) {
                            final int percent = (int) (loaded * 100 / total);
                            if (percent != lastPercent) {
                                lastPercent = percent;
                                final long current = loaded;
                                getActivity().runOnUiThread(() -> {
                                    JSObject data = new JSObject();
                                    data.put("percent", percent);
                                    data.put("loaded", current);
                                    data.put("total", total);
                                    notifyListeners(EVENT_PROGRESS, data);
                                });
                            }
                        }
                    }
                }

                if (!tmp.renameTo(target)) {
                    // 某些机型 rename 跨挂载点会失败，退化为复制
                    try (FileOutputStream out = new FileOutputStream(target);
                         InputStream in = new BufferedInputStream(new java.io.FileInputStream(tmp))) {
                        byte[] buf = new byte[16 * 1024];
                        int r;
                        while ((r = in.read(buf)) != -1) out.write(buf, 0, r);
                    }
                    //noinspection ResultOfMethodCallIgnored
                    tmp.delete();
                }

                long size = target.length();
                if (size == 0) {
                    throw new IOException("下载文件为空");
                }

                JSObject data = new JSObject();
                data.put("path", target.getAbsolutePath());
                data.put("size", size);
                getActivity().runOnUiThread(() -> {
                    JSObject done = new JSObject();
                    done.put("percent", 100);
                    done.put("loaded", size);
                    done.put("total", size);
                    notifyListeners(EVENT_PROGRESS, done);
                    call.resolve(data);
                });
            } catch (Exception e) {
                Log.e(TAG, "download failed", e);
                getActivity().runOnUiThread(() -> call.reject("下载失败: " + e.getMessage()));
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    /** 已下载 APK 的本地路径（不存在返回 null） */
    @PluginMethod
    public void getDownloadedPath(PluginCall call) {
        String rawName = call.getString("fileName", "app-update.apk");
        String fileName = rawName.replaceAll("[^a-zA-Z0-9._-]", "_");
        File file = new File(new File(getContext().getCacheDir(), "updater"), fileName);
        JSObject ret = new JSObject();
        if (file.exists()) {
            ret.put("path", file.getAbsolutePath());
            ret.put("size", file.length());
        }
        call.resolve(ret);
    }

    /** 通过 FileProvider 触发系统安装器 */
    @PluginMethod
    public void install(PluginCall call) {
        String path = call.getString("path");
        if (path == null || path.trim().isEmpty()) {
            call.reject("安装包路径不能为空");
            return;
        }
        try {
            File apk = new File(path);
            if (!apk.exists()) {
                call.reject("安装包不存在，请先下载");
                return;
            }
            if (!apk.getName().toLowerCase().endsWith(".apk")) {
                call.reject("文件不是 APK 格式");
                return;
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                    && !getContext().getPackageManager().canRequestPackageInstalls()) {
                JSObject ret = new JSObject();
                ret.put("needPermission", true);
                call.resolve(ret);
                return;
            }

            Uri uri = FileProvider.getUriForFile(
                    getContext(), getContext().getPackageName() + ".fileprovider", apk);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);

            Activity activity = getActivity();
            if (activity != null) {
                activity.startActivity(intent);
            } else {
                getContext().startActivity(intent);
            }
            JSObject ret = new JSObject();
            ret.put("needPermission", false);
            call.resolve(ret);
        } catch (Exception e) {
            Log.e(TAG, "install failed", e);
            call.reject("调起安装失败: " + e.getMessage());
        }
    }
}
