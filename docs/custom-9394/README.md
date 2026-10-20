# RustDesk 9394 GitHub 构建入口

**当前正式版：[v1.5.0-9394-build9 / Latest](https://github.com/hacxer/rustdesk/releases/tag/v1.5.0-9394-build9)。2026-10-20已补齐ARM64、Windows x64及Windows x86 Sciter。**

| 平台 | 直接下载 | 校验说明 |
| --- | --- | --- |
| Android ARM32 | [armv7-signed.apk](https://github.com/hacxer/rustdesk/releases/download/v1.5.0-9394-build9/armv7-signed.apk) | 原build9不变；V1/V2及原证书，15011009；T2真机待验收 |
| Android ARM64 | [aarch64-signed.apk](https://github.com/hacxer/rustdesk/releases/download/v1.5.0-9394-build9/aarch64-signed.apk) | ELF64 AArch64、V1/V2及原证书；实际versionCode15013009 |
| Windows x64 | [x86_64.exe](https://github.com/hacxer/rustdesk/releases/download/v1.5.0-9394-build9/x86_64.exe) | AMD64完整Flutter自解压包；Authenticode未签名 |
| Windows x86 Sciter | [x86-sciter.exe](https://github.com/hacxer/rustdesk/releases/download/v1.5.0-9394-build9/x86-sciter.exe) | I386/PE32完整Sciter自解压包；Authenticode未签名 |

四个平台使用相同固定上游与build9公开配置。新增包分别记录实际构建run和扩展提交，校验摘要、独立manifest及报告见Release附件，详细记录见validation.md。Android按下方清单由安装人员交付前配置；Windows需完成上游安装流程才具备安装后的自动服务。新增平台完整设备运行、安装后重启及30分钟稳定性仍待验收。下方Actions ZIP为原构建归档入口。

- [需求与问题记录](requirements.zh-CN.md)
- [构建及设备验收](validation.md)
- [armv7 Actions](https://github.com/hacxer/rustdesk/actions/workflows/custom-9394-armv7.yml)

## 首阶段：armv7

在 Actions 选择 `9394 armv7 - SUNMI T2 Android 7.1` → `Run workflow`，分支选 `master`；`Upstream tag or SHA` 填上游正式 tag（首版为 `1.5.0`）或已审查的完整提交 SHA。

工作流在 GitHub runner 中检出该版本与子模块，严格匹配并应用本仓库的定制适配，然后编译。上游变化导致适配锚点或 Android 7.1 前置条件不匹配时会失败，必须先把问题、日志和验收标准加入需求文档，再改配置/适配脚本；不能静默跳过补丁。

成功后下载 `armv7-signed-9394-运行编号` artifact ZIP，内含 `armv7-signed.apk`、`SHA256SUMS`、`build-manifest.json`、签名校验和 APK 信息。只有签名和 ABI 检查通过才会上传这个交付产物。名称含 `unverified-checkpoint` 的 artifact 仅用于 CI 故障诊断，未通过最终校验，不作为安装交付包；名称含 `diagnostics` 的 artifact 为非秘密检查报告。

`build-manifest.json` 记录真实上游 SHA、递归子模块、定制提交、配置摘要、工具链、APK 摘要及证书指纹。所有运行状态以 Actions 实际结果为准。产物的商米 T2 验收默认标记 PENDING，不能因构建绿色就改成兼容通过。

## 签名与密码

复用仓库 Secrets：`ANDROID_KEYSTORE_BASE64`、`ANDROID_KEYSTORE_PASSWORD`、`ANDROID_KEY_ALIAS`、`ANDROID_KEY_PASSWORD`、`RUSTDESK_PRESET_PASSWORD`。工作流检查旧 keystore 的约定摘要，并比较旧 APK 与新 APK 的证书；固定密码仅经编译环境注入。不可将私钥或密码加入源码、日志、artifact 或 Release。

## 上游升级与后续平台

更新前先修改需求/问题记录及来源版本，再调整适配，先单独构建并验收 armv7；同一批次的其他平台必须使用相同的上游真实 SHA 和配置。定制适配保存在本仓库独立文件中，无需在本地安装 Rust、Flutter 或 Android 构建工具。

armv7已按用户明确授权正式发布，T2真机验收仍待完成。v0.7新增ARM64及Windows x64，v0.8新增Windows x86 Sciter；均按相同固定上游与build9配置完成构建校验，追加同一正式版。来源和验收范围见validation.md。自动升级PR入口尚未实施，没有启用定时任务。

2026-10-19：按用户要求，APK 安装与雷电模拟器运行测试由用户手动完成；[验收清单](validation.md)包含首次授权、自动服务、认证与远控功能检查。本轮助手完成 GitHub 打包和静态校验后提供交付 artifact 链接。

## v0.4 用户手动回归重点

1. 只安装本轮成功运行中名称为 armv7-signed-9394-运行编号的交付 ZIP 内 APK，先核对 SHA256SUMS 与 build-manifest；不要安装 unverified-checkpoint。保留应用数据覆盖安装，以验证一次迁移和设置保留。
2. 冷启动检查应用内重复提示已去掉；系统要求录屏授权时由用户确认，RustDesk Input 未开时按引导开启。授权后自动继续，不反复请求；主动停止后本会话不自动拉起。
3. 检查 TCP 打洞与 IPv6 P2P 默认开、启动检查更新关闭；本轮升级会一次关闭不可用的 WebSocket 模式，继续使用原生 UDP/TCP。修改开关后再次启动应保留后续选择。
4. 控制端与被控端使用同一组服务器和 Key。连续连接、断开、重连后临时密码保持；手动刷新后产生新六位数字。远程画面、输入、文件和剪贴板逐项测试。
5. 会话建立通知横幅约3秒后收起；必要的前台服务及录屏状态仍保留。API 管理列表按服务端的设备管理和账号筛选分别核对，“我的设备”列表缺失不能单独证明 hbbs 未注册。
6. 雷电 Android7 x86 环境应进入软件界面渲染兼容路径，检查建立共享、切换页面、后台返回与30分钟会话。若再崩溃，保留发生时刻，尽量不要重启或清理日志，再读取对应应用的系统崩溃记录；仅分享脱敏摘要。ARM 商米 T2 保持原渲染路径，仍需真机验收。

助手可按用户授权只读现有雷电日志定位问题；APK 安装、授权和功能回归仍由用户手动执行，诊断不代表已经运行验收通过。


## v0.5 覆盖安装与 TUN 回归

本轮在用户普通U盘侧载条件下，保留必要系统录屏确认；已有有效授权自动使用，系统要求重新授予时不承诺永久免确认。电池优化已豁免就不再请求；未豁免的自动引导只请求一次，拒绝/取消后可从系统设置或开机设置手动处理。

新包首次运行执行一次 UDP 默认迁移：启用UDP打洞，关闭“禁用UDP”；后续主动关闭UDP打洞应保留。请用覆盖安装测试，勿清数据；检查其他服务器、密码、TCP/IPv6、更新检查设置没有被本轮迁移重置。

当前已验证：Clash TUN开启时，模拟器ID后添加 /r 可以通过指定中继看到画面。默认连接失败日志指向模拟器NAT私网直连路径，尚未证明该路径已修复。测试时可输入“模拟器ID/r”（替换为实际ID），只影响本次连接；若希望固定，可在电脑RustDesk该设备的连接选项选择“总是使用中继”。不需要关闭整个Clash，也不要为此给所有设备强制中继。已有私网DIRECT规则并不等同于绕过TUN系统路由。

build8日志已确认自建服务器注册、API系统信息更新及中继会话；未发现安装后的新崩溃，旧模拟器渲染修复已命中。仍需30分钟连续会话、输入/文件/剪贴板及商米T2真机回归，不能将模拟器短时通过作为T2验收。


## 雷电桥接与系统确认（P037/P038）

图中的“不再显示”是Android系统控件，普通APK不能预勾选；请在首次系统请求中手动勾选并确认，后续是否保存由设备系统决定。不要把应用内提示开关误认为系统录屏授权。

本次桥接现场已确认：能访问LAN网关，但全策略路由表缺少IPv4默认路由，所有外部IPv4报os error101。先在雷电/路由器修正DHCP网关，或为模拟器分配路由器保留的静态IP、正确掩码、LAN网关及DNS，保存重启；静态地址应做保留以避免冲突。直到全路由表出现可用IPv4默认网关并收到hbbs注册响应之前，不标记桥接修复。无需更换APK服务器地址，也不能通过ADB root添加临时路由冒充产品修复。

UDP打洞原默认关闭的源码依据：自建服务器下get_local_option在enable-udp-punch为空时返回N。本轮显式LocalConfig默认Y及一次迁移解决这个默认值问题；不保证不可达网络因此自动变得可达。


## 当前下载：v0.5 / build9

[armv7-signed-9394-9 ZIP](https://github.com/hacxer/rustdesk/actions/runs/39234351129/artifacts/12179272527)，解压后覆盖安装armv7-signed.apk（保留数据）。版本1.5.0.9394 / 15011009；V1/V2及原证书、ARM32、minSdk22检查通过。APK SHA-256：2447958f38f0e6967343fd55ea25c229d608915e830c7c0059b206f1974e6b77。清单已标注v0.5，T2硬件仍待验收。

本轮新增UDP默认开启和一次升级迁移，以及电池引导只自动请求一次的记录；已有授权仍按真实系统状态判断。桥接故障已通过用户补齐IPv4网关恢复注册/API/中继，详见验收记录。系统录屏框“不再显示”需要用户首次手动勾选，普通APK无法设置默认勾选；TUN默认直连仍待对照，已验证可用ID/r中继。新包运行回归请按上方v0.5清单执行。


2026-10-19后续复测更新：用户确认桥接网关恢复后，Clash TUN开启、不加/r且不固定中继的普通连接也能显示画面。当前测试仍为build8；最新可读日志实际最终采用中继，不能据“不加/r”声称纯P2P通过。此结果已同步需求第16节和验收记录；无需为文档更新重新编译，build9下载保持不变。


## v0.6 已确认：安装人员交付前统一配置

2026-10-19用户已选择方案A。安装/维护人员完成以下配置和验收后再交付，顾客日常使用不参与授权。需求约定见[第17节](requirements.zh-CN.md)，逐机记录见[验收表](validation.md)。本轮仅落实部署流程，继续使用v0.5/build9，不重新编译。

### 安装人员操作清单

1. 下载上方build9交付ZIP并解压，核对APK摘要及版本15011009。在实际商米T2上记录Android、SUNMI OS和完整固件版本。已有同包名、同证书安装应保留数据覆盖安装，避免卸载或清数据导致配置丢失；安装过程由维护人员手动完成。
2. 首次打开RustDesk，在系统录屏确认框手动勾选“不再显示”（该固件提供此项时），再点击“立即开始”。返回APP，确认屏幕共享服务运行并已接入指定RustDesk服务器；安装人员完成此步骤后再交给顾客。
3. 系统询问忽略电池优化时选择“是”。若此前拒绝或关闭过提示，则进入系统电池优化设置，将RustDesk设为“不优化/允许后台运行”（名称以固件为准）。实际豁免状态必须为true；提示没有出现不代表已经获得豁免。
4. 在系统无障碍设置启用RustDesk Input并返回APP；按该固件提供的界面完成开机自启、后台和悬浮窗权限。确认应用内开机自启开启，录屏、输入控制、传输文件及剪贴板功能逐项实测，不能只核对开关颜色。
5. 完成下方交付检查，在验收表记录结果、时间和固件。保留必要的前台服务/录屏状态及停止入口。权限被撤销、卸载、清数据、恢复出厂或固件变更后，由维护人员重新配置和复验。

### 交付检查

- 多次返回APP和重新启动APP：不重复请求已经保存的授权，可正常注册服务器并远控。
- 系统重启及真实断电再开机：验证无需顾客确认即可恢复预期服务，并可看到远程画面、执行输入；分别记录开机恢复与手动打开APP后的结果。
- 后续同签名覆盖升级：保留数据后复查授权及配置；维护测试机可覆盖安装同包检查保存行为，真实新版本升级仍需单独回归，不能用卸载重装代替。
- 连续远控至少30分钟，验证输入、文件双向传输、双向剪贴板、断线重连、无崩溃/ANR，并记录2GB真机内存及剩余存储。

T2固件是否保存跨重启投屏许可必须实测。如果安装人员已勾选并同意后仍重复弹窗，记录具体固件、操作步骤及发生时刻，先补充需求问题记录，再读取脱敏日志决定修复；该设备不标记“交付后免重复授权通过”。必要时再核实商米官方预授权能力。普通APK不自行代点系统按钮或伪造授权。

当前状态：方案A已确认，安装人员执行与T2真机验收待完成。build9已通过ARM32、V1/V2及原签名静态检查；本节不表示首次静默授权或T2运行验收已通过。


## v0.8 Windows x86 Sciter 下载与构建

[x86-sciter.exe](https://github.com/hacxer/rustdesk/releases/download/v1.5.0-9394-build9/x86-sciter.exe)为Windows32位Sciter旧版UI完整自解压客户端，15,217,152字节，SHA-256：a9eb897532e189d2c1f16300f566fc6f210092dbdfe942b9cb6950643576a3e4。主程序、Sciter DLL与外壳均PE32/I386，内嵌文件逐项核验及版本命令冒烟通过；Authenticode未签名。界面与Flutter有所不同，旧Windows兼容及真实远控、安装后服务/重启仍待设备验收。便携运行不等于安装开机服务。

[成功构建与发布39360221285](https://github.com/hacxer/rustdesk/actions/runs/39360221285)，来源扩展350cb6e7e2ea34ea7a5534e2712cacf2eb9b3931，沿用build9上游、配置及共用初始化。独立manifest、SHA256及验证JSON见同一Release附件；原ARM32、ARM64及Windows x64附件不变。

后续手动构建入口：[9394 Windows x86 Sciter package](https://github.com/hacxer/rustdesk/actions/workflows/custom-9394-x86-sciter.yml)。同名已发布包若摘要不同，发布步骤会拒绝覆盖；新迭代先更新需求并规划新版本/文件名，不强行覆盖正式包。
