---
name: java-dto-converter
description: Create DTOs and MapStruct converters for Spring Boot layered architecture projects. Covers naming conventions, validation annotations, OpenAPI schemas, and conversion patterns. Use when creating DTOs, request/response objects, converters, object mapping, or when working with MapStruct.
---

# DTO 与 Converter

为分层架构项目创建规范的 DTO（数据传输对象）和 MapStruct Converter（对象转换器）。

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

### 请求 DTO 模板

```java
@Data
@Schema(description = "策略创建请求")
public class PolicyCreateReq {

    @Schema(description = "策略名称", example = "火灾预警策略")
    @NotBlank(message = "策略名称不能为空")
    private String name;

    @Schema(description = "策略描述")
    private String description;

    @Schema(description = "告警等级")
    @NotNull(message = "告警等级不能为空")
    private AlertLevelEnum alertLevel;

    @Schema(description = "关联设备ID列表")
    @NotEmpty(message = "设备ID列表不能为空")
    private List<String> deviceIds;
}
```

### 响应 DTO 模板

```java
@Data
@Schema(description = "策略卡片")
public class PolicyCard {

    @Schema(description = "策略ID")
    private Long id;

    @Schema(description = "策略名称")
    private String name;

    @Schema(description = "是否启用")
    private Boolean enabled;

    @Schema(description = "告警等级")
    private AlertLevelEnum alertLevel;

    @Schema(description = "创建时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}
```

### 详情继承卡片

```java
@Data
@EqualsAndHashCode(callSuper = true)
@Schema(description = "策略详情")
public class PolicyDetail extends PolicyCard {

    @Schema(description = "策略描述")
    private String description;

    @Schema(description = "时间计划列表")
    private List<TimePlanResp> timePlans;

    @Schema(description = "更新时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updateTime;
}
```

### 分页请求继承基类

```java
@Data
@EqualsAndHashCode(callSuper = true)
@Schema(description = "策略分页查询请求")
public class PolicyPageReq extends PageReq {

    @Schema(description = "策略名称（模糊查询）")
    private String name;

    @Schema(description = "告警等级列表（多选）")
    private List<AlertLevelEnum> alertLevels;

    @Schema(description = "开始时间")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime startTime;
}
```

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

## MapStruct Converter

### 统一配置

所有 Converter 共享的配置：

```java
@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.IGNORE,
    unmappedSourcePolicy = ReportingPolicy.IGNORE
)
public interface ConverterConfig {
}
```

### Converter 接口模板

```java
@Mapper(componentModel = "spring")
public interface PolicyConverter {

    // Entity → DTO
    PolicyCard toCard(AlertPolicy entity);
    PolicyDetail toDetail(AlertPolicy entity);
    List<PolicyCard> toCards(List<AlertPolicy> entities);

    // DTO → Entity (忽略自动填充字段)
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    @Mapping(target = "createTime", ignore = true)
    @Mapping(target = "updateTime", ignore = true)
    @Mapping(target = "createUser", ignore = true)
    @Mapping(target = "updateUser", ignore = true)
    AlertPolicy toEntity(PolicyCreateReq req);
}
```

### 方法命名规范

| 方法 | 用途 |
|------|------|
| `toEntity(Req)` | 请求 DTO → Entity |
| `toCard(Entity)` | Entity → 列表卡片 DTO |
| `toDetail(Entity)` | Entity → 详情 DTO |
| `toResp(Entity)` | Entity → 通用响应 DTO |
| `toCards(List)` | 批量转换 |

### 字段映射

```java
// 忽略字段
@Mapping(target = "id", ignore = true)

// 字段名不同
@Mapping(source = "sort", target = "sortOrder")

// 常量值
@Mapping(target = "status", constant = "DISABLED")

// 表达式
@Mapping(target = "syncTime", expression = "java(java.time.LocalDateTime.now())")

// 嵌套属性
@Mapping(target = "typeName", source = "entity.modelType.label")
```

### 后处理 (@AfterMapping)

用于 null 值标准化和复杂逻辑：

```java
@AfterMapping
default void normalizeStrings(@MappingTarget PolicyCard card) {
    if (card.getName() == null) card.setName("");
    if (card.getDescription() == null) card.setDescription("");
}

@AfterMapping
default void setDefaultValues(@MappingTarget AlertPolicy entity) {
    if (entity.getEnabled() == null) entity.setEnabled(false);
}
```

### 自定义转换 (default 方法)

用于枚举、时间戳等需要逻辑的转换：

```java
@Mapper(componentModel = "spring")
public interface AlertConverter {

    AlertCard toCard(AlertRecord entity);

    // 自定义时间戳转换
    default LocalDateTime timestampToLocalDateTime(long timestamp) {
        if (timestamp == 0) return null;
        return LocalDateTime.ofInstant(
            Instant.ofEpochSecond(timestamp),
            ZoneId.systemDefault()
        );
    }

    // 自定义枚举转换
    default OnlineStatus convertOnlineStatus(String videoUrlStatus) {
        return OnlineStatus.fromVideoUrlStatus(videoUrlStatus);
    }
}
```

### 带 ConverterConfig 的写法

```java
// 使用统一配置（自动 IGNORE 未映射字段）
@Mapper(config = ConverterConfig.class)
public interface PolicyConverter {
    // 无需逐个 @Mapping(ignore=true)
    AlertPolicy toEntity(PolicyCreateReq req);
}
```

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
