# 飞牛 fnOS FPK 详细参考

## manifest 完整字段说明

### 必填字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `appname` | 应用唯一标识符 | `com.example.myapp` |
| `version` | 版本号 `x[.y[.z]][-build]` | `1.0.0`、`2.1.3-beta` |
| `display_name` | 应用中心显示名称 | `我的应用` |
| `desc` | 应用详细介绍（支持HTML） | `这是一个<b>示例</b>应用` |
| `source` | 应用来源，固定为 `thirdparty` | `thirdparty` |

### 系统要求

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `platform` | 架构类型 V1.1.8+ | `x86` |
| `os_min_version` | 最低系统版本 | - |
| `os_max_version` | 最高系统版本 | - |

**platform 可选值**：
- `x86` - 仅支持 x86 架构
- `arm` - 仅支持 arm 架构
- `loongarch` - loongarch 架构（暂未支持）
- `risc-v` - risc-v 架构（暂未支持）
- `all` - 所有架构（适用于 Docker 应用，即将支持）

**注意**：`arch` 字段已废弃，使用 `platform` 替代。不支持多个值填写。

### 开发者信息

| 字段 | 说明 |
|------|------|
| `maintainer` | 应用开发者/团队名称 |
| `maintainer_url` | 开发者网站 |
| `distributor` | 应用发布者 |
| `distributor_url` | 发布者网站 |

### 安装控制

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `ctl_stop` | 是否显示启停按钮。设为 `false` 时隐藏启停按钮和运行状态，适用于无进程应用 | `true` |
| `install_type` | `root` 安装到 `/usr/local/apps/@appcenter/`，空则用户选择 `/vol${x}/@appcenter/` | 空 |
| `install_dep_apps` | 依赖列表 `app1>2.2.2:app2:app3`，`>` 表示最低版本要求 | - |

### 用户界面（桌面图标）

| 字段 | 说明 |
|------|------|
| `desktop_uidir` | Web UI 目录路径（相对于应用根目录，即 target），通常为 `ui` |
| `desktop_applaunchname` | 默认入口 ID（必须与 `{uidir}/config` 中 `.url` 下的 key 一致） |

**开发时** `ui/` 目录放在 `app/` 下（`app/ui/`），因为 `app/` 在打包后对应 `target`。

### 端口管理

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `service_port` | 应用监听端口（单个端口） | - |
| `checkport` | 启动前是否检查端口占用 | `true` |

### 其他

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `disable_authorization_path` | 禁用授权目录功能 | `false` |
| `changelog` | 更新日志（升级时展示） | - |

---

## config/privilege 完整说明

### 默认权限模式（推荐）

```json
{
    "defaults": {
        "run-as": "package"
    },
    "username": "myapp_user",
    "groupname": "myapp_group"
}
```

- 系统自动创建专用用户和用户组
- 未指定 username/groupname 时使用 manifest 中的 `appname`
- 应用只能访问自己的目录和系统允许的公共资源

### Root 权限模式

```json
{
    "defaults": {
        "run-as": "root"
    },
    "username": "myapp_user",
    "groupname": "myapp_group"
}
```

**重要**：仅官方合作企业开发者可发布 root 权限应用。

### 文件夹权限（folder-permission）

声明应用需要访问的额外系统目录。通常与 `run-as: "root"` 配合使用（root 权限应用需明确声明访问范围）。

```json
{
    "defaults": {
        "run-as": "root"
    },
    "folder-permission": {
        "rw": ["/var/log", "/some/path"],
        "ro": ["/var/log"]
    }
}
```

**注意**：`run-as: "package"` 模式下应用只能访问自己的目录和系统公共资源，如需访问外部目录建议通过 `data-share` 或用户在应用设置中手动授权。

### 外部文件访问

用户可在应用设置中授权目录访问：
- 禁止访问
- 只读权限
- 读写权限

也可通过 `config/resource` 的 `data-share` 设置默认共享目录。

---

## config/resource 完整说明

### data-share 共享目录

```json
{
    "data-share": {
        "shares": [
            {
                "name": "shared-folder-name",
                "permission": {
                    "rw": ["appname"]
                }
            }
        ]
    }
}
```

声明的共享目录自动创建在应用的 `shares/` 下，实际路径为 `/vol[x]/@appshare/shared-folder-name`。

权限数组说明：
- `"rw": ["appname"]` 中的数组元素为 privilege 中定义的 `username`
- 若 privilege 未指定 `username`，默认使用 manifest 中的 `appname`
- 多个应用共享同一目录时，可在数组中列出多个用户名

