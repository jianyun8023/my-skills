# 飞牛 fnOS FPK 开发示例

## 示例 1：最小化应用骨架

### 目录结构

```
myapp/
├── app/                    # 打包后 → target（TRIM_APPDEST）
│   └── ui/                 # 桌面图标配置（可选）
│       ├── images/
│       │   ├── icon-64.png
│       │   └── icon-256.png
│       └── config
├── cmd/
│   ├── main
│   ├── install_init
│   ├── install_callback
│   ├── uninstall_init
│   ├── uninstall_callback
│   ├── upgrade_init
│   ├── upgrade_callback
│   ├── config_init
│   └── config_callback
├── config/
│   ├── privilege
│   └── resource
├── wizard/
│   └── install
├── manifest
├── ICON.PNG
└── ICON_256.PNG
```

### manifest

```ini
appname=com.example.myapp
version=1.0.0
display_name=我的应用
desc=一个简单的示例应用
platform=x86
source=thirdparty
maintainer=开发者
distributor=发布者
service_port=8080
checkport=true
os_min_version=0.9.0
```

### config/privilege

```json
{
    "defaults": {
        "run-as": "package"
    }
}
```

### config/resource

```json
{
    "data-share": {
        "shares": []
    }
}
```

### cmd/main

```bash
#!/bin/bash
APP_BIN="${TRIM_APPDEST}/myapp"
PID_FILE="${TRIM_PKGVAR}/myapp.pid"
LOG_FILE="${TRIM_PKGVAR}/myapp.log"

start_app() {
    if check_running; then
        return 0
    fi
    
    if [ ! -x "$APP_BIN" ]; then
        echo "应用程序文件不存在或无执行权限" > "${TRIM_TEMP_LOGFILE}"
        exit 1
    fi
    
    nohup "$APP_BIN" \
        --port "$TRIM_SERVICE_PORT" \
        --data "$TRIM_PKGVAR" \
        --config "$TRIM_PKGETC" \
        >> "$LOG_FILE" 2>&1 &
    
    echo $! > "$PID_FILE"
    sleep 2
    
    if check_running; then
        return 0
    else
        echo "应用启动失败，请检查日志" > "${TRIM_TEMP_LOGFILE}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_app() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" | tr -d '[:space:]')
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid"
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    return 0
}

check_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" | tr -d '[:space:]')
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        rm -f "$PID_FILE"
    fi
    return 1
}

case $1 in
start)
    start_app
    ;;
stop)
    stop_app
    ;;
status)
    if check_running; then exit 0; else exit 3; fi
    ;;
*)
    exit 1
    ;;
esac
```

### cmd/install_init（空脚本占位）

```bash
#!/bin/bash
# 安装前准备，不需要可留空
```

### cmd/install_callback

```bash
#!/bin/bash
# 安装后初始化
mkdir -p "${TRIM_PKGVAR}"
mkdir -p "${TRIM_PKGETC}"

# 读取安装向导输入
APP_PORT="${wizard_app_port:-8080}"

# 生成初始配置
cat > "${TRIM_PKGETC}/config.json" << EOF
{
    "port": ${APP_PORT}
}
EOF
```

### cmd/uninstall_callback

```bash
#!/bin/bash
# 卸载后清理
DATA_ACTION="${wizard_data_action:-keep}"
if [ "$DATA_ACTION" = "delete" ]; then
    rm -rf "${TRIM_PKGVAR}"
fi
```

### wizard/install

```json
[
    {
        "stepTitle": "应用配置",
        "items": [
            {
                "type": "tips",
                "helpText": "欢迎安装！请配置应用基本参数。"
            },
            {
                "type": "text",
                "field": "wizard_app_port",
                "label": "应用端口",
                "initValue": "8080",
                "rules": [
                    { "required": true, "message": "请输入端口号" },
                    { "pattern": "^[0-9]+$", "message": "端口号必须是数字" }
                ]
            }
        ]
    }
]
```

---

## 示例 2：版本升级处理（upgrade_callback）

处理配置格式变更和版本迁移的典型模式。

### cmd/upgrade_callback

