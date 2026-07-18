# DTO 与 Converter 详细示例

当你需要直接复制 DTO / MapStruct 模板时，再读取本文件。主技能保留命名和约束，这里只放完整示例。

## 通用 DTO 示例

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

## 请求 DTO 模板

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

## 更新 DTO 模板

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

## 响应 DTO 模板

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

## 详情 DTO 模板

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

## 分页请求 DTO 模板

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

## 枚举序列化示例

```java
@Getter
@AllArgsConstructor
public enum AlertLevelEnum {
    HIGH("high", "高"),
    MEDIUM("medium", "中"),
    LOW("low", "低");

    @JsonValue
    private final String value;

    private final String label;

    @JsonCreator
    public static AlertLevelEnum fromValue(String value) {
        for (AlertLevelEnum e : values()) {
            if (e.value.equals(value)) return e;
        }
        throw new IllegalArgumentException("未知告警等级: " + value);
    }
}
```

## ConverterConfig 示例

```java
@MapperConfig(
    componentModel = "spring",
    unmappedTargetPolicy = ReportingPolicy.IGNORE,
    unmappedSourcePolicy = ReportingPolicy.IGNORE
)
public interface ConverterConfig {
}
```

## Converter 接口模板

```java
@Mapper(config = ConverterConfig.class)
public interface PolicyConverter {

    PolicyCard toCard(AlertPolicy entity);
    PolicyDetail toDetail(AlertPolicy entity);
    List<PolicyCard> toCards(List<AlertPolicy> entities);

    AlertPolicy toEntity(PolicyCreateReq req);

    @BeanMapping(nullValuePropertyMappingStrategy = NullValuePropertyMappingStrategy.IGNORE)
    void updateEntity(PolicyUpdateReq req, @MappingTarget AlertPolicy entity);
}
```

## @AfterMapping 示例

```java
@AfterMapping
default void enrichCard(AlertPolicy entity, @MappingTarget PolicyCard card) {
    card.setDisplayName(entity.getName() + " (" + entity.getAlertLevel().getLabel() + ")");
}

@AfterMapping
default void setDefaultValues(@MappingTarget AlertPolicy entity) {
    if (entity.getEnabled() == null) entity.setEnabled(false);
    if (entity.getStatus() == null) entity.setStatus(PolicyStatusEnum.DISABLED);
}
```

## 自定义转换示例

```java
@Mapper(config = ConverterConfig.class)
public interface AlertConverter {

    AlertCard toCard(AlertRecord entity);

    default LocalDateTime timestampToLocalDateTime(long timestamp) {
        if (timestamp == 0) return null;
        return LocalDateTime.ofInstant(
            Instant.ofEpochSecond(timestamp),
            ZoneId.systemDefault()
        );
    }

    default OnlineStatus convertOnlineStatus(String videoUrlStatus) {
        return OnlineStatus.fromVideoUrlStatus(videoUrlStatus);
    }
}
```

## uses 组合示例

```java
@Mapper(config = ConverterConfig.class, uses = {TimePlanConverter.class})
public interface PolicyConverter {
    PolicyDetail toDetail(AlertPolicy entity);
}

@Mapper(config = ConverterConfig.class)
public interface TimePlanConverter {
    TimePlanResp toResp(TimePlan entity);
    List<TimePlanResp> toResps(List<TimePlan> entities);
}
```
