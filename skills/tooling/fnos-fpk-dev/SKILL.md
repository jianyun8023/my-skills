---
name: fnos-fpk-dev
description: 飞牛 fnOS FPK 应用包开发指南。涵盖目录结构、manifest 配置、生命周期脚本、用户向导、权限管理、resource 资源声明和桌面图标配置。Use when developing fnOS FPK packages, creating fnOS apps, writing cmd scripts, configuring wizard/manifest/privilege/resource, desktop icons, ui/config, or when the user mentions 飞牛、fnOS、fpk。
---

# 飞牛 fnOS FPK 应用开发

## 应用目录结构

FPK 安装后的标准目录结构：

```
/var/apps/[appname]
├── cmd/                    # 生命周期脚本（必须）
│   ├── main                # 启停和状态检查
│   ├── install_init        # 安装前
│   ├── install_callback    # 安装后
│   ├── uninstall_init      # 卸载前
│   ├── uninstall_callback  # 卸载后
│   ├── upgrade_init        # 更新前
│   ├── upgrade_callback    # 更新后
│   ├── config_init         # 配置前
│   └── config_callback     # 配置后
├── config/
│   ├── privilege           # 权限声明（JSON）
│   └── resource            # 资源/能力声明（JSON）
├── wizard/
│   ├── install             # 安装向导（JSON）
│   ├── uninstall           # 卸载向导（JSON）
│   ├── upgrade             # 更新向导（JSON）
│   └── config              # 配置向导（JSON）
├── manifest                # 应用身份信息（key=value）
├── ICON.PNG                # 小图标 64x64
├── ICON_256.PNG            # 大图标 256x256
├── LICENSE                 # 隐私协议（可选）
├── etc -> /vol[x]/@appconf/[appname]    # 静态配置
├── home -> /vol[x]/@apphome/[appname]   # 用户数据
├── target -> /vol[x]/@appcenter/[appname] # 可执行文件（TRIM_APPDEST）
│   └── ui/                 # 桌面图标 Web UI 配置（可选，由 desktop_uidir 指定）
│       ├── images/
│       │   ├── icon-64.png   # 64x64 桌面图标
│       │   └── icon-256.png  # 256x256 桌面图标
│       └── config            # 入口配置文件（JSON）
├── tmp -> /vol[x]/@apptemp/[appname]    # 临时文件（TRIM_PKGTMP）
├── var -> /vol[x]/@appdata/[appname]    # 运行时数据（TRIM_PKGVAR）
├── meta -> /vol[x]/@appmeta/[appname]   # 应用元数据（TRIM_PKGMETA）
└── shares/                 # 数据共享目录（由 resource 定义）
```

## 开发目录与安装目录映射

| 开发时 | 安装后 | 环境变量 | 说明 |
|--------|--------|---------|------|
| `app/` | `target/` | `TRIM_APPDEST` | 可执行文件、UI 资源 |
| `cmd/` | `cmd/` | — | 生命周期脚本 |
| `config/` | `config/` | — | privilege + resource |
| `wizard/` | `wizard/` | — | 向导定义 |
| `manifest` | `manifest` | — | 应用元信息 |
| `ICON.PNG` | `ICON.PNG` | — | 小图标 64x64 |
| — | `var/` | `TRIM_PKGVAR` | 运行时数据（系统创建） |
| — | `etc/` | `TRIM_PKGETC` | 静态配置（系统创建） |
| — | `home/` | `TRIM_PKGHOME` | 用户数据（系统创建） |
| — | `tmp/` | `TRIM_PKGTMP` | 临时文件（系统创建） |
| — | `meta/` | `TRIM_PKGMETA` | 元数据（系统创建） |
| — | `shares/` | — | 共享目录（由 resource 定义） |

**关键**：`app/` 目录对应安装后的 `target`（`TRIM_APPDEST`），桌面 UI 配置必须放在 `app/ui/` 下。

## 核心系统环境变量

所有 `cmd/` 脚本中可用，完整列表见 [reference.md](reference.md)。

### 常用路径变量

| 变量 | 说明 |
|------|------|
| `TRIM_APPDEST` | 应用可执行文件目录（target） |
| `TRIM_PKGVAR` | 运行时数据目录（var） |
| `TRIM_PKGETC` | 静态配置目录（etc） |
| `TRIM_PKGHOME` | 用户数据目录（home） |
| `TRIM_PKGTMP` | 临时文件目录（tmp） |

