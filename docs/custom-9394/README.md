# RustDesk 9394 GitHub 构建入口

- [需求与问题记录](requirements.zh-CN.md)
- [构建及设备验收](validation.md)
- [armv7 Actions](https://github.com/hacxer/rustdesk/actions/workflows/custom-9394-armv7.yml)

## 首阶段：armv7

在 Actions 选择 `9394 armv7 - SUNMI T2 Android 7.1` → `Run workflow`，分支选 `master`；`Upstream tag or SHA` 填上游正式 tag（首版为 `1.5.0`）或已审查的完整提交 SHA。

工作流在 GitHub runner 中检出该版本与子模块，严格匹配并应用本仓库的定制适配，然后编译。上游变化导致适配锚点或 Android 7.1 前置条件不匹配时会失败，必须先把问题、日志和验收标准加入需求文档，再改配置/适配脚本；不能静默跳过补丁。

成功后下载 `armv7-signed-9394-运行编号` artifact ZIP，内含 `armv7-signed.apk`、`SHA256SUMS`、`build-manifest.json`、签名校验和 APK 信息。只有签名和 ABI 检查通过才会上传这个产物；失败时仅提供不含秘密的诊断清单。

`build-manifest.json` 记录真实上游 SHA、递归子模块、定制提交、配置摘要、工具链、APK 摘要及证书指纹。所有运行状态以 Actions 实际结果为准。产物的商米 T2 验收默认标记 PENDING，不能因构建绿色就改成兼容通过。

## 签名与密码

复用仓库 Secrets：`ANDROID_KEYSTORE_BASE64`、`ANDROID_KEYSTORE_PASSWORD`、`ANDROID_KEY_ALIAS`、`ANDROID_KEY_PASSWORD`、`RUSTDESK_PRESET_PASSWORD`。工作流检查旧 keystore 的约定摘要，并比较旧 APK 与新 APK 的证书；固定密码仅经编译环境注入。不可将私钥或密码加入源码、日志、artifact 或 Release。

## 上游升级与后续平台

更新前先修改需求/问题记录及来源版本，再调整适配，先单独构建并验收 armv7；同一批次的其他平台必须使用相同的上游真实 SHA 和配置。定制适配保存在本仓库独立文件中，无需在本地安装 Rust、Flutter 或 Android 构建工具。

当前只实施 armv7 入口。aarch64、Windows 和自动升级 PR 入口待首阶段验收后开发；没有启用定时任务，也没有自动发布未经设备验收的 Release。
