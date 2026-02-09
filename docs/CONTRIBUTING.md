# 贡献指南

## Skill 编写规范

### 文件结构

每个 Skill 是一个独立目录，至少包含 `SKILL.md`：

```
skill-name/
├── SKILL.md              # 必需 - 主文件
├── reference.md          # 可选 - 详细参考
├── examples.md           # 可选 - 使用示例
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
  What this skill does.
  Use when [trigger conditions].
---
```

#### Description 编写要点

- 说明 Skill **做什么** 以及 **什么时候使用**
- 包含 "Use when" 触发条件
- 最大 1024 字符
- 包含关键词，便于 AI Agent 搜索发现

### 内容规范

1. **主文件控制在 500 行以内**，详细参考放 `reference.md`
2. **使用中文**编写面向中文用户的 Skill
3. **提供代码示例**，而非纯文字描述
4. **包含 Checklist**，方便检查完成度
5. **列出常见错误**和反模式

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
2. 运行 `./scripts/install.sh` 同步到本地工具目录
3. 测试效果
4. 提交更改
