# 9394 Android 验收记录

需求基线：[v0.3](requirements.zh-CN.md)。所有产品源码适配、工具链安装及编译均在 GitHub Actions 完成；本地仅使用现有 ADB 和用户已安装的雷电模拟器做运行验收。

## 2026-10-19 首轮开发

- 上游：RustDesk 1.5.0，提交 fada664df7a294d1d1a9ca3e7cd3637069122f17；每次产物以 build-manifest.json 的实际值为准。
- 首轮：[Actions #1](https://github.com/hacxer/rustdesk/actions/runs/39144255352)，定制提交 599d5e8d8b6dccff71c1547b5276c0c9179eb1cf。签名 Secrets / 既有 keystore SHA-256 预检、Python 编译、补丁匹配、锁定依赖和桥接生成通过。Flutter analyzer 报 await_only_futures，按需求 P015 先登记后修复；未产出 APK，未执行安装。
- 第二轮：[Actions #2](https://github.com/hacxer/rustdesk/actions/runs/39144947641)，定制提交 32870ac8035083c357bac237f04ccfc34d294598。运行中，尚不能标记编译或签名通过。

## 当前测试设备

| 项目 | 读取结果 |
| --- | --- |
| 用户指定环境 | 已安装的雷电模拟器 5 |
| ADB | 127.0.0.1:5555 |
| Android | 7.1.2 / API 25 |
| 型号报告 | PCRT00 |
| ABI | x86,armeabi-v7a,armeabi |
| MemTotal | 3629260 kB，约 3.46 GiB |
| 现有 RustDesk | 未发现安装包 com.carriez.flutter_hbb |

模拟器通过 ARM 兼容层运行 armv7，与商米 T2 的 ARM 硬件、2GB 内存及商米固件不同，不能替代真机验证。另一个已连接的 Galaxy Note9 不属于本轮指定测试设备。

## 待执行

- APK ABI / ELF32 / minSdk 检查、V1 + V2 校验、新旧签名证书一致性、SHA-256。
- 雷电 Android 7.1 安装与冷启动；自动服务、系统投屏确认、RustDesk Input 引导及返回后检测；取消/拒绝不循环，主动停止后不立即拉起。
- 四项服务器、六位数字密码、固定密码、IP 直连、开机选项的默认与用户修改保留。
- 远控画面、输入、文件、双向剪贴板、断线重连和重启；逐项如实记录，不以开关状态代替端到端功能。
- 商米 T2 真机资源、30 分钟会话及固件差异：待设备验收。
