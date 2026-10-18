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
replace_once("src/flutter_ffi.rs", "    // core_main's load_custom_client does not work for flutter since it is only applied to its load_library in main.c", '    #[cfg(target_os = "android")]\n    crate::custom_9394::initialize();\n    // core_main's load_custom_client does not work for flutter since it is only applied to its load_library in main.c')
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