权限类型：
- `rw` - 读写权限：应用可以读取和修改文件
- `ro` - 只读权限：应用只能读取文件

### usr-local-linker 系统集成

应用启动时自动创建软链接到系统目录，应用停止时自动移除：

```json
{
    "usr-local-linker": {
        "bin": ["bin/myapp-cli", "bin/myapp-server"],
        "lib": ["lib/mylib.so", "lib/mylib.a"],
        "etc": ["etc/myapp.conf", "etc/myapp.d/default.conf"]
    }
}
```

链接说明：
- `bin` → `/usr/local/bin/` — 可执行文件
- `lib` → `/usr/local/lib/` — 库文件
- `etc` → `/usr/local/etc/` — 配置文件

使用场景：
- 命令行工具：提供 CLI 工具供其他应用使用
- 开发库：提供共享库供其他应用调用
- 配置文件：提供标准配置文件供系统使用

### docker-project Docker 项目支持

将 Docker Compose 配置集成到 fnOS Docker 管理界面：

```json
{
    "docker-project": {
        "compose-file": "docker-compose.yml",
        "project-name": "myapp"
    }
}
```

- `compose-file` — Docker Compose 文件路径（相对于 target）
- `project-name` — Docker 项目名称
- 安装后在 fnOS Docker 管理界面可见并可管理
- 适用于基于 Docker 的应用

---

## wizard 表单项完整说明

### text 文本输入

```json
{
    "type": "text",
    "field": "wizard_username",
    "label": "用户名",
    "initValue": "admin",
    "description": "字段说明文字",
    "rules": [
        { "required": true, "message": "请输入用户名" },
        { "min": 3, "max": 20, "message": "长度限制" },
        { "pattern": "^[a-zA-Z0-9_]+$", "message": "格式限制" }
    ]
}
```

### password 密码输入

```json
{
    "type": "password",
    "field": "wizard_password",
    "label": "密码",
    "rules": [
        { "required": true, "message": "请输入密码" },
        { "min": 6, "message": "密码不少于6位" }
    ]
}
```

### radio 单选

```json
{
    "type": "radio",
    "field": "wizard_install_type",
    "label": "安装类型",
    "initValue": "standard",
    "options": [
        { "label": "标准安装", "value": "standard" },
        { "label": "自定义安装", "value": "custom" }
    ],
    "rules": [{ "required": true, "message": "请选择" }]
}
```

### checkbox 多选

```json
{
    "type": "checkbox",
    "field": "wizard_modules",
    "label": "安装模块",
    "initValue": ["web", "api"],
    "options": [
        { "label": "Web界面", "value": "web" },
        { "label": "API接口", "value": "api" },
        { "label": "数据库", "value": "database" }
    ],
    "rules": [{ "required": true, "message": "至少选一个" }]
}
```

### select 下拉选择

```json
{
    "type": "select",
    "field": "wizard_database_type",
    "label": "数据库类型",
    "initValue": "sqlite",
    "options": [
        { "label": "SQLite (推荐)", "value": "sqlite" },
        { "label": "MySQL", "value": "mysql" }
    ],
    "rules": [{ "required": true, "message": "请选择" }]
}
```

### switch 开关

```json
{
    "type": "switch",
    "field": "wizard_enable_backup",
    "label": "启用自动备份",
    "initValue": "true"
}
```

### tips 提示文本

```json
{
    "type": "tips",
    "helpText": "支持 <a href='https://example.com'>HTML链接</a> 格式"
}
```

### 验证规则汇总

| 规则 | 字段 | 说明 |
|------|------|------|
| 必填 | `required: true` | 不能为空 |
| 最小长度 | `min: N` | 最少 N 个字符 |
| 最大长度 | `max: N` | 最多 N 个字符 |
| 精确长度 | `len: N` | 恰好 N 个字符 |
| 正则 | `pattern: "regex"` | 正则表达式匹配 |

每条规则都需要 `message` 字段作为错误提示。

### 向导最佳实践

**设计原则**：
- 步骤尽量少，只收集必要配置项
- 提供合理的默认值（`initValue`），减少用户操作
- 密码字段不设默认值，使用 `password` 类型隐藏输入
- 使用 `tips` 类型提供上下文帮助信息

**安全考虑**：
- 敏感信息使用 `password` 类型
- 在 callback 脚本中验证输入，不要盲目信任向导值
- 避免在 `tips` 的 HTML 中暴露敏感信息