```bash
#!/bin/bash
LOG_FILE="${TRIM_PKGVAR}/app.log"
SETTINGS_FILE="${TRIM_PKGETC}/settings.json"

log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [upgrade] $1" >> "$LOG_FILE"
}

log_msg "Upgrade callback started: ${TRIM_OLD_APPVER} -> ${TRIM_APPVER}"

# 根据旧版本号执行迁移
case "$TRIM_OLD_APPVER" in
1.0.*)
    log_msg "Migrating from 1.0.x to ${TRIM_APPVER}"
    # 1.0.x → 2.0.0：配置文件格式变更，port 字段从数字改为字符串
    if [ -f "$SETTINGS_FILE" ]; then
        # 备份旧配置
        cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak.${TRIM_OLD_APPVER}"
        log_msg "Old config backed up"
    fi
    # 重新生成配置（使用新格式）
    cat > "$SETTINGS_FILE" << 'EOF'
{
    "version": 2,
    "port": "8080"
}
EOF
    log_msg "Config migrated to v2 format"
    ;;
2.0.*)
    log_msg "Migrating from 2.0.x — no migration needed"
    ;;
*)
    log_msg "Unknown old version: ${TRIM_OLD_APPVER}, skipping migration"
    ;;
esac

# 确保必要目录存在（新版本可能新增了目录需求）
mkdir -p "${TRIM_PKGVAR}/cache"

log_msg "Upgrade callback completed"
```

**关键点**：
- 使用 `TRIM_OLD_APPVER` 判断旧版本，按需执行迁移逻辑
- 升级前**备份旧配置**，便于回退排查
- 使用 `case` 分支处理不同版本区间的迁移路径
- 升级失败时写入 `$TRIM_TEMP_LOGFILE` 并 `exit 1`

---

## 示例 3：Docker 应用（使用 docker-compose）

### cmd/main

```bash
#!/bin/bash
COMPOSE_FILE="${TRIM_APPDEST}/docker-compose.yml"
PROJECT_NAME="myapp"

case $1 in
start)
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    if [ $? -ne 0 ]; then
        echo "Docker 容器启动失败" > "${TRIM_TEMP_LOGFILE}"
        exit 1
    fi
    exit 0
    ;;
stop)
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    exit 0
    ;;
status)
    running=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps --status running -q 2>/dev/null | wc -l)
    if [ "$running" -gt 0 ]; then
        exit 0
    else
        exit 3
    fi
    ;;
*)
    exit 1
    ;;
esac
```

---

## 示例 4：带认证的配置向导

### wizard/config

```json
[
    {
        "stepTitle": "服务配置",
        "items": [
            {
                "type": "tips",
                "helpText": "配置服务连接参数。"
            },
            {
                "type": "text",
                "field": "wizard_server_url",
                "label": "服务器地址",
                "initValue": "http://localhost:8080",
                "rules": [
                    { "required": true, "message": "请输入服务器地址" },
                    { "pattern": "^https?://", "message": "地址必须以 http:// 或 https:// 开头" }
                ]
            },
            {
                "type": "switch",
                "field": "wizard_auth_enabled",
                "label": "启用认证",
                "description": "需要认证时请开启"
            }
        ]
    },
    {
        "stepTitle": "认证信息",
        "items": [
            {
                "type": "tips",
                "helpText": "如需认证请填写以下信息，否则可跳过。"
            },
            {
                "type": "text",
                "field": "wizard_auth_username",
                "label": "用户名",
                "initValue": ""
            },
            {
                "type": "password",
                "field": "wizard_auth_password",
                "label": "密码"
            }
        ]
    }
]
```

### cmd/config_callback

```bash
#!/bin/bash
LOG_FILE="${TRIM_PKGVAR}/app.log"
SETTINGS_FILE="${TRIM_PKGETC}/settings.json"

log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [config] $1" >> "$LOG_FILE"
}

log_msg "Config callback started"

# 读取向导环境变量
SERVER_URL="${wizard_server_url:-http://localhost:8080}"
AUTH_ENABLED="${wizard_auth_enabled:-false}"
AUTH_USERNAME="${wizard_auth_username:-}"
AUTH_PASSWORD="${wizard_auth_password:-}"

# 转换 boolean
if [ "$AUTH_ENABLED" = "true" ] || [ "$AUTH_ENABLED" = "1" ]; then
    AUTH_BOOL="true"
else
    AUTH_BOOL="false"
fi

# 保存配置
cat > "$SETTINGS_FILE" << EOF
{
    "server_url": "${SERVER_URL}",
    "auth_enabled": ${AUTH_BOOL},
    "auth_username": "${AUTH_USERNAME}",
    "auth_password": "${AUTH_PASSWORD}"
}
EOF

log_msg "Settings saved: server_url=${SERVER_URL}, auth=${AUTH_BOOL}"

# 重载应用配置
# TRIM_APPDEST 指向 target 目录，cmd/ 在应用根目录 /var/apps/${TRIM_APPNAME}/cmd/
APP_ROOT="/var/apps/${TRIM_APPNAME}"
if [ -x "${APP_ROOT}/cmd/main" ]; then
    "${APP_ROOT}/cmd/main" reload >> "$LOG_FILE" 2>&1
fi

log_msg "Config callback completed"
```

