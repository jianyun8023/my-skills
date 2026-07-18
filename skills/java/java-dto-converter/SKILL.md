---
name: java-dto-converter
description: Use when creating DTOs and MapStruct converters in Spring Boot layered projects. Covers naming, validation annotations, OpenAPI schemas, enum serialization, and update and response mapping patterns.
---

# DTO 与 Converter

为分层架构项目创建规范的 DTO（数据传输对象）和 MapStruct Converter（对象转换器）。

## 适用场景

- 新建请求 DTO、响应 DTO
- 为 Entity 和 DTO 建立 MapStruct 转换
- 统一分页模型、批量模型和枚举序列化约定
- 重构旧接口的对象映射方式

## 不适用

- 直接把 Entity 作为 API 契约输出的临时脚本
- 不使用 MapStruct 的轻量项目
- 只改数据库表结构、不涉及接口模型的任务

## 快速工作流

1. 先确定 DTO 角色：创建、更新、卡片、详情或分页
2. 再确定字段校验、Schema 注解和日期/枚举序列化方式
3. 最后补 Converter：创建映射、更新合并、必要的 `@AfterMapping`

## DTO 命名体系

### 请求 DTO

| 用途 | 命名 | 示例 |
|------|------|------|
| 创建 | `{Resource}CreateReq` | `PolicyCreateReq` |
| 更新 | `{Resource}UpdateReq` | `PolicyUpdateReq` |
| 分页查询 | `{Resource}PageReq` | `PolicyPageReq` |
| 批量操作 | `{Resource}BatchReq` | `TaskBatchReq` |

### 响应 DTO

| 用途 | 命名 | 示例 |
|------|------|------|
| 列表卡片 | `{Resource}Card` | `PolicyCard` |
| 详情 | `{Resource}Detail` | `PolicyDetail` |
| 通用响应 | `{Resource}Resp` | `VideoSourceResp` |
| 批量结果 | `{Resource}BatchResp` | `TaskBatchResp` |

### 通用 DTO

| 类 | 用途 |
|---|---|
| `IdResp` | 创建操作返回 ID |
| `PageReq` | 分页请求基类 (page, size) |
| `PageResult<T>` | 偏移分页结果 (records, total, page, size) |
| `CursorPageResult<T>` | 游标分页结果 (records, nextCursor, hasMore, count) |

完整示例见 [reference.md](reference.md)。

### 包组织

DTO 按业务模块分子目录：

```
dto/
├── policy/
│   ├── PolicyCreateReq.java
│   ├── PolicyUpdateReq.java
│   ├── PolicyCard.java
│   └── PolicyDetail.java
├── task/
│   ├── AnalysisTaskCreateReq.java
│   └── ...
├── ApiResponse.java
├── IdResp.java
├── PageReq.java
├── PageResult.java
└── CursorPageResult.java
```

## DTO 注解规范

请求 / 更新 / 响应 / 详情 / 分页 DTO 的完整模板见 [reference.md](reference.md)。

- 创建 DTO：必填字段补齐 `@NotBlank` / `@NotNull` / `@NotEmpty`
- 更新 DTO：默认允许部分更新，只传需要修改的字段
- 详情 DTO 继承卡片时，必须带 `@EqualsAndHashCode(callSuper = true)` 和 `@ToString(callSuper = true)`
- 分页 DTO 继承 `PageReq`，筛选字段只放业务查询条件

> **设计策略**: 若业务要求全量更新（每次提交完整数据），则 UpdateReq 可加必填校验，与 CreateReq 类似。

### 常用注解速查

| 注解 | 用途 | 示例 |
|------|------|------|
| `@Schema(description, example)` | OpenAPI 字段说明 | `@Schema(description = "用户名", example = "张三")` |
| `@NotBlank` | 字符串非空 | 必填 String 字段 |
| `@NotNull` | 非 null | 必填枚举/对象字段 |
| `@NotEmpty` | 集合非空 | 必填 List 字段 |
| `@JsonFormat(pattern)` | JSON 日期格式 | `"yyyy-MM-dd HH:mm:ss"` |
| `@JsonProperty` | JSON 字段名 | `@JsonProperty("sourceId")` |
| `@DateTimeFormat(pattern)` | 查询参数日期解析 | GET 请求的日期参数 |

### 枚举序列化

DTO 中使用枚举类型时，需明确 JSON 序列化/反序列化策略。完整示例见 [reference.md](reference.md)。

