# CRUD 模块完整代码参考

以"分析任务 (AnalysisTask)"模块为参考，展示完整 9 文件的代码结构。

---

## 1. Migration SQL

```sql
-- // 创建分析任务相关表
-- Migration SQL that makes the change goes here.

CREATE TABLE `analysis_task` (
    `id`          BIGINT(20)   NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name`        VARCHAR(255) NOT NULL COMMENT '任务名称',
    `description` TEXT                  COMMENT '任务描述',
    `status`      VARCHAR(20)  NOT NULL DEFAULT 'STOPPED' COMMENT '任务状态',
    `enabled`     TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否启用',
    `agent_ids`   JSON         NOT NULL COMMENT '智能体ID数组',
    `policy_id`   BIGINT(20)            COMMENT '关联策略ID',
    `deleted`     TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    `create_user` BIGINT(20)            COMMENT '创建人',
    `update_user` BIGINT(20)            COMMENT '修改人',
    `create_time` DATETIME     NOT NULL COMMENT '创建时间',
    `update_time` DATETIME     NOT NULL COMMENT '更新时间',
    `version_num` INT          NOT NULL DEFAULT 1 COMMENT '版本号(乐观锁)',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`, `deleted`),
    KEY `idx_status` (`status`),
    KEY `idx_policy_id` (`policy_id`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析任务表';

-- //@UNDO
-- SQL to undo the change goes here.

DROP TABLE IF EXISTS `analysis_task`;
```

---

## 2. Entity

```java
@Data
@EqualsAndHashCode(callSuper = true)
@TableName(value = "analysis_task", autoResultMap = true)
@Schema(description = "分析任务")
public class AnalysisTask extends BizEntity {

    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    @TableField("name")
    private String name;

    @TableField("description")
    private String description;

    @TableField("status")
    private TaskStatusEnum status;

    @TableField("enabled")
    private Boolean enabled;

    @TableField(value = "agent_ids", typeHandler = JacksonTypeHandler.class)
    private List<String> agentIds;

    @TableField("policy_id")
    private Long policyId;

    @TableLogic
    @TableField("deleted")
    private Boolean deleted;

    @Version
    @TableField("version_num")
    private Integer versionNum;

    // 非数据库字段 - 由 Facade/Service 填充
    @TableField(exist = false)
    private List<AnalysisSubTask> subTasks;
}
```

---

## 3. Mapper

```java
@Mapper
public interface AnalysisTaskMapper extends BaseMapper<AnalysisTask> {
    // 空接口
}
```

---

## 4. DTOs

### 创建请求
```java
@Data
@Schema(description = "分析任务创建请求")
public class AnalysisTaskCreateReq {

    @Schema(description = "任务名称", example = "视频监控任务1")
    @NotBlank(message = "任务名称不能为空")
    private String name;

    @Schema(description = "任务描述")
    private String description;

    @Schema(description = "智能体ID列表")
    @NotEmpty(message = "智能体ID列表不能为空")
    private List<String> agentIds;

    @Schema(description = "关联策略ID")
    private Long policyId;
}
```

### 更新请求
```java
@Data
@Schema(description = "分析任务更新请求")
public class AnalysisTaskUpdateReq {

    @Schema(description = "任务名称")
    private String name;

    @Schema(description = "任务描述")
    private String description;

    @Schema(description = "智能体ID列表")
    private List<String> agentIds;

    @Schema(description = "关联策略ID")
    private Long policyId;
}
```

### 列表卡片
```java
@Data
@Schema(description = "分析任务卡片")
public class AnalysisTaskCard {

    @Schema(description = "任务ID")
    private Long id;

    @Schema(description = "任务名称")
    private String name;

    @Schema(description = "任务状态")
    private TaskStatusEnum status;

    @Schema(description = "是否启用")
    private Boolean enabled;

    @Schema(description = "智能体名称列表")
    private List<String> agentNames;

    @Schema(description = "创建时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
}
```

### 详情
```java
@Data
@EqualsAndHashCode(callSuper = true)
@Schema(description = "分析任务详情")
public class AnalysisTaskDetail extends AnalysisTaskCard {

    @Schema(description = "任务描述")
    private String description;

    @Schema(description = "智能体ID列表")
    private List<String> agentIds;

    @Schema(description = "关联策略ID")
    private Long policyId;

    @Schema(description = "子任务列表")
    private List<AnalysisSubTaskResp> subTasks;

    @Schema(description = "更新时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updateTime;
}
```

---

