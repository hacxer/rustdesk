#!/usr/bin/env python3
"""Apply the reviewed Android profile to an explicit upstream checkout."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[2]
ROOT = Path(sys.argv[1]).resolve()
CHANGED = []


def replace_once(path, old, new):
    target = ROOT / path
    text = target.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"Upstream compatibility check failed: {path}; expected one anchor")
    target.write_text(text.replace(old, new))
    CHANGED.append(path)


def copy_source(name, destination):
    target = ROOT / destination
    if target.exists():
        raise SystemExit(f"Refusing to overwrite upstream file: {destination}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROFILE / "scripts/custom-9394/source" / name, target)
    CHANGED.append(destination)


config = json.loads((PROFILE / "config/custom-9394.json").read_text())
for key in ("custom-rendezvous-server", "relay-server", "api-server", "key"):
    if not config.get(key):
        raise SystemExit(f"Missing required profile option: {key}")
(ROOT / "config").mkdir(exist_ok=True)
shutil.copyfile(PROFILE / "config/custom-9394.json", ROOT / "config/custom-9394.json")
copy_source("custom_9394.rs", "src/custom_9394.rs")
copy_source("bootstrap_9394.dart", "flutter/lib/mobile/bootstrap_9394.dart")
replace_once("src/lib.rs", "mod custom_server;", '#[cfg(target_os = "android")]\nmod custom_9394;\nmod custom_server;')
replace_once("src/flutter_ffi.rs", "    // core_main's load_custom_client does not work for flutter since it is only applied to its load_library in main.c", "    #[cfg(target_os = \"android\")]\n    crate::custom_9394::initialize();\n    // core_main's load_custom_client does not work for flutter since it is only applied to its load_library in main.c")
replace_once("flutter/lib/mobile/pages/home_page.dart", "import '../../models/state_model.dart';", "import '../../models/state_model.dart';\nimport '../bootstrap_9394.dart';")
replace_once("flutter/lib/mobile/pages/home_page.dart", "    super.initState();\n    initPages();", "    super.initState();\n    initPages();\n    WidgetsBinding.instance.addPostFrameCallback((_) => Bootstrap9394.start());")
replace_once("flutter/lib/models/server_model.dart", "    // Initial keyboard status is off on mobile\n    if (isMobile) {", "    // Android follows the actual accessibility service state.\n    if (isIOS) {")
kotlin = "flutter/android/app/src/main/kotlin/com/carriez/flutter_hbb/"
for file in ("MainActivity.kt", "BootReceiver.kt"):
    replace_once(kotlin + file, "getBoolean(KEY_START_ON_BOOT_OPT, false)", "getBoolean(KEY_START_ON_BOOT_OPT, true)")
replace_once(kotlin + "MainActivity.kt", '                "check_service" -> {', '                "9394_input_ready" -> result.success(InputService.isOpen)\n                "check_service" -> {')
settings = "flutter/lib/mobile/pages/settings_page.dart"
replace_once(settings, """      if (enableStartOnBoot) {
        if (!await canStartOnBoot()) {
          enableStartOnBoot = false;
          gFFI.invokeMethod(AndroidChannel.kSetStartOnBootOpt, false);
        }
      }