### 常用信息变量

| 变量 | 说明 |
|------|------|
| `TRIM_APPNAME` | 应用名称（来自 manifest appname） |
| `TRIM_APPVER` | 应用版本号（来自 manifest version） |
| `TRIM_OLD_APPVER` | 升级前的版本号（仅在 upgrade 脚本中可用） |
| `TRIM_SERVICE_PORT` | manifest 中声明的服务端口 |
| `TRIM_USERNAME` / `TRIM_GROUPNAME` | 应用专用用户名/组名 |
| `TRIM_RUN_USERNAME` | 实际运行用户（root 或 package 用户） |
| `TRIM_TEMP_LOGFILE` | 系统日志文件路径（写入错误信息供前端展示） |
| `wizard_*` | 向导表单字段值（仅在对应 callback 脚本中可用） |

## cmd/main 脚本（必须）

管理应用的启停和状态检查：

```bash
#!/bin/bash
PID_FILE="${TRIM_PKGVAR}/app.pid"

case $1 in
start)
    # 启动应用，成功返回 0，失败返回 1
    # TODO: 替换为实际启动命令
    exit 0
    ;;
stop)
    # 停止应用，成功返回 0，失败返回 1
    # TODO: 替换为实际停止命令
    exit 0
    ;;
status)
    # 运行中返回 0，未运行返回 3
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" | tr -d '[:space:]')
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            exit 0
        fi
        rm -f "$PID_FILE"
    fi
    exit 3
    ;;
*)
    exit 1
    ;;
esac
```

**关键规则**：
- `status` 返回 `exit 0` = 运行中，`exit 3` = 未运行
- 错误时写入 `$TRIM_TEMP_LOGFILE` 后 `exit 1`，不要直接 `echo`
- 系统会定期轮询 `status` 检查健康状态

## manifest 文件

`key=value` 格式（等号前后无空格），定义应用基本信息：

```ini
appname=com.example.myapp                # 唯一标识（必须）
version=1.0.0                            # 版本号 x[.y[.z]][-build]
display_name=我的应用                      # 显示名称
desc=应用描述，支持HTML                    # 应用介绍
platform=x86                             # x86 | arm | all（V1.1.8+）
source=thirdparty                        # 固定值
maintainer=开发者名称
distributor=发布者名称
service_port=8080                        # 服务端口
checkport=true                           # 启动前检查端口占用
os_min_version=0.9.0                     # 最低系统版本
install_dep_apps=mariaDB:redis           # 依赖应用（冒号分隔，支持版本号 app1>2.0:app2）
desktop_uidir=ui                         # Web UI 目录（相对于应用根目录，即 target）
desktop_applaunchname=com.example.myapp.main  # 入口 ID（对应 ui/config 中 .url 下的 key）
ctl_stop=true                            # 显示启停按钮
install_type=                            # root 安装到系统分区，空则用户选择
changelog=修复已知问题                      # 更新日志（升级时展示）
```

**注意**：
- `arch` 已废弃，使用 `platform` 替代，不支持多个值填写。
- `desktop_applaunchname` 必须与 `app/ui/config` 中 `.url` 下定义的入口 key 一致。
- `ctl_stop=false` 时隐藏启停按钮和运行状态，适用于无进程应用。
- `install_type=root` 时安装到系统分区 `/usr/local/apps/@appcenter/`，为空时用户选择 `/vol${x}/@appcenter/`。
- `install_dep_apps` 格式：`app1>2.2.2:app2:app3`，`>` 表示最低版本要求。

## config/privilege（权限声明）

```json
{
    "defaults": {
        "run-as": "package"
    },
    "username": "myapp",
    "groupname": "myapp"
}
```

- `run-as: "package"` — 应用用户运行（推荐，安全）
- `run-as: "root"` — root 权限运行（仅官方合作开发者可发布）
- 未指定 `username` / `groupname` 时默认使用 manifest 中的 `appname`
- 完整说明（含 `folder-permission`）见 [reference.md](reference.md)

## config/resource（资源声明）

支持三种资源类型，常用的是 `data-share`：

