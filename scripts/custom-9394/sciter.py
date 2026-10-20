#!/usr/bin/env python3
"""Prepare, verify and publish the frozen 9394 Windows x86 Sciter package."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

BASE = "ece437c54f2a22da2e212b19ca2f84e8d45899fb"
UPSTREAM = "fada664df7a294d1d1a9ca3e7cd3637069122f17"
CONFIG = "90e2e177cbca2bf4553a1d1f544c7fc57eed84894cf6f74fea20b729be2f1ffd"
SCITER = "674e07d3066ca9a92ced3816203ab6b652629d1e"
SDK = "1c6b588cd090506d4b044dead06d7eae6e2235b7"
REPO = "hacxer/rustdesk"
TAG = "v1.5.0-9394-build9"
ROOT = Path("upstream")
DIST = Path("dist")
FILES = {"x86-sciter.exe", "x86-sciter-build-manifest.json", "x86-sciter-validation.json", "x86-sciter-SHA256SUMS"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    subprocess.run(list(args), check=True)


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def pe(path):
    b = Path(path).read_bytes()
    assert b[:2] == b"MZ", str(path)
    p = struct.unpack_from("<I", b, 0x3c)[0]
    assert b[p:p+4] == b"PE\0\0", str(path)
    return struct.unpack_from("<H", b, p+4)[0], struct.unpack_from("<H", b, p+24)[0]


def same_profile():
    assert git("baseline", "rev-parse", "HEAD") == BASE
    assert git(ROOT, "rev-parse", "HEAD") == UPSTREAM
    assert sha("baseline/config/custom-9394.json") == CONFIG
    assert sha(ROOT / "config/custom-9394.json") == CONFIG
    assert sha(ROOT / "src/custom_9394.rs") == sha("baseline/scripts/custom-9394/source/custom_9394.rs")


def api(path, *args):
    return json.loads(subprocess.check_output(["gh", "api", "repos/" + REPO + "/" + path, *args], text=True))


def prepare():
    run(sys.executable, "scripts/custom-9394/platforms.py", "normalize-windows")
    run(sys.executable, "baseline/scripts/custom-9394/prepare.py", "upstream")
    run(sys.executable, "scripts/custom-9394/platforms.py", "prepare-windows")
    same_profile()
    cargo = ROOT / "Cargo.toml"
    content = cargo.read_text(encoding="utf-8")
    anchor = 'sciter-rs = { git = "https://github.com/rustdesk-org/rust-sciter", branch = "dyn" }'
    assert content.count(anchor) == 1
    cargo.write_text(content.replace(anchor, 'sciter-rs = { git = "https://github.com/rustdesk-org/rust-sciter", branch = "dyn_x86" }'), encoding="utf-8")
    core = (ROOT / "src/core_main.rs").read_text(encoding="utf-8")
    assert core.index("crate::custom_9394::initialize();") < core.index("crate::platform::windows::bootstrap()")
    main = (ROOT / "src/main.rs").read_text(encoding="utf-8")
    assert "crate::core_main::core_main()" in main and "ui::start(args)" in main
    assert 'start= auto' in (ROOT / "src/platform/windows.rs").read_text(encoding="utf-8")
    assert 'fn update_temporary_password' in (ROOT / "src/ui.rs").read_text(encoding="utf-8")
    print("Frozen profile and Sciter/core/service entry points verified")


def verify():
    import brotli
    same_profile()
    bundle = ROOT / "Release"
    required = {"rustdesk.exe", "sciter.dll"}
    paths = [p for p in bundle.rglob("*") if p.is_file()]
    assert required <= {p.name for p in paths}
    assert pe(bundle / "rustdesk.exe") == (0x14c, 0x10b)
    assert pe(bundle / "sciter.dll") == (0x14c, 0x10b)
    assert pe(DIST / "x86-sciter.exe") == (0x14c, 0x10b)
    native = (bundle / "rustdesk.exe").read_bytes()
    for marker in [b"rustdesk.9394.cn", b"http://rustdesk.9394.cn:21114", b"allow-numeric-one-time-password", b"9394-password-initialized-v1"]:
        assert marker in native, "Missing embedded configuration marker"
    lock = (ROOT / "Cargo.lock").read_text(encoding="utf-8")
    assert "branch=dyn_x86#" + SCITER in lock
    inline = ROOT / "src/ui/inline.rs"
    assert inline.is_file() and inline.stat().st_size > 10000
    assert b"flutter_windows.dll" not in {p.name.encode() for p in paths}
    blob = (ROOT / "libs/portable/data.bin").read_bytes()
    assert blob[:8] == b"rustdesk" and blob in (DIST / "x86-sciter.exe").read_bytes()
    offset = 8
    packaged = {}
    while blob[offset:offset+8] != b"rustdesk":
        length = int.from_bytes(blob[offset:offset+4], "big")
        offset += 4
        name = blob[offset:offset+length].decode("utf-8").replace("\\", "/").removeprefix("./")
        offset += length
        length = int.from_bytes(blob[offset:offset+4], "big")
        offset += 4
        raw = brotli.decompress(blob[offset:offset+length])
        offset += length
        md5 = blob[offset:offset+32].decode("ascii")
        offset += 32
        assert hashlib.md5(raw).hexdigest() == md5
        assert name not in packaged and ".." not in Path(name).parts
        target = bundle / name
        assert target.is_file() and target.read_bytes() == raw, name
        packaged[name] = hashlib.sha256(raw).hexdigest()
    assert blob[offset+8:].decode("utf-8").replace("\\", "/") == "./rustdesk.exe"
    assert set(packaged) == {p.relative_to(bundle).as_posix() for p in paths}
    payload = []
    for p in paths:
        relative = p.relative_to(bundle).as_posix()
        arch = None
        if p.suffix.lower() in {".exe", ".dll", ".sys"}:
            machine, optional = pe(p)
            assert (machine, optional) == (0x14c, 0x10b) or (relative.startswith("usbmmidd_v2/") and (machine, optional) == (0x8664, 0x20b)), relative
            arch = "I386" if machine == 0x14c else "AMD64 auxiliary driver/helper"
        payload.append({"path": relative, "sha256": sha(p), "bytes": p.stat().st_size, "pe": arch})
    validation = json.loads((DIST / "x86-sciter-validation.json").read_text(encoding="utf-8-sig"))
    assert validation["version_smoke"] == "PASS" and validation["authenticode"] == "NotSigned"
    validation.update(pe_i386=True, complete_sciter_bundle=True, embedded_payload_verified=True, shared_config_hash_match=True, runtime_acceptance="PENDING: manual device, installation/service/reboot and remote session checks")
    (DIST / "x86-sciter-validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    m = {"platform": "windows-x86-sciter", "file": "x86-sciter.exe", "sha256": sha(DIST / "x86-sciter.exe"), "bytes": (DIST / "x86-sciter.exe").stat().st_size,
         "upstream_sha": UPSTREAM, "baseline_profile_sha": BASE, "profile_sha256": CONFIG,
         "shared_module_sha256": sha(ROOT / "src/custom_9394.rs"), "platform_extension_sha": os.environ["GITHUB_SHA"], "source_run": os.environ["GITHUB_RUN_ID"],
         "requirements": "v0.8; frozen build9 defaults", "authenticode": "UNSIGNED", "package": "self-extracting Sciter UI complete bundle", "product_version": "1.5.0",
         "submodules": git(ROOT, "submodule", "status", "--recursive").splitlines(), "cargo_lock_sha256": sha(ROOT / "Cargo.lock"), "inline_ui_sha256": sha(inline),
         "toolchains": {"rust": "nightly-2023-10-13-i686-pc-windows-msvc", "llvm": "15.0.6 x86", "vcpkg": "9e593bb18ea69cc5095e012465dcd675a822ed0d", "features": "inline,vram,hwcodec"},
         "sciter_rs_commit": SCITER, "sciter_sdk_commit": SDK, "sciter_dll_sha256": sha(bundle / "sciter.dll"), "usbmmidd_archive_sha256": sha(ROOT / "usbmmidd_v2.zip"), "payload": payload,
         "device_validation": "PENDING: Windows x86/x64 manual acceptance; old Windows versions not proven"}
    (DIST / "x86-sciter-build-manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    checks = "".join(sha(DIST / n) + "  " + n + "\n" for n in sorted(FILES - {"x86-sciter-SHA256SUMS"}))
    (DIST / "x86-sciter-SHA256SUMS").write_text(checks, encoding="utf-8")
    print("I386 PE32, pinned Sciter DLL, exact embedded bundle, shared profile and smoke checks passed")


def publish():
    assert os.environ["GITHUB_REPOSITORY"] == REPO
    assert {p.name for p in DIST.iterdir() if p.is_file()} == FILES
    m = json.loads((DIST / "x86-sciter-build-manifest.json").read_text())
    assert m["platform"] == "windows-x86-sciter" and m["profile_sha256"] == CONFIG and m["baseline_profile_sha"] == BASE and m["upstream_sha"] == UPSTREAM
    assert m["source_run"] == os.environ["GITHUB_RUN_ID"] and m["platform_extension_sha"] == os.environ["GITHUB_SHA"]
    assert m["sha256"] == sha(DIST / "x86-sciter.exe") and m["bytes"] == (DIST / "x86-sciter.exe").stat().st_size
    assert m["authenticode"] == "UNSIGNED" and m["sciter_rs_commit"] == SCITER and m["sciter_sdk_commit"] == SDK
    assert pe(DIST / "x86-sciter.exe") == (0x14c, 0x10b)
    validation = json.loads((DIST / "x86-sciter-validation.json").read_text())
    assert all(validation[k] is True for k in ["pe_i386", "complete_sciter_bundle", "embedded_payload_verified", "shared_config_hash_match"])
    assert validation["version_smoke"] == "PASS" and validation["authenticode"] == "NotSigned"
    assert (DIST / "x86-sciter-SHA256SUMS").read_text() == "".join(sha(DIST / n) + "  " + n + "\n" for n in sorted(FILES - {"x86-sciter-SHA256SUMS"}))
    r = api("releases/tags/" + TAG)
    assert r["id"] == 417427248 and not r["draft"] and not r["prerelease"]
    assert api("releases/latest")["id"] == r["id"]
    assert api("git/ref/tags/" + TAG)["object"]["sha"] == BASE
    old = {a["name"]: a for a in r["assets"]}
    original = {"armv7-signed.apk": "2447958f38f0e6967343fd55ea25c229d608915e830c7c0059b206f1974e6b77", "aarch64-signed.apk": "e81eeb67fbe76ba34a0727aeedee312188562b677605dc3126cfa3a55aef7e7a", "x86_64.exe": "71b5e42c75cc7da35204b950c7f6f853e533c814b2607b805d2374b95ffe684b"}
    for n, expected in original.items():
        assert old[n]["digest"] == "sha256:" + expected
    for n in sorted(FILES):
        if n in old:
            assert old[n]["digest"] == "sha256:" + sha(DIST / n), "Refusing different existing asset: " + n
        else:
            run("gh", "release", "upload", TAG, str(DIST / n), "--repo", REPO)
    current = api("releases/tags/" + TAG)
    assets = {a["name"]: a for a in current["assets"]}
    for n in FILES:
        assert assets[n]["state"] == "uploaded" and assets[n]["size"] == (DIST / n).stat().st_size
        assert assets[n]["digest"] == "sha256:" + sha(DIST / n)
    for n, a in old.items():
        assert (assets[n]["id"], assets[n]["size"], assets[n]["digest"]) == (a["id"], a["size"], a["digest"])
    marker = "### v0.8 Windows x86 Sciter"
    body = current["body"]
    assert marker not in body, "Already published; inspect release before another build"
    body += "\n\n" + marker + "\n\n- x86-sciter.exe：Windows 32位I386/PE32、Sciter旧版UI完整自解压包，主程序及Sciter DLL均32位；包含上游辅助驱动资源，Authenticode未签名。\n"
    body += "- 沿用build9服务器、公钥、默认选项及共用初始化模块；新扩展提交 " + m["platform_extension_sha"] + "，来源及校验 [Actions " + m["source_run"] + "](https://github.com/" + REPO + "/actions/runs/" + m["source_run"] + ")。\n"
    body += "- SHA-256：" + m["sha256"] + "；字节数：" + str(m["bytes"]) + "；独立manifest、摘要及验证报告见附件。\n"
    body += "- 版本命令冒烟、PE32、完整内嵌payload及配置检查通过；实际远控、安装/服务/重启和旧Windows兼容待验收，不能替代T2 Android验收。便携运行不自动安装开机服务。既有包、标签及附件保持不变。\n"
    Path("sciter-release-update.json").write_text(json.dumps({"name": "RustDesk 9394 1.5.0 - Android ARM32/ARM64 + Windows x64/x86 Sciter (build9)", "body": body, "draft": False, "prerelease": False, "make_latest": "true"}))
    api("releases/" + str(r["id"]), "--method", "PATCH", "--input", "sciter-release-update.json")
    final = api("releases/latest")
    assert final["id"] == r["id"] and not final["draft"] and not final["prerelease"]
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write("x86 Sciter published; all new server digests and existing assets verified.\n\n" + final["html_url"] + "\n\nSHA-256: " + m["sha256"] + "\n\nWindows Authenticode: UNSIGNED. Device acceptance: PENDING.\n")
    print(final["html_url"])


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify, "publish": publish}[sys.argv[1]]()
