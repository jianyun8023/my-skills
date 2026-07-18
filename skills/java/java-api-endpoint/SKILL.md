---
name: java-api-endpoint
description: Use when adding RESTful API endpoints to Spring Boot layered projects, including CRUD routes, pagination, batch actions, and OpenAPI annotations. Covers Controller and Facade patterns plus request and response conventions.
---

# API 端点开发

在 Spring Boot 分层架构项目中添加 RESTful API 端点。

**前置**: 遵守 `java-architecture-guide` 中的分层原则。

## 适用场景

- 新增 RESTful 接口
- 为现有资源补充分页、详情、启停、批量操作等端点
- 统一 Controller / Facade 层的接口风格

## 不适用

- RPC、消息消费、定时任务等非 HTTP 入口
- 仅修改 Service / Repository 内部逻辑而不暴露新接口
- 不遵循该仓库 Java 分层约定的项目

## 快速工作流

1. 先确认资源名、路径和返回模型，再决定端点形态
2. Controller 只做参数接收、校验和响应封装
3. 读写编排放 Facade，数据查询和落库逻辑放 Service
4. 最后补齐 `@Tag`、`@Operation`、`@Parameter` 等 OpenAPI 注解

## RESTful 规范

### 路径格式

```
/api/v{version}/{resources}
```

- 资源名: **复数名词**, **kebab-case**
- 示例: `/api/v1/alert-policies`, `/api/v1/video-sources`

### 标准 CRUD 映射

| 操作 | 方法 | 路径 | 返回 |
|------|------|------|------|
| 创建 | POST | `/api/v1/policies` | `ApiResponse<IdResp>` |
| 更新 | PUT | `/api/v1/policies/{id}` | `ApiResponse<Void>` |
| 删除 | DELETE | `/api/v1/policies/{id}` | `ApiResponse<Void>` |
| 详情 | GET | `/api/v1/policies/{id}` | `ApiResponse<DetailDTO>` |
| 分页列表 | GET | `/api/v1/policies?page=1&size=20` | `ApiResponse<PageResult<Card>>` |
| 游标分页 | GET | `/api/v1/policies/stream?cursor=&size=20` | `ApiResponse<CursorPageResult<Card>>` |
| 批量操作 | POST | `/api/v1/policies/batch/{action}` | `ApiResponse<BatchResp>` |

## Controller 模式

### 类声明

```java
@Slf4j
@RestController
@RequestMapping(path = "/api/v1/policies", produces = MediaType.APPLICATION_JSON_VALUE)
@Tag(name = "预警策略", description = "预警策略管理接口")
@RequiredArgsConstructor
public class PolicyController {
    private final PolicyFacade facade;  // 只注入 Facade
}
```

**必需注解**:
- `@Tag(name, description)` — OpenAPI 分组
- `@RequestMapping(path, produces=JSON)` — 统一 JSON 响应
- `@RequiredArgsConstructor` — 构造器注入

### 统一响应

所有方法返回 `ApiResponse<T>`:

```java
ApiResponse.ok()              // 无数据成功
ApiResponse.ok(data)          // 带数据成功
ApiResponse.error(code, msg)  // 错误
```

### 参数校验

```java
// Request Body 校验
@PostMapping
public ApiResponse<IdResp> create(@Valid @RequestBody PolicyCreateReq req)

// Path Variable 校验 (类上需加 @Validated)
@Validated
@RestController
public class PolicyController {
    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(
        @NotNull(message = "ID不能为空")
        @Positive(message = "ID必须为正数")
        @PathVariable Long id)
}
```

## 5 种端点模板

### 1. 分页查询 (偏移分页)

适用于小数据量，前端需要页码跳转。

```java
@Operation(summary = "分页查询策略列表")
@GetMapping
public ApiResponse<PageResult<PolicyCard>> getPage(
        @Parameter(description = "页码", example = "1")
        @RequestParam(defaultValue = "1") int page,
        @Parameter(description = "每页大小", example = "20")
        @RequestParam(defaultValue = "20") int size,
        @Parameter(description = "策略名称")
        @RequestParam(required = false) String name,
        @Parameter(description = "状态")
        @RequestParam(required = false) String status) {
    return ApiResponse.ok(facade.getPage(page, size, name, status));
}
```

### 2. 游标分页 (大数据量)

适用于大数据量，避免深分页性能问题。

```java
@Operation(summary = "游标分页查询")
@GetMapping("/stream")
public ApiResponse<CursorPageResult<PolicyCard>> getStreamPage(
        @Parameter(description = "游标(上页最后一条ID)")
        @RequestParam(required = false) Long cursor,
        @Parameter(description = "每页大小")
        @RequestParam(defaultValue = "20") int size,
        @Parameter(description = "策略名称")
        @RequestParam(required = false) String name) {
    if (cursor != null && cursor < 0L) {
        cursor = null;
    }
    return ApiResponse.ok(facade.getStreamPage(cursor, size, name));
}
```

**Service 层游标分页实现要点**:
```java
LambdaQueryWrapper<Entity> wrapper = new LambdaQueryWrapper<>();
if (cursor != null) {
    wrapper.lt(Entity::getId, cursor);  // ID < cursor
}
wrapper.orderByDesc(Entity::getId)
       .last("LIMIT " + (size + 1));   // 多查一条判断 hasMore

List<Entity> list = mapper.selectList(wrapper);
boolean hasMore = list.size() > size;
if (hasMore) list = list.subList(0, size);
```