```json
{
    "data-share": {
        "shares": [
            {
                "name": "myapp-data",
                "permission": {
                    "rw": ["myapp"]
                }
            }
        ]
    }
}
```

- `permission` 数组中填写 privilege 中定义的 `username`（未定义则为 manifest `appname`）
- 声明的共享目录自动创建在 `shares/` 下
- 权限类型：`rw`（读写）、`ro`（只读）
- 其他资源类型（`usr-local-linker`、`docker-project`）见 [reference.md](reference.md)

## wizard（用户向导）

JSON 数组格式，每个元素是一个步骤页面：

```json
[
    {
        "stepTitle": "步骤标题",
        "items": [
            { "type": "text|password|radio|checkbox|select|switch|tips", ... }
        ]
    }
]
```

### 表单项类型速查

| 类型 | 用途 | 关键字段 |
|------|------|---------|
| `text` | 文本输入 | field, label, initValue, rules |
| `password` | 密码输入 | field, label, rules |
| `radio` | 单选 | field, label, options, initValue |
| `checkbox` | 多选 | field, label, options, initValue |
| `select` | 下拉选择 | field, label, options, initValue |
| `switch` | 开关 | field, label, initValue（字符串 `"true"` / `"false"`） |
| `tips` | 提示文本 | helpText（支持HTML） |

### 验证规则

```json
{ "required": true, "message": "必填提示" }
{ "min": 3, "max": 20, "message": "长度限制" }
{ "len": 6, "message": "精确长度" }
{ "pattern": "^[a-zA-Z0-9]+$", "message": "正则验证" }
```

### 获取向导输入

向导 `field` 字段名直接作为环境变量名，在对应 callback 脚本中读取：

```bash
LOKI_URL="${wizard_loki_url:-默认值}"
```

## 桌面图标配置（Desktop UI）

为应用添加 fnOS 桌面图标，点击后在浏览器中打开应用 Web UI。

### 开发时目录结构

```
app/
└── ui/                     # 对应 manifest 的 desktop_uidir = ui
    ├── images/
    │   ├── icon-64.png     # 64x64 桌面图标
    │   └── icon-256.png    # 256x256 桌面图标
    └── config              # 入口配置文件
```

**重要**：`app/` 目录 = 安装后的 `target`（`TRIM_APPDEST`）。`ui/` 必须放在 `app/` 下，否则 fnpack 打包时会报 `no such file or directory` 错误。

### manifest 必填字段

```ini
desktop_uidir=ui
desktop_applaunchname=com.example.myapp.main
```

### app/ui/config 格式

入口定义在 `.url` key 下，key 名**必须以 appname 为前缀**：

```json
{
    ".url": {
        "com.example.myapp.main": {
            "title": "我的应用",
            "icon": "images/icon-{0}.png",
            "type": "url",
            "protocol": "http",
            "port": "8080",
            "url": "/",
            "allUsers": true
        }
    }
}
```

### config 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 桌面图标显示名称 |
| `icon` | string | 图标路径（相对于 ui 目录），`{0}` 为尺寸占位符（系统自动替换为 64/256） |
| `type` | string | 入口方式：`url`（新标签页打开）/ `iframe`（内嵌页面） |
| `protocol` | string | 访问协议：`http` / `https` |
| `port` | string | 应用端口（字符串类型），与 manifest `service_port` 一致 |
| `url` | string | 应用访问路径（相对路径，如 `/`、`/admin`） |
| `allUsers` | boolean | 是否所有用户可见，`false` 则仅管理员可见 |

### 关键规则

- 图标 `{0}` 是尺寸占位符，系统自动替换为 64/256，必须提供两个尺寸文件
- `.url` 下的 key 名**必须以 manifest `appname` 为前缀**
- `desktop_applaunchname` 指定默认入口（应用中心"打开"按钮使用）
- `port` 是**字符串类型**，应与 manifest `service_port` 一致

### 协议注意事项

fnOS 桌面点击图标时，URL 拼接逻辑：`{protocol}://{当前浏览器hostname}:{port}{url}`

| 模式 | config 配置 | 适用场景 |
|------|------------|---------|
| 直连（HTTP + IP） | `"protocol": "http", "port": "8080"` | 局域网直接访问 |
| 反代（HTTPS + 域名） | 不声明 `port`，由 fnOS Nginx 反代转发 | 通过域名/HTTPS 访问 |