| 注解 | 用途 |
|------|------|
| `@JsonValue` | 控制枚举序列化输出（推荐使用业务值而非 name/ordinal） |
| `@JsonCreator` | 控制枚举反序列化匹配逻辑 |

## MapStruct Converter

### 统一配置（推荐）

所有 Converter 共享的配置，自动忽略未映射字段，无需逐个 `@Mapping(ignore=true)`：

完整 `ConverterConfig` 示例见 [reference.md](reference.md)。

> **推荐策略**: 优先使用 `config = ConverterConfig.class`（简洁、统一）。仅在需要**显式控制映射关系**（如字段名不同、常量赋值）时才使用 `@Mapping`。

### Converter 接口模板

完整接口模板见 [reference.md](reference.md)。

> **不使用 ConverterConfig 的写法**: 将 `@Mapper(config = ConverterConfig.class)` 替换为 `@Mapper(componentModel = "spring")`，并手动添加 `@Mapping(target = "id", ignore = true)` 等忽略注解。

### 方法命名规范

| 方法 | 用途 |
|------|------|
| `toEntity(Req)` | 请求 DTO → 新 Entity（创建） |
| `updateEntity(Req, @MappingTarget Entity)` | 请求 DTO 合并到已有 Entity（更新） |
| `toCard(Entity)` | Entity → 列表卡片 DTO |
| `toDetail(Entity)` | Entity → 详情 DTO |
| `toResp(Entity)` | Entity → 通用响应 DTO |
| `toCards(List)` | 批量转换 |

### 字段映射

- 忽略字段：`@Mapping(target = "id", ignore = true)`
- 字段名不同：`@Mapping(source = "sort", target = "sortOrder")`
- 常量值：`@Mapping(target = "status", constant = "DISABLED")`
- 表达式：`@Mapping(target = "syncTime", expression = "java(...)")`
- 嵌套属性：`@Mapping(target = "typeName", source = "entity.modelType.label")`

### 后处理 (@AfterMapping)

用于 MapStruct 自动映射后的**补充逻辑**（组装显示名称、计算派生字段等）。完整示例见 [reference.md](reference.md)。

> **null 值处理**: 简单的 null → 默认值场景优先使用 `@BeanMapping(nullValuePropertyMappingStrategy)` 或 `ConverterConfig` 级别配置，`@AfterMapping` 保留给需要自定义逻辑的场景。

### 自定义转换 (default 方法)

用于枚举、时间戳等需要逻辑的转换，完整示例见 [reference.md](reference.md)。

### 组合 Converter (uses)

当 Entity 含有嵌套对象需要转换时，使用 `uses` 引入其他 Converter。完整示例见 [reference.md](reference.md)。

## 必须忽略的字段

当 DTO → Entity 转换时，以下字段必须 ignore（由框架自动填充）：

| 字段 | 原因 |
|------|------|
| `id` | 数据库自增 |
| `deleted` | 默认值 0 |
| `createTime` / `updateTime` | MetaObjectHandler 自动填充 |
| `createUser` / `updateUser` | MetaObjectHandler 自动填充 |
| `versionNum` | 默认值 1 |

当 Entity → DTO 转换时，以下字段由 Facade 层填充，Converter 应 ignore：
- 关联数据字段（如 `agentNames`, `regionPath`, `deviceGroups`）
- 计算字段（如 `sourceCount`, `taskCount`）
- URL 转换字段（如存储路径 → 下载链接）

## Checklist

编写前：
- [ ] 已明确 DTO 是对外契约，而不是数据库结构镜像
- [ ] 已确认创建/更新/列表/详情模型是否需要拆分
- [ ] 已确认项目是否已有统一的 `ConverterConfig`

完成后：
- [ ] 请求 DTO 补齐必要的校验注解和 `@Schema`
- [ ] 更新时间场景采用 `updateEntity(..., @MappingTarget ...)`
- [ ] DTO → Entity 时忽略框架自动维护字段
- [ ] 关联数据和计算字段没有错误地下沉到 Converter

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| CreateReq 和 UpdateReq 完全复用同一套必填校验 | 根据业务决定 UpdateReq 是否允许部分更新 |
| 在 Converter 里组装大量跨服务关联数据 | 把关联丰富逻辑放到 Facade / Service |
| DTO → Entity 时覆盖 `id`、`createTime` 等自动字段 | 明确 ignore 自动维护字段 |
| 用 `ordinal` 序列化枚举 | 显式使用业务值并配合 `@JsonValue` / `@JsonCreator` |
