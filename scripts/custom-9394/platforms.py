#!/usr/bin/env python3
"""Extend the frozen build9 profile and verify additional release platforms."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

BASELINE = "ece437c54f2a22da2e212b19ca2f84e8d45899fb"
UPSTREAM = "fada664df7a294d1d1a9ca3e7cd3637069122f17"
CONFIG_HASH = "90e2e177cbca2bf4553a1d1f544c7fc57eed84894cf6f74fea20b729be2f1ffd"
ROOT = Path("upstream")
DIST = Path("dist")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace(path, old, new):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit("Platform anchor mismatch: " + path)
    p.write_text(text.replace(old, new), encoding="utf-8")


def baseline_check():
    assert subprocess.check_output(["git", "-C", "baseline", "rev-parse", "HEAD"], text=True).strip() == BASELINE
    assert subprocess.check_output(["git", "-C", "upstream", "rev-parse", "HEAD"], text=True).strip() == UPSTREAM
    assert digest("baseline/config/custom-9394.json") == CONFIG_HASH
    assert digest(ROOT / "config/custom-9394.json") == CONFIG_HASH
    assert digest(ROOT / "src/custom_9394.rs") == digest("baseline/scripts/custom-9394/source/custom_9394.rs")


def manifest(platform):
    return {
        "platform": platform, "upstream_sha": UPSTREAM,
        "submodules": subprocess.check_output(["git", "-C", "upstream", "submodule", "status", "--recursive"], text=True).splitlines(),
        "baseline_profile_sha": BASELINE, "platform_extension_sha": os.environ["GITHUB_SHA"],
        "profile_sha256": CONFIG_HASH,
        "shared_module_sha256": digest("baseline/scripts/custom-9394/source/custom_9394.rs"),
        "source_run": os.environ["GITHUB_RUN_ID"], "requirements": "v0.7 additional platforms; same build9 configuration",
        "device_validation": "PENDING: manual platform acceptance",
    }


def pe64(path):
    b = Path(path).read_bytes()
    assert b[:2] == b"MZ", str(path)
    p = struct.unpack_from("<I", b, 0x3c)[0]
    assert b[p:p+4] == b"PE\0\0"
    assert struct.unpack_from("<H", b, p+4)[0] == 0x8664, str(path)
    assert struct.unpack_from("<H", b, p+24)[0] == 0x20b, str(path)


command = sys.argv[1]
if command == "normalize-windows":
    for name in ["config/custom-9394.json", "scripts/custom-9394/source/custom_9394.rs", "scripts/custom-9394/source/bootstrap_9394.dart", "scripts/custom-9394/source/audit_ack_9394.rs"]:
        data = subprocess.check_output(["git", "-C", "baseline", "show", "HEAD:" + name])
        (Path("baseline") / name).write_bytes(data)
    Path("config/custom-9394.json").write_bytes(Path("baseline/config/custom-9394.json").read_bytes())
    assert digest("baseline/config/custom-9394.json") == CONFIG_HASH
    print("Canonical frozen Git bytes restored and verified")
elif command == "prepare-windows":
    baseline_check()
    replace("src/lib.rs", '#[cfg(target_os = "android")]\nmod custom_9394;', '#[cfg(any(target_os = "android", target_os = "windows"))]\nmod custom_9394;')
    replace("src/lib.rs", '#[cfg(target_os = "android")]\nmod audit_ack_9394;', '#[cfg(any(target_os = "android", target_os = "windows"))]\nmod audit_ack_9394;')
    replace("src/flutter_ffi.rs", '    #[cfg(target_os = "android")]\n    crate::custom_9394::initialize();', '    #[cfg(any(target_os = "android", target_os = "windows"))]\n    crate::custom_9394::initialize();')
    replace("src/core_main.rs", '    crate::load_custom_client();', '    crate::load_custom_client();\n    #[cfg(target_os = "windows")]\n    crate::custom_9394::initialize();')
    replace("src/server/connection.rs", '#[cfg(not(target_os = "android"))]\n        password::update_temporary_password();', '#[cfg(not(any(target_os = "android", target_os = "windows")))]\n        password::update_temporary_password();')
    replace("src/server/connection.rs", 'if cfg!(target_os = "android") {\n            return;', 'if cfg!(any(target_os = "android", target_os = "windows")) {\n            return;')
    replace("src/server/connection.rs", '#[cfg(target_os = "android")]\n                            if crate::audit_ack_9394::is_legacy_success', '#[cfg(any(target_os = "android", target_os = "windows"))]\n                            if crate::audit_ack_9394::is_legacy_success')
    assert 'start= auto' in (ROOT / "src/platform/windows.rs").read_text(encoding="utf-8")
    replace("flutter/pubspec.yaml", "version: 1.5.0+68", "version: 1.5.0+9394")
    print("Windows core/service and Flutter entry points initialized; shared profile unchanged")
elif command == "arm64-verifier":
    baseline_check()
    text = Path("baseline/scripts/custom-9394/verify.py").read_text()
    text = text.replace("armv7-signed.apk", "aarch64-signed.apk").replace("armeabi-v7a", "arm64-v8a")
    text = text.replace("data[4] == 1", "data[4] == 2").replace('data, 18)[0] == 40', 'data, 18)[0] == 183')
    Path("verify-arm64-generated.py").write_text(text)
elif command == "finish-arm64":
    m = json.loads((DIST / "build-manifest.json").read_text())
    assert m["abi"] == "arm64-v8a" and m["signature_v1"] and m["signature_v2"]
    assert m["profile_sha256"] == CONFIG_HASH
    m.update(manifest("android-aarch64"))
    m["device_validation"] = "PENDING: Android ARM64 manual validation; not a SUNMI T2 ARM32 build"
    (DIST / "aarch64-build-manifest.json").write_text(json.dumps(m, indent=2))
    (DIST / "build-manifest.json").unlink()
    for a, b in [("SHA256SUMS", "aarch64-SHA256SUMS"), ("signature-verification.txt", "aarch64-signature-verification.txt"), ("apk-badging.txt", "aarch64-apk-badging.txt")]:
        (DIST / a).rename(DIST / b)
    (DIST / "previous-cert.txt").unlink(missing_ok=True)
elif command == "verify-windows":
    baseline_check()
    bundle = ROOT / "rustdesk"
    files = [p for p in bundle.rglob("*") if p.is_file()]
    required = ["rustdesk.exe", "librustdesk.dll", "flutter_windows.dll", "dylib_virtual_display.dll", "WindowInjection.dll", "data/icudtl.dat", "data/flutter_assets/AssetManifest.bin"]
    for name in required:
        assert (bundle / name).is_file(), name
    for p in files:
        if p.suffix.lower() in [".exe", ".dll"]:
            pe64(p)
    pe64(DIST / "x86_64.exe")
    blob = (ROOT / "libs/portable/data.bin").read_bytes()
    assert len(blob) > 1000000 and blob[:8] == b"rustdesk"
    native = (bundle / "librustdesk.dll").read_bytes()
    for value in [b"rustdesk.9394.cn", b"http://rustdesk.9394.cn:21114", b"allow-numeric-one-time-password", b"9394-password-initialized-v1"]:
        assert value in native, "Missing embedded configuration marker"
    m = manifest("windows-x86_64")
    m.update(file="x86_64.exe", sha256=digest(DIST / "x86_64.exe"), bytes=(DIST / "x86_64.exe").stat().st_size,
             version="1.5.0.9394", authenticode="UNSIGNED", package="self-extracting complete Flutter bundle", 
             toolchains={"rust": "1.75.0", "flutter": "3.24.5", "vcpkg": "9e593bb18ea69cc5095e012465dcd675a822ed0d"},
             payload=[{"path": str(p.relative_to(bundle)).replace("\\", "/"), "sha256": digest(p), "bytes": p.stat().st_size} for p in files])
    (DIST / "windows-build-manifest.json").write_text(json.dumps(m, indent=2))
    (DIST / "windows-SHA256SUMS").write_text(m["sha256"] + "  x86_64.exe\n")
    (DIST / "windows-validation.json").write_text(json.dumps({"pe_amd64": True, "complete_bundle": True, "shared_config_hash_match": True, "authenticode": "UNSIGNED", "runtime_acceptance": "PENDING"}, indent=2))
    print("AMD64 PE, complete bundle and embedded profile checks passed")
else:
    raise SystemExit("Unknown platform command")