**注意**：HTTPS 页面中声明 `protocol: "http"` 会导致协议降级和端口不可达。完整的协议适配说明和多入口配置见 [reference.md](reference.md)。

## 生命周期脚本流程

### 安装：install_init → 解压文件 → install_callback
### 卸载：uninstall_init → 删除文件 → uninstall_callback
### 更新：upgrade_init → 替换文件 → upgrade_callback
### 配置：config_init → 更新环境变量 → config_callback

卸载保留 `var` 和 `shares` 目录（保护用户数据）。

## 错误处理（V1.1.8+）

脚本中遇到错误时，写入 `TRIM_TEMP_LOGFILE` 后 `exit 1`：

```bash
if [ ! -f "$TRIM_PKGETC/config.conf" ]; then
    echo "配置文件不存在，应用启动失败！" > "${TRIM_TEMP_LOGFILE}"
    exit 1
fi
```

系统会将内容以 Dialog 对话框形式展示给用户。

## 打包工具 fnpack

使用 `fnpack` 命令行工具创建和打包 FPK 应用：

```bash
# 创建应用项目骨架
fnpack create myapp

# 打包为 .fpk 文件
fnpack pack [项目目录]
```

- 下载地址：https://developer.fnnas.com/docs/cli/fnpack
- 打包前确保 `app/` 目录包含所有需要部署到 `target` 的文件
- 桌面图标的 `ui/` 目录必须放在 `app/` 下，否则打包报错

## Bash 脚本安全实践

所有 `cmd/` 脚本建议遵循：

- **变量加双引号**：`"$TRIM_PKGVAR"` 而非 `$TRIM_PKGVAR`，防止路径含空格时出错
- **错误写入日志**：遇到错误必须写入 `"${TRIM_TEMP_LOGFILE}"`，不要直接 `echo` 到 stdout
- **明确退出码**：成功 `exit 0`，失败 `exit 1`，status 未运行 `exit 3`
- **用 `$TRIM_APPNAME` 构建路径**：不要硬编码 `/var/apps/com.example.myapp`，用 `/var/apps/${TRIM_APPNAME}`
- **heredoc 生成 JSON 时注意转义**：用户输入的特殊字符（引号、反斜杠）可能破坏 JSON 格式，建议在 callback 中校验

## 调试技巧

- **模拟环境变量**：本地测试脚本时，手动 `export TRIM_PKGVAR=/tmp/test-var` 等模拟环境
- **查看错误日志**：脚本失败后查看 `$TRIM_TEMP_LOGFILE` 中写入的内容
- **验证打包内容**：`fnpack pack` 生成的 `.fpk` 实质是压缩包，可解压检查文件结构是否正确
- **检查脚本权限**：常见问题是脚本缺少执行权限，确保 `chmod +x cmd/*`
- **Docker 应用调试**：在 fnOS 终端中手动执行 `docker compose` 命令排查容器启动失败

## 开发检查清单

- [ ] `manifest` 包含所有必填字段（`key=value` 格式，无空格）
- [ ] `cmd/main` 正确处理 start/stop/status
- [ ] `status` 返回码正确（0=运行中, 3=未运行）
- [ ] `config/privilege` 权限声明合理（优先 package）
- [ ] `wizard/install` 提供合理默认值和验证规则
- [ ] callback 脚本正确读取 wizard 环境变量
- [ ] 错误信息写入 `$TRIM_TEMP_LOGFILE`
- [ ] 图标文件：ICON.PNG(64x64) + ICON_256.PNG(256x256)
- [ ] 脚本有执行权限（`chmod +x cmd/*`）
- [ ] 桌面图标（如需要）：`app/ui/config` 格式正确、`.url` key 下使用 appname 前缀、`app/ui/images/` 包含 64 和 256 尺寸图标
- [ ] 使用 `fnpack pack` 打包并在 fnOS 上测试安装

## 详细参考

- manifest 完整字段说明：[reference.md](reference.md)
- 实际项目示例：[examples.md](examples.md)
- 官方文档：https://developer.fnnas.com/docs/core-concepts/framework
- 打包工具：https://developer.fnnas.com/docs/cli/fnpack
