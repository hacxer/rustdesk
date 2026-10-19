#!/usr/bin/env python3
"""Append only verified additional-platform assets to the existing formal release."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

TAG = "v1.5.0-9394-build9"
REPO = "hacxer/rustdesk"
OLD_APK = "2447958f38f0e6967343fd55ea25c229d608915e830c7c0059b206f1974e6b77"
CONFIG = "90e2e177cbca2bf4553a1d1f544c7fc57eed84894cf6f74fea20b729be2f1ffd"
BASE = "ece437c54f2a22da2e212b19ca2f84e8d45899fb"


def api(path, *args):
    return json.loads(subprocess.check_output(["gh", "api", "repos/" + REPO + "/" + path, *args], text=True))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert os.environ["GITHUB_REPOSITORY"] == REPO
r = api("releases/tags/" + TAG)
assert r["id"] == 417427248 and not r["draft"] and not r["prerelease"]
assert api("git/ref/tags/" + TAG)["object"]["sha"] == BASE
old_assets = {a["name"]: a for a in r["assets"]}
assert old_assets["armv7-signed.apk"]["digest"] == "sha256:" + OLD_APK
root = Path("dist")
expected = {"aarch64-signed.apk", "aarch64-SHA256SUMS", "aarch64-build-manifest.json", "aarch64-signature-verification.txt", "aarch64-apk-badging.txt", "x86_64.exe", "windows-SHA256SUMS", "windows-build-manifest.json", "windows-validation.json"}
assert {p.name for p in root.iterdir() if p.is_file()} == expected
for name in ["aarch64-build-manifest.json", "windows-build-manifest.json"]:
    m = json.loads((root / name).read_text())
    assert m["profile_sha256"] == CONFIG and m["baseline_profile_sha"] == BASE
    assert m["platform_extension_sha"] == os.environ["GITHUB_SHA"]
    assert m["source_run"] == os.environ["GITHUB_RUN_ID"]
    assert m["upstream_sha"] == "fada664df7a294d1d1a9ca3e7cd3637069122f17"
android = json.loads((root / "aarch64-build-manifest.json").read_text())
windows = json.loads((root / "windows-build-manifest.json").read_text())
assert android["apk_sha256"] == sha(root / "aarch64-signed.apk")
assert android["signature_v1"] and android["signature_v2"] and android["original_certificate_match"]
assert windows["sha256"] == sha(root / "x86_64.exe") and windows["authenticode"] == "UNSIGNED"
(root / "SHA256SUMS-extra").write_text("".join(sha(root / n) + "  " + n + "\n" for n in sorted(expected)))
expected.add("SHA256SUMS-extra")
for name in sorted(expected):
    p = root / name
    if name in old_assets:
        assert old_assets[name]["digest"] == "sha256:" + sha(p), "Refusing to overwrite different asset: " + name
    else:
        subprocess.run(["gh", "release", "upload", TAG, str(p), "--repo", REPO], check=True)
r = api("releases/tags/" + TAG)
assets = {a["name"]: a for a in r["assets"]}
for name in expected:
    assert assets[name]["state"] == "uploaded"
    assert assets[name]["size"] == (root / name).stat().st_size
    assert assets[name]["digest"] == "sha256:" + sha(root / name)
for name, old in old_assets.items():
    assert assets[name]["digest"] == old["digest"] and assets[name]["id"] == old["id"]
body = r["body"].replace("此版本仅包含ARM32 Android，不包含aarch64或Windows。", "此版本包含ARM32、ARM64 Android及Windows x64，分别下载对应附件。")
marker = "### v0.7 追加平台"
assert marker not in body, "Release notes already extended; inspect before editing"
body += "\n\n" + marker + "\n\n"
body += "- aarch64-signed.apk：Android arm64-v8a / ELF64 AArch64；版本1.5.0.9394 / 15011009，V1+V2及原证书校验通过。\n"
body += "- x86_64.exe：Windows AMD64完整Flutter自解压包，包含DLL与资源；Authenticode未签名。安装后沿用上游自动服务，便携运行不等同于安装开机服务。\n"
body += "- 两包与armv7使用相同上游SHA、build9公开配置和共用初始化模块；Windows新增入口适配与手动刷新临时密码行为。\n"
body += "- 基准定制提交：" + BASE + "；平台扩展提交：" + os.environ["GITHUB_SHA"] + "。\n"
body += "- [追加构建与校验](https://github.com/" + REPO + "/actions/runs/" + os.environ["GITHUB_RUN_ID"] + ")；摘要与独立清单见新增附件，原ARM32包和既有附件保持不变。\n"
body += "- Android ARM64与Windows完整设备运行/安装后重启验收仍待完成；T2真机验收仍为待完成。\n"
Path("release-update.json").write_text(json.dumps({"name": "RustDesk 9394 1.5.0 - Android ARM32/ARM64 + Windows x64 (build9)", "body": body, "draft": False, "prerelease": False, "make_latest": "true"}))
api("releases/" + str(r["id"]), "--method", "PATCH", "--input", "release-update.json")
final = api("releases/latest")
assert final["id"] == r["id"] and not final["draft"] and not final["prerelease"]
with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
    f.write("Additional platforms published and every uploaded SHA-256 verified.\n\n" + final["html_url"] + "\n\nWindows Authenticode: UNSIGNED. Device acceptance remains PENDING.\n")
print(final["html_url"])
