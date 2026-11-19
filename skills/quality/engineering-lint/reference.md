# Engineering Lint — 工具与实施参考

本文件是按需读取的参考，不要求每个项目安装所有工具。工具的维护状态、最新版本、语言支持和许可证可能变化；实际选型时核对官方文档、项目当前工具链和 CI 环境。

## 工具选型原则

- 先确认仓库当前语言、框架、编译器、构建系统和 CI。
- 已有工具能表达规则时，不增加第二套重复检查。
- 对确定性规则优先使用编译器、类型系统、AST 或依赖图。
- 不要把格式工具当成 Bug 检查，也不要把安全扫描结果直接等同于架构正确性。
- 新工具需要说明维护活跃度、版本兼容、运行成本、误报率、离线/自托管能力和许可证。
- 先在代表性目录试跑，再扩大范围；新增工具应锁定版本并有升级策略。

## 语言与生态参考

| 生态 | 优先检查 | 架构 / 依赖规则 | 备注 |
| --- | --- | --- | --- |
| Kotlin / Android | Android Lint、Detekt、Kotlin compiler | Konsist、自定义 Detekt 规则、Gradle 依赖检查 | Android Lint 关注 Android API/资源；Detekt 关注 Kotlin 源码；Konsist 适合包与类架构测试。ktlint 主要解决格式和风格，不应代替 Bug 规则。 |
| Java | Error Prone、SpotBugs、PMD、Checkstyle | ArchUnit、依赖分析 | 根据构建插件和 JDK 版本选择；避免 Checkstyle/PMD/SpotBugs 规则重复。 |
| Rust | rustc、Clippy、rustfmt | cargo tree、cargo-deny；必要时 Dylint | Clippy 先启用高信号 lint group；自定义 Dylint 仅用于现有 lint 无法表达的规则。 |
| Go | gofmt、go vet、staticcheck、golangci-lint | 自定义 analyzer、depguard | golangci-lint 可以统一编排多种检查；不要重复跑相同 analyzer。 |
| TypeScript / JavaScript | TypeScript compiler、ESLint | dependency-cruiser、Knip、ast-grep | ESLint 负责代码规则；依赖图检查负责模块边界；类型检查不能由 ESLint 代替。 |
| Python | Ruff、mypy / Pyright | import-linter、deptry | Ruff 统一 lint/format 的部分场景；类型检查和依赖边界是不同问题。 |
| Swift | Swift compiler、SwiftLint、SwiftFormat | 自定义架构测试、依赖检查 | 格式/风格与并发、可访问性等正确性约束分开。 |
| 多语言仓库 | 各语言原生工具 | ast-grep、Semgrep、专用契约测试 | 只有确实跨语言且规则表达一致时才引入统一工具。 |

### 常见工具的职责边界

- **Android Lint**：Android API 使用、Manifest、资源、兼容性及平台特定问题。
- **Detekt**：Kotlin 代码静态规则、潜在 Bug、协程和性能模式；可通过自定义规则扩展。
- **ktlint**：Kotlin 格式与风格。启用前评估全仓格式化成本。
- **Konsist**：通过 Kotlin 测试表达包、类、命名和依赖架构约束。
- **Clippy**：Rust 编译期静态分析。优先保留 correctness/suspicious 等高信号规则，逐步收紧。
- **rustfmt**：Rust 格式规范，不判断业务正确性。
- **Dylint**：在需要编写 Rust 专属自定义 lint 时评估；增加工具链和维护负担。
- **ast-grep**：基于 AST 搜索和规则匹配，适合跨语言或单语言的结构模式；规则能力和语言解析支持需按实际版本验证。
- **Semgrep**：模式匹配与安全规则平台，适合有明确跨文件/安全检查需求的场景；与 ast-grep 的职责可能重叠。
- **ArchUnit**：Java 架构测试；Kotlin 项目也需核对语言/字节码模型和实际规则表达能力。

不要因为表中出现某个工具就默认采用。最终选型以当前项目实际版本和官方能力为准。

## 规则类别与推荐机制

| 规则类型 | 首选机制 | 何时需要自定义 |
| --- | --- | --- |
| 禁止/限制 API | 编译器、现有 Linter 的禁用 API 规则 | 需要额外上下文或专门修复信息 |
| 包/模块依赖方向 | 依赖图、架构测试 | 工具无法描述项目特有的允许边 |
| 唯一状态所有者 | 架构测试、代码所有权清单、契约测试 | 有可稳定识别的 AST 模式 |
| 线程约束 | 类型/线程注解、平台 Lint、静态分析 | 规则能可靠识别阻塞调用及线程上下文 |
| 资源生命周期 | RAII、类型系统、静态分析、测试 | 可识别具体未配对的 acquire/release 模式 |
| 危险错误处理 | 编译器/Linter、返回类型约束 | 需要识别特定边界入口 |
| 性能坏模式 | profiler/benchmark 先取证，再做静态规则 | 有稳定且可解释的语法模式 |
| 代码格式 | 官方 formatter | 一般不需要自定义 |
| 依赖许可证/漏洞 | 包管理器与专用供应链扫描 | 需要组织策略或 allowlist |
| 动态时序/并发行为 | 单元、属性、集成、压力或设备测试 | 不应仅用静态 Lint 替代 |

