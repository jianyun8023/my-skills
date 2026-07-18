# Grafana Alloy HCL 参考资料

当你在 FnOS / FPK 场景下编写 Alloy 配置时，再读取本文件。主技能保留通用流水线规则，这里只放环境相关路径、示例和调试技巧。

## FnOS 最佳实践

### 目录与文件结构

- **模块化**: 将不同类型的配置（如 `system.alloy`, `docker.alloy`）分开，虽然最终会在一个进程运行，但逻辑上保持清晰。
- **注释**: 充分使用 `//` 注释，标记每个 `component` 的用途和数据流向 (`forward_to`)。

### 目录规范 (FnOS Standard Paths)

在 FnOS 环境下，建议遵循以下日志路径标准：

- **Trim 应用日志**: `/var/log/apps/trim.*.log`
  - 例如: `trim.photos.log`, `trim.media.log`
- **系统服务日志**: `/var/log/trim_*/*.log`
  - 例如: `/var/log/trim_app_center/`, `/var/log/trim_sac/`
- **Nginx (Trim Web Server)**: `/usr/trim/nginx/logs/*.log`
  - **安全关键**: 包含 `access.log` 和 `error.log`
- **系统日志**: `/var/log/*` (通常使用 `loki.source.journal` 采集)

### FnOS 组件配置示例

#### 1. 采集 Trim 应用日志

```hcl
loki.source.file "trim_apps" {
  targets = [
    {
      __path__ = "/var/log/apps/trim.*.log",
      job      = "fnos-apps",
      category = "trim-app",
    }
  ]
  forward_to = [loki.write.local.receiver]
}
```

#### 2. 采集 Nginx 安全日志

```hcl
loki.source.file "nginx_security" {
  targets = [
    {
      __path__ = "/usr/trim/nginx/logs/access.log",
      job      = "fnos-nginx-access",
      category = "security",
    },
    {
      __path__ = "/usr/trim/nginx/logs/error.log",
      job      = "fnos-nginx-error",
      level    = "error",
    },
  ]
  forward_to = [loki.write.local.receiver]
}
```

### 动态配置模板

在 FPK 开发中，常通过 `envsubst` 或自定义脚本替换模板变量：

- `{{LOKI_URL}}`
- `{{AUTH_USERNAME}}`
- `{{HOSTNAME}}`

### 调试技巧

1. **格式化**: `alloy fmt config.alloy` (由于是在 FPK 内运行，开发时可安装本地 alloy 工具)
2. **调试组件**: 使用 `livedebugging` (Web UI http://localhost:12345/graph) 查看数据流向。
3. **日志输出**: 在 `logging {}` 块中设置 `level = "debug"`。