### 3. 详情查询

```java
@Operation(summary = "查询策略详情")
@GetMapping("/{id}")
public ApiResponse<PolicyDetail> getDetail(
        @Parameter(description = "策略ID", example = "1")
        @PathVariable Long id) {
    return ApiResponse.ok(facade.getDetail(id));
}
```

### 4. 创建 / 更新 / 删除

```java
@Operation(summary = "创建策略")
@PostMapping
public ApiResponse<IdResp> create(@Valid @RequestBody PolicyCreateReq req) {
    Long id = facade.create(req);
    return ApiResponse.ok(new IdResp(id));
}

@Operation(summary = "更新策略")
@PutMapping("/{id}")
public ApiResponse<Void> update(
        @Parameter(description = "策略ID") @PathVariable Long id,
        @Valid @RequestBody PolicyUpdateReq req) {
    facade.update(id, req);
    return ApiResponse.ok();
}

@Operation(summary = "删除策略")
@DeleteMapping("/{id}")
public ApiResponse<Void> delete(
        @Parameter(description = "策略ID") @PathVariable Long id) {
    facade.delete(id);
    return ApiResponse.ok();
}
```

### 5. 批量操作

```java
@Operation(summary = "批量启动任务")
@PostMapping("/batch/start")
public ApiResponse<TaskBatchResp> batchStart(
        @Valid @RequestBody TaskBatchReq req) {
    return ApiResponse.ok(facade.batchStart(req));
}
```

**Facade 层批量操作模式** (部分成功):
```java
public TaskBatchResp batchStart(TaskBatchReq req) {
    TaskBatchResp resp = new TaskBatchResp();
    for (Long taskId : req.getTaskIds()) {
        try {
            startTask(taskId);
            resp.addSuccess(taskId);
        } catch (Exception e) {
            resp.addFailure(taskId, e.getMessage());
        }
    }
    return resp;
}
```

## Facade 编排模式

### 写操作: 验证 → 执行 → 返回

```java
@Transactional(rollbackFor = Exception.class)
public Long create(PolicyCreateReq req) {
    // 1. 验证关联数据有效性
    validateRelatedData(req);
    // 2. 调用 Service 执行
    Long id = policyService.create(req);
    // 3. 创建关联数据
    createTimePlans(id, req.getTimePlans());
    return id;
}
```

### 读操作: 查询 → 批量关联 → 丰富结果

```java
public PageResult<PolicyCard> getPage(int page, int size, String name, String status) {
    // 1. 查询主数据
    PageResult<PolicyCard> result = policyService.getPage(page, size, name, status);
    // 2. 提取 ID 批量查询关联数据
    List<Long> policyIds = result.getRecords().stream()
            .map(PolicyCard::getId).toList();
    Map<Long, List<TimePlan>> planMap = timePlanService.batchGetByPolicyIds(policyIds);
    // 3. 丰富结果
    result.getRecords().forEach(card ->
            card.setTimePlans(planMap.getOrDefault(card.getId(), List.of())));
    return result;
}
```

## OpenAPI 注解速查

| 注解 | 位置 | 用途 |
|------|------|------|
| `@Tag(name, description)` | Controller 类 | API 分组 |
| `@Operation(summary, description)` | 方法 | 操作说明 |
| `@Parameter(description, example)` | 参数 | 参数说明 |
| `@Schema(description, example)` | DTO 字段 | 字段说明 |

## 启用/禁用端点模式

```java
@Operation(summary = "切换启用状态")
@PatchMapping("/{id}/enabled")
public ApiResponse<Void> switchEnabled(
        @PathVariable Long id,
        @RequestParam boolean enabled) {
    facade.switchEnabled(id, enabled);
    return ApiResponse.ok();
}
```

**Facade 层**:
```java
@Transactional(rollbackFor = Exception.class)
public void switchEnabled(Long id, boolean enabled) {
    if (enabled) {
        // 启用前检查依赖是否就绪
        validateDependenciesReady(id);
    } else {
        // 禁用前检查是否被其他模块使用
        checkNotInUse(id);
    }
    policyService.switchEnabled(id, enabled);
}
```

## Checklist

实现前：
- [ ] 已确认资源名使用复数 kebab-case，且路径与语义匹配
- [ ] 已确认返回 DTO / 分页模型 / 批量响应模型
- [ ] 已确认该接口是读操作、写操作还是批量操作

实现后：
- [ ] Controller 只注入 Facade，没有直接调用 Service
- [ ] 所有接口统一返回 `ApiResponse<T>`
- [ ] 请求参数包含必要的校验注解和 OpenAPI 注解
- [ ] 写操作的事务边界放在 Facade / Service 合适位置

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 用单数路径如 `/api/v1/policy` | 使用复数资源路径，如 `/api/v1/policies` |
| Controller 里直接编排多个 Service | 把跨服务编排上推到 Facade |
| 为列表查询直接返回 Entity | 返回 `Card` / `Detail` 等 DTO |
| 批量接口逐条抛异常中断 | 明确设计成全成功或部分成功，并返回结构化结果 |
