---
name: java-architecture-guide
description: Java 业务项目架构原则和编码规范。适用于 Spring Boot + MyBatis-Plus 分层架构项目。在编写/审查/重构 Java 业务代码时主动参考。Use when writing, reviewing, or refactoring Java business code, or when the user mentions architecture, coding standards, layering, or best practices.
---

# Java 业务项目架构指南

## 分层架构

四层单向调用，禁止反向或跨层依赖：

```
Controller → Facade → Service → Repository (Mapper)
```

### 各层职责

| 层 | 职责 | 注入 | 禁止 |
|---|---|---|---|
| **Controller** | HTTP 入口、参数校验、响应封装 | Facade | 注入 Service；包含业务逻辑；添加事务 |
| **Facade** | 跨服务编排、事务边界、DTO 组装 | 多个 Service、Converter | 直接操作 Mapper |
| **Service** | 单一领域业务逻辑、数据操作 | 本域 Mapper、Converter | 注入其他 Service 或其他域的 Mapper |
| **Repository** | 数据访问（继承 BaseMapper） | — | 添加自定义方法（查询在 Service 中构建） |

### 为什么引入 Facade 层

- **单一职责**: Service 层专注自己领域，不承担编排逻辑
- **降低耦合**: Service 不依赖其他 Service，可独立测试
- **事务清晰**: 跨服务事务统一在 Facade 管理
- **便于定位**: 业务编排集中在 Facade，排查问题路径清晰

## 层间调用铁律

### 规则 1: Controller 只注入 Facade

```java
// CORRECT
@RestController
@RequiredArgsConstructor
public class PolicyController {
    private final PolicyFacade facade;  // ✅

    @PostMapping
    public ApiResponse<IdResp> create(@Valid @RequestBody PolicyCreateReq req) {
        return ApiResponse.ok(new IdResp(facade.create(req)));
    }
}

// WRONG
public class PolicyController {
    private final PolicyService service;  // ❌ 禁止直接注入 Service
}
```

### 规则 2: Service 禁止注入其他 Service

这是**最常被违反的规则**。跨域数据需求必须上推到 Facade 层。

```java
// WRONG - Service 跨域调用
@Service
public class AlgoServiceServiceImpl {
    private final LlmServiceMapper llmServiceMapper;  // ❌ 注入其他域 Mapper
    private final VideoSourceService videoSourceService;  // ❌ 注入其他 Service
}

// CORRECT - Facade 编排
@Component
@RequiredArgsConstructor
public class AlgoServiceFacade {
    private final AlgoServiceService algoServiceService;  // ✅
    private final LlmServiceService llmServiceService;    // ✅ Facade 注入多个 Service
    
    public AlgoServiceDetail getDetail(Long id) {
        AlgoServiceDetail detail = algoServiceService.getDetail(id);
        if (detail.getLlmServiceId() != null) {
            LlmService llm = llmServiceService.getById(detail.getLlmServiceId());
            detail.setLlmServiceName(llm.getName());
        }
        return detail;
    }
}
```

### 规则 3: Mapper 保持空接口

查询逻辑在 Service 中使用 `LambdaQueryWrapper` 构建，保证类型安全。
**禁止** 在 Mapper 中新增方法或 Mapper XML 自定义 SQL，复杂条件仍在 Service 使用 Wrapper/`apply` 构建。

```java
// CORRECT
@Mapper
public interface PolicyMapper extends BaseMapper<AlertPolicy> {
    // 空接口，不添加任何方法
}

// Service 中构建查询
LambdaQueryWrapper<AlertPolicy> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(AlertPolicy::getEnabled, true)
       .orderByDesc(AlertPolicy::getCreateTime);
List<AlertPolicy> list = baseMapper.selectList(wrapper);

// WRONG
@Mapper
public interface PolicyMapper extends BaseMapper<AlertPolicy> {
    @Select("SELECT * FROM alert_policy WHERE enabled = 1")  // ❌
    List<AlertPolicy> findEnabled();
}
```

## 事务管理

### 事务边界

| 场景 | 事务位置 | 示例 |
|---|---|---|
| 跨服务写操作 | Facade 层 | 创建任务 + 创建子任务 |
| 单服务复杂写操作 | Service 层 | 批量删除 + 依赖检查 |
| 读操作 | 无事务 | 查询列表、查询详情 |
| Controller 层 | **禁止** | — |

### 事务注解标准写法

```java
@Transactional(rollbackFor = Exception.class)
public Long create(TaskCreateReq req) {
    // 业务逻辑
}
```

