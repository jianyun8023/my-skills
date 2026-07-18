---
name: java-db-migration
description: Use when creating MyBatis Migration scripts for schema changes such as new tables, added columns, and index updates. Covers file format, standard columns, rollback sections, and migration bootstrap patterns.
---

# 数据库迁移脚本

生成符合 MyBatis Migration 规范的数据库迁移脚本。

## 适用场景

- 新建业务表
- 为现有表新增字段、索引或 JSON 列
- 调整唯一索引 / 普通索引
- 任何需要生成 MyBatis Migration 脚本的 Schema 变更

## 不适用

- 直接在线手改生产数据库
- 仅写查询 SQL、存储过程或数据修复脚本
- 不使用 MyBatis Migration 管理的项目

## 快速工作流

1. 先确认变更类型：建表、加列、改索引还是初始化迁移体系
2. 按标准模板写正向 SQL 和 `@UNDO` 逆向 SQL
3. 检查列注释、逻辑删除字段、索引命名和唯一约束是否符合规范
4. 在非生产环境执行迁移并验证回滚

## 脚本格式

### 文件命名

```
YYYYMMDDHHMMSS_description.sql
```

示例: `20251027082057_create_analysis_task_tables.sql`

### 必需结构

每个脚本必须包含两段：

```sql
-- // 脚本描述（一句话说明变更内容）
-- Migration SQL that makes the change goes here.

-- 变更 SQL 放在这里

-- //@UNDO
-- SQL to undo the change goes here.

-- 回滚 SQL 放在这里
```

`-- //` 和 `-- //@UNDO` 是 MyBatis Migration 的必需标记，不可省略。

## 标准列规范

### 必备列（所有业务表）

```sql
`id`          BIGINT(20)   NOT NULL AUTO_INCREMENT COMMENT '主键',
`deleted`     TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '逻辑删除',
`create_time` DATETIME     NOT NULL COMMENT '创建时间',
`update_time` DATETIME     NOT NULL COMMENT '更新时间',
```

### 可选列（按需添加）

```sql
`create_user` BIGINT(20)   COMMENT '创建人',
`update_user` BIGINT(20)   COMMENT '修改人',
`version_num` INT          NOT NULL DEFAULT 1 COMMENT '版本号(乐观锁)',
`sort_num`    INT          COMMENT '排序序号',
```

### 强制要求

- 所有列必须有 `COMMENT`
- 表必须有 `COMMENT`
- 使用 `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`

## 索引命名规范

| 类型 | 前缀 | 示例 |
|------|------|------|
| 主键 | `PRIMARY KEY` | `PRIMARY KEY (id)` |
| 唯一索引 | `uk_` | `uk_name_version` |
| 普通索引 | `idx_` | `idx_create_time` |

**关键规则**: 唯一约束必须包含 `deleted` 字段，以支持逻辑删除后重新创建同名记录。

```sql
-- CORRECT: 包含 deleted
UNIQUE KEY `uk_name` (`name`, `deleted`)

-- WRONG: 不包含 deleted，逻辑删除后无法创建同名记录
UNIQUE KEY `uk_name` (`name`)
```

### 外键字段

- 命名: `{关联表}_id`（如 `policy_id`, `task_id`）
- 类型: `BIGINT(20)` 数字ID 或 `VARCHAR(100)` 业务ID
- **不使用物理外键约束**，通过应用层保证一致性
- 外键字段必须建索引: `KEY idx_{field} ({field})`

## 场景模板

### 场景 1: 创建表

```sql
-- // 创建告警策略表
-- Migration SQL that makes the change goes here.

CREATE TABLE IF NOT EXISTS `alert_policy` (
    `id`             BIGINT(20)   NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name`           VARCHAR(255) NOT NULL COMMENT '策略名称',
    `description`    TEXT                  COMMENT '策略描述',
    `enabled`        TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否启用',
    `alert_level`    VARCHAR(20)  NOT NULL DEFAULT 'LEVEL_3' COMMENT '告警等级',
    `storage_plan`   VARCHAR(20)  NOT NULL DEFAULT '7D' COMMENT '存储计划',
    `policy_id`      BIGINT(20)            COMMENT '关联策略ID',
    `deleted`        TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    `create_user`    BIGINT(20)            COMMENT '创建人',
    `update_user`    BIGINT(20)            COMMENT '修改人',
    `create_time`    DATETIME     NOT NULL COMMENT '创建时间',
    `update_time`    DATETIME     NOT NULL COMMENT '更新时间',
    `version_num`    INT          NOT NULL DEFAULT 1 COMMENT '版本号(乐观锁)',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`, `deleted`),
    KEY `idx_alert_level` (`alert_level`),
    KEY `idx_policy_id` (`policy_id`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警策略表';

-- //@UNDO
-- SQL to undo the change goes here.

DROP TABLE IF EXISTS `alert_policy`;
```

