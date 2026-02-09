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

```java
@Data
@Schema(description = "分页请求基类")
public class PageReq {
    @Schema(description = "页码", example = "1")
    @Min(value = 1, message = "页码不能小于1")
    private Integer page = 1;

    @Schema(description = "每页大小", example = "20")
    @Range(min = 1, max = 100, message = "每页大小需在1-100之间")
    private Integer size = 20;
}

@Data
@Schema(description = "创建操作返回ID")
public class IdResp {
    @Schema(description = "资源ID")
    private Long id;

    public IdResp(Long id) { this.id = id; }
}
```

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

### 更新 DTO 模板

更新 DTO 与创建 DTO 的区别：字段通常**全部可选**（仅传入需要修改的字段），不加 `@NotBlank` 等必填校验。

```java
@Data
@Schema(description = "策略更新请求")
public class PolicyUpdateReq {

    @Schema(description = "策略名称", example = "火灾预警策略V2")
    private String name;

    @Schema(description = "策略描述")
    private String description;

    @Schema(description = "告警等级")
    private AlertLevelEnum alertLevel;

    @Schema(description = "关联设备ID列表")
    private List<String> deviceIds;
}
```

> **设计策略**: 若业务要求全量更新（每次提交完整数据），则 UpdateReq 可加必填校验，与 CreateReq 类似。

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
@ToString(callSuper = true)
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

> **继承场景必须**: `@EqualsAndHashCode(callSuper = true)` + `@ToString(callSuper = true)`，否则父类字段不参与 equals/toString。

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

### 枚举序列化

DTO 中使用枚举类型时，需明确 JSON 序列化/反序列化策略：

```java
@Getter
@AllArgsConstructor
public enum AlertLevelEnum {
    HIGH("high", "高"),
    MEDIUM("medium", "中"),
    LOW("low", "低");

    @JsonValue   // 序列化时输出 value 值（如 "high"）
    private final String value;

    private final String label;

    @JsonCreator // 反序列化时按 value 匹配
    public static AlertLevelEnum fromValue(String value) {
        for (AlertLevelEnum e : values()) {
            if (e.value.equals(value)) return e;
        }
        throw new IllegalArgumentException("未知告警等级: " + value);
    }
}
```

| 注解 | 用途 |
|------|------|
| `@JsonValue` | 控制枚举序列化输出（推荐使用业务值而非 name/ordinal） |
| `@JsonCreator` | 控制枚举反序列化匹配逻辑 |

## MapStruct Converter

### 统一配置（推荐）

所有 Converter 共享的配置，自动忽略未映射字段，无需逐个 `@Mapping(ignore=true)`：

```java
@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.IGNORE,
    unmappedSourcePolicy = ReportingPolicy.IGNORE
)
public interface ConverterConfig {
}
```

> **推荐策略**: 优先使用 `config = ConverterConfig.class`（简洁、统一）。仅在需要**显式控制映射关系**（如字段名不同、常量赋值）时才使用 `@Mapping`。

### Converter 接口模板

```java
@Mapper(config = ConverterConfig.class)
public interface PolicyConverter {

    // Entity → DTO
    PolicyCard toCard(AlertPolicy entity);
    PolicyDetail toDetail(AlertPolicy entity);
    List<PolicyCard> toCards(List<AlertPolicy> entities);

    // 创建: DTO → Entity
    AlertPolicy toEntity(PolicyCreateReq req);

    // 更新: DTO 合并到已有 Entity（仅覆盖非 null 字段）
    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(PolicyUpdateReq req, @MappingTarget AlertPolicy entity);
}
```

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

用于 MapStruct 自动映射后的**补充逻辑**（组装显示名称、计算派生字段等）：

```java
@AfterMapping
default void enrichCard(AlertPolicy entity, @MappingTarget PolicyCard card) {
    // 组装显示名称
    card.setDisplayName(entity.getName() + " (" + entity.getAlertLevel().getLabel() + ")");
}

@AfterMapping
default void setDefaultValues(@MappingTarget AlertPolicy entity) {
    if (entity.getEnabled() == null) entity.setEnabled(false);
    if (entity.getStatus() == null) entity.setStatus(PolicyStatusEnum.DISABLED);
}
```

> **null 值处理**: 简单的 null → 默认值场景优先使用 `@BeanMapping(nullValuePropertyMappingStrategy)` 或 `ConverterConfig` 级别配置，`@AfterMapping` 保留给需要自定义逻辑的场景。

### 自定义转换 (default 方法)

用于枚举、时间戳等需要逻辑的转换：

```java
@Mapper(config = ConverterConfig.class)
public interface AlertConverter {

    AlertCard toCard(AlertRecord entity);

    // 自定义时间戳转换（MapStruct 自动调用匹配的类型转换方法）
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

### 组合 Converter (uses)

当 Entity 含有嵌套对象需要转换时，使用 `uses` 引入其他 Converter：

```java
@Mapper(config = ConverterConfig.class, uses = {TimePlanConverter.class})
public interface PolicyConverter {
    // MapStruct 自动调用 TimePlanConverter 转换嵌套的 TimePlan → TimePlanResp
    PolicyDetail toDetail(AlertPolicy entity);
}

@Mapper(config = ConverterConfig.class)
public interface TimePlanConverter {
    TimePlanResp toResp(TimePlan entity);
    List<TimePlanResp> toResps(List<TimePlan> entities);
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