## 如何判断规则是否适合静态检查

适合静态检查：
- 目标 API 或调用位置可明确识别。
- 模块依赖边可从构建文件或 AST 提取。
- 规则有明确允许列表和禁止列表。
- 违规能稳定映射到具体文件、符号和修复建议。

不适合单独用静态检查：
- 依赖运行时事件顺序、线程调度或设备固件行为。
- 需要判断业务意图、状态机完整性或协议语义。
- 只有“看起来复杂”“文件太大”或“最好不要这样写”等主观判断。
- 需要证明没有资源泄漏，但无法完整观察资源所有权和所有退出路径。

对不适合静态检查的问题，采用测试、类型建模、运行时断言、诊断指标或人工审查；不要编造一个不可靠的 Lint。

## Agent 友好错误信息

推荐格式：

```text
<RULE-ID>: <short violation>

Reason:
<the invariant and the concrete risk>

Fix:
<the preferred owner/API/pattern to use>

Allowed:
<narrow exceptions, if any>

Reference:
<project rule or architecture document>
```

要求：
- 信息足够短，适合 Agent 作为下一轮输入。
- 明确项目的正确接口或责任归属。
- 不把未证实的后果写成必然结果。
- 对有替代 API 的禁用规则，直接给出替代项。
- 不输出只要求“添加 suppress”的建议。

## 历史基线策略

1. 在启用 Error 前对目标目录运行完整检查并保存报告。
2. 对每条历史违规记录规则 ID、路径和数量；尽量使用工具原生 baseline。
3. baseline 只包含已存在问题，不把整个目录、整个规则组或未来问题都豁免。
4. 新增文件和新增违规必须被检查；验证工具是否会把新违规错误地归入 baseline。
5. 清理历史问题后缩小或删除对应 baseline。
6. suppress/ignore 必须局部、可检索、有具体理由；定期复核。
7. 避免将生成代码、vendor 和测试代码混入生产规则，除非它们本身是检查目标。

## CI 集成策略

- 在本地命令与 CI 使用相同工具版本、配置、目录和构建变体。
- 对需要阻断合并的检查纳入一个稳定 required status；避免路径过滤导致必需检查永远 Pending。
- 对昂贵检查使用缓存、任务分片和合理超时。
- 先让低风险、高信号规则阻断；覆盖率趋势、重型安全扫描或不稳定任务可先非阻断。
- 失败时上传文本/SARIF/HTML 等有用报告，但避免上传密钥、敏感源码或过大的诊断数据。
- 工具升级时先比较规则结果和 baseline 变化，再合并版本升级。
- 对 CI 没有运行的检查，不得在交付中声称“CI 已覆盖”。

## DiPlay-ECARX 应用参考

以下仅是当前已知项目背景下的候选方向；每次实际调用仍必须读取当前 checkout、AGENTS.md、架构文档和 CI，不能把这里当成永久事实。

已知项目是 Android 车机应用，生产核心大量迁移到 Rust，Kotlin 保留 Android Host/Platform Adapter。可重点评估：

1. **Rust/Kotlin 职责边界**：Rust 拥有协议、会话决策、媒体队列/调度、恢复、导航与车辆数据转换；Kotlin 保留 UI、Activity/Service 生命周期、平台权限、焦点、蓝牙/热点、USB/VPN、存储和车机 SDK 适配。静态规则只能检查明确的依赖/入口模式；“是否重复实现了业务决策”通常还需要代码审查和契约测试。
2. **JNI/FFI 边界**：检查 JNI 声明、转换和资源释放是否集中在项目指定 owner；禁止为了方便增加根层兼容 re-export 或平行实现。以当前架构文档为准。
3. **资源生命周期**：FD、Native Buffer、codec、AAudio、USB URB 等资源，优先通过 RAII/Closeable owner 和生命周期测试保护；不要仅靠查找 close() 文本判断泄漏。
4. **线程与平台约束**：Android 主线程阻塞、SDK 回调线程、Handler/Executor 生命周期等，只有在可准确识别上下文时才做静态门禁；否则使用线程封装、StrictMode、测试和实车验证。
5. **错误与 panic 边界**：JNI/FFI、线程入口和平台回调的 panic/异常处理应按项目既有合同审查；不要全局禁止所有 unwrap/expect 或 catch。
6. **现有工具优先**：复用项目已经配置的 Android Lint、Detekt、Clippy、rustfmt；核对它们实际扫描的模块、source set 和 CI job，再决定是否增加 Konsist、ast-grep 或自定义规则。

历史经验：DiPlay 曾通过 P0 工程护栏落地记录加入 Detekt bug 级规则、Clippy correctness/suspicious、rustfmt、库模块 Android Lint 和非阻断 Kover 报告。此类历史事实只能作为线索，不能替代当前分支检查。

## 维护与停止条件

当新增规则：
- 保护了新发现且已确认的不变量；
- 有测试证明不会误伤合法代码；
- 已接入实际 CI；
- 文档与配置同步；
- 不再有会改变选型的未决问题；

即可停止，不为增加规则数量继续扩张。