## 5. Converter

```java
@Mapper(componentModel = "spring")
public interface AnalysisTaskConverter {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "enabled", ignore = true)
    @Mapping(target = "createTime", ignore = true)
    @Mapping(target = "updateTime", ignore = true)
    @Mapping(target = "deleted", ignore = true)
    AnalysisTask toEntity(AnalysisTaskCreateReq req);

    AnalysisTaskCard toCard(AnalysisTask entity);

    AnalysisTaskDetail toDetail(AnalysisTask entity);

    List<AnalysisTaskCard> toCards(List<AnalysisTask> entities);

    @AfterMapping
    default void normalizeStrings(@MappingTarget AnalysisTaskCard card) {
        if (card.getName() == null) card.setName("");
    }
}
```

---

## 6. Service 接口

```java
public interface AnalysisTaskService {

    AnalysisTask getById(Long id);

    Long create(AnalysisTaskCreateReq req);

    void update(Long id, AnalysisTaskUpdateReq req);

    void delete(Long id);

    AnalysisTaskDetail getDetail(Long id);

    PageResult<AnalysisTaskCard> getPage(int page, int size, String name, String status);

    CursorPageResult<AnalysisTaskCard> getStreamPage(Long cursor, int size, String name);
}
```

---

## 7. Service 实现

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class AnalysisTaskServiceImpl implements AnalysisTaskService {

    private final AnalysisTaskMapper taskMapper;
    private final AnalysisTaskConverter converter;

    @Override
    public AnalysisTask getById(Long id) {
        AnalysisTask entity = taskMapper.selectById(id);
        if (entity == null) {
            throw new BusinessException(ErrorCode.TASK_NOT_FOUND, "任务不存在: " + id);
        }
        return entity;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long create(AnalysisTaskCreateReq req) {
        validateNameUnique(req.getName(), null);
        AnalysisTask entity = converter.toEntity(req);
        entity.setStatus(TaskStatusEnum.STOPPED);
        entity.setEnabled(false);
        taskMapper.insert(entity);
        log.info("创建分析任务: id={}, name={}", entity.getId(), entity.getName());
        return entity.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(Long id, AnalysisTaskUpdateReq req) {
        AnalysisTask entity = getById(id);
        if (req.getName() != null) {
            validateNameUnique(req.getName(), id);
            entity.setName(req.getName());
        }
        if (req.getDescription() != null) {
            entity.setDescription(req.getDescription());
        }
        if (req.getAgentIds() != null) {
            entity.setAgentIds(req.getAgentIds());
        }
        taskMapper.updateById(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(Long id) {
        AnalysisTask entity = getById(id);
        // 检查是否可删除（如任务正在运行则不允许）
        taskMapper.deleteById(id);
        log.info("删除分析任务: id={}, name={}", id, entity.getName());
    }

    @Override
    public PageResult<AnalysisTaskCard> getPage(int page, int size, String name, String status) {
        LambdaQueryWrapper<AnalysisTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.like(name != null, AnalysisTask::getName, name)
               .eq(status != null, AnalysisTask::getStatus, status)
               .orderByDesc(AnalysisTask::getCreateTime);

        IPage<AnalysisTask> pageResult = taskMapper.selectPage(new Page<>(page, size), wrapper);
        List<AnalysisTaskCard> cards = converter.toCards(pageResult.getRecords());
        return new PageResult<>(cards, pageResult.getTotal(), page, size);
    }

    @Override
    public CursorPageResult<AnalysisTaskCard> getStreamPage(Long cursor, int size, String name) {
        LambdaQueryWrapper<AnalysisTask> wrapper = new LambdaQueryWrapper<>();
        if (cursor != null) {
            wrapper.lt(AnalysisTask::getId, cursor);
        }
        wrapper.like(name != null, AnalysisTask::getName, name)
               .orderByDesc(AnalysisTask::getId)
               .last("LIMIT " + (size + 1));

        List<AnalysisTask> entities = taskMapper.selectList(wrapper);
        boolean hasMore = entities.size() > size;
        if (hasMore) {
            entities = entities.subList(0, size);
        }

        List<AnalysisTaskCard> cards = converter.toCards(entities);
        CursorPageResult<AnalysisTaskCard> result = new CursorPageResult<>();
        result.setRecords(cards);
        result.setHasMore(hasMore);
        result.setCount(cards.size());
        if (!entities.isEmpty()) {
            result.setNextCursor(entities.get(entities.size() - 1).getId());
        }
        return result;
    }

    private void validateNameUnique(String name, Long excludeId) {
        LambdaQueryWrapper<AnalysisTask> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AnalysisTask::getName, name);
        if (excludeId != null) {
            wrapper.ne(AnalysisTask::getId, excludeId);
        }
        if (taskMapper.selectCount(wrapper) > 0) {
            throw new BusinessException(ErrorCode.TASK_NAME_DUPLICATE, "任务名称已存在: " + name);
        }
    }
}
```

---

## 8. Facade

```java
@Slf4j
@Component
@RequiredArgsConstructor
public class AnalysisTaskFacade {

    private final AnalysisTaskService taskService;
    private final AgentService agentService;  // 可注入其他 Service

    @Transactional(rollbackFor = Exception.class)
    public Long create(AnalysisTaskCreateReq req) {
        // 1. 验证关联数据
        validateAgents(req.getAgentIds());
        // 2. 创建任务
        Long taskId = taskService.create(req);
        return taskId;
    }

    public AnalysisTaskDetail getDetail(Long id) {
        AnalysisTaskDetail detail = taskService.getDetail(id);
        // 丰富关联数据
        enrichAgentNames(detail);
        return detail;
    }

    public PageResult<AnalysisTaskCard> getPage(int page, int size, String name, String status) {
        PageResult<AnalysisTaskCard> result = taskService.getPage(page, size, name, status);
        // 批量丰富关联数据
        batchEnrichAgentNames(result.getRecords());
        return result;
    }

    private void validateAgents(List<String> agentIds) {
        for (String agentId : agentIds) {
            // 验证智能体存在且可用
        }
    }

    private void enrichAgentNames(AnalysisTaskCard card) {
        if (card.getAgentIds() != null) {
            List<String> names = agentService.getNamesByIds(card.getAgentIds());
            card.setAgentNames(names);
        }
    }

    private void batchEnrichAgentNames(List<AnalysisTaskCard> cards) {
        cards.forEach(this::enrichAgentNames);
    }
}
```

---

## 9. Controller

```java
@Slf4j
@RestController
@RequestMapping(path = "/api/v1/tasks", produces = MediaType.APPLICATION_JSON_VALUE)
@Tag(name = "任务中心 / 分析任务", description = "分析任务管理接口")
@RequiredArgsConstructor
public class AnalysisTaskController {

    private final AnalysisTaskFacade facade;

    @Operation(summary = "创建分析任务")
    @PostMapping
    public ApiResponse<IdResp> create(@Valid @RequestBody AnalysisTaskCreateReq req) {
        Long id = facade.create(req);
        return ApiResponse.ok(new IdResp(id));
    }

    @Operation(summary = "更新分析任务")
    @PutMapping("/{id}")
    public ApiResponse<Void> update(
            @Parameter(description = "任务ID") @PathVariable Long id,
            @Valid @RequestBody AnalysisTaskUpdateReq req) {
        facade.update(id, req);
        return ApiResponse.ok();
    }

    @Operation(summary = "删除分析任务")
    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(
            @Parameter(description = "任务ID") @PathVariable Long id) {
        facade.delete(id);
        return ApiResponse.ok();
    }

    @Operation(summary = "查询任务详情")
    @GetMapping("/{id}")
    public ApiResponse<AnalysisTaskDetail> getDetail(
            @Parameter(description = "任务ID") @PathVariable Long id) {
        return ApiResponse.ok(facade.getDetail(id));
    }

    @Operation(summary = "分页查询任务列表")
    @GetMapping
    public ApiResponse<PageResult<AnalysisTaskCard>> getPage(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页大小") @RequestParam(defaultValue = "20") int size,
            @Parameter(description = "任务名称") @RequestParam(required = false) String name,
            @Parameter(description = "任务状态") @RequestParam(required = false) String status) {
        return ApiResponse.ok(facade.getPage(page, size, name, status));
    }

    @Operation(summary = "游标分页查询")
    @GetMapping("/stream")
    public ApiResponse<CursorPageResult<AnalysisTaskCard>> getStreamPage(
            @Parameter(description = "游标") @RequestParam(required = false) Long cursor,
            @Parameter(description = "每页大小") @RequestParam(defaultValue = "20") int size,
            @Parameter(description = "任务名称") @RequestParam(required = false) String name) {
        if (cursor != null && cursor < 0L) {
            cursor = null;
        }
        return ApiResponse.ok(facade.getStreamPage(cursor, size, name));
    }
}
```