**用户体验**：
- 每步一个主题（如"基本配置"、"认证信息"）
- 使用 `description` 字段为复杂表单项添加说明
- 卸载向导中提供数据保留选项（推荐默认保留）
- `switch` 的 `initValue` 必须是字符串 `"true"` 或 `"false"`

---

## 系统环境变量完整列表

### 路径变量

| 变量 | 说明 | 对应目录 |
|------|------|---------|
| `TRIM_APPDEST` | 应用可执行文件目录 | target |
| `TRIM_PKGVAR` | 运行时数据目录 | var |
| `TRIM_PKGETC` | 静态配置目录 | etc |
| `TRIM_PKGHOME` | 用户数据目录 | home |
| `TRIM_PKGTMP` | 临时文件目录 | tmp |
| `TRIM_PKGMETA` | 元数据目录 | meta |
| `TRIM_APPDEST_VOL` | 应用安装的存储空间路径 | - |

### 应用信息变量

| 变量 | 说明 |
|------|------|
| `TRIM_APPNAME` | 应用名称（来自 manifest appname） |
| `TRIM_APPVER` | 应用版本号（来自 manifest version） |
| `TRIM_OLD_APPVER` | 升级前的版本号（仅在 upgrade 脚本中可用） |
| `TRIM_SERVICE_PORT` | manifest 声明的服务端口 |

### 用户和权限变量

| 变量 | 说明 |
|------|------|
| `TRIM_USERNAME` | 应用专用用户名 |
| `TRIM_GROUPNAME` | 应用专用用户组名 |
| `TRIM_UID` | 应用用户 ID |
| `TRIM_GID` | 应用用户组 ID |
| `TRIM_RUN_USERNAME` | 实际运行用户（root 或应用用户） |
| `TRIM_RUN_GROUPNAME` | 实际运行用户组 |
| `TRIM_RUN_UID` | 实际运行用户 ID |
| `TRIM_RUN_GID` | 实际运行用户组 ID |

### 数据和日志变量

| 变量 | 说明 |
|------|------|
| `TRIM_TEMP_LOGFILE` | 用户可见系统日志文件路径（写入错误信息前端展示） |
| `TRIM_DATA_SHARE_PATHS` | 数据共享路径列表（多个路径用冒号分隔） |
| `TRIM_DATA_ACCESSIBLE_PATHS` | 授权目录列表（冒号分隔，V1.1.8+，变更时通过 config 流程通知） |

### 向导变量

向导中 `field` 字段名直接作为环境变量名，仅在对应 callback 脚本中可用：

```bash
# wizard/install 中 field: "wizard_loki_url"
# 在 cmd/install_callback 中：
echo "$wizard_loki_url"
```

---

## 生命周期详细流程

### 安装流程
1. `install_init` - 安装前准备（环境检查、依赖确认）
2. 系统解压文件
3. `install_callback` - 安装后处理（初始化配置、创建目录）

### 卸载流程
1. 如应用运行中 → 先调用 `main stop`
2. `uninstall_init` - 卸载前准备
3. 系统删除 `target`、`tmp`、`home`、`etc`
4. `uninstall_callback` - 卸载后清理
5. **保留** `var` 和 `shares`（保护用户数据）

### 更新流程
1. 如应用运行中 → 先调用 `main stop`
2. `upgrade_init` - 更新前准备（数据备份）
3. 系统替换文件
4. `upgrade_callback` - 更新后处理（数据库迁移、配置迁移）
5. 如原本运行中 → 调用 `main start`

### 配置流程
1. `config_init` - 配置前准备
2. 系统更新环境变量
3. `config_callback` - 配置后处理（重载配置）

### 错误处理（V1.1.8+）

```bash
# 在任何脚本中遇到错误：
echo "错误描述信息" > "${TRIM_TEMP_LOGFILE}"
exit 1
```

**规则**：
- 必须写入 `$TRIM_TEMP_LOGFILE`，否则系统展示 "执行XX脚本出错且原因未知"
- 不要直接 `exit` 不带错误码
- 不要直接 `echo` 到 stdout，要写入日志文件

---

## 应用状态监控

系统通过 `cmd/main status` 检测应用健康状态：
- 返回 `exit 0` = 运行中
- 返回 `exit 3` = 未运行

检查时机：
- 应用运行期间定期轮询
- 应用启动前检查一次

典型实现：

```bash
status)
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" | tr -d '[:space:]')
        if kill -0 "$pid" 2>/dev/null; then
            exit 0
        fi
        rm -f "$PID_FILE"
    fi
    exit 3
    ;;
```

