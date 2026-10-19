import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:flutter_hbb/consts.dart';
import 'package:flutter_hbb/models/platform_model.dart';

class Bootstrap9394 extends WidgetsBindingObserver {
  static Bootstrap9394? _instance;
  bool _busy = false;
  bool _resumePending = false;
  bool _askedInput = false;
  bool _askedBattery = false;
  bool _askedOverlay = false;
  bool _attemptedMedia = false;

  static void start() {
    if (!isAndroid || _instance != null || bind.isOutgoingOnly()) return;
    final instance = Bootstrap9394();
    _instance = instance;
    WidgetsBinding.instance.addObserver(instance);
    instance._continueStartup();
  }

  static void onMediaReady() {
    _instance?._continueStartup();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _continueStartup();
  }

  Future<void> _continueStartup() async {
    if (_busy) {
      _resumePending = true;
      return;
    }
    if (bind.mainGetLocalOption(key: '9394-auto-start') == 'N') return;
    _busy = true;
    try {
      await gFFI.invokeMethod('check_service');
      await gFFI.serverModel.checkAndroidPermission();
      final mediaReady = await gFFI.invokeMethod('9394_media_ready') == true;
      if (!_attemptedMedia) {
        _attemptedMedia = true;
        // Start first; optional boot optimizations must not block capture authorization.
        if (!mediaReady || !gFFI.serverModel.isStart) {
          await gFFI.serverModel.startService();
          return;
        }
      }
      // Cancellation/stop never causes an automatic authorization request loop.
      if (!mediaReady || !gFFI.serverModel.isStart) return;
      await gFFI.invokeMethod('start_capture');
      final inputReady = await gFFI.invokeMethod('9394_input_ready') == true;
      if (!inputReady && !_askedInput) {
        _askedInput = true;
        final context = globalKey.currentContext;
        if (context != null) {
          final open = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('RustDesk Input'),
              content: const Text('请在系统无障碍设置中开启 RustDesk Input，以允许远程输入控制。开启后返回 RustDesk，应用将自动继续启动服务。'),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context, false), child: Text(translate('Cancel'))),
                TextButton(onPressed: () => Navigator.pop(context, true), child: Text(translate('Open System Setting'))),
              ],
            ),
          );
          if (open == true) {
            AndroidPermissionManager.startAction(kActionAccessibilitySettings);
            return;
          }
        }
      }
      final boot = await gFFI.invokeMethod('get_start_on_boot_opt') == true;
      if (boot && androidVersion >= 23) {
        final batteryGranted = await AndroidPermissionManager.check(
            kRequestIgnoreBatteryOptimizations);
        final batteryPrompted = bind.mainGetLocalOption(
                key: '9394-battery-prompted-v1') ==
            'Y';
        if (!_askedBattery && !batteryGranted && !batteryPrompted) {
          _askedBattery = true;
          // Remember the request, never pretend it granted the OS exemption.
          // A denied/cancelled request can still be granted manually in Settings.
          bind.mainSetLocalOption(key: '9394-battery-prompted-v1', value: 'Y');
          await gFFI.invokeMethod('request_permission', kRequestIgnoreBatteryOptimizations);
          return;
        }
        if (!_askedOverlay && !await AndroidPermissionManager.check(kSystemAlertWindow)) {
          _askedOverlay = true;
          await gFFI.invokeMethod('request_permission', kSystemAlertWindow);
          return;
        }
      }
    } catch (error) {
      debugPrint('9394 startup failed: $error');
      showToast('启动未完成，请在屏幕共享页面检查系统授权并重试。');
    } finally {
      _busy = false;
      if (_resumePending) {
        _resumePending = false;
        Future.microtask(_continueStartup);
      }
    }
  }
}
