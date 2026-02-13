---
name: context-detective
description: >
  深度上下文收集，防止 AI 幻觉。在任务开始前探索代码库，建立经过验证的事实基础。
  Use proactively BEFORE any feature work, code generation, design, or planning.
  Use when starting a new task, exploring an unfamiliar module, or before creating any new file.
---

# Context Detective — 上下文侦探

在生成任何内容（需求、设计、计划、代码）之前，按 **DNA → Trace → Align** 三阶段收集上下文，产出经过验证的 Context Artifact。

> 用户请求只是冰山一角 (10%)，代码库才是水下的 90%。忽略水下部分会导致：
> - **重复造轮子**：重新实现已有的工具类
> - **风格不一致**：项目用 `fetch` 却引入 `axios`
> - **隐性回归**：破坏隐藏的依赖关系

## 适用场景

- 开始任何非平凡任务之前
- 创建新文件之前（先查重）
- 遇到不熟悉的领域术语时
- 编写需求、设计或计划之前

## 不适用

- 单行修改、拼写修正等平凡任务
- 当前对话中已执行过 Context Detective 且任务范围未变
- 用户明确指定了文件路径和修改内容的精确指令

## 深度控制

根据任务规模选择调查深度，避免分析瘫痪：

| 任务规模 | 调查深度 | 说明 |
|----------|----------|------|
| **小**（单文件修改、Bug 修复） | 仅 Phase 1 + 快速 Phase 2 | 确认依赖和直接调用者即可 |
| **中**（新增功能模块） | 完整三阶段 | 产出完整 Context Artifact |
| **大**（架构重构、跨模块变更） | 三阶段 + 多轮验证 | 需追踪完整爆炸半径 |

**终止条件**：如果 Phase 2 搜索超过 3 轮仍无新收获，停止并在 Artifact 中记录"信息不足，需人工确认"。

## 语言速查表

先识别项目语言，再按对应列查找关键文件和惯例：

| 关注点 | Java | Go | JS / TS | Python |
|--------|------|----|---------|--------|
| **依赖文件** | `pom.xml` / `build.gradle` | `go.mod` | `package.json` | `pyproject.toml` / `requirements.txt` |
| **配置文件** | `application.yml` / `.properties` | `.env` / `config.yaml` | `tsconfig.json` / `next.config.*` / `.env` | `settings.py` / `pyproject.toml` / `.env` |
| **入口/路由** | `@RestController` / `@RequestMapping` | `http.HandleFunc` / `gin.Engine` | `app.get()` / `pages/` / `app/` | `@app.route` / `urlpatterns` |
| **数据层** | Entity + Mapper (MyBatis) / JPA | struct + sqlx / GORM | Prisma / TypeORM / Mongoose | SQLAlchemy / Django ORM |
| **测试框架** | JUnit 5 / Mockito | `testing` / testify | Jest / Vitest / Mocha | pytest / unittest |
| **架构惯例** | Controller → Facade → Service → Mapper | Handler → Service → Repository | Route → Controller → Service → Model | View → Serializer → Service → Model |
| **常见工具类目录** | `**/util/**`, `**/common/**` | `**/pkg/**`, `**/internal/util/**` | `**/utils/**`, `**/lib/**`, `**/helpers/**` | `**/utils/**`, `**/common/**`, `**/helpers/**` |

## 操作步骤

### Phase 1: DNA 分析 — 识别项目骨架

读取，不要猜测。先用 `Glob` 在项目根目录查找依赖文件，确定语言和技术栈，再按语言速查表定位关键文件。

1. **语言识别** — 用 `Glob` 查找根目录的依赖文件，确定项目语言
   - `Glob("pom.xml")` / `Glob("go.mod")` / `Glob("package.json")` / `Glob("pyproject.toml")`
   - 注意：可能是多语言项目（如 Java 后端 + JS 前端），需逐一识别
2. **依赖清单** — 用 `Read` 读取对应的依赖文件，确认安装了哪些库
   - 确认：用了哪些框架？版本号是什么？有无锁定文件？
3. **配置文件** — 用 `Read` 读取配置文件（参考语言速查表），识别约束和惯例
   - 确认：有哪些环境约束？路径别名？运行模式？
