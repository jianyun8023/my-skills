# my-skills

AI Agent Skills 的集中管理仓库。通过 Git 管理版本，通过符号链接部署到各 AI 工具（Cursor、Claude Code 等）。

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
│   │   ├── github-actions-multi-platform-build/
│   │   └── dockerizing-vpn-clients/
│   └── tooling/                    # 工具配置
│       └── surge-configuration/
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

将仓库中的 Skill 符号链接到 Cursor 和 Claude Code 的 skills 目录：

```bash
# 预览安装
./scripts/install.sh --dry-run

# 执行安装
./scripts/install.sh

# 清理链接
./scripts/install.sh --clean
```

安装后，AI Agent 即可自动发现和使用这些 Skill。

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

### DevOps & CI/CD (2)

| Skill | 描述 |
|-------|------|
| `github-actions-multi-platform-build` | GitHub Actions 多平台 Docker 镜像构建（amd64/arm64） |
| `dockerizing-vpn-clients` | VPN 客户端 Docker 容器化，支持 GUI（VNC）和 CLI（Web 管理）模式 |

### 工具配置 (1)

| Skill | 描述 |
|-------|------|
| `surge-configuration` | Surge 代理工具配置，含规则、策略、DNS、MITM 等 |

> 完整索引见 [docs/CATALOG.md](docs/CATALOG.md)

## 分类说明

| 分类 | 目录 | 说明 |
|------|------|------|
| Java 技术栈 | `skills/java/` | Spring Boot、MyBatis-Plus 相关 |
| DevOps | `skills/devops/` | CI/CD、Docker、GitHub Actions |
| 工具配置 | `skills/tooling/` | 编辑器、代理、系统工具 |
| 开发方法论 | `skills/development/` | TDD、DDD 等（待添加） |
| 质量保证 | `skills/quality/` | 代码审查、测试（待添加） |
| 工作流 | `skills/workflow/` | 协作流程（待添加） |
| AI 提示 | `skills/prompting/` | 提示技巧（待添加） |

## 工作原理

```
┌─────────────┐     symlink      ┌──────────────────┐
│  my-skills  │ ──────────────── │ ~/.cursor/skills/ │
│  (Git 仓库)  │                 └──────────────────┘
│             │     symlink      ┌──────────────────┐
│  skills/**  │ ──────────────── │ ~/.claude/skills/ │
└─────────────┘                  └──────────────────┘
```

- **单一数据源**: 所有 Skill 在仓库中管理
- **符号链接部署**: `install.sh` 创建软链接到各工具目录
- **版本控制**: Git 管理变更历史
- **自动索引**: `catalog.sh` 扫描 frontmatter 生成目录

## License

[Apache License 2.0](LICENSE)
