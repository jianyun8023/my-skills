---
name: grafana-alloy-hcl
description: Use when editing `.alloy` files, configuring Grafana Alloy pipelines, or debugging log collection and relabeling behavior. Covers HCL syntax, common Loki/Prometheus components, processing stages, Docker discovery, and FnOS-specific patterns.
---

# Grafana Alloy HCL 配置指南

Grafana Alloy 使用 HCL (HashiCorp Configuration Language) 作为配置语言，支持模块化、组件化的数据处理流水线。

## 适用场景

- 新增或修改 `.alloy` 配置文件
- 配置日志采集、处理流水线或 Loki 写入链路
- 调试 `forward_to`、`discovery.relabel`、`stage.*` 等配置问题
- 在 FnOS / Docker 环境下落地 Alloy 日志采集

## 不适用

- 安装 Alloy 二进制、systemd 服务或容器编排本身
- Loki / Grafana 仪表盘查询语句、告警规则设计
- 不涉及 Alloy 的普通 HCL/Terraform 配置

## 快速工作流

1. 先确定链路：`source -> process/relabel -> write`
2. 先写最小可运行配置，再逐步增加 `stage.*` 和标签处理
3. 涉及 Docker relabel 时，优先确认 `.output` / `.rules` 的使用位置
4. 涉及正则时，优先检查 HCL 双反斜杠转义
5. 最后用 `alloy fmt`、livedebugging 或示例配置对照验证

## 核心概念

Alloy 的配置由 **Components（组件）** 组成，组件之间通过 **Capabilities（能力）** 连接（如 `forward_to`）。

### 基本语法

```hcl
// 组件类型 "标签" { 属性... }
component.type "label" {
  attribute = "value"
  
  block {
    sub_attribute = 123
  }
}
```

### HCL 正则转义规则

> **重要**: HCL 字符串中使用 `\\` 表示一个字面的 `\`。正则表达式中常见的 `\s`、`\S`、`\d`、`\b` 等需要写成 `\\s`、`\\S`、`\\d`、`\\b`。

```hcl
// ✅ 正确 — HCL 将 \\s 解析为 \s 传给正则引擎
expression = "(?i)(password|passwd|pwd)\\s*[=:]\\s*\\S+"

// ❌ 错误 — \s 在 HCL 中不是合法转义，会导致语法错误或意外行为
expression = "(?i)(password|passwd|pwd)\s*[=:]\s*\S+"
```

命名捕获组同理：`(?P<name>...)` 在 HCL 中写为 `(?P<name>...)`（尖括号不需要转义）。

### 常用组件

#### 1. 日志采集 (Loki)

- `loki.source.file`: 采集本地文件
- `loki.source.journal`: 采集 Systemd Journal
- `loki.source.api`: 接收 HTTP 推送
- `loki.source.docker`: 采集 Docker 容器日志

```hcl
loki.source.file "app_logs" {
  targets = [
    {
      __path__ = "/var/log/app/*.log",
      job      = "my-app",
    }
  ]
  forward_to = [loki.write.local.receiver]
}
```

**动态文件发现** — 使用 `local.file_match` 替代静态 targets：

```hcl
local.file_match "app_logs" {
  path_targets = [{
    __path__ = "/var/log/app/*.log",
    job      = "app-logs",
  }]
}

loki.source.file "app_logs" {
  targets    = local.file_match.app_logs.targets
  forward_to = [loki.process.pipeline.receiver]
}
```

#### 2. 数据处理

- `loki.process`: 解析、过滤、修改日志
- `discovery.relabel`: 修改发现阶段的元数据标签
- `loki.relabel`: 运行时修改日志条目标签（区别于 `discovery.relabel`）

```hcl
loki.process "json_parser" {
  forward_to = [loki.write.local.receiver]
  
  stage.json {
    expressions = {
      level   = "level",
      message = "msg",
    }
  }
  
  stage.labels {
    values = { level = "" }
  }
}
```

#### 3. 容器日志 (Docker)

- `discovery.docker`: 发现 Docker 容器
- `loki.source.docker`: 采集容器日志

**`discovery.relabel` 导出字段说明**:
- `.output` — relabel 后的 targets 列表 (`list(map(string))`)，用于传递给 `loki.source.docker` 的 `targets`
- `.rules` — 当前配置的 relabel 规则 (`RelabelRules`)，用于传递给 `relabel_rules` 参数

**推荐写法** （官方文档模式 — 使用 `.output`）:

```hcl
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
  filter {
    name   = "status"
    values = ["running"]
  }
}

// 标签处理（提取容器名、镜像等）
discovery.relabel "docker_labels" {
  targets = discovery.docker.containers.targets
  
  // 提取容器名称 (例如 /my-app -> my-app)
  rule {
    source_labels = ["__meta_docker_container_name"]
    regex         = "/(.*)"
    target_label  = "container"
  }
  
  // 提取镜像名称
  rule {
    source_labels = ["__meta_docker_container_image"]
    target_label  = "image"
  }
}

