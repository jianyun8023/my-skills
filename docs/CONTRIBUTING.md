# 贡献指南

## Skill 编写规范

### 文件结构

每个 Skill 是一个独立目录，至少包含 `SKILL.md`：

```
skill-name/
├── SKILL.md              # 必需 - 主文件
├── reference.md          # 可选 - 详细参考
├── examples.md           # 可选 - 使用示例
├── scripts/              # 可选 - 可执行脚本
├── resources/            # 可选 - 配置/模板/样例
└── templates/            # 可选 - 模板文件
    └── ...
```

### 命名规范

- **目录名**: 全小写，用连字符分隔，如 `java-api-endpoint`
- **SKILL.md**: 固定文件名，大写
- **辅助文件**: 全小写，用连字符分隔

### Frontmatter 格式

```yaml
---
name: skill-name            # 必需，与目录名一致
description: >              # 必需，简短描述
  Use when [trigger conditions].
  Covers [scope], [constraints], and [key outputs].
---
```

#### Description 编写要点

- 优先把 **Use when** 触发条件放在前面，便于被 AI 工具发现
- 说明 Skill **做什么**、**不做什么**，以及关键约束
- 包含 "Use when" 触发条件
- 最大 1024 字符
- 包含关键词，便于 AI Agent 搜索发现

### 内容规范

1. **主文件控制在 500 行以内**，超过 300 行时优先评估是否可拆到 `reference.md` / `examples.md`
2. **使用中文**编写面向中文用户的 Skill；必要时可中英混排关键词
3. **提供代码示例**，而非纯文字描述
4. **至少包含**：`适用场景`、`不适用`、`Checklist`、`常见错误`
5. **先给工作流，再给细节**；把大段参考内容下沉到 `reference.md`
6. **不要提交生成产物**（如测试报告、执行日志、筛选结果）到 Skill 目录；这类文件应放到临时目录或仓库外
7. **避免写死环境信息**（服务地址、密钥、个人路径）；优先通过配置文件或环境变量读取

### 分类目录

将 Skill 放到对应的分类目录下：

| 分类 | 目录 | 说明 |
|------|------|------|
| Java 技术栈 | `skills/java/` | Spring Boot、MyBatis-Plus 等 |
| DevOps | `skills/devops/` | CI/CD、Docker、GitHub Actions |
| 工具配置 | `skills/tooling/` | 编辑器、代理、系统工具 |
| 开发方法论 | `skills/development/` | TDD、DDD 等方法论 |
| 质量保证 | `skills/quality/` | 代码审查、测试、调试 |
| 工作流 | `skills/workflow/` | 协作、规划、执行流程 |
| AI 提示 | `skills/prompting/` | AI 提示技巧、Skill 编写 |

如需新增分类，先在 PR 中说明理由。

## 新增 Skill 流程

1. 从模板创建：`cp -r templates/SKILL_TEMPLATE.md skills/<category>/<skill-name>/SKILL.md`
2. 编写内容
3. 运行 `./scripts/catalog.sh` 更新索引
4. 运行 `./scripts/install.sh` 验证安装
5. 提交 PR

## 修改现有 Skill

1. 直接编辑仓库中的文件
2. 如有结构性改动，检查是否需要同步更新 `reference.md` / `examples.md`
3. 运行 `./scripts/catalog.sh` 更新索引
4. 运行 `./scripts/install.sh` 同步到本地工具目录
5. 测试效果
6. 提交更改
