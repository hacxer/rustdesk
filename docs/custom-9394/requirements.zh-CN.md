# RustDesk 9394 定制客户端：需求与实施方案

- 版本：0.8，2026-10-20（Asia/Shanghai；新增Windows x86 Sciter）
- 仓库：https://github.com/hacxer/rustdesk
- 状态：v0.7三平台已发布；v0.8新增Windows 32位Sciter构建中，沿用build9配置，原附件不变。T2及新增平台完整设备验收仍待完成。
- 用户消息为需求来源；截图用于核对参数，旧工作流用于分析现状，不自动扩展本次需求。

## 1. 需求清单

| 编号 | 需求 | 约定 |
| --- | --- | --- |
| R01 | 跟进上游最新版 | 首版以当前最新稳定版 1.5.0 为基线；另提供明确指定 master 提交的测试渠道 |
| R02 | ID 服务器 | rustdesk.9394.cn |
| R03 | 中继服务器 | rustdesk.9394.cn |
| R04 | API 服务器 | http://rustdesk.9394.cn:21114 |
| R05 | 公钥 | 6SM+NeAH25BBbI3wLINUrc56GJsImMLWvRTIsQL6fYQ= |
| R06 | 允许远程修改配置 | 新安装默认开启 |
| R07 | 一次性密码 | 纯数字 6 位；连接成功、断开及重连后保持不变，仅用户点击刷新时更换（v0.4 调整） |
| R08 | 固定密码 | 使用用户本次指定的值；由 GitHub Secret RUSTDESK_PRESET_PASSWORD 注入，不在公开文档或日志记录明文 |
| R09 | 验证方式 | 临时密码和固定密码均可使用 |
| R10 | IP 直接访问 | 新安装默认开启；实际连接仍需网络和防火墙允许 |
| R11 | 默认开机启动服务 | Windows 完成安装后自动启动服务；Android 默认开启启动意愿，按系统权限和版本限制启动 |
| R12 | 全程 GitHub | 需求、源码编辑、静态检查、编译、签名与打包均在 GitHub/Actions；雷电运行验收由用户手动执行，不在用户电脑安装编译工具 |
| R13 | 先方案再开发 | 方案提交并供用户评审后进入代码开发 |
| R14 | 文档先于代码 | 每个问题先登记需求、复现和验收标准，再修改代码 |
| R15 | armv7 优先 | 首先仅构建 armv7-signed.apk；通过签名、ABI、配置检查及设备验收后再构建 aarch64-signed.apk 和 x86_64.exe |
| R16 | 沿用 Android 签名 | 使用用户提供的旧证书材料，核对旧 APK 签名指纹，保持兼容包名并提高 versionCode |
| R17 | 商米 T2 兼容 | armv7-signed.apk 必须支持用户指定的商米 T2：Android 7.1、2GB RAM、16GB 存储；作为首批必测设备，未通过真机验收不标记支持 |
| R18 | Android 打开即启动服务 | 正常打开 APP 后默认自动执行启动服务流程；所需授权齐备时自动运行，缺少授权时发起系统请求或引导，完成后自动继续 |
| R19 | Android 默认功能权限 | 默认启用屏幕录制、输入控制、传输文件和允许同步剪贴板；分别检查应用开关、系统授权及实际功能，不能只把开关显示为开启 |
| R20 | armv7 APK 必带 V1 签名 | armv7-signed.apk 为 armeabi-v7a（32 位），必须包含并验证通过 V1（JAR）签名，兼容 Android 7.1；同时保留 V2 签名 |
| R21 | RustDesk Input 无障碍 | 已由用户启用时自动连接并使用 RustDesk Input；未开启时主动引导用户进入系统无障碍设置，开启并返回后自动复查与恢复服务 |

“默认”是新安装或尚未明确设置时的初始值，不在每次启动时重置用户设置。保留非空自定义服务器和用户后来修改的开关。固定密码只初始化一次，用户修改或清除后，重启和升级不恢复初始值；若未来需要强制锁定，应先修改本文。

统一预置密码由所有设备共用；二进制不能可靠保密其预置值。Secrets 用于避免公开仓库和日志额外泄露，不代表可防止二进制分析。

## 2. 本次源码核对基线

| 项目 | SHA / 版本 |
| --- | --- |
| 最新稳定版 | 1.5.0 |
| 稳定版提交 | fada664df7a294d1d1a9ca3e7cd3637069122f17 |
| 稳定版 hbb_common 子模块 | 229b904508364c8997aad0fb5af57effac859f60 |
| 上游 master（核对时） | 53996e3c404ea5083df0775057e4149e49102084 |
| master 的 hbb_common 子模块 | 5d52530b636fb296a324260b074780cf559e0093 |
| 用户仓库 master（本文提交前） | 85fdd602a941afcc2980b51ab53c7fc8f165cae1 |

每次构建只解析一次版本，冻结真实 SHA，各平台使用相同来源。构建清单记录父仓库、子模块、定制补丁、配置摘要及工具链版本，不能只更改文件名或版本字符串。