loki.source.docker "docker_logs" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.relabel.docker_labels.output   // ✅ 使用 .output 获取 relabel 后的 targets
  forward_to = [loki.process.process_logs.receiver]
}
```

**替代写法** （使用 `relabel_rules`，功能等价）:

```hcl
// targets 直接引用 discovery.docker，relabel 在 source 层面执行
loki.source.docker "docker_logs" {
  host          = "unix:///var/run/docker.sock"
  targets       = discovery.docker.containers.targets
  relabel_rules = discovery.relabel.docker_labels.rules  // 使用 .rules
  forward_to    = [loki.process.process_logs.receiver]
}
```

#### 4. 数据发送

- `loki.write`: 发送到 Loki 实例

**基本配置**:
```hcl
loki.write "local" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

**生产级配置** (认证 + 重试 + WAL):
```hcl
loki.write "production" {
  endpoint {
    url = "https://logs.example.com/loki/api/v1/push"
    
    // 基本认证
    basic_auth {
      username = "user123"
      password = env("LOKI_API_KEY")
    }
    
    // 批次控制
    batch_size = "1MiB"
    batch_wait = "1s"
    
    // 重试策略
    min_backoff_period  = "500ms"
    max_backoff_period  = "5m"
    max_backoff_retries = 10
    
    // 多租户
    tenant_id = "production"
  }
  
  external_labels = {
    cluster = "prod-cluster",
    region  = "us-east-1",
  }
  
  // Write-Ahead Log 持久化（防止数据丢失）
  wal {
    enabled         = true
    dir             = "/var/lib/alloy/wal"
    max_segment_age = "2h"
  }
}
```

### 高级数据处理 (Advanced Processing)

#### 完整 Stage 列表

| Stage | 用途 | 备注 |
|-------|------|------|
| `stage.json` | 解析 JSON 日志 | 最常用 |
| `stage.logfmt` | 解析 logfmt 格式 | `mapping = { "key" = "source_key" }` |
| `stage.regex` | 正则提取字段 | 使用命名捕获组 `(?P<name>...)` |
| `stage.labels` | 将提取值设为标签 | `values = { label = "source" }` |
| `stage.template` | Go 模板转换值 | 如 `{{ .Value \| ToUpper }}` |
| `stage.replace` | 正则替换日志内容 | 常用于脱敏 |
| `stage.drop` | 丢弃匹配的日志 | 支持 `expression` 或 `source+value` |
| `stage.match` | 条件处理 | 支持 `action = "drop"` |
| `stage.output` | 设置最终日志内容 | `source = "extracted_field"` |
| `stage.timestamp` | 修正日志时间戳 | Go 时间格式 |
| `stage.docker` | 解析 Docker JSON 日志 | `stage.docker {}` |
| `stage.static_labels` | 添加静态标签 | `values = { key = "value" }` |

#### 1. 敏感数据脱敏 (Masking)
使用 `stage.replace` 隐藏密码、Token 等敏感信息。

```hcl
loki.process "masking" {
  forward_to = [loki.write.local.receiver]

  // 隐藏 password=xxx
  stage.replace {
    expression = "(?i)(password|passwd|pwd)\\s*[=:]\\s*[\"']?\\S+"
    replace    = "$1=***"
  }
  
  // 隐藏 Bearer Token
  stage.replace {
    expression = "(?i)(authorization|auth)\\s*:\\s*[\"']?Bearer\\s+\\S+"
    replace    = "$1: Bearer ***"
  }
  
  // 隐藏 API Key / Secret
  stage.replace {
    expression = "(?i)(token|api_key|apikey|secret)\\s*[=:]\\s*[\"']?\\S+"
    replace    = "$1=***"
  }
}
```

#### 2. 噪音过滤 (Filtering)
使用 `stage.drop` 或 `stage.match` 丢弃不需要的日志。

```hcl
loki.process "filtering" {
  forward_to = [loki.write.local.receiver]

  // 方式1: 按正则匹配日志内容丢弃
  stage.drop {
    expression          = ".*(health|healthcheck|heartbeat).*"
    drop_counter_reason = "health_check"
  }
  
  // 方式2: 按提取值精确匹配丢弃
  stage.drop {
    source = "is_secret"
    value  = "true"
  }
  
  // 方式3: 嵌套在 stage.match 中，仅针对特定容器
  stage.match {
    selector = "{container=\"noisy-app\"}"
    stage.drop {
      expression = ".*DEBUG.*"
    }
  }
  
  // 方式4: stage.match + action="drop" (更简洁的条件丢弃)
  stage.match {
    selector            = "{app=\"example\"} |~ \".*noisy error.*\""
    action              = "drop"
    drop_counter_reason = "discard_noisy_errors"
  }
}
```

