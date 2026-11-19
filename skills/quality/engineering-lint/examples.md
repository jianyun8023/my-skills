# Engineering Lint — 规则设计示例

这些示例说明如何把架构约束变成可执行检查。它们是规则设计样例，不代表任何项目已经实现或启用这些规则。落地前必须核对当前项目实际目录、所有者、调用链和例外。

## 示例 1：Rust Core / Kotlin Host 单一职责边界

**目标不变量**

Rust 是协议与会话策略的唯一所有者；Kotlin 只保留 Android 平台适配和执行。Kotlin 不应重新实现 Rust 已拥有的状态机、恢复预算或协议解析。

**适合自动化的部分**

- 生产 Kotlin 不得直接依赖 Rust 内部实现目录或非公开桥接符号。
- 新增 JNI 声明必须位于已批准的桥接/owner 位置。
- 旧 Kotlin 参考实现只能存在于明确的测试 source set。
- 依赖方向必须符合项目已有模块图。

**不应伪装成静态规则的部分**

“这段 Kotlin 是否重复了 Rust 的业务决策”通常需要语义判断。可以通过审查清单、架构文档和成对契约测试辅助，不能仅凭函数名或文本搜索断言。

**示例错误**

```text
DP-ARCH-001: Production Kotlin adds a second
implementation of Rust-owned recovery policy.

Reason:
Recovery budget and reset rules have one owner in Rust.
A parallel implementation can diverge on mixed failures.

Fix:
Keep Android scheduling and callback execution in Kotlin;
delegate the decision to the existing Rust owner.

Allowed:
Independent test reference code in test-only source sets.
```

## 示例 2：跨模块依赖方向

**目标不变量**

高层业务模块可以依赖公共核心接口，公共核心不能反向依赖 UI 或平台宿主。

推荐实现顺序：
1. 先使用构建系统导出的依赖图或架构测试。
2. 对明确禁止的依赖边建立正反例测试。
3. 检查静态导入、类型引用、再导出和测试 source set。
4. 只允许经过评审的窄例外。

不要只用文件路径前缀判断模块依赖，也不要把测试依赖与生产依赖混为一谈。

## 示例 3：资源生命周期与 FD 泄漏

**目标不变量**

Native FD、buffer、codec 和其他资源必须有明确 owner，并在成功、失败、取消和异常路径上释放。

先考虑：
- Rust 使用 RAII owner、Drop 和明确的借用关系。
- Kotlin 使用 Closeable/use、结构化生命周期或明确的 owner。
- 对启动失败、部分初始化和重复关闭编写测试。

静态规则可以阻止绕过统一 owner 的特定 API，也可以限制敏感构造器的调用位置；但不能通过“每个 open 都必须在同一文件出现 close”证明无泄漏。

## 示例 4：主线程阻塞

**目标不变量**

Android 主线程不能执行明确的阻塞 I/O、长时间等待或重型计算。

实现前必须确认：
- 线程上下文是否可由注解、调用图或框架入口确定。
- API 是否真的阻塞，还是仅仅名字相似。
- 是否已有 dispatcher、executor 或异步封装。
- 测试、初始化和受控同步路径是否有合理例外。

对无法静态判断的路径，使用 StrictMode、性能测试或运行时监控，而不是扩大禁止列表。

## 示例 5：禁止危险 API 并提供替代方案

当项目已统一封装某个 API，可以禁止生产代码直接调用底层入口。

```text
API-004: Direct platform client construction is forbidden
outside the approved adapter module.

Reason:
The adapter owns retry, timeout, telemetry and lifecycle policy.

Fix:
Use PlatformClientProvider from the owning module.

Allowed:
The provider implementation and isolated test fixtures.
```

此规则需要 AST/类型级匹配，且必须测试 import alias、静态调用、构造器引用和测试 source set，避免只匹配单一文本写法。

## 示例 6：如何判断一个候选是否应该成为 Lint

| 候选问题 | 推荐处理 | 原因 |
| --- | --- | --- |
| 新代码调用已弃用且禁止的 API | Lint Error | 目标明确、易检测 |
| 模块 A 反向依赖模块 B | 架构测试 / 依赖图 | 依赖边可确定 |
| Agent 经常重复写一个危险模式 | AST 自定义规则 | 需要阻止坏模式复制 |
| 大类超过 2,000 行 | 通常不直接设 Error | 行数不是架构缺陷的充分证据 |
| 所有函数都必须少于 30 行 | 不建议 | 机械阈值容易制造无意义拆分 |
| 资源可能在异常路径泄漏 | RAII + 生命周期测试，必要时静态检查 | 单纯语法匹配无法证明完整释放 |
| 某操作必须在真实车机固件上验证 | 设备测试/验收清单 | 静态 Lint 无法证明运行时行为 |
| 新增 TODO 必须有关联 issue | 项目明确要求时做轻量规则 | 属于团队流程约束，不是普遍 Bug |

## 示例 7：规则反馈的质量

较差：

```text
Do not use setTimeout.
```

更好：

```text
UI-LIFECYCLE-002: Timer is not allowed in this
declarative UI state owner.

Reason:
This timer duplicates the controller lifecycle and
can fire after the owning view has been replaced.

Fix:
Move the transition into the lifecycle-aware controller
or use the project's scheduling abstraction.

Allowed:
The centralized scheduler implementation and tested
platform adapters.
```

即使示例采用了特定框架，真实规则也必须服从当前项目的架构，不要照搬“禁止所有定时器”等绝对结论。
