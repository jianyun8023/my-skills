# my-skills

AI Agent Skills 的集中管理仓库。通过 Git 管理版本，自动部署到 Cursor、Claude Code、Gemini CLI 和 Gemini Antigravity 四个 AI 工具。

## 目录结构

```
my-skills/
├── skills/                         # 所有 Skill
│   ├── java/                       # Java 技术栈
│   │   ├── java-api-endpoint/
│   │   ├── java-architecture-guide/
│   │   ├── java-crud-module/
│   │   ├── java-db-migration/
│   │   └── java-dto-converter/
│   ├── devops/                     # DevOps & CI/CD
│   │   ├── dockerizing-vpn-clients/
│   │   ├── github-actions-multi-platform-build/
│   │   └── grafana-alloy-hcl/
│   ├── tooling/                    # 工具配置
│   │   ├── fnos-fpk-dev/
│   │   └── surge-configuration/
│   └── workflow/                   # 工作流 & 协作
│       └── context-detective/
├── scripts/                        # 工具脚本
│   ├── install.sh                  # 安装到各 AI 工具
│   └── catalog.sh                  # 生成 Skill 索引
├── templates/                      # 新建 Skill 模板
│   └── SKILL_TEMPLATE.md
└── docs/                           # 文档
    ├── CONTRIBUTING.md             # 贡献指南
    └── CATALOG.md                  # Skill 索引（自动生成）
```

## 快速开始

### 安装

将仓库中的 Skill 部署到各 AI 工具的 skills 目录：

```bash
# 预览安装
./scripts/install.sh --dry-run

# 执行安装
./scripts/install.sh

# 清理已安装的 Skill
./scripts/install.sh --clean
```

安装后，AI Agent 即可自动发现和使用这些 Skill。

> **安装方式说明**: 由于各工具对符号链接的支持不同，脚本自动选择最佳方式：
>
> | 工具 | 目录 | 方式 | 原因 |
> |------|------|------|------|
> | Cursor | `~/.cursor/skills/` | 复制 | 不支持符号链接 |
> | Claude Code | `~/.claude/skills/` | 复制 | 符号链接支持不稳定 |
> | Gemini CLI | `~/.gemini/skills/` | 符号链接 | 原生支持 |
> | Gemini Antigravity | `~/.gemini/antigravity/skills/` | 复制 | 不支持符号链接 |

### 新建 Skill

```bash
# 1. 创建 Skill 目录
mkdir -p skills/<category>/<skill-name>

# 2. 从模板创建
cp templates/SKILL_TEMPLATE.md skills/<category>/<skill-name>/SKILL.md

# 3. 编写内容...

# 4. 更新索引
./scripts/catalog.sh

# 5. 安装到工具
./scripts/install.sh
```

## Skill 索引

### Java 技术栈 (5)

| Skill | 描述 |
|-------|------|
| `java-architecture-guide` | Java 业务项目架构原则和编码规范，适用于 Spring Boot + MyBatis-Plus 分层架构 |
| `java-crud-module` | 完整 CRUD 业务模块脚手架（9 个文件） |
| `java-api-endpoint` | RESTful API 端点开发，含 Controller、Facade 模式 |
| `java-db-migration` | MyBatis Migration 数据库迁移脚本生成 |
| `java-dto-converter` | DTO 与 MapStruct Converter 编写规范 |

### DevOps & CI/CD (3)

| Skill | 描述 |
|-------|------|
| `github-actions-multi-platform-build` | GitHub Actions 多平台 Docker 镜像构建（amd64/arm64） |
| `dockerizing-vpn-clients` | VPN 客户端 Docker 容器化，支持 GUI（VNC）和 CLI（Web 管理）模式 |
| `grafana-alloy-hcl` | Grafana Alloy HCL 配置编写，含日志采集、数据处理流水线及 FnOS 配置模式 |

### 工具配置 (2)

| Skill | 描述 |
|-------|------|
| `fnos-fpk-dev` | 飞牛 fnOS FPK 应用包开发，含目录结构、生命周期脚本、权限与资源声明 |
| `surge-configuration` | Surge 代理工具配置，含规则、策略、DNS、MITM 等 |

### 工作流 & 协作 (1)

| Skill | 描述 |
|-------|------|
| `context-detective` | 深度上下文收集，防止 AI 幻觉。任务开始前探索代码库，建立经过验证的事实基础 |

> 完整索引见 [docs/CATALOG.md](docs/CATALOG.md)

## 分类说明

| 分类 | 目录 | 说明 |
|------|------|------|
| Java 技术栈 | `skills/java/` | Spring Boot、MyBatis-Plus 相关 |
| DevOps | `skills/devops/` | CI/CD、Docker、GitHub Actions、可观测性 |
| 工具配置 | `skills/tooling/` | 平台开发、代理工具等 |
| 工作流 | `skills/workflow/` | AI 协作流程、上下文收集 |
| 开发方法论 | `skills/development/` | TDD、DDD 等（待添加） |
| 质量保证 | `skills/quality/` | 代码审查、测试（待添加） |
| AI 提示 | `skills/prompting/` | 提示技巧（待添加） |

## 工作原理

```
                                  ┌──────────────────────────────┐
                        copy      │ ~/.cursor/skills/            │
                   ┌─────────────▶│ (Cursor)                     │
                   │              └──────────────────────────────┘
                   │    copy      ┌──────────────────────────────┐
┌─────────────┐    ├─────────────▶│ ~/.claude/skills/            │
│  my-skills  │    │              │ (Claude Code)                │
│  (Git 仓库)  │────┤              └──────────────────────────────┘
│  skills/**  │    │   symlink    ┌──────────────────────────────┐
└─────────────┘    ├─────────────▶│ ~/.gemini/skills/            │
                   │              │ (Gemini CLI)                 │
                   │              └──────────────────────────────┘
                   │    copy      ┌──────────────────────────────┐
                   └─────────────▶│ ~/.gemini/antigravity/skills/│
                                  │ (Gemini Antigravity)         │
                                  └──────────────────────────────┘
```

- **单一数据源**: 所有 Skill 在仓库中集中管理
- **智能部署**: `install.sh` 根据工具兼容性自动选择复制或符号链接
- **版本控制**: Git 管理变更历史
- **自动索引**: `catalog.sh` 扫描 frontmatter 生成目录

## License

[Apache License 2.0](LICENSE)