#### 3. 时间戳修正 (Timestamp)
使用 `stage.timestamp` 提取日志中的时间，解决延迟问题。

```hcl
loki.process "timestamp_fix" {
  forward_to = [loki.write.local.receiver]

  // 提取时间戳 regex
  stage.regex {
    expression = "^(?P<timestamp>\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}\\.\\d{3})"
  }
  
  // 应用时间戳
  stage.timestamp {
    source = "timestamp"
    format = "2006-01-02 15:04:05.000"
  }
}
```

#### 4. 日志级别标准化
使用 `stage.regex` + `stage.template` + `stage.labels` 提取并标准化日志级别。

```hcl
loki.process "level_extraction" {
  forward_to = [loki.write.local.receiver]

  // 通用日志级别提取正则
  stage.regex {
    expression = "(?i)\\b(?P<extracted_level>TRACE|DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|ERR|CRITICAL|CRIT|FATAL|PANIC)\\b"
  }
  
  // 标准化为大写
  stage.template {
    source   = "extracted_level"
    template = "{{ .Value | ToUpper }}"
  }
  
  // 添加为标签
  stage.labels {
    values = {
      level = "extracted_level",
    }
  }
}
```

#### 5. Docker 日志专用解析
使用 `stage.docker` 解析 Docker 默认的 JSON 日志格式。

```hcl
loki.process "docker_parser" {
  stage.docker {}
  forward_to = [loki.write.local.receiver]
}
```

#### 6. 设置最终输出内容
使用 `stage.output` 指定最终日志行的内容来源。

```hcl
loki.process "custom_output" {
  forward_to = [loki.write.local.receiver]

  stage.json {
    expressions = { log_line = "message" }
  }
  
  // 将 "message" 字段的值作为最终日志输出
  stage.output {
    source = "log_line"
  }
}
```

### `discovery.relabel` rule 支持的 action

| Action | 说明 |
|--------|------|
| `replace` | (默认) 用 `replacement` 替换 `target_label` 的值 |
| `keep` | 保留 `source_labels` 匹配 `regex` 的 targets |
| `drop` | 丢弃 `source_labels` 匹配 `regex` 的 targets |
| `hashmod` | 对 `source_labels` 做哈希取模，写入 `target_label` |
| `labelmap` | 匹配所有标签名，将匹配的标签复制到新名称 |
| `labeldrop` | 删除匹配 `regex` 的标签 |
| `labelkeep` | 仅保留匹配 `regex` 的标签 |

```hcl
discovery.relabel "filter_example" {
  targets = discovery.docker.containers.targets
  
  // 仅保留 app="backend" 的 targets
  rule {
    source_labels = ["app"]
    action        = "keep"
    regex         = "backend"
  }
  
  // 添加静态标签
  rule {
    target_label = "env"
    replacement  = "production"
  }
  
  // 合并多个标签为一个
  rule {
    source_labels = ["__address__", "instance"]
    separator     = "/"
    target_label  = "destination"
    action        = "replace"
  }
}
```

## FnOS 参考

FnOS 路径规范、组件示例和调试技巧已拆到 [reference.md](reference.md)。在 FnOS / FPK 场景下，先读该文件，再回到本技能主流程拼装配置。

### 常见错误清单

| 错误写法 | 正确写法 | 说明 |
|----------|----------|------|
| `targets = discovery.docker.X.targets` (配合 relabel 使用时) | `targets = discovery.relabel.X.output` | relabel 后应使用 `.output` |
| `expression = "\s+"` | `expression = "\\s+"` | HCL 中 `\` 需要双重转义 |
| `stage.labels { values = { level = "level" } }` 提取同名字段 | `stage.labels { values = { level = "" } }` | 空字符串表示使用同名键 |
| 在 `loki.process` 外使用 stage | 放在 `loki.process` 块内 | 所有 stage 必须嵌套在 `loki.process` 中 |
| `forward_to = loki.write.X.receiver` | `forward_to = [loki.write.X.receiver]` | `forward_to` 始终是数组 |

## Checklist

实现前：
- [ ] 已明确日志来源、处理链路和最终写入目标
- [ ] 已确认是否需要 `discovery.relabel`、`loki.relabel` 或 `loki.process`
- [ ] 已确认运行环境路径、Docker socket 或 FnOS 日志目录

实现后：
- [ ] 所有 `forward_to` 都是数组，且接收端存在
- [ ] 正则表达式中的反斜杠已按 HCL 规则双重转义
- [ ] Docker relabel 相关配置正确使用 `.output` 或 `.rules`
- [ ] 已参考 `resources/example.alloy` 验证整体结构是否一致

## 完整示例

请参考 `resources/example.alloy` 获取包含系统日志、Docker 发现及高级处理的完整配置示例。