---

## 桌面图标配置完整说明

### 目录结构

```
app/                        # 开发目录（打包后 → target / TRIM_APPDEST）
└── ui/                     # desktop_uidir 指向此目录
    ├── images/
    │   ├── icon-64.png     # 64x64 桌面图标
    │   └── icon-256.png    # 256x256 桌面图标
    └── config              # 入口配置（JSON）
```

### app/ui/config 完整格式

```json
{
    ".url": {
        "{appname}.{entry_id}": {
            "title": "显示标题",
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

### 字段详细说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `.url` | object | 是 | 顶层 key，所有入口定义在此对象下 |
| `{appname}.{id}` | key | 是 | 入口唯一 ID，**必须以 manifest appname 为前缀**（如 `com.example.myapp.main`） |
| `title` | string | 是 | 桌面图标显示名称 |
| `icon` | string | 是 | 图标文件路径（相对于 ui 目录），`{0}` 为尺寸占位符（系统替换为 64 或 256） |
| `type` | string | 是 | 入口打开方式：`url`（浏览器新标签页）/ `iframe`（内嵌在 fnOS 桌面窗口中） |
| `protocol` | string | 是 | 访问协议：`http` / `https` |
| `port` | string | 条件 | 应用端口（**字符串类型**），应与 manifest `service_port` 一致。通过反向代理访问时可不声明（CGI 方案） |
| `url` | string | 是 | 应用访问路径（相对路径，如 `/`、`/admin`、`/dashboard`） |
| `allUsers` | boolean | 否 | 是否所有用户可见，默认 `true`。设为 `false` 则仅管理员可见 |

### 图标文件

- `{0}` 是尺寸占位符，系统自动用 `64` 和 `256` 替换
- 例如 `images/icon-{0}.png` → 加载 `images/icon-64.png` 和 `images/icon-256.png`
- 必须提供两个尺寸文件
- 图标文件位于 `app/ui/images/` 下（开发时）

### manifest 与 config 的关联

```
manifest:
  desktop_uidir         = ui                           ← 指向 target/ui/ 目录
  desktop_applaunchname = com.example.myapp.main       ← 对应 config 中的 key

app/ui/config:
  { ".url": { "com.example.myapp.main": { ... } } }   ← 与上面的值一致
```

`desktop_applaunchname` 指定应用中心"打开"按钮使用的默认入口。如有多入口，其余入口仅在桌面显示独立图标。

### 协议适配（HTTP vs HTTPS）

fnOS 桌面图标点击时，URL 拼接逻辑为：`{protocol}://{当前浏览器hostname}:{port}{url}`

**场景对比**：

| 用户访问方式 | config protocol | config port | 拼接结果 | 是否可用 |
|---|---|---|---|---|
| `http://192.168.1.100:5666` | `http` | `8080` | `http://192.168.1.100:8080/` | 可用 |
| `https://nas.example.com` | `http` | `8080` | `http://nas.example.com:8080/` | 不可用（协议降级 + 端口不可达） |
| `https://nas.example.com` | `https` | - (不声明) | `https://nas.example.com/app-path/` | 可用（需反代配置） |

**推荐做法**：

1. **应用原生只支持 HTTP**（常见情况）：声明 `"protocol": "http"` + `"port"`，适用于局域网 HTTP 直连。HTTPS 场景需用户自行配置反向代理。
2. **应用支持 HTTPS**（自带证书）：声明 `"protocol": "https"` + `"port"`。
3. **通过 fnOS 反代**（CGI 方案）：不声明 `port`，由 fnOS 内置 Nginx 转发。协议自动跟随主页面。

### 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `stat .../app/ui: no such file or directory` | `ui/` 放在了项目根目录而非 `app/` 下 | 移到 `app/ui/` |
| 桌面无图标 | `.url` key 缺失或入口 key 未使用 appname 前缀 | 检查 config JSON 格式 |
| 点击图标 404 | `port` 或 `url` 与实际服务不匹配 | 确认端口和路径 |
| 图标显示空白 | 图标文件缺失或命名不含 `{0}` 占位符 | 检查 `images/icon-64.png` 和 `icon-256.png` 是否存在 |
| HTTPS 页面点击图标无法打开 | config 声明 `http` 但主页面是 `https` | 协议降级被浏览器拦截，需改用反向代理或 HTTPS |
| 点击图标连接超时 | 声明了 `port` 但端口未对外暴露 | 反代场景不声明 `port`，或确保端口可达 |