### 场景 2: 添加列

```sql
-- // 告警记录表新增处置相关字段
-- Migration SQL that makes the change goes here.

ALTER TABLE `alert_records`
    ADD COLUMN `handle_status` VARCHAR(32) COMMENT '处置状态' AFTER `message`,
    ADD COLUMN `handle_time`   DATETIME    COMMENT '处置时间' AFTER `handle_status`,
    ADD COLUMN `handle_remark` TEXT        COMMENT '处置备注' AFTER `handle_time`;

ALTER TABLE `alert_records`
    ADD INDEX `idx_handle_status` (`handle_status`);

-- //@UNDO
-- SQL to undo the change goes here.

ALTER TABLE `alert_records`
    DROP INDEX `idx_handle_status`,
    DROP COLUMN `handle_remark`,
    DROP COLUMN `handle_time`,
    DROP COLUMN `handle_status`;
```

### 场景 3: 修改索引

```sql
-- // 修复子任务唯一索引为普通索引
-- Migration SQL that makes the change goes here.

DROP INDEX `uk_task_source` ON `analysis_sub_task`;

CREATE INDEX `idx_task_source` ON `analysis_sub_task` (`task_id`, `source_id`);

-- //@UNDO
-- SQL to undo the change goes here.

DROP INDEX `idx_task_source` ON `analysis_sub_task`;

CREATE UNIQUE INDEX `uk_task_source` ON `analysis_sub_task` (`task_id`, `source_id`);
```

## 回滚脚本要求

- 回滚必须是变更的精确逆操作
- 删表: `DROP TABLE IF EXISTS`
- 删列: 按添加的逆序 DROP
- 删索引: 先删索引再删列
- 恢复索引: 重建原来的索引

## 常用命令

```bash
# 创建新迁移脚本
MODULE={module} ENV=dev ./script/migration_new.sh "create_alert_policy"

# 执行迁移
MODULE={module} ENV=dev ./script/migration_up.sh

# 回滚最近一次迁移
MODULE={module} ENV=dev ./script/migration_down.sh

# 查看迁移状态
MODULE={module} ENV=dev ./script/migration_status.sh
```

## 深入参考

以下内容已拆到 [reference.md](reference.md)：

- 新项目从零搭建 MyBatis Migration 的目录结构与 Maven 配置
- 环境配置文件模板、bootstrap.sql 与 shell 脚本模板
- 空白迁移脚本模板
- JSON 字段使用建议

## 最佳实践

1. **一次一变更**: 每个脚本只做一个变更（创建表、添加字段等）
2. **不可修改已发布脚本**: 已部署的脚本不能修改，只能创建新脚本
3. **测试回滚**: 在非生产环境测试 `@UNDO` 脚本
4. **备份数据**: 生产环境执行前备份数据库

## Checklist

编写前：
- [ ] 已确认该项目使用 MyBatis Migration 管理 Schema
- [ ] 已明确本次变更的正向动作和精确回滚动作
- [ ] 已确认表名、字段名、索引名符合现有命名规范

完成后：
- [ ] 脚本包含 `-- //` 与 `-- //@UNDO` 两段
- [ ] 所有新增列和表都带有 `COMMENT`
- [ ] 唯一索引已评估是否需要包含 `deleted`
- [ ] 已在非生产环境验证迁移和回滚

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 只写正向 SQL，不写 `@UNDO` | 始终补齐精确逆操作 |
| 唯一索引不包含 `deleted` | 逻辑删除场景下把 `deleted` 纳入唯一约束 |
| 一个脚本混入多类大改动 | 保持一次一变更，便于审计和回滚 |
| 发布后修改旧脚本 | 创建新的迁移脚本修正问题 |