4. **目录结构** — 用 `Glob` 探索 2-3 层目录，识别架构模式
   - Java: `Glob("src/main/java/**")` | Go: `Glob("cmd/**")`, `Glob("internal/**")` | JS: `Glob("src/**")` | Python: `Glob("app/**")` 或 `Glob("src/**")`
   - 确认：分层方式？业务逻辑位置？共享模块在哪？

### Phase 2: 语义追踪 — 追踪关系和模式

超越关键词匹配，追踪依赖关系。

1. **关键词扩展** — 对用户提到的概念，用 `Grep` 和 `SemanticSearch` 搜索同义词和关联术语
   - 用户说"订单管理" → 搜索 `Order`, `订单`, `Purchase`, `Cart`, `交易`
   - 用 `Grep` 做精确匹配，用 `SemanticSearch` 做语义发现
2. **依赖链追踪** — 对找到的核心实体，用 `Grep` 追踪引用：
   - 找 **调用者**（参考语言速查表的"入口/路由"行）
   - 找 **被调用者**（参考语言速查表的"数据层"行，以及外部 API、工具类）
   - 画出变更的**爆炸半径**（哪些文件会受影响）
3. **双胞胎功能** — 用 `SemanticSearch` 找一个已有的、模式相似的功能作为参照
   - 要建"文档评论"？先看"任务评论"怎么做的
   - 复制**模式**（命名、分层、错误处理），而非代码
   - **降级策略**：如果找不到模式相似的功能：
     - 退而求其次：找同层级任意一个完整模块作为结构参照
     - 或在 Artifact 中记录："无可参照的已有功能，需从零设计模式"

### Phase 3: 差距对齐 — 叠加需求到现实

1. **集成点审计** — 用 `Read` 读取实际内容：
   - 数据库：Schema / Migration / ORM 模型定义
   - 路由：API 注册文件 / 路由表（参考语言速查表的"入口/路由"行）
   - 配置：权限 / 中间件 / 菜单配置
2. **复用验证** — 创建任何新东西之前先用工具确认：
   - 用 `Glob` 搜索常见工具类目录（参考语言速查表的"常见工具类目录"行）
   - 用 `Grep` 确认："现有文件的命名惯例是什么？"
3. **约束识别** — 记录硬约束：
   - 认证模式、分页方式、错误处理惯例、日志模式
   - 测试框架、代码风格（Linter / Formatter 配置）、部署方式

## 产出模板

完成三个阶段后，产出以下结构化 Artifact（所有事实均须通过工具读取确认，非假设）：

```markdown
# Context Artifact
> **Module**: [模块名]
> **Date**: YYYY-MM-DD
> **Status**: VERIFIED — 所有事实均通过工具读取确认

## 1. Project DNA
- **语言/版本**: [如 Java 17 / Go 1.22 / TypeScript 5.x / Python 3.12]
- **框架**: [如 Spring Boot 3.x / Gin / Next.js 14 / FastAPI]
- **构建工具**: [如 Maven / go build / pnpm / Poetry]
- **架构模式**: [如 Controller → Service → Repository]
- **数据库**: [如 PostgreSQL + Prisma / MySQL + MyBatis-Plus / MongoDB + Mongoose]
- **测试框架**: [如 JUnit 5 / go test + testify / Vitest / pytest]
- **关键库**: [列出核心依赖]

## 2. 相关现实
- **核心实体**: [实体名, 文件路径, 行号]
- **API 模式**: [端点结构方式]
- **类似功能**: [可作为参照的已有功能，含路径]
- **可复用组件**: [已存在的可复用 Service/组件/工具类/包]

## 3. 差距
- [ ] [需要创建的]
- [ ] [需要修改的]
- [ ] [需要扩展的]

## 4. 风险与约束（下游阶段必须遵守）
1. [硬约束，如：认证必须使用 xxx 方式]
2. [风格约束，如：错误处理必须遵循 xxx 模式]
3. [性能约束，如：接口响应时间 < 200ms]

## 5. 验证记录
| 工具 | 命令/参数 | 验证了什么 |
|------|-----------|-----------|
| Read | `[依赖文件]` | 确认框架版本 |
| Grep | `"[核心类/函数名]"` | 确认核心实体已存在 |
| Glob | `[目录模式]` | 确认文件结构 |
| SemanticSearch | "[语义查询]" | 发现相关实现 |
```