---

## 示例 5：带共享目录的 resource

### config/resource

```json
{
    "data-share": {
        "shares": [
            {
                "name": "myapp-data",
                "permission": {
                    "rw": ["myapp"]
                }
            },
            {
                "name": "myapp-backup",
                "permission": {
                    "rw": ["myapp"]
                }
            }
        ]
    }
}
```

安装后系统自动创建：
- `shares/myapp-data -> /vol[x]/@appshare/myapp-data`
- `shares/myapp-backup -> /vol[x]/@appshare/myapp-backup`

---

## 示例 6：卸载向导（数据保留确认）

### wizard/uninstall

```json
[
    {
        "stepTitle": "确认卸载",
        "items": [
            {
                "type": "tips",
                "helpText": "您即将卸载此应用。请选择如何处理应用数据："
            },
            {
                "type": "radio",
                "field": "wizard_data_action",
                "label": "数据保留选项",
                "initValue": "keep",
                "options": [
                    { "label": "保留数据（推荐）- 重新安装时可恢复", "value": "keep" },
                    { "label": "删除所有数据 - 不可恢复！", "value": "delete" }
                ],
                "rules": [{ "required": true, "message": "请选择" }]
            },
            {
                "type": "tips",
                "helpText": "<b style='color:red'>警告：</b>选择删除数据后，所有应用数据将永久丢失。"
            }
        ]
    }
]
```

### cmd/uninstall_callback

```bash
#!/bin/bash
DATA_ACTION="${wizard_data_action:-keep}"

if [ "$DATA_ACTION" = "delete" ]; then
    rm -rf "${TRIM_PKGVAR}"
    # 清理共享目录中的数据
    # shares/ 在应用根目录 /var/apps/${TRIM_APPNAME}/ 下，不在 TRIM_APPDEST(target) 下
    APP_ROOT="/var/apps/${TRIM_APPNAME}"
    rm -rf "${APP_ROOT}/shares/myapp-data/"
    rm -rf "${APP_ROOT}/shares/myapp-backup/"
fi
```

---

## 示例 7：桌面图标配置（单入口）

为 Web 应用添加桌面图标，点击后打开应用页面。

### 目录结构

```
myapp/
├── app/
│   ├── bin/
│   │   └── myapp           # 应用二进制
│   └── ui/
│       ├── images/
│       │   ├── icon-64.png
│       │   └── icon-256.png
│       └── config
├── manifest
├── cmd/
├── config/
├── ICON.PNG
└── ICON_256.PNG
```

### manifest

```ini
appname=com.example.myapp
version=1.0.0
display_name=我的应用
desc=一个示例 Web 应用
platform=x86
source=thirdparty
maintainer=开发者
distributor=发布者
service_port=8080
checkport=true
desktop_uidir=ui
desktop_applaunchname=com.example.myapp.main
ctl_stop=true
```

### app/ui/config

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

安装后，fnOS 桌面会出现"我的应用"图标，点击后打开 `http://<NAS_IP>:8080/`。

---

## 示例 8：桌面图标配置（多入口）

一个应用提供多个桌面入口：用户界面 + 管理后台。

### app/ui/config

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
        },
        "com.example.myapp.admin": {
            "title": "管理后台",
            "icon": "images/admin-{0}.png",
            "type": "url",
            "protocol": "http",
            "port": "8080",
            "url": "/admin",
            "allUsers": false
        }
    }
}
```

### manifest（仅桌面相关字段）

```ini
desktop_uidir=ui
desktop_applaunchname=com.example.myapp.main
```

- `desktop_applaunchname` 指定默认入口 → 应用中心"打开"按钮使用 `com.example.myapp.main`
- 两个入口在桌面各显示一个图标
- `allUsers: false` 的"管理后台"仅管理员可见

### 图标文件

```
app/ui/images/
├── icon-64.png       # 用户入口 64x64
├── icon-256.png      # 用户入口 256x256
├── admin-64.png      # 管理入口 64x64
└── admin-256.png     # 管理入口 256x256
```