""", "")
replace_once(settings, """  Future<bool> checkAndUpdateStartOnBoot() async {
    if (!await canStartOnBoot() && _enableStartOnBoot) {
      _enableStartOnBoot = false;
      debugPrint(
          "checkAndUpdateStartOnBoot and set _enableStartOnBoot -> false");
      gFFI.invokeMethod(AndroidChannel.kSetStartOnBootOpt, false);
      return true;
    } else {
      return false;
    }
  }""", """  Future<bool> checkAndUpdateStartOnBoot() async {
    final value = await gFFI.invokeMethod(AndroidChannel.kGetStartOnBootOpt);
    if (_enableStartOnBoot == value) return false;
    _enableStartOnBoot = value;
    return true;
  }""")
replace_once("flutter/android/app/build.gradle", "signingConfig signingConfigs.release", "signingConfig signingConfigs.debug")


# v0.4 manual-test fixes. Each anchor must still match the reviewed upstream.
replace_once("src/flutter_ffi.rs", "        std::thread::spawn(move || start_server(true));", "        crate::custom_9394::initialize();\n        std::thread::spawn(move || start_server(true));")
replace_once(kotlin + "MainActivity.kt", '                "9394_input_ready" -> result.success(InputService.isOpen)', '                "9394_media_ready" -> result.success(MainService.isReady)\n                "9394_input_ready" -> result.success(InputService.isOpen)')
replace_once(kotlin + "MainActivity.kt", "    private fun requestMediaProjection() {", """    private var mediaProjectionRequestPending9394 = false

    private fun requestMediaProjection() {
        if (MainService.isReady || mediaProjectionRequestPending9394) return
        mediaProjectionRequestPending9394 = true""")
replace_once(kotlin + "MainActivity.kt", """        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQ_IMPORT_FILES) {""", """        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQ_INVOKE_PERMISSION_ACTIVITY_MEDIA_PROJECTION) {
            mediaProjectionRequestPending9394 = false
        }
        if (requestCode == REQ_IMPORT_FILES) {""")
replace_once("flutter/lib/models/server_model.dart", """      final res = await parent.target?.dialogManager
          .show<bool>((setState, close, context) {
        submit() => close(true);
        return CustomAlertDialog(
          title: Row(children: [
            const Icon(Icons.warning_amber_sharp,
                color: Colors.redAccent, size: 28),
            const SizedBox(width: 10),
            Text(translate("Warning")),
          ]),
          content: Text(translate("android_service_will_start_tip")),
          actions: [
            dialogButton("Cancel", onPressed: close, isOutline: true),
            dialogButton("OK", onPressed: submit),
          ],
          onSubmit: submit,
          onCancel: close,
        );
      });
      if (res == true) {
        startService();
      }""", """      await startService();""")
replace_once("src/server/connection.rs", """        // One-time means gone once it has let a peer in, not once that peer
        // leaves. This session's later logins come in on the password the
        // session remembers, so they are not affected.
        password::update_temporary_password();""", """        // 9394 Android keeps the displayed password until an explicit refresh.
        #[cfg(not(target_os = "android"))]
        password::update_temporary_password();""")
replace_once("src/server/connection.rs", """    fn check_update_temporary_password(&self, temporary_password_success: bool) {
        const MAX_CONSECUTIVE_FAILURES: i32 = 10;""", """    fn check_update_temporary_password(&self, temporary_password_success: bool) {
        // Independent login throttling / IP and prefix blocking remain unchanged.
        if cfg!(target_os = "android") {
            return;
        }
        const MAX_CONSECUTIVE_FAILURES: i32 = 10;""")
replace_once(kotlin + "MainService.kt", "        val restartCapture = wasCapturing || captureRestartPending", "        val restartCapture = true // 9394: capture immediately after genuine system authorization")
replace_once(kotlin + "MainService.kt", "    private lateinit var notificationBuilder: NotificationCompat.Builder", """    private lateinit var notificationBuilder: NotificationCompat.Builder
    private val connectionNoticeHandler9394 = Handler(Looper.getMainLooper())
    private val connectionNoticeTokens9394 = java.util.concurrent.ConcurrentHashMap<Int, Any>()""")
replace_once(kotlin + "MainService.kt", """        cancelNotification(clientID)
        val notification = notificationBuilder
            .setOngoing(false)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setContentTitle("$type ${translate("Established")}")
            .setContentText("$username - $peerId")
            .build()
        notificationManager.notify(getClientNotifyID(clientID), notification)""", """        cancelNotification(clientID)
        // A separate builder keeps connection-event state out of the foreground notice.
        val notification = NotificationCompat.Builder(this, notificationChannel)
            .setSmallIcon(R.mipmap.ic_stat_logo)
            .setOngoing(false)
            .setAutoCancel(true)
            .setDefaults(Notification.DEFAULT_ALL)
            .setOnlyAlertOnce(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setTimeoutAfter(3000L)
            .setContentTitle("$type ${translate("Established")}")
            .setContentText("$username - $peerId")
            .build()
        val token = Any()
        connectionNoticeTokens9394[clientID] = token
        notificationManager.notify(getClientNotifyID(clientID), notification)
        // API 25 ignores timeoutAfter, so explicitly cancel this event as well.
        connectionNoticeHandler9394.postDelayed({
            if (connectionNoticeTokens9394.remove(clientID, token)) {
                notificationManager.cancel(getClientNotifyID(clientID))
            }
        }, 3000L)""")
replace_once(kotlin + "MainService.kt", """    fun cancelNotification(clientID: Int) {
        notificationManager.cancel(getClientNotifyID(clientID))""", """    fun cancelNotification(clientID: Int) {
        connectionNoticeTokens9394.remove(clientID)
        notificationManager.cancel(getClientNotifyID(clientID))""")
replace_once(kotlin + "MainService.kt", """    private fun voiceCallRequestNotification(
        clientID: Int,
        type: String,
        username: String,
        peerId: String
    ) {
        val notification""", """    private fun voiceCallRequestNotification(
        clientID: Int,
        type: String,
        username: String,
        peerId: String
    ) {
        cancelNotification(clientID)
        val notification""")


copy_source("audit_ack_9394.rs", "src/audit_ack_9394.rs")
replace_once("src/lib.rs", "mod custom_9394;", 'mod custom_9394;\n#[cfg(target_os = "android")]\nmod audit_ack_9394;')
replace_once("src/server/connection.rs", """                            if text.trim().is_empty() {
                                return Ok(text);
                            }
                            let server_err""", """                            if text.trim().is_empty() {
                                return Ok(text);
                            }
                            #[cfg(target_os = "android")]
                            if crate::audit_ack_9394::is_legacy_success(&text) {
                                return Ok(text);
                            }
                            let server_err""")


replace_once("flutter/lib/mobile/pages/server_page.dart", "import 'home_page.dart';", "import 'home_page.dart';\nimport '../bootstrap_9394.dart';")
replace_once("flutter/lib/mobile/pages/server_page.dart", """            gFFI.serverModel.changeStatue(name, value);
            break;""", """            final wasMediaReady = gFFI.serverModel.mediaOk;
            gFFI.serverModel.changeStatue(name, value);
            if (name == "media" && value && !wasMediaReady) {
              Bootstrap9394.onMediaReady();
            }
            break;""")
replace_once(kotlin + "MainActivity.kt", "    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {", """    override fun getFlutterShellArgs(): io.flutter.embedding.engine.FlutterShellArgs {
        val args = super.getFlutterShellArgs()
        val x86Host = Build.SUPPORTED_ABIS.any { it == "x86" || it == "x86_64" }
        if (Build.VERSION.SDK_INT in 24..25 && x86Host) {
            // P026: avoid the emulator GLES/Houdini raster crash; ARM devices keep their GPU.
            args.add(io.flutter.embedding.engine.FlutterShellArgs.ARG_ENABLE_SOFTWARE_RENDERING)
            Log.i("9394Render", "Android 7 x86: software UI rendering enabled")
        }
        return args
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {""")

# Android 7.1 support must include native ABI and platform checks, not just manifest edits.
assert "minSdkVersion 22" in (ROOT / "flutter/android/app/build.gradle").read_text()
assert "--platform 21" in (ROOT / "flutter/ndk_arm.sh").read_text()
assert "VCPKG_CMAKE_SYSTEM_VERSION 21" in (ROOT / "res/vcpkg-triplets/arm-neon-android.cmake").read_text()
assert config["allow-numeric-one-time-password"] == "Y"
assert config["verification-method"] == "use-both-passwords"
assert 'getBoolean(KEY_START_ON_BOOT_OPT, false)' not in (ROOT / (kotlin + "BootReceiver.kt")).read_text()
(ROOT / "custom-9394-changes.json").write_text(json.dumps({"changed_paths": sorted(set(CHANGED)), "scope": "Android only; hbb_common unchanged"}, indent=2))
print("9394 Android source compatibility checks passed")
print("Changed runtime paths:", ", ".join(sorted(set(CHANGED))))