**各语言验证记录示例**：

| 语言 | 工具 | 命令/参数 | 验证了什么 |
|------|------|-----------|-----------|
| Java | Read | `pom.xml` | 确认 Spring Boot 版本为 3.2.x |
| Java | Grep | `"class OrderService"` | 确认 OrderService 已存在 |
| Go | Read | `go.mod` | 确认 gin v1.9 + sqlx 已引入 |
| Go | Glob | `internal/handler/**` | 发现 Handler 层目录结构 |
| JS/TS | Read | `package.json` | 确认使用 Next.js 14 + Prisma |
| JS/TS | Grep | `"export.*function.*useAuth"` | 确认 Auth Hook 已存在 |
| Python | Read | `pyproject.toml` | 确认 FastAPI 0.110 + SQLAlchemy |
| Python | Glob | `**/routers/*.py` | 发现 API 路由文件结构 |

## QA 自检清单

产出 Artifact 后，切换到 **Fact Checker** 视角进行自检。任何一项不通过则必须补充调查。

### DNA 检查
- [ ] **框架感知**：是否确认了项目实际使用的框架？（而非假设）
- [ ] **依赖感知**：是否在建议引入新库之前检查了依赖文件？
- [ ] **风格对齐**：提议的方案是否与项目现有风格一致？

### 语义追踪检查
- [ ] **关系映射**：是否找到了关联文件，而不仅是精确关键词匹配？
- [ ] **双胞胎功能**：是否找到了可作为模式参照的已有功能？
- [ ] **爆炸半径**：是否识别了变更可能影响的范围？

### 差距对齐检查
- [ ] **路径验证**：所有文件路径均通过工具确认存在？
- [ ] **集成点验证**：是否读取了 Schema / 路由 / 配置的实际内容？
- [ ] **查重验证**：是否确认没有创建已存在的组件？

### 否决条件（出现以下任一情况需退回重做）
- "建议使用 X 库，但依赖文件中并没有 X"
- "假设 `src/utils/api.ts` 存在，但未验证"
- "创建了新组件，但同名组件已存在"
- "未读取 Schema/Migration 就提出了数据模型变更"

## 与其他技能的关系

本技能是**语言无关的前置技能**，产出的 Context Artifact 可直接输入到需求分析、设计和计划阶段。

当识别到项目语言后，联动对应的领域技能：

| 项目语言 | 联动技能 | 联动时机 |
|----------|----------|----------|
| Java | `java-crud-module` | 创建新模块前收集上下文 |
| Java | `java-api-endpoint` | 新增 API 前了解现有模式 |
| Java | `java-architecture-guide` | 理解项目遵循的架构规范 |
| 所有语言 | 需求/设计/计划类技能 | Context Artifact 作为输入 |

## 铁律

| 禁止 | 必须 |
|------|------|
| 猜测文件路径 | 用 `Glob` / `Read` 验证路径存在 |
| 假设某个库可用 | 用 `Read` 检查依赖文件确认 |
| 创建已存在的东西 | 用 `Glob` + `Grep` 先搜索再决定 |
| 跳过语义追踪 | 至少追踪一层调用链（调用者 + 被调用者） |
| 无来源的断言 | 在验证记录中记录工具和参数 |
| 分析瘫痪（无限调查） | 遵守深度控制，达到终止条件时停止 |

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| "项目应该用了 Redis" | 用 `Read` 读依赖文件确认（Java: `pom.xml`、Go: `go.mod`、JS: `package.json`、Python: `pyproject.toml`） |
| "创建 `DateUtils`" | 先用 `Glob` 搜索工具类目录（参考语言速查表），再用 `Grep("DateUtil")` 确认不存在 |
| "这个表有 `user_id` 字段" | 用 `Read` 读 Migration / Schema 文件或 ORM 模型定义确认字段存在 |
| 只搜索 `Order` | 扩展搜索 `Order`, `订单`, `Purchase`, `交易` |
| 直接开始写代码 | 先用 `SemanticSearch` 找双胞胎功能，复制其模式 |
| 用 Java 的分层术语描述 Go 项目 | 根据语言速查表使用正确的术语（如 Go 用 Handler 而非 Controller） |
| 调查 30 分钟还没结论 | 记录已知事实，标注"信息不足"，推进到下一步 |