### 事务内禁止

- 远程调用（HTTP / RPC / 消息发送）
- 耗时操作（文件 IO、大量计算）
- `@Async` 方法调用

## 异常处理体系

### 异常层次

```
RuntimeException
  └── BusinessException (业务异常，含 ErrorCode)
        └── AuthConsoleException (外部系统异常)
```

### 各层异常职责

| 层 | 职责 |
|---|---|
| Service | 抛出 `BusinessException`（资源不存在、业务规则违反） |
| Facade | **不捕获** BusinessException，透传给全局处理器；仅捕获需要补偿的外部调用异常 |
| Controller | 不处理异常 |
| GlobalExceptionHandler | 统一捕获，转换为 `ApiResponse` |

### 错误码分段管理

按业务模块分配错误码范围（如 2xxx 算法服务、3xxx 预警策略），避免冲突。

### 日志级别规范

| 场景 | 级别 | 堆栈 |
|---|---|---|
| 业务异常（BusinessException） | WARN | 无 |
| 参数校验失败 | WARN | 无 |
| 系统异常（未预期） | ERROR | 有 |
| 关键业务操作（创建/更新/删除） | INFO | 无 |

## 命名规范

### Java 命名

| 类型 | 规则 | 示例 |
|---|---|---|
| 类名 | PascalCase | `AnalysisTaskService` |
| 方法 / 变量 | camelCase | `getTaskById`, `videoSourceId` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| 包名 | 全小写 | `com.example.service.impl` |

### 分层命名

| 类型 | 命名模式 |
|---|---|
| Controller | `{Resource}Controller` |
| Facade | `{Resource}Facade` （直接类，无接口） |
| Service 接口 | `{Resource}Service` |
| Service 实现 | `{Resource}ServiceImpl` |
| Mapper | `{Resource}Mapper` |
| Entity | `{Resource}` |
| Converter | `{Resource}Converter` |

### 数据库命名

| 类型 | 规则 | 示例 |
|---|---|---|
| 表名 | snake_case | `alert_policy`, `video_source_cache` |
| 字段名 | snake_case | `create_time`, `llm_service_id` |
| 外键字段 | `{关联表}_id` | `policy_id`, `task_id` |
| 唯一索引 | `uk_{fields}` | `uk_name_version` |
| 普通索引 | `idx_{fields}` | `idx_create_time` |

### API 路径

- 格式: `/api/v{version}/{resources}` (复数, kebab-case)
- 示例: `/api/v1/llm-services`, `/api/v1/analysis-tasks`

## 代码质量原则

### 必须遵守

- 公共 API 方法必须有 Javadoc
- 使用 `LambdaQueryWrapper` 保证类型安全，避免字符串列名
- 不使用物理外键约束，通过应用层保证数据一致性
- 所有表使用逻辑删除（`deleted` 字段）
- 写操作考虑乐观锁（`version_num` 字段）
- 删除前检查依赖关系，防止数据不一致

### 统一响应格式

所有 API 返回 `ApiResponse<T>`:

```java
ApiResponse.ok()           // 无数据成功
ApiResponse.ok(data)       // 带数据成功
ApiResponse.error(code, msg)  // 错误
```

### 参数校验

- Request Body: `@Valid @RequestBody XxxReq req`
- Path Variable 校验: 类上加 `@Validated`，参数上加 `@NotBlank`
- 校验注解: `@NotBlank`, `@NotNull`, `@NotEmpty` (Jakarta Validation)

## 常见反模式

| 反模式 | 为什么不行 | 正确做法 |
|---|---|---|
| Service 注入其他 Service | 循环依赖、职责混乱、难以测试 | 跨域编排放 Facade 层 |
| Controller 直接调用 Service | 跳过 Facade 编排层，业务逻辑散落 | Controller → Facade → Service |
| Mapper 中写自定义 SQL | 丢失类型安全，SQL 散落 | Service 中用 LambdaQueryWrapper |
| 事务内做 HTTP/RPC 调用 | 长事务、锁争用、调用失败导致回滚 | 事务外调用，或拆分事务 |
| 捕获 BusinessException 后吞掉 | 错误被隐藏，调用方无法感知 | 让全局处理器统一处理 |
| Entity 直接作为 API 响应 | 暴露内部结构，难以演化 | 使用 DTO 做 API 契约 |
| 不指定 rollbackFor | 默认只回滚 RuntimeException | `@Transactional(rollbackFor = Exception.class)` |
