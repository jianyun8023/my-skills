---
name: java-crud-module
description: Scaffold a complete CRUD business module for Spring Boot + MyBatis-Plus layered architecture. Creates all 9 required files (Migration, Entity, Mapper, DTOs, Converter, Service, Facade, Controller) following established conventions. Use when creating a new business module, CRUD feature, or module scaffolding.
---

# CRUD 模块脚手架

为 Spring Boot + MyBatis-Plus 分层架构项目创建完整的业务模块。

**前置**: 遵守 `java-architecture-guide` 中的分层原则。

## 模块创建 Checklist

按此顺序创建，每步依赖前一步的产出：

```
Step 1: Migration SQL  → 建表，定义数据模型
Step 2: Entity         → 映射表结构到 Java 类
Step 3: Mapper         → 空接口，继承 BaseMapper
Step 4: DTOs           → 请求/响应对象
Step 5: Converter      → MapStruct Entity ↔ DTO 转换
Step 6: Service 接口   → 定义业务方法签名
Step 7: Service 实现   → 实现业务逻辑
Step 8: Facade         → 跨服务编排、事务管理
Step 9: Controller     → HTTP 入口、参数校验
```

完成后更新 CHANGELOG.md。

## 命名规范速查

以资源名 `AlertPolicy`（表名 `alert_policy`）为例：

| 文件 | 命名 | 包路径 |
|------|------|--------|
| Migration | `YYYYMMDDHHMMSS_create_alert_policy.sql` | `migrations/{module}/scripts/` |
| Entity | `AlertPolicy.java` | `{service-module}/.../entity/` |
| Mapper | `AlertPolicyMapper.java` | `{service-module}/.../repository/` |
| Create DTO | `PolicyCreateReq.java` | `{service-module}/.../dto/policy/` |
| Update DTO | `PolicyUpdateReq.java` | `{service-module}/.../dto/policy/` |
| Card DTO | `PolicyCard.java` | `{service-module}/.../dto/policy/` |
| Detail DTO | `PolicyDetail.java` | `{service-module}/.../dto/policy/` |
| Converter | `PolicyConverter.java` | `{service-module}/.../converter/` |
| Service | `PolicyService.java` / `PolicyServiceImpl.java` | `{service-module}/.../service/` |
| Facade | `PolicyFacade.java` | `{web-module}/.../facade/` |
| Controller | `PolicyController.java` | `{web-module}/.../controller/` |
| API 路径 | `/api/v1/policies` | — |

**规则**:
- 类名 PascalCase，表名 snake_case，API 路径 kebab-case 复数
- DTO 包按模块子目录组织（`dto/policy/`, `dto/task/`）
- Facade 和 Controller 在 web 模块，其余在 service 模块

## 典型目录结构

```
project/
├── {service-module}/src/main/java/com/example/service/
│   ├── entity/           # Step 2
│   ├── repository/       # Step 3 (Mapper)
│   ├── dto/
│   │   └── {module}/     # Step 4
│   ├── converter/        # Step 5
│   └── service/
│       └── impl/         # Step 6-7
├── {web-module}/src/main/java/com/example/web/
│   ├── facade/           # Step 8
│   └── controller/       # Step 9
└── migrations/{module}/scripts/  # Step 1
```

## 各步骤要点

### Step 1: Migration SQL
参考 `java-db-migration` Skill。必备列：id, deleted, create_time, update_time。

### Step 2: Entity
```java
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("alert_policy")
public class AlertPolicy extends BizEntity {
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    @TableField("name")
    private String name;

    // 枚举字段
    @TableField("status")
    private PolicyStatusEnum status;

    // JSON 字段
    @TableField(value = "config_json", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> configJson;

    // 逻辑删除
    @TableLogic
    private Boolean deleted;
}
```

### Step 3: Mapper
```java
@Mapper
public interface AlertPolicyMapper extends BaseMapper<AlertPolicy> {
    // 空接口 - 不添加任何方法
}
```
**禁止** Mapper XML 自定义 SQL，所有查询在 Service 层用 `LambdaQueryWrapper` 构建。

### Step 4-5: DTOs + Converter
参考 `java-dto-converter` Skill。

### Step 6-7: Service
```java
// 接口
public interface PolicyService {
    AlertPolicy getById(Long id);
    Long create(PolicyCreateReq req);
    void update(Long id, PolicyUpdateReq req);
    void delete(Long id);
    PageResult<PolicyCard> getPage(int page, int size, String name);
}

// 实现
@Slf4j
@Service
@RequiredArgsConstructor
public class PolicyServiceImpl implements PolicyService {
    private final AlertPolicyMapper policyMapper;
    private final PolicyConverter converter;

    @Override
    public AlertPolicy getById(Long id) {
        AlertPolicy entity = policyMapper.selectById(id);
        if (entity == null) {
            throw new BusinessException(ErrorCode.POLICY_NOT_FOUND, "策略不存在: " + id);
        }
        return entity;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long create(PolicyCreateReq req) {
        validateNameUnique(req.getName(), null);
        AlertPolicy entity = converter.toEntity(req);
        entity.setStatus(PolicyStatusEnum.DISABLED);
        policyMapper.insert(entity);
        return entity.getId();
    }
}
```

### Step 8: Facade
```java
@Component
@Slf4j
@RequiredArgsConstructor
public class PolicyFacade {
    private final PolicyService policyService;
    private final TaskService taskService;  // 可注入多个 Service

    @Transactional(rollbackFor = Exception.class)
    public Long create(PolicyCreateReq req) {
        return policyService.create(req);
    }

    // 读操作：查询 + 丰富关联数据
    public PolicyDetail getDetail(Long id) {
        PolicyDetail detail = policyService.getDetail(id);
        // 丰富关联数据
        enrichWithRelatedData(detail);
        return detail;
    }
}
```

### Step 9: Controller
参考 `java-api-endpoint` Skill。

## 完成后检查

- [ ] 9 个文件全部创建
- [ ] 分层调用方向正确 (Controller → Facade → Service → Mapper)
- [ ] Service 没有注入其他 Service
- [ ] Mapper 是空接口
- [ ] 无 Mapper XML 自定义 SQL（查询均在 Service 构建）
- [ ] 写操作有 @Transactional(rollbackFor = Exception.class)
- [ ] DTO 有 @Schema 注解
- [ ] Controller 有 @Tag / @Operation 注解
- [ ] CHANGELOG.md 已更新

## 完整代码参考

详细的 9 文件完整代码示例见 [reference.md](reference.md)。