来源：[稳定版](https://github.com/rustdesk/rustdesk/releases/tag/1.5.0)、[稳定版提交](https://github.com/rustdesk/rustdesk/commit/fada664df7a294d1d1a9ca3e7cd3637069122f17)、[master 提交](https://github.com/rustdesk/rustdesk/commit/53996e3c404ea5083df0775057e4149e49102084)。

## 3. 参数配置位置与实现依据

### 3.1 实际配置键

| 界面/行为 | 配置键 | 初始值 |
| --- | --- | --- |
| ID 服务器 | custom-rendezvous-server | rustdesk.9394.cn |
| 中继服务器 | relay-server | rustdesk.9394.cn |
| API 服务器 | api-server | http://rustdesk.9394.cn:21114 |
| Key | key | R05 中的公钥 |
| 允许远程修改配置 | allow-remote-config-modification | Y |
| 纯数字一次性密码 | allow-numeric-one-time-password | Y |
| 一次性密码长度 | temporary-password-length | 6 |
| 允许 IP 直接访问 | direct-server | Y |
| 服务停止标记 | stop-service | N（新安装） |
| 密码验证方式 | verification-method | 保留上游两类密码均可的默认行为 |

布尔值按上游 Y/N 语义设置，不能任意替换成字符串 true/false。纯数字密码已有专用选项，不修改随机密码通用字符表，以免影响盐和其他密码生成。

### 3.2 核心源码

- 1.5.0 的客户端选项入口是 libs/base/src/config/keys.rs，重导出 hbb_common 中少量共用键。
- 配置读取、优先级、持久化位于 libs/hbb_common/src/config.rs。
- 优先级：OVERWRITE_SETTINGS 强制覆盖 > CONFIG2.options 设备持久化设置 > DEFAULT_SETTINGS 默认设置。
- 本项目使用可修改的默认值，优先写入 DEFAULT_SETTINGS，不把普通服务器参数和开关锁入 OVERWRITE_SETTINGS。
- 固定密码不是普通 options 中增加 password 即可。应在正确配置目录及进程上下文调用 Config::set_permanent_password，并检查写入结果；桌面服务场景还须核对 IPC 确认与密码同步。
- 数字密码生成位于 hbb_common/src/password_security.rs，读取 allow-numeric-one-time-password。
- 桌面 UI 通过 src/ui_interface.rs / src/ipc.rs 获取服务配置；界面显示正确不能代替后台服务验证。
- 只改官方 RENDEZVOUS_SERVERS 和 RS_PUB_KEY 常量不足以设置中继、API 和服务配置。
- src/common.rs 中 custom.txt 读取链会验证官方签名，任意自制 JSON 不能直接当成官方定制配置使用。

拟采用单一公开配置文件加独立 9394 默认配置模块。在桌面、系统服务、Android 共用初始化链路尽早加载，开发时验证其先于首次取配置和首次生成临时密码。客户端专用逻辑优先放客户端模块，尽量保留 hbb_common 子模块原样；确需修改子模块时先记录原因与范围。

旧版本持久化的空白服务器字段可能遮蔽默认值，需要对四项服务器字段做有版本标记的一次性迁移，保留有效非空自定义值。单项 getter、整表 getter、桌面 UI 缓存与服务实际使用的值应一致，不能仅给输入框填默认文字。

来源：[选项键](https://github.com/rustdesk/rustdesk/blob/1.5.0/libs/base/src/config/keys.rs)、[配置核心](https://github.com/rustdesk/hbb_common/blob/229b904508364c8997aad0fb5af57effac859f60/src/config.rs)、[密码生成](https://github.com/rustdesk/hbb_common/blob/229b904508364c8997aad0fb5af57effac859f60/src/password_security.rs)、[公共初始化及定制配置读取](https://github.com/rustdesk/rustdesk/blob/1.5.0/src/common.rs)、[IPC](https://github.com/rustdesk/rustdesk/blob/1.5.0/src/ipc.rs)。

### 3.3 开机启动的平台差异

Windows：上游 src/platform/windows.rs 的 get_create_service 已使用 start= auto 并启动服务。沿用安装和管理员授权流程，核对 stop-service、普通用户与系统服务配置同步及重启。便携 EXE 未安装系统服务时，不能仅靠默认开关保证无人登录运行；该项验收以完成安装为准。x86_64.exe 若没有代码签名证书，准确标注未做 Authenticode 签名。

Android：AndroidManifest.xml 已有 RECEIVE_BOOT_COMPLETED 和 BootReceiver；BootReceiver.kt 与 MainActivity.kt 对 KEY_START_ON_BOOT_OPT 的缺省值为 false。需要统一首次初始化、读取和 UI 状态，并尊重已明确保存的 false。BootReceiver 还检查电池优化及悬浮窗授权；屏幕捕获、无障碍输入、通知和后台启动受系统版本及厂商限制。首次启动提供必要授权引导，分别验证服务进程、注册 ID、投屏和输入控制，不把普通 APK 描述为无需系统授权即可工作。

来源：[Windows 服务](https://github.com/rustdesk/rustdesk/blob/1.5.0/src/platform/windows.rs)、[AndroidManifest](https://github.com/rustdesk/rustdesk/blob/1.5.0/flutter/android/app/src/main/AndroidManifest.xml)、[BootReceiver](https://github.com/rustdesk/rustdesk/blob/1.5.0/flutter/android/app/src/main/kotlin/com/carriez/flutter_hbb/BootReceiver.kt)、[MainActivity](https://github.com/rustdesk/rustdesk/blob/1.5.0/flutter/android/app/src/main/kotlin/com/carriez/flutter_hbb/MainActivity.kt)。

### 3.4 商米 T2（Android 7.1、2GB + 16GB）兼容要求

设备型号、系统及容量来自用户新增需求，尚未通过设备读取核实。首个 armv7-signed.apk 必须以该配置的商米 T2 为必测目标，不能用 arm64 构建或新系统模拟器结果代替。

- 安装与加载：APK 包含 armeabi-v7a 原生库；minSdkVersion 不高于设备系统 API 级别。Flutter、Rust 原生库、NDK 目标级别和第三方依赖也必须兼容 Android 7.1，不能只降低 manifest 数值或重命名 APK。
- 功能：在该设备上验证首次安装/启动、四项服务器配置、ID 注册、固定/临时密码认证、IP 直连、远程画面与输入控制。按系统要求完成无障碍、屏幕捕获及开机启动相关授权。
- 资源：针对 2GB RAM、16GB 总存储控制内存、安装体积与日志增长；总存储不代表当前可用空间。记录 APK 大小、安装后占用、运行内存及可用空间，避免默认启用高负载画质配置；编码能力以实机检测为准，提供可用的兼容路径。
- 稳定性：完成至少 30 分钟远程会话，并测试断线重连、后台恢复及授权后重启；验收期间不得出现崩溃、ANR 或因内存不足退出，发现问题先登记本文再修复。
- 验收证据：记录 T2 实际系统版本/固件、支持的 ABI、剩余存储、APK SHA-256、签名指纹和运行结果。若没有真机结果，状态保持“待商米 T2 验收”，不能以编译成功宣称兼容。

### 3.5 Android 打开即启动与权限引导

按用户 2026-10-19 的新增要求，正常打开 APP 后默认自动尝试启动服务，不再要求用户先点击“启动服务”按钮。先检查实际权限状态；已授权则自动继续，未授权则按顺序发起必要系统请求/引导，用户完成并返回 APP 后自动复查和继续启动。初始化与恢复应避免并发启动、重复弹窗和请求循环；用户拒绝或取消时显示缺失项及重试入口，不能显示为已授权或服务已就绪。本次会话主动停止服务后不立即反复拉起；用户显式关闭自动启动或功能开关的状态仍按文档默认值约定保留。

| 功能 | 默认目标与行为 | 实际生效条件 |
| --- | --- | --- |
| 启动服务 | APP 打开后自动启动，授权完成后自动续接 | 后台服务真实运行，并能注册 ID；服务状态和投屏就绪状态分别显示 |
| 屏幕录制 | 默认请求用于远程画面共享的屏幕捕获权限 | 普通 APP 使用系统 MediaProjection 授权；需要用户确认时自动弹出系统界面，收到有效结果后启用，不伪造或绕过授权；不是默认保存本地录像 |
| 输入控制 | 应用内允许输入，自动检查 RustDesk Input | 无障碍服务已在系统启用且实际连接；未启用则展示用途、引导进入该服务设置，用户开启并返回后复查；若设备不能直达具体服务页，则进入无障碍列表并明确告知服务名称 |
| 传输文件 | 应用内允许文件传输，自动检查对应访问能力 | 按系统版本及上游实际存储实现申请必要权限或目录访问；在允许范围实测上传、下载，不能把应用内开关等同于系统全盘访问权限 |
| 允许同步剪贴板 | 应用内同步开关默认开启 | 按系统版本检查实际剪贴板读取/写入能力和必要服务条件，验证控制端与 Android 端的双向同步，以平台支持的数据类型为准 |

RustDesk Input 已被用户启用时，APP 自动使用系统绑定的无障碍服务；未启用时由用户在系统界面开启。普通 APP 不能仅凭一个默认选项静默授予屏幕捕获或开启无障碍服务。若未来需要使用商米提供的受管/系统授权能力，须先核实实际固件与可用接口，并先更新需求；本次不假设设备已具备这些权限。

本次截图只作为上述功能名称和界面位置的参考；不将截图中的音频录制状态或固定密码提示作为新增需求。

来源：[Android 屏幕捕获授权](https://developer.android.com/reference/android/media/projection/MediaProjectionManager)、[Android 无障碍服务](https://developer.android.com/guide/topics/ui/accessibility/service)。

### 3.6 armeabi-v7a 32 位 APK 与 V1 签名

首个 armv7-signed.apk 必须包含 armeabi-v7a 的 32 位原生库，并在商米 T2 Android 7.1 上验证安装和运行；不能用 aarch64 APK 重命名代替。Android 7.1 兼容仍包括 SDK、Flutter、原生依赖及运行功能，不以签名通过代替。

签名阶段显式设置 --v1-signing-enabled true，同时启用 --v2-signing-enabled true，沿用已约定的证书。不能依赖工具默认推断是否附加 V1。V1 为用户明确要求，并不表示 Android 7.1 只支持 V1。

签名后必须执行 apksigner verify --verbose --print-certs，并确认日志中 Verified using v1 scheme (JAR signing): true，整体校验成功；同时核对 V2 结果和新旧证书指纹。将 V1/V2 验证结果、ABI、APK SHA-256 记入构建清单和验收记录。先 zipalign 再签名，签名后不得再改写 APK；缺失 V1 或验证失败时阻止发布。

来源：[Android apksigner 的 V1/V2 签名及验证参数](https://developer.android.com/tools/apksigner)。

## 4. 现有仓库的问题

本次只读检查发现：

1. 已有 build-custom-1.4.9.yml、build-custom-1.4.9-x64-android.yml、build-custom-1.4.9-x64-server-fix.yml。
2. 多处 checkout 固定旧提交 6c578292e8ebbbec708b76986ba8c4bc7c509747，因此同步 master 不等于使用新源码构建。
3. YAML 内嵌大段 Python 字符串及 Base64 补丁，升级后难以定位、审查和维护，应拆为明确配置及可审查脚本/补丁。
4. 部分工作流标题、Windows/Android 版本与文件名不同，需统一实际来源和产物标识。
5. 旧工作流包含服务器空值及 IPC 回退修复，迁移时要保留必要行为并验证，不能假定新默认配置自动涵盖。
6. 旧 Android 流程主要构建 aarch64，需要新增先 armv7 的独立入口。
7. 旧工作流还含 b.9394.cn 更新渠道和 root 授权逻辑，超出本次明确需求，不自动照搬；升级前先记录保留、移除或另行开发的决定。

来源：[旧 Android/Windows 工作流](https://github.com/hacxer/rustdesk/blob/master/.github/workflows/build-custom-1.4.9-x64-android.yml)、[服务器回退修复工作流](https://github.com/hacxer/rustdesk/blob/master/.github/workflows/build-custom-1.4.9-x64-server-fix.yml)。

## 5. 实施结构与构建流程

实施结构（首阶段已提交公开配置、Android 初始化模块、源码适配脚本、armv7 专用 Actions 及验收记录；其他平台与升级入口待后续阶段）：

- 本文：需求、问题和行为约定的入口。
- config/custom-9394.json：公开服务器参数和普通默认值，不放私钥及口令。
- 独立客户端配置模块：共享加载、首次密码初始化及必要旧配置迁移。
- scripts/custom-9394/ 与 patches/custom-9394/：配置生成、显式补丁、版本清单及检查。
- .github/workflows/custom-9394-armv7.yml：已实现的 armv7 独立入口，支持手动指定上游 tag/SHA。
- .github/workflows/custom-9394-update.yml：启用后检查上游并创建升级 PR。
- docs/custom-9394/validation.md、changelog.md：验收与迭代记录。

每次构建顺序：

1. 解析 stable / master / 指定 tag 或 SHA，冻结真实 SHA。
2. 递归检出对应子模块，以该版本官方 CI 的 Rust、Flutter、Java、NDK、vcpkg 组合为起点。
3. 检查补丁前置条件，补丁不匹配立即失败，禁止静默跳过仍声称定制成功。
4. 读取配置及 Secrets，生成定制内容，执行必要回归测试。
5. 首先编译 armv7，仅产出 armv7-signed.apk；避免其他平台提前并发编译。
6. zipalign 后使用 apksigner 显式启用 V1 + V2 签名；verify --verbose --print-certs 必须确认 V1 为 true，核对 armeabi-v7a 32 位原生库及证书指纹，失败即停止发布。
7. 上传 APK、SHA256SUMS、build-manifest.json，进入设备验收。
8. armv7 验收通过后，用相同源码和配置构建 aarch64-signed.apk、x86_64.exe。
9. 记录验证结果并发布定制 Release，保留历史版本便于回滚。

编译成功、静态校验通过、真实设备运行通过是不同状态。GitHub runner 不能证明 armv7 设备上的重启、投屏与控制；未实测时只能记录待验收。

持续升级：稳定渠道检查正式 Release，测试渠道可跟进 master 指定提交。fork 不会因上游 push 自动同步并触发自身构建，需要显式定时检查或手动触发。升级先提交文档/变更摘要，再改代码和补丁，再运行构建。未来上游不兼容时应准确失败并修复，不承诺任何未来源码都无需适配。定时频率及自动发布策略在实施前写入本文；本次不创建调度。

## 6. Android 签名与覆盖升级

用户提供旧 Release v1.4.9-custom-9394 中的 rustdesk-9394.keystore 和 keystore-info.txt，按沿用现有签名处理。

已核对 Release 元数据中的 keystore 文件 SHA-256：d88572222dbe472b4b191bd9734859e27bcd115f06a2b711eec193b4c29d0d91。该值是文件摘要，不是 APK 证书指纹。

现有工作流引用四个 Secrets：ANDROID_KEYSTORE_BASE64、ANDROID_KEYSTORE_PASSWORD、ANDROID_KEY_ALIAS、ANDROID_KEY_PASSWORD。2026-10-19 已在首轮 Actions 确认四项 Secrets 可用，解码后的旧 keystore SHA-256 与约定一致；最终 APK 证书对比仍待签名阶段。只在 GitHub runner 临时还原证书，禁止上传为 artifact 或 Release 附件，不将其下载到用户本地作为构建前置步骤。

必须比较旧 APK 和新 APK 的签名证书 SHA-256，并核对包名与 versionCode，才能标记支持覆盖升级；文件名相同不能代替验证。

公开 Release 已列出证书材料，应视为已公开。是否清理历史附件或迁移新证书另行形成方案；本次不删除现有资产，不擅自换证书导致已装客户端无法覆盖升级。

来源：[现有 Release](https://github.com/hacxer/rustdesk/releases/tag/v1.4.9-custom-9394)。

## 7. 验收清单

| 项目 | 验收标准 |
| --- | --- |
| 来源一致 | 清单中的真实源码、子模块、补丁 SHA 与构建实际使用值一致 |
| armv7 优先 | 首轮仅编译 armv7，原生库为 armeabi-v7a（32 位），V1 + V2 签名有效 |
| V1 签名 | 显式启用 V1，apksigner 校验确认 V1 为 true；Android 7.1 实机安装/覆盖升级通过 |
| 打开 APP 自动服务 | 已授权时无需点击启动按钮即运行；首次授权完成返回后自动继续，拒绝时准确提示且不循环弹窗 |
| 四项权限功能 | 屏幕共享、输入控制、传输文件、双向剪贴板分别实测；应用开关和真实授权状态一致 |
| RustDesk Input | 已开启自动使用，未开启可引导到设置；用户开启返回后自动检测，关闭后状态及时更新 |
| 商米 T2 | Android 7.1、2GB RAM、16GB 存储实机安装与远控正常；按 3.4 节完成资源、30 分钟会话及重启验收 |
| 服务器 | 新装四项正确，服务后台注册和实际连接与界面一致 |
| 旧配置 | 缺失/空白值迁移，非空自定义值保留，UI/IPC/服务一致 |
| 远程修改 | 默认开关开启，已认证会话可按上游权限规则修改 |
| 数字密码 | 首次及刷新均为 6 位数字，刷新规则正常 |
| 固定密码 | 初次可认证，用户修改/清除后升级重启不恢复初始值 |
| IP 直连 | 初始开启，网络可达时经认证连接成功 |
| Windows 服务 | 安装后自动启动，重启无人登录场景可用 |
| Android 开机 | 授权后分 OS 重启测试，分别记录进程、ID、投屏与输入 |
| Android 覆盖升级 | 签名指纹一致、包名兼容、versionCode 增长、配置保留 |
| 发布完整性 | 三类约定产物、校验和、无秘密清单及验收记录齐全 |

2026-10-19：Actions #5 已完成 armv7 构建与签名/ABI/SDK 静态检查；安装、服务器/API 可用性及远控运行功能待用户验证。

## 8. 问题迭代规则

每次发现问题，先记录问题编号、平台/版本、期望与实际行为、复现及证据、需求调整、验收标准。文档提交后才改代码；随后关联代码提交、Actions run、产物摘要、实测及未通过项，不能仅凭编译成功关闭运行问题。

| 问题 | 状态 |
| --- | --- |
| P001 工作流固定旧 SHA | 新 armv7 入口已检出指定上游并记录真实 SHA；旧工作流保留 |
| P002 配置和补丁分散在多个 YAML | 首阶段已集中到公开配置、独立源码及适配/验证脚本 |
| P003 服务器空值及服务/UI 一致性 | 默认值及空值迁移已实现，运行回归待用户验证 |
| P004 armv7 先构建 | 单独 armv7 构建和产物已完成 |
| P005 Android 启动默认值与系统授权 | Android 启动默认值与权限续接已开发，待用户实测 |
| P006 签名复用与覆盖升级 | Secrets、旧 keystore 摘要、新旧 APK 证书及 versionCode 增长已核对；覆盖安装待实测 |
| P007 商米 T2 Android 7.1 兼容 | SDK/ARM32 静态检查通过；商米 T2 真机资源和稳定性验收待执行 |
| P008 Android 打开 APP 自动服务及四项权限 | 自动服务及权限引导已开发，待用户运行验收 |
| P009 armv7 APK 强制 V1 签名 | V1/V2 校验均为 true；安装验证待用户执行 |
| P010 RustDesk Input 自动检测及未启用引导 | 无障碍检测与引导已开发，待用户运行验收 |

## 9. 本次记录

2026-10-18：整理用户第 1–6 条要求，核查上游稳定版、master、现有定制工作流及 Release 元数据；用户指定 hacxer/rustdesk 和旧签名材料。仅提交方案文档，待用户评审后进入代码及工作流开发。

2026-10-18（v0.2）：按用户新增要求，将商米 T2（Android 7.1、2GB RAM、16GB 存储）列为 armv7-signed.apk 的必测目标，增加 R17、3.4 节、验收项及 P007；本次仅修订需求文档，未修改代码、未构建、未完成真机测试。

2026-10-19（v0.3）：加入用户新增的 Android 打开 APP 自动启动服务、屏幕录制/输入控制/传输文件/剪贴板默认启用及系统授权引导、armeabi-v7a（32 位）APK 强制 V1 签名、RustDesk Input 自动检测与未开启引导；新增 R18–R21、3.5–3.6 节、验收项及 P008–P010。仅更新需求文档，尚未实现或编译。

## 10. v0.3 开发记录（文档先行）

2026-10-19：用户确认实施。首阶段在本仓库保存独立配置、源代码适配脚本和 armv7 专用 Actions；Actions 检出指定上游 tag 并记录实际 SHA，在远程应用可审查适配，不复用旧流程固定的 1.4.9 提交。暂不运行 aarch64 和 Windows 构建。

| 问题 | 发现及验收 | 状态 |
| --- | --- | --- |
| P011 上游输入控制初始化覆盖默认值 | ServerModel 构造时对移动端无条件写 enable-keyboard=N；应改为从实际无障碍状态同步，已授权输入不会被每次打开重置，未授权引导开启 | Android 适配代码已调整，待用户运行验证 |
| P012 启动意愿与权限状态混淆 | 设置页会因权限缺失把开机启动写回 false；应保留用户启动意愿，另外提示并引导补齐悬浮窗/电池优化权限 | Android 适配代码已调整，待用户运行验证 |
| P013 构建预置密码与旧证书 | 开始编译前检查所需 Secrets，仅用既有证书；缺少时停止并准确提示，不退回临时签名或公开明文密码 | Actions #1/#2 Secrets 与 keystore 预检通过；APK 证书待最终核对 |

固定密码初始化先检查设备已有密码，首次初始化成功后持久化标记；后续主动修改或清除不重置。首阶段只在 Android 初始化接入配置，Windows 服务上下文的验证留待后续平台阶段。

2026-10-19 / P014：提交后的适配脚本回读审查发现 Python 字符串内的 core_main's 单引号未正确转义，会阻止源码准备。先记录本文，再修正该行，并在 Actions 中增加 py_compile 预检；尚未运行正式编译。

2026-10-19 / 测试环境补充：用户授权使用已安装的雷电模拟器 5 和现有本地 ADB 测试，不安装新工具。已连接 127.0.0.1:5555，系统 Android 7.1.2 / API 25，报告 ABI 为 x86,armeabi-v7a,armeabi，约 3.46GiB 可见内存。用于 Android 7.1 安装、自动启动、系统授权及基本远控验证；因 ARM 兼容层、内存和固件与商米 T2 不同，不替代 T2 2GB 真机资源与稳定性验收。

2026-10-19 / P015：首轮 Actions 39144255352 在 Analyze Android startup 阶段失败；bootstrap_9394.dart 对同步返回 String 的 mainGetLocalOption 使用 await，触发 await_only_futures。先记录本文，再移除该处多余 await；保留静态检查，验收要求该步骤零问题通过，然后继续 armv7 构建。日志：https://github.com/hacxer/rustdesk/actions/runs/39144255352/job/117724760487 。

2026-10-19 / 构建进展：Actions #2（39144947641，定制提交 32870ac8035083c357bac237f04ccfc34d294598）已通过 P015 修复后的 Flutter analyze、NDK/vcpkg 准备及 armv7 原生依赖编译，正在编译 Rust 核心。P014 的 py_compile 预检通过；尚无可供安装的 APK。验收明细统一记录于 [validation.md](validation.md)。

2026-10-19 / P016：Actions #2（39144947641）已完成 armv7 Rust 与 APK 构建，apksigner 明确输出 V1=true、V2=true；但新版 build-tools 的证书行以 V3.0 Signer 开头，原脚本只识别 Signer #1，导致最终证书一致性检查失败，产物未上传。先记录本文，再统一 Python 解析证书 SHA-256：兼容两种标签，只接受唯一证书摘要，缺失/多证书或新旧摘要不同仍失败；保留签名校验，不降低检查。为后续失败修复保留非秘密编译缓存，避免无谓重复构建。验收要求重新构建并通过真实新旧证书、V1/V2、ABI 及模拟器安装检查。日志：https://github.com/hacxer/rustdesk/actions/runs/39144947641/job/117726792146 。

2026-10-19 / P016 复查补充：旧 apksigner 的 Signer #1 与 certificate 之间没有冒号，新格式的 V3.0 Signer 后有冒号；解析必须分别处理这两个完整前缀。修正前先记录本文；取消尚未完成的第三轮并基于修正版启动新一轮，避免使用未覆盖旧前缀的解析。

2026-10-19 / 交付与验收分工更新（用户明确要求）：继续在 GitHub 完成 armv7-signed.apk 的构建、V1/V2、旧证书一致性、32 位 ABI 与 Android 7.1 静态检查并交付下载链接；雷电模拟器安装及运行测试改由用户手动执行。本轮不再自动安装 APK、操作模拟器或连接 Windows 控制端。交付时将运行功能状态标记为待用户验证，商米 T2 真机兼容状态仍保持待验收。用户反馈问题后继续先更新本文，再修改代码和重新构建。

2026-10-19 / P017：Actions #4（39147055221）再次完成 APK 和 V1/V2 签名，但签名步骤在下载旧 APK 后、Python 验证成功消息前以 exit 1 退出。旧 APK 验证报告和 aapt 输出被重定向且未作为失败诊断上传，现有日志不能确定究竟是旧 APK 验证还是 badging 命令失败，因此不能继续仅归因于证书标签。先记录本文，再增加独立的 GitHub 签名诊断入口，打印旧 APK 在默认 SDK 范围及 Android 7.1 / API25 下的验证退出码、证书报告和 badging；诊断不解码私钥、不编译产品。根据真实结果再修正完整流程，并始终保留新 APK 的 V1/V2 与旧证书一致性检查。完整流程失败诊断应保留非秘密签名/badging 报告，避免再次丢失证据。

2026-10-19 / P017 诊断结论与 P018 提交生效核验：独立诊断 Actions 39149234803 证实旧 APK 的默认/API25 签名验证及 aapt 均返回 0，旧证书摘要 ab939122d67c380c76ec0d89da27a1e9f18d89557b36241788a6555d621e7a39。回读 #4 固定提交中的真实工作流后发现旧 AWK 标签解析仍存在，之前网页编辑未形成预期工作流变更；不能仅依赖“已提交”的助手消息判断成功。先记录本文，再重新修改该工作流，移除旧 AWK，统一使用已适配的 Python 证书比较；每次工作流修改后从 GitHub API 回读实际 blob 和提交 diff，核对后才触发构建。增加失败时的非秘密签名/badging 报告，并在最终校验前保存明确标记为未验收的编译检查点；检查点不得作为交付链接，最终交付仍必须通过全部校验。

2026-10-19 / 首阶段交付：Actions #5 https://github.com/hacxer/rustdesk/actions/runs/39149539436 成功。构建定制提交 033562d3e71c6f80ca80d8255f5279af3683c49c，上游 1.5.0 / fada664df7a294d1d1a9ca3e7cd3637069122f17；APK versionName=1.5.0.9394、versionCode=15011005（旧 APK=14911394）、minSdk=22、targetSdk=36，原生库均为 armeabi-v7a ELF32 ARM。V1=true、V2=true，新旧证书 SHA-256 均为 ab939122d67c380c76ec0d89da27a1e9f18d89557b36241788a6555d621e7a39。APK SHA-256：bf7f7c1b4c8042d3c32e44b31b4119ca03a5c560ef313b574f8da339ed098702。交付 ZIP：https://github.com/hacxer/rustdesk/actions/runs/39149539436/artifacts/12145032913 。P014/P015 构建检查已通过，P016/P017/P018 的最终验证及提交生效问题由该成功运行确认解决；运行功能和商米 T2 状态仍待验收。

## 11. v0.4 用户实测反馈与修复验收（先文档后代码）

2026-10-19：用户明确说明已自行下载 v0.3 APK，在雷电模拟器手动测试；以下来自本轮文字反馈及截图。截图仅作现象证据，不包含崩溃堆栈或网络注册日志，不能据此认定根因。公开记录不复制设备 ID、会话口令、账号、IP 或私有日志。继续全程 GitHub 远程编辑和构建，只先产出 armv7-signed.apk，用户负责安装和功能验收。

| 需求 / 问题 | 反馈与目标 | 验收标准 / 边界 | 当前状态 |
| --- | --- | --- | --- |
| R22 / P019 启动与应用内重复确认 | APP 打开即进入屏幕共享启动；移除应用内反诈骗提示和“开启录屏将自动开启服务”的重复确认，避免用户反复点启动服务 | 自动启动入口与手动入口行为一致；已具备授权时直接启动；用户主动停止后不在当前会话反复拉起；保留可见服务及停止入口 | 修复已编译并通过静态检查，待用户复测 |
| R23 / P020 系统录屏授权 | 用户希望不再每次点击系统“立即开始” | 普通 APK 不伪造系统同意、不用无障碍自动点击授权框、不执行 root/appops 绕过。尽量复用本次有效的 MediaProjection/服务状态，避免应用自身重复请求；系统要求时仍需用户确认，并准确说明限制；取消后不循环请求 | 系统授权边界已核对；续接修复已提交，待复测 |
| R24 / P021 就绪但远端离线 | 共享页显示就绪，控制端报远程离线，管理后台未显示该设备；需确保使用预置服务器真实注册 | 核对四项参数在 UI、持久化和后台读值的一致性、配置初始化先后、注册/重试；区分本地服务运行、ID 注册、API 设备上报和实际中继会话。不能把管理列表缺失直接当作 hbbs 离线根因，也不能伪造就绪；需同一服务器控制端端到端连接通过 | 已取得实际注册与中继证据，WebSocket404 迁移已提交；端到端回归待执行 |
| R25 / P022 密码只手动刷新 | 六位数字临时密码在每次连接后变化，改为仅用户刷新时改变 | 连续连接、断开、重连后数值一致；点击刷新生成新六位数字，旧密码失效；保留固定密码行为。默认不承诺跨卸载或进程重建保留，若要求跨重启持久化另行定义 | 修复已编译并通过静态检查，待用户复测 |
| R26 / P023 网络默认项 | 默认启用 TCP 打洞及 IPv6 P2P | 真实选项值和设置页一致；默认开启不覆盖用户后来主动关闭；UDP 与 WebRTC 行为不因本条无故改变 | LocalConfig 键已核对并提交默认值；待复测 |
| R27 / P024 连接通知短暂显示 | “共享屏幕 已建立”的横幅显示一下即收起，不持续遮挡操作 | 连接事件通知约 3 秒后撤销或停止横幅，避免重复提醒；Android 必需的前台服务通知、录屏状态指示及停止入口保留；不能用隐藏必需通知维持隐蔽录屏 | 连接事件限时撤销已提交，前台服务通知保留；待复测 |
| R28 / P025 关闭启动检查更新 | 默认关闭“启动时检查软件更新” | 首装关闭；本次 v0.4 升级执行一次关闭迁移（旧版不能可靠区分默认值与明确选择），之后保留用户选择；启动不发自动检查更新请求，手动检查入口保留 | 修复已编译并通过静态检查，待用户复测 |
| R29 / P026 远控时崩溃 | 截图显示会话建立通知后“RustDesk 已停止运行” | 先定位 Java/native/Flutter 异常与复现阶段，按证据修复；安装、首次授权、会话建立、输入、剪贴板、断开及 30 分钟会话无崩溃/ANR；没有堆栈或复现证据时不得声称已修复 | 已取得 native crash，模拟器渲染兼容修复已提交；待复测 |

本轮不以应用开关、绿色“就绪”或 Actions 成功代替端到端验收。每项修复后补充代码提交、构建 run 与实测结果；仍未通过的项目保持开放。v0.3 的成功构建和签名证据作为历史记录保留，不作为上述新问题已解决的证明。

2026-10-19 / v0.4 源码定位补充：连接授权成功会主动调用临时密码刷新；Android 定制将停止连接成功和失败计数触发的自动换码，保留上游独立的错误密码限流、封禁和认证校验。TCP/IPv6/更新检查属于 LocalConfig，须写 DEFAULT_LOCAL_SETTINGS，不能混入服务端 DEFAULT_SETTINGS。启动协调器在授权返回时可能丢失 resumed 事件，应增加串行续接；屏幕授权流程优先于可选开机优化引导。原生开机服务入口也必须在启动 Rust 服务前加载定制配置，不能只依赖 Flutter 首页初始化。当前 getter 与整表均合并 DEFAULT_SETTINGS，尚无证据证明“未持久化默认值”本身就是离线根因，不作此断言。连接通知独立定时撤销，前台服务通知保持。旧版更新开关的历史选择无法可靠区分，本次按用户要求一次关闭，后续主动重新开启应保留。

P026 诊断记录：尝试只读获取指定雷电的 Android crash buffer 时设备未连接，已停止等待；未安装或操作 APP，没有取得异常堆栈。继续修复已确认问题，崩溃保持待诊断，不凭截图推测已解决。

2026-10-19 / P021 实机日志补充：雷电重新连接后，仅只读现有公开存储中的 RustDesk 日志；未安装或操作 APP。日志显示 UDP 连接 rustdesk.9394.cn:21116、收到服务器响应并更新延迟、sysinfo updated，以及来自指定中继服务器的 create_relay 请求，证明定制配置曾实际生效；不能继续描述为始终没有连到自建服务器。另有启用 WebSocket 后 ws://rustdesk.9394.cn/ws/id 返回 HTTP404 的记录，此部署目前没有可用的该路径。v0.4 默认使用原生 UDP/TCP，将 allow-websocket 默认设 N，并随本次一次迁移关闭现存 WebSocket 选项以恢复原生连接；后续用户明确开启仍保留。验收应记录离线发生时的传输方式、双方服务器与同一时刻状态，而非仅核对 ID 数字。

P027 / R30 API 审计响应兼容：日志中 API 返回 HTTP2xx 且 JSON 为 code=0、message=success、data=空字符串，上游新版审计逻辑只接受空响应体，误判为失败并多次重试。Android 定制仅为这个精确成功结构增加兼容；非2xx、非零 code、error 字段、未知/畸形正文仍按原失败与重试处理，保留审计上报与认证，不通过关闭审计消除错误。验收要求精确成功响应不重试，错误与未知响应不误认成功。此问题与崩溃没有已证实因果关系，不将其标记为崩溃根因。

P026 进一步诊断：当前 Android crash buffer 为空，release 包不允许 run-as 读取私有目录；未提权、未更改权限。现有外部日志没有 panic/fatal/Java 异常堆栈，因此崩溃仍待用户复现后的即时错误日志；不凭 IPv6 不可达、视频 SWITCH 或 JNI 警告认定原因。IPv6 默认启用仅表示允许尝试，模拟器网络不支持 IPv6 时仍应走可用 IPv4 路径。

P026 / 2026-10-19 系统保留记录定位：重新连接的雷电以 emulator-5554 可读，Android 7.1.2。DropBox 保留了 v15011005（1.5.0.9394）的 data_app_native_crash：Flutter 1.raster 线程 SIGSEGV / SEGV_ACCERR；调用链为 libc memcpy → libstagefright_soft_gl2enc → glTexSubImage2D → libGLESv2_adreno → libhoudini，实际 ABI 为 x86 并通过 Houdini 运行 ARM APK。这是模拟器图形/ARM 翻译路径的明确崩溃证据，不是已证实的 Rust 服务器配置错误。首轮按证据增加 Android 7.x x86 模拟环境专用的 Flutter 软件渲染兼容路径，避免该 GLES 纹理上传路径；ARM 商米 T2 保持原硬件渲染路径，远程屏幕采集与编码不随 UI 渲染开关改变。新包仍需用户复测同一步骤，未复测前状态为“已定位崩溃路径，兼容修复待验收”，不承诺所有崩溃已解决。验收补充：雷电检测命中软件渲染，冷启动、共享建立、切换页面/后台与 30 分钟会话稳定；ARM 真机不命中该模拟器条件。

P028 / 2026-10-19 构建缓存与 Flutter SDK 补丁：Actions #6（39196685904，定制源码97a5a3d2e73f17277f160f1294586084de5158ce）已通过源码适配与 API 兼容 Rust 测试（2 passed），在 Analyze Android startup 中对 Flutter SDK 应用 dropdown_menu 补丁时报 patch does not apply；尚未运行应用 Dart analyzer，也未生成 APK。可能是恢复的 SDK 缓存已含同一补丁，需在远程验证而不是直接跳过。先登记本文，再把步骤改为先 git apply --check，能正向应用则应用；否则仅在 git apply --reverse --check 通过时接受“已应用”的状态；两者均失败则继续阻止构建。验收要求新运行明确输出补丁状态并通过 Dart 分析，不能因使用缓存降低匹配检查。

2026-10-19 / P028 修复提交与构建：工作流已改为正向检查/应用，或反向检查确认已存在；实际文件已从 GitHub 回读确认。定制提交670879cd91cecd79a246f60a129a755b87d56da5；Actions #7：https://github.com/hacxer/rustdesk/actions/runs/39197097944 。当前等待远程构建与完整静态检查；运行回归仍由用户执行。

P029 / 2026-10-19 静态分析范围扩展：Actions #7（39197097944）已确认 Flutter SDK 补丁反向检查通过，即缓存已有同一补丁，P028 机制生效；API Rust 测试2项通过。扩大 Dart 分析到上游 server_page.dart 后，仅报3条既有 MaterialStateProperty / MaterialStatePropertyAll 的 deprecated_member_use 信息，未出现 error 或 warning，但 Flutter 默认把 info 也作为失败。先登记本文，再将检查拆分：新增 bootstrap_9394.dart 保持原严格分析；既有 server_model.dart/server_page.dart 保留完整分析输出，仅使用 --no-fatal-infos 允许信息级弃用提示，error/warning 仍使构建失败。不为消除提示修改无关上游 UI，也不关闭 analyzer。验收要求两步分析通过，日志仍保留弃用提示并确认无错误/警告。

## 12. v0.4 armv7 静态交付结果

2026-10-19：[Actions #8](https://github.com/hacxer/rustdesk/actions/runs/39197576862) 成功。实际编译来源为定制提交25e13b8ef4b107cfc1b878ca1cc1b186563ef471，上游1.5.0 / fada664df7a294d1d1a9ca3e7cd3637069122f17。API 响应兼容 Rust 测试2项通过；新增启动模块 analyzer 无问题，扩展页面无 error/warning、保留3条上游弃用 info；Rust 和 Android/Kotlin release 构建成功。P028 缓存补丁反向检查通过，P029 检查范围调整通过。

- 交付：[armv7-signed-9394-8 ZIP](https://github.com/hacxer/rustdesk/actions/runs/39197576862/artifacts/12163027056)，解压安装 armv7-signed.apk；不使用 unverified-checkpoint。
- APK：versionName=1.5.0.9394，versionCode=15011008（高于已测试旧包15011005）；28,938,291字节；minSdk22、targetSdk36；armeabi-v7a，全部原生库 ELF32 ARM，原生目标API21。
- APK SHA-256：cb0926b0c1391f2ee85cb35cde8b71a173827a86c66ac185febef073b7baff9a。ZIP 摘要与 APK 不同，以包内 SHA256SUMS 的 APK 值为安装包校验依据。
- V1=true、V2=true；原证书一致，证书SHA-256：ab939122d67c380c76ec0d89da27a1e9f18d89557b36241788a6555d621e7a39。
- P019–P027 已按前文范围实现并编译，运行状态均为待用户复测。P026 为根据保留 native crash 添加的模拟器兼容路径，不以编译成功关闭崩溃。Android 系统授权仍按平台要求保留；商米 T2 仍待真机验收。

P030 / 交付元数据文案：该次 build-manifest 的 requirements 描述仍为“v0.3 plus implementation records”，实际不可变 profile_sha 已包含本文 v0.4 及 P019–P029 的源码；该文案不影响 APK 内容或校验结果。先记录本文，再将生成器未来构建的需求标签改为 v0.4 with implementation records。本次 APK 字节和已验证摘要保持不变，不为纯描述文字重新编译产品；本节明确提供当前包与 v0.4 的实际来源对应关系。


## 13. v0.5 用户覆盖安装反馈（先需求、后代码）

2026-10-19：用户已自行安装 build8；助手仅使用现有 ADB 对指定雷电只读查询，以及读取当前控制端相关日志和路由摘要，不安装、启动、操作 APP，不清空日志，不修改 Clash/系统网络设置。用户随后明确选择“只有普通 U 盘安装，保留必要的一次系统确认”。该答复替代本轮最初希望静默代为同意系统授权的要求。

| 需求 / 问题 | 目标与实施约定 | 验收标准 / 当前证据 |
| --- | --- | --- |
| R31 / P031 普通 U 盘部署授权 | 打开 APP 自动执行启动；已有有效 MediaProjection 自动使用，缺少或失效时只合并请求一个必要的系统确认，取消不自动循环。普通侧载 APK 不具备静默授予录屏、电池白名单或无障碍权限的能力，不伪造同意，不自动点击系统授权，不使用 root/appops/隐藏接口。不能承诺确认一次后跨进程、撤销或所有系统版本永久免确认 | 用户已接受必要的一次系统确认。持续有效会话返回 APP 不应重复申请；权限撤销、进程重建后按系统实际要求处理。保留可见服务与停止入口；Android14+不重用单次授权 token |
| R32 / P032 电池优化确认 | 已获豁免时直接继续，不再弹窗；普通 APK 首次确实缺少时保留必要系统确认。记录本定制引导已请求状态，用户拒绝/取消后不因每次打开 APP 重复打扰，后续仍可手动通过开机设置或系统设置授予；不得把请求过等同于已获授权 | 当前雷电 deviceidle 白名单已包含应用，说明已获豁免，不需要继续请求。覆盖升级保留真实白名单与用户选择；拒绝场景应保留未获授权状态且不循环 |
| R33 / P033 UDP 默认开启 | 显式 enable-udp-punch=Y，写 DEFAULT_LOCAL_SETTINGS；disable-udp=N，写 DEFAULT_SETTINGS。首次进入本轮配置执行一次同值迁移，以纠正当前截图中的 UDP 打洞关闭；旧设置无法可靠区分默认与用户选择，按本次明确要求只迁移一次，后续主动关闭必须保留。TCP/IPv6默认仍开，WebRTC不改变 | 初装、从build8覆盖安装均实际开启 UDP/UDP打洞；此后用户关闭再重启保持关闭；配置键、页面和运行读取一致。不能将 UDP 开关等同于 UDP 传输必定成功 |
| R34 / P034 Clash TUN 下连接被关闭 | 分别验证直连、UDP、IPv6、中继，不把关闭 TUN 作为修复。先读取双方日志、路由和匹配规则；不通过 Android 默认强制所有连接中继、禁用 UDP/IPv6、降低认证或任意过滤私网网段掩盖问题 | 12:45–12:48 控制端对雷电私网目标报 is_local=true，TCP connect 很快完成、约5秒后 Reset by peer；Android 对应监听在18秒后超时且未进入认证。当前该目标实际选路 Mihomo，TUN gvisor/auto-route开启、route-exclude为空，已有私网 DIRECT 规则。因此重复添加 DIRECT 不能证明解决；优先验证 TUN开启 + ID/r 单次中继。具体TUN回环根因及修复仍开放，不能宣称 APK 已修好 |
| R35 / P035 新包服务器/崩溃复核 | 区分旧崩溃、当前包和普通视频重建日志；仅发布脱敏摘要，不上传原始日志、设备标识、会话身份、Clash订阅或凭据 | 当前包15011008 / 1.5.0.9394，安装时间12:40:55；12:40/12:53指定服务器UDP注册响应、sysinfo updated，12:52及12:56经指定中继建立会话并启动VP8。13:01仍有服务器延迟响应。DropBox仅有02:32/02:58旧崩溃，无安装后新记录；12:53命中Android7 x86软件渲染。仅代表本次已观察区间未发现新崩溃，30分钟连续会话和T2真机仍待验收 |
| R36 / P036 构建来源 | 未来清单需求标签改为 v0.5 with implementation records；只构建 armv7-signed.apk，保留 V1/V2、原证书、ELF32 ARM、minSdk22 和更高versionCode | 所有代码和构建均在GitHub；文档提交回读确认后才改代码，交付以实际profile_sha和最终校验为准 |

### 本轮诊断解释与待验证项

- 指定服务器已实际生效。API设备列表、ID注册、会话建立三者分别记录；未将模拟器缺少可用IPv6、视频分辨率变化引起的SWITCH或JNI警告当作崩溃证据。
- TUN失败目标为模拟器NAT私网地址，另一Windows设备连接成功可能走中继或不同网络路径，不能据平台名称推断协议兼容问题。现有控制端为旧1.4.9，若其把TUN伪TCP建立误判为直连成功，Android APK无法单独更改电脑侧的路由和失败回退；需单次中继对照结果后决定控制端或TUN的精确修复范围。
- 本轮先完成明确的UDP默认迁移、必要授权不重复引导以及构建元数据；TUN按真实证据保持开放。受管/商米系统预授权接口不在当前普通U盘部署条件内，不编造可用能力。
- 平台依据：[Android MediaProjection](https://developer.android.com/media/grow/media-projection)、[Android Doze与电池豁免](https://developer.android.com/training/monitoring-device-state/doze-standby)。网络依据：[RustDesk force relay](https://github.com/rustdesk/rustdesk/wiki/FAQ#force-relay)、[Mihomo TUN配置](https://github.com/MetaCubeX/Meta-Docs/blob/main/docs/config/inbound/tun.en.md)。


2026-10-19 / P034 单次中继对照：用户保持 Clash TUN 开启，在模拟器ID后加 /r 后确认可以连接并看到画面。13:08日志与反馈相符：Android收到指定中继请求、连接打开并启动VP8；控制端记录 establish Relay connection。结论：自建服务器、中继和当前APK在该TUN环境下具有可用画面链路，失败集中在模拟器私网直连路径。/r 是已验证的单次绕行方法，不等于默认直连问题已修复，也不意味着UDP默认开启就必然解决。保留TCP/UDP/IPv6默认和认证逻辑，不为此在Android全局强制中继。TUN直连兼容仍开放；可在电脑端为该模拟器保存“总是使用中继”或每次用ID/r。若继续修复直连，应先验证模拟器网络可达性及TUN排除后的系统路由，再决定精确配置；已有私网DIRECT规则，不能重复添加规则后冒充完成。

v0.5实施：配置新增 enable-udp-punch=Y / disable-udp=N，UDP打洞列入LocalConfig；9394-udp-defaults-v1只迁移UDP两项一次，不重跑v0.4服务器/WebSocket/更新迁移。启动协调器增加9394-battery-prompted-v1请求记录，继续依据真实系统检查判断豁免，不伪造已授权。录屏有效状态复用与请求合并沿用已实现路径；系统必须的确认按用户最新选择保留。未来构建清单标签更新v0.5。源码均经GitHub文件回读核对，等待Actions静态检查和armv7打包；未将本轮尚未构建的改动标记运行通过。


## 14. v0.5 追加：系统“不再显示”与雷电桥接故障

2026-10-19 / R37、P037：用户希望图中系统录屏确认框默认勾选“不再显示”。此控件由Android SystemUI管理，普通侧载RustDesk没有公开接口设置它的初始勾选状态。实现范围仍按用户已接受的一次必要系统确认：用户可首次手动勾选并选择立即开始，系统若保存则由系统决定后续免提示；应用继续复用有效投屏状态，不能通过无障碍点击、隐藏API、伪造系统同意或修改系统设置达到预勾选。该需求记录为“系统限制，普通APK不支持默认勾选”，不宣称已开发。更换固件/签名、卸载重装或权限重置后不能保证保存。

2026-10-19 / R38、P038：用户反馈雷电5改为Realtek物理网卡桥接 + DHCP后持续“正在接入RustDesk网络”。先只读诊断，分清模拟器桥接驱动/DHCP/网关/DNS/可达性与应用重连。现存13:12–13:17日志显示ID UDP、NAT TCP、API21114及TCP代理回退全部报NetworkUnreachable / os error101，尚未进入服务器认证，不是录屏权限或固定密码错误；13:17:54以后恢复指定服务器UDP延迟、13:17:57 sysinfo updated，13:18中继会话启动。应用已有约17秒重试，不因这个现象直接改服务器或关闭UDP。

当前只读状态：配置13:17:40保存，桥接networkSwitching=false，运行172.16私网NAT地址；Android策略路由表有默认网关（不能仅凭主路由表无default误报缺路由）。物理网卡可见两种LD桥接过滤驱动均Enabled，但这不能证明桥接时驱动/DHCP成功。当前DNS解析返回198.18.0.0/15范围，可能由Mihomo Fake-IP接管，单次ping响应不证明真实hbbs可达。要复核桥接，需要用户手动开启并重启后保留现场，再读取桥接实际IP/网关/DNS/全路由与最新报错；本轮不擅自改模拟器/Clash/系统网络设置，不安装驱动。

验收：桥接应取得当前LAN有效DHCP地址与默认路由，普通外网/DNS和指定服务器21114/21116/21117可达；断网恢复后可自动重新注册；保留TUN开启/关闭与ID/r对照。若环境没有基本网络可达性，应明确记录环境故障与恢复步骤，不能用APK绿色就绪或隐藏错误冒充修复。桥接现场暂缺时保持P038待复测，继续交付已明确修正的UDP/授权引导版本。


2026-10-19 17:58–18:00 / P038 桥接现场确认：用户开启桥接并重启后，配置networkSwitching=true / DHCP，ADB目标切换为127.0.0.1:5555，仍为API25。模拟器实际获得LAN IPv4 /24，能ping通同网段路由器，但ip route show table all和Connectivity LinkProperties均没有IPv4默认路由；只有IPv6默认路由。访问外部IPv4立即NetworkUnreachable，RustDesk的UDP注册、NAT TCP、API21114及回退TCP均os error101。因此本次“正在接入”明确由桥接环境缺少IPv4默认网关导致，不是APK密码、录屏同意或服务器参数错误。宿主物理网卡有正常IPv4网关，说明问题集中在模拟器桥接DHCP/路由配置。

修复路径：优先修正桥接DHCP网关分发；或由用户在雷电界面设置路由器保留的空闲静态IP、正确/24掩码、与物理LAN一致的IPv4网关和可用DNS，保存重启后复读全路由与服务器注册。已有租约地址若改静态需在路由器保留，避免冲突。助手不在APK中硬编码用户LAN地址/网关，不执行root路由修改，不安装驱动。用户已获具体配置指导，等待手动调整后的复核；在此之前P038状态为“已定位环境缺默认网关，修复待验证”，不是“APK已修好桥接”。后续文档只保留脱敏网络摘要。


2026-10-19 18:07–18:08 / P038 恢复验证：用户手动设置路由器LAN内静态地址、正确掩码、网关及DNS并重启。只读ADB确认IPv4默认路由已存在，外部IPv4 ping成功；18:07:28收到rustdesk.9394.cn:21116/21115 NAT响应与18.645ms mediator延迟，18:07:31 sysinfo updated；18:08:08收到指定中继请求并Connection opened，随后启动视频服务。结论：本次桥接无法接入问题由缺少IPv4默认网关造成，用户补齐网关后已恢复实际注册、API及中继会话。该项网络恢复验证通过，不需要为模拟器私网地址修改APK。真实画面/输入/剪贴板和长会话仍按端到端清单执行；TUN默认直连与本项分别记录，不因中继恢复关闭P034。静态地址由用户管理保留，公开文档不复制实际LAN地址或设备标识。


## 15. v0.5 / build9 最终静态交付（2026-10-19）

[Actions #9](https://github.com/hacxer/rustdesk/actions/runs/39234351129) 于18:25完成且成功。冻结定制profile=ece437c54f2a22da2e212b19ca2f84e8d45899fb，上游1.5.0/fada664df7a294d1d1a9ca3e7cd3637069122f17，hbb_common229b904508364c8997aad0fb5af57effac859f60。后续文档补充不改变本次APK来源。

- 下载：[armv7-signed-9394-9](https://github.com/hacxer/rustdesk/actions/runs/39234351129/artifacts/12179272527)，ZIP解压得到armv7-signed.apk及SHA256SUMS、build-manifest.json和校验报告；不使用unverified-checkpoint。
- APK：versionName1.5.0.9394，versionCode15011009，高于用户当前build8的15011008；minSdk22、targetSdk36、native API21，全部原生库armeabi-v7a/ELF32 ARM，字节数28,938,291。
- APK SHA-256：2447958f38f0e6967343fd55ea25c229d608915e830c7c0059b206f1974e6b77。
- V1=true、V2=true；原证书匹配=true，证书SHA-256：ab939122d67c380c76ec0d89da27a1e9f18d89557b36241788a6555d621e7a39。
- ZIP字节数28,575,983，ZIP SHA-256：93d9608702086093362f44a88405df2f9a346fda5168d134b780febe8012bf3d；与APK摘要区分。
- API兼容测试2项通过；新启动模块Dart分析No issues，既有页面分析无error/warning；ARM原生依赖、Rust、Android/Kotlin release和最终签名/旧证书/ABI校验全部通过。manifest需求标签明确v0.5 with implementation records，T2设备验收明确PENDING。
- 本轮实现P032电池自动引导请求记录、P033显式UDP默认及独立一次升级迁移、P036清单标签；P031/P037保留真实系统确认，系统“不再显示”不能由普通APK预勾选。P038桥接恢复是用户网关修正后的build8实测；P034的/r中继可用已实测，默认直连未关闭问题。未声称新build9运行功能或T2硬件已通过。

用户下一步：保留数据覆盖安装build9，验证UDP默认迁移和后续手动选择保留、已有授权不重复申请、首次系统必要确认及取消不循环、电池豁免实际状态和请求记录；继续输入/文件/剪贴板、通知、密码及30分钟稳定性。全程源码和编译在GitHub，助手本地仅现有工具只读诊断及保存交付截图，没有安装构建工具或APK。


## 16. TUN普通连接用户复测通过（2026-10-19追加）

用户对“保持TUN开启、不加/r、取消该设备总是使用中继”的对照问题明确反馈：不加/r也能连接并看到画面。结合P038已验证的桥接静态地址/IPv4默认网关恢复，本场景的普通连接与显示画面功能验收通过，无需为这次反馈修改代码或重新打包。

证据范围：当前ADB读取安装仍为versionCode15011008 / build8，默认IPv4网关正常；最新可读控制端18:56:52会话日志写明 establish Relay connection with TCP punch，Android18:56:54也有指定中继create_relay及Connection opened。因此“不加/r”表示默认连接入口可用，不等于纯P2P直连；不能将此记录为TCP/UDP/IPv6直连均通过。用户的画面反馈与日志的传输路径分别记录，未上传设备ID、会话身份或原始日志。

P034状态细分：桥接网关恢复后TUN开启+默认入口无需/r可显示画面，已通过用户复测；纯P2P路径与原NAT环境的兼容仍未证明，不宣称已根治全部TUN直连问题。本轮仅更新需求/验收文档，继续使用已交付且签名检查通过的build9；build9尚待覆盖安装回归，30分钟连续会话、输入/文件/剪贴板及商米T2真机验收仍开放。


## 17. v0.6 收银机交付后免重复授权（先需求、后实现）

最新用户需求：本产品用于收银机远程维护，顾客不应手动同意录屏、勾选“不再显示”或确认忽略电池优化。将“交付后顾客免操作”与“普通APK安装即自行获得系统权限”区分；后者在现有普通U盘侧载条件下没有对应系统能力，不能标注已实现。v0.5曾接受一次确认是历史约定，本轮重新提出的业务目标必须单独登记。

| 需求 / 问题 | 目标与实现条件 | 验收 |
| --- | --- | --- |
| R39 / P039 录屏授权预配置 | 顾客日常启动及远控不重复同意。Android7.1的复选框由SystemUI维护，普通APK无公开接口预勾选。交付前可由安装人员在系统框勾选并确认；系统若保存许可，后续请求可自动获得结果。继续复用有效会话，不伪造同意、不自动代点、不保存已失效token冒充跨进程许可 | 在目标T2固件上测试APP返回、冷启动、断电重启、同签名覆盖升级是否免提示；撤销、卸载和恢复出厂另行处理 |
| R40 / P040 电池豁免预配置 | 顾客使用时已经真正进入电池豁免名单。由安装人员交付前选择系统豁免，或由具备该能力的官方设备管理接口配置；普通APP请求接口仍需系统确认。记录请求过或隐藏提示不能当作已获豁免 | 系统isIgnoringBatteryOptimizations返回true，重启/升级保持，后台维护可用；拒绝或撤销后不伪报成功 |
| R41 / P041 部署职责 | 方案A：安装/维护人员U盘安装后完成一次系统配置并验收再交付。方案B：商米提供适配T2具体固件的系统预授权/设备管理接口，核对能力后集成。收银机用途、V1签名、自签名APK或仅称Device Owner/MDM均不能证明能静默授予投屏 | 明确配置责任人、SUNMI OS/固件版本及保存行为；条件不具备时保持待实现 |

### 方案A：交付前安装人员配置清单

1. 记录实际T2的Android、SUNMI OS和完整固件版本；安装同包名、同签名APK，后续正常升级使用覆盖安装。
2. 安装人员首次在Android录屏框勾选“不再显示”并选择立即开始；不是让顾客日常操作，也不是APP自行代勾或代点。
3. 安装人员在系统中设置忽略电池优化，并按固件要求配置RustDesk Input、开机/后台权限；检查真实系统状态与实际远控，不能只看应用开关。
4. 验证多次返回/冷启动、断电重启、一次同签名覆盖升级后，录屏和电池授权不再要求顾客选择，服务器注册、画面、输入正常。若T2固件不能保存投屏许可，则方案A不能承诺跨重启免确认，转方案B或明确型号限制。
5. 保留必要前台服务/录屏状态及停止入口。撤销权限、卸载、清理数据或恢复出厂后的重新配置由维护人员处理；长时会话和2GB真机资源验收仍需完成。

### 方案B：官方能力接入前置条件

需要商米官方提供T2/Android7.1具体固件可用的SDK/API说明、第三方包授权方式及公开签名白名单要求，分别核实投屏、电池豁免、输入与自启。静默安装不等于静默投屏授权；不能仅凭DMP产品介绍编造RustDesk可调用的授权接口，也不要求用户提供厂商私钥。已检索商米官方DMP/远程协助介绍，尚未确认本包可直接调用的T2首次静默授权接口。取得实际接口后，先补充本文方法、条件及失败路径，再远程修改代码并优先构建armv7。

平台依据：[Android7.1.2 SystemUI源码](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-7.1.2_r39/packages/SystemUI/src/com/android/systemui/media/MediaProjectionPermissionActivity.java)先检查已有projection permission，具备则直接返回授权，复选框也由SystemUI管理；这是AOSP证据，不等于商米固件验收已通过。[MediaProjectionManager公开API](https://developer.android.com/reference/android/media/projection/MediaProjectionManager)及[Android电池优化豁免](https://developer.android.com/training/monitoring-device-state/doze-standby)说明普通请求和真实状态检查。[商米DMP](https://official-website-onl.sunmi.com/partner)只作为厂商能力线索。

2026-10-19 用户确认：“可以，交付前由安装人员统一配置”。本轮正式采用方案A，由安装/维护人员承担首次系统授权及交付检查，顾客日常使用不参与配置；方案B仅保留为目标固件不能保存授权时的后续选项，不是本轮开发前置条件。

实施基线继续使用v0.5/build9（versionCode15011009）。已有代码按真实录屏和电池授权状态继续启动；本次部署职责确认不要求新增产品代码或重新编译，也不将文档更新称为v0.6权限功能已完成。具体安装步骤见README，逐机验收表见validation.md。目标T2尚未执行的项目保持待验收；安装人员确认多次启动、断电重启及同签名覆盖升级均免重复提示且远控正常后，方可标记该固件交付通过。若出现已保存授权仍反复请求，先记录固件、复现时刻和脱敏日志至本文，再判断并修改代码。


## 18. R42 / P042 发布 build9 正式 Release（2026-10-19）

用户明确要求把当前版本在GitHub发布正式版本。本次发布标签v1.5.0-9394-build9，非草稿、非预发布，设为Latest；仅发布Actions #9已经签名校验的armv7包，不重编译、不重新签名。标签指向实际构建profile ece437c54f2a22da2e212b19ca2f84e8d45899fb，上游与APK摘要沿用第15节。

发布先在GitHub runner核验源run成功、artifact ID12179272527及名称、ZIP和APK摘要、签名报告与manifest。只上传armv7-signed.apk、SHA256SUMS、build-manifest.json、APK信息和签名验证报告；不上传密钥、口令、未校验checkpoint或原始设备日志。先创建草稿并上传核对所有附件，再转正式公开版本，失败不得把不完整草稿发布。

本次用户授权覆盖此前“设备验收后再发布”的发布时间限制，但不改变验收事实：T2真机、30分钟稳定性及build9完整运行回归仍待完成。发行说明必须明确该范围，v0.6安装人员交付前配置方案已确认，不宣传APK能自行静默授予系统权限。发布成功后回读Release状态、标签目标和附件摘要，更新下载入口及验收记录。


### P043 发布流程：草稿尚未生成标签时查询404

首次发布任务39273820575已通过原ZIP、APK摘要、manifest、签名报告与ELF32 ARM核验，gh release create已建立草稿并上传附件；随后按tags路径查询草稿返回404，因此正式发布步骤未执行。GitHub草稿可能显示untagged地址，不能据此把APK判为损坏或重复创建版本。修复为通过Release集合按精确tag_name取得唯一Release ID，再按ID读取并校验草稿和附件；若已有同名草稿则仅复用且要求来源目标与所有附件摘要一致，不覆盖不匹配附件。核验后按ID转为非草稿、非预发布及Latest，再复读正式标签指向和附件。原APK保持不变；修复后重新手动运行发布工作流。


2026-10-19 23:01（Asia/Shanghai）/ R42、P042、P043完成：修正后的[发布任务39274217579](https://github.com/hacxer/rustdesk/actions/runs/39274217579)成功，复用原草稿并核验全部附件后发布[正式版v1.5.0-9394-build9](https://github.com/hacxer/rustdesk/releases/tag/v1.5.0-9394-build9)。API回读draft=false、prerelease=false，Latest指向本版；标签实际指向ece437c54f2a22da2e212b19ca2f84e8d45899fb。五个附件（APK、SHA256SUMS、manifest、签名报告、APK信息）全部uploaded并核对服务端摘要；APK仍为28,938,291字节，SHA-256与第15节一致。无重新编译或签名，无额外平台包。T2真机及长会话验收保持待完成，安装人员预配置约定不变。


## 19. v0.7 / R43–R45 多平台补齐现有正式版

用户明确授权继续按相同配置编译aarch64-signed.apk、x86_64.exe，并上传现有正式版v1.5.0-9394-build9；先更新需求，全程GitHub。此授权允许在T2真机验收尚未完成时继续其他平台构建，但不得把待验收状态写成已通过。

- R43 Android ARM64：固定上游fada664df7a294d1d1a9ca3e7cd3637069122f17及hbb_common229b904508364c8997aad0fb5af57effac859f60。使用build9定制来源ece437c54f2a22da2e212b19ca2f84e8d45899fb的config/custom-9394.json、Android适配和初始化模块；公开配置摘要必须与build9相同。仅切换arm64-v8a原生ABI与64位ELF检查，保持versionName1.5.0.9394、原证书和V1+V2；versionCode接受Flutter按ABI增加的偏移，ARM64实际15013009，高于原ARM32的15011009；不能用ARM32包改名代替。Android系统授权仍按安装人员交付前配置与真实授权检查执行。
- R44 Windows x64：同一上游SHA及公开配置文件，沿用相同初始化模块及Secret注入固定密码，新增明确Windows入口适配：核心入口在启动服务前加载配置，Flutter DLL初始化也加载默认值；服务进程与普通用户分别使用正确上下文，保留既有非空自定义值、用户密码与后续选择。Windows临时密码按相同需求只手动刷新，错误密码限流/封禁不变。沿用上游安装与自动服务，便携运行不能承诺自动安装或开机运行。发布Flutter完整自解压x64 EXE，不能只上传缺DLL/资源的runner。未提供Windows代码签名证书，明确标注Authenticode未签名，不冒用上游签名。
- R45 追加发布：原正式版标签与armv7及已有附件保持不变；两个新包分别附带独立构建清单、SHA256和平台校验报告。记录build9基准profile及新增平台适配提交，公开配置及共用模块摘要核对，不能将扩展提交误写成原build9全部源码。上传前检查Release身份及原armv7摘要，不覆盖同名不同内容附件，保留Latest和正式状态。

实施：新增独立平台构建/验证/追加发布流程，工具链依照固定上游CI，Android复用已通过的流程。需要修复时先在本节登记新问题，再修改代码或构建步骤。校验包括原证书/V1/V2、ELF64 AArch64，Windows PE AMD64、自解压所需资源/依赖、配置初始化入口及必要冒烟检查；运行设备验收与静态构建通过分别记录。助手不在本地安装任何构建工具或APK/EXE，构建、签名、打包和上传都在GitHub runner完成。


### P044 追加平台构建前检查

静态审查发现：ARM64校验报告改为独立前缀后，摘要展示和诊断上传仍引用旧文件名；应统一为aarch64前缀，不能因改名漏校验或假报构建失败。Windows检出须禁止自动CRLF转换，按Git原始字节验证与build9公开配置摘要一致；不得通过忽略配置摘要绕过。新平台构建须先执行Python语法、源码锚点及配置一致性检查，失败不发布。


### P045 Windows检出字节一致性与单平台重试

首轮Windows任务118154864937在准备阶段触发baseline/config/custom-9394.json摘要断言；共享桥接已成功生成，ARM64构建继续。此前仅设置core.autocrlf=false仍不足以保证工作区字节。修复为在GitHub Windows runner明确UTF-8与LF设置，并从固定baseline Git对象以二进制方式恢复公开配置及共用模块文件，再验证原固定摘要；不能放松摘要或改服务器参数。源码差异检查允许平台CRLF行尾，但继续检查其他空白问题。

为避免重编译已通过的桥接及ARM64，允许手动指定同仓库原构建run复用其verified ARM64 artifact，Windows独立重试。发布必须分别记录每个平台真实source_run、extension SHA，并与相应workflow run的head_sha及既定工作流路径核对；原run可能因另一平台失败而整体失败，不能因此把已验证artifact改记为新run构建。仍要求两包来源、配置、签名/ABI及摘要校验通过，原正式版附件不变。状态接口出现明显滞后时结合完整job日志与artifact证据，不能只据queued字样判定尚未执行。


### P046 ARM64实际版本与发布辅助文件

2026-10-20 00:23：原ARM64任务已上传verified-extra-aarch64-39279619028，V1/V2及原证书通过，原生库arm64-v8a/ELF64验证通过；实际APK为versionName1.5.0.9394、versionCode15013009、minSdk22、target36。此前需求自行约定15011009未计Flutter分ABI偏移，本轮采用实际上游版本编码，版本更高可覆盖已有包，不为修正文字重新编译或重新签名；发行说明须从APK报告读取实际值，不能继续硬编码旧代码。

ARM64 artifact上传6个文件，比五项发布正文多一个签名辅助文件。追加发布采用严格正文白名单；允许仅附带aarch64-signed.apk.idsig作为不上传的可选辅助文件，其他未知文件仍拦截。先在GitHub列出实际下载文件名并复核，再上传。为复用已完成的两平台构建，新增独立追加发布入口，分别指定原ARM64/Windows来源run并验证各自真实head_sha；只重跑发布核验，不重编译。原二进制与原正式版附件均保持不变，来源与设备待验收状态继续准确记录。


### v0.7 追加发布完成（2026-10-20 00:42，Asia/Shanghai）

[独立发布39287683611](https://github.com/hacxer/rustdesk/actions/runs/39287683611)成功，已将两个新包及独立报告追加至[原正式版v1.5.0-9394-build9](https://github.com/hacxer/rustdesk/releases/tag/v1.5.0-9394-build9)。Release ID417427248、原标签目标及原五个附件ID/摘要保持不变；draft=false、prerelease=false、Latest仍指向该版本。新增正文白名单与每项服务端SHA-256、大小均验证通过；实际存在的aarch64-signed.apk.idsig未作为必需安装附件发布。

| 新包 | 最终校验与来源 | 字节数 / SHA-256 |
| --- | --- | --- |
| aarch64-signed.apk | arm64-v8a / ELF64 AArch64，minSdk22、target36，1.5.0.9394 / 15013009；V1/V2及原证书通过。源run39279619028，扩展aec372ecddbddb8132426f84acd8f168f003e051 | 30,601,356 / e81eeb67fbe76ba34a0727aeedee312188562b677605dc3126cfa3a55aef7e7a |
| x86_64.exe | AMD64 PE、完整Flutter自解压包、嵌入配置及版本命令冒烟通过；Authenticode未签名。源run39281643811，扩展037f045a5397542b79a0809b1e89d6dc6c4f8c13 | 28,661,760 / 71b5e42c75cc7da35204b950c7f6f853e533c814b2607b805d2374b95ffe684b |

两平台清单均匹配基准profile ece437c54f2a22da2e212b19ca2f84e8d45899fb、上游fada664df7a294d1d1a9ca3e7cd3637069122f17与公开配置摘要90e2e177cbca2bf4553a1d1f544c7fc57eed84894cf6f74fea20b729be2f1ffd。ARM32摘要仍为2447958f38f0e6967343fd55ea25c229d608915e830c7c0059b206f1974e6b77。每个平台实际来源与仅执行上传的发布任务分别记录，未把重试/发布提交冒充原构建。

附件新增aarch64与Windows独立manifest、摘要与校验报告，以及SHA256SUMS-extra；总计15个上传附件，另有GitHub自动生成的两项源码归档。Windows无代码签名证书、安装后服务/重启及新增平台完整远控仍待设备验收；T2继续使用ARM32并按原清单验收，不能将ARM64或编译成功代替T2实测。全程源码、编译、签名、打包和上传均在GitHub完成。


## 20. v0.8 / R46 Windows x86 Sciter版（先需求、后实现）

用户要求再生成x86-sciter.exe，沿用当前正式版本的服务器、公钥、默认选项及Secret注入固定密码。目标为i686-pc-windows-msvc的Windows 32位Sciter UI完整自解压客户端，不得用x64 Flutter包改名。采用同一冻结上游fada664df7a294d1d1a9ca3e7cd3637069122f17、hbb_common229b904508364c8997aad0fb5af57effac859f60、build9 profile ece437c54f2a22da2e212b19ca2f84e8d45899fb及公开配置SHA-256 90e2e177cbca2bf4553a1d1f544c7fc57eed84894cf6f74fea20b729be2f1ffd。

- Sciter使用上游legacy UI及对应x86 Rust/Sciter适配，不切换产品配置；沿用Windows核心/服务初始化、只手动刷新临时密码和原有登录限流。初始化模块与公开配置必须核对相同摘要；保留已有非空服务器、自定义密码和用户后续选择。安装后自动服务沿用上游，便携运行不自动安装服务。
- 工具链按冻结上游Sciter CI：Windows2022、i686 MSVC nightly-2023-10-13、32位LLVM15.0.6、x86-windows-static依赖；sciter-rs固定上游x86补丁674e07d3066ca9a92ced3816203ab6b652629d1e，运行时Sciter DLL记录真实来源提交和摘要，不依赖未记录的浮动文件。
- 发布前校验主程序、Sciter运行库及自解压外壳PE I386/PE32；完整内嵌UI、配置和打包payload摘要；在GitHub runner完成不安装的版本/启动冒烟。虚拟显示如含上游x64辅助驱动文件，单独列出用途，不误判为x86主程序。未提供Windows签名证书，明确Authenticode未签名。
- 追加同一正式Release v1.5.0-9394-build9，保留原标签、Latest/正式状态与全部既有附件ID、大小和摘要；不覆盖同名不同内容文件。新增独立manifest、SHA256和校验报告，准确记录新构建run和扩展提交。全部源码编辑、编译、打包及上传在GitHub完成，本地不安装构建工具或运行新EXE。
- Sciter界面属上游旧版，不能承诺与Flutter所有菜单功能完全一致；Windows32位/64位实际远控、输入、剪贴板、安装服务与重启及老系统兼容仍待设备验收，不以PE32或GitHub构建通过替代实测。每次失败先在本节记录原因与验收修订，再改脚本重试。


### P047 新版Rustup拦截旧i686 host工具链

首次Sciter任务39359619230在安装工具链阶段失败：rustup提示nightly-2023-10-13-i686-pc-windows-msvc may not be able to run on this system，并要求--force-non-host。配置准备及32位LLVM已通过，尚未编译客户端。GitHub Windows2022 runner为64位、可通过WOW64运行32位程序；保持上游指定的i686编译器及版本，改用显式rustup toolchain install --force-non-host，再选择该已安装工具链并打印rustc详细版本。该选项只允许安装交叉host工具链，不关闭产品安全检查、不更换依赖或服务器参数。重试必须实际运行i686 rustc成功并继续PE32/完整包校验。
