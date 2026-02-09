---
name: java-db-migration
description: Generate MyBatis Migration database scripts following established conventions. Handles table creation, column addition, and index changes with proper undo sections. Use when creating migration scripts, adding tables, adding columns, changing indexes, or making any database schema change.
---

# 数据库迁移脚本

生成符合 MyBatis Migration 规范的数据库迁移脚本。

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

## 独立使用指南

以下模板可以让 MyBatis Migration 在任何新项目中独立使用，无需依赖已有项目。

### 1. 目录结构

```
project-root/
├── pom.xml                          # 根 pom，配置 migration 插件
├── script/                          # Migration 管理脚本
│   ├── migration_init.sh            # 初始化迁移环境
│   ├── migration_bootstrap.sh       # 引导迁移（执行 bootstrap.sql）
│   ├── migration_new.sh             # 创建新迁移脚本
│   ├── migration_up.sh              # 执行迁移
│   ├── migration_down.sh            # 回滚迁移
│   └── migration_status.sh          # 查看迁移状态
└── migrations/{module}/             # 迁移目录（module 可自定义）
    ├── environments/                # 环境配置
    │   ├── dev.properties
    │   ├── local.properties
    │   └── prod.properties
    └── scripts/                     # 迁移脚本
        ├── bootstrap.sql            # 初始化引导脚本
        └── YYYYMMDDHHMMSS_xxx.sql   # 业务迁移脚本
```

### 2. Maven 插件配置

在项目**根 `pom.xml`** 中配置（使用 `-N` 非递归执行，不影响子模块）：

```xml
<properties>
    <mybatis-migration-maven-plugin.version>1.2.0</mybatis-migration-maven-plugin.version>
    <mysql-connector-j.version>8.3.0</mysql-connector-j.version>
</properties>

<build>
    <plugins>
        <!-- MyBatis Migrations Maven 插件 - 仅用于命令行独立执行 migration:up/down -->
        <plugin>
            <groupId>org.mybatis.maven</groupId>
            <artifactId>migrations-maven-plugin</artifactId>
            <version>${mybatis-migration-maven-plugin.version}</version>
            <dependencies>
                <dependency>
                    <groupId>com.mysql</groupId>
                    <artifactId>mysql-connector-j</artifactId>
                    <version>${mysql-connector-j.version}</version>
                </dependency>
            </dependencies>
        </plugin>
    </plugins>
</build>
```

**关键说明**：
- 插件 `artifactId` 是 `migrations-maven-plugin`（注意复数），不是 `mybatis-migrations-maven-plugin`
- 必须在 `<dependencies>` 中引入数据库驱动（如 MySQL Connector）
- 插件版本 `1.2.0` 对应 MyBatis Migration 核心库 `3.4.0`
- 不需要在 `<configuration>` 中设置 `path` 和 `env`，由 shell 脚本通过 `-D` 参数传入

### 3. 环境配置文件模板

文件路径: `migrations/{module}/environments/{env}.properties`

```properties
driver=com.mysql.cj.jdbc.Driver
url: jdbc:mysql://{host}:{port}/{database}?useSSL=false&verifyServerCertificate=false&allowPublicKeyRetrieval=true&characterEncoding=utf8&characterSetResults=utf8&autoReconnect=true&failOverReadOnly=false&serverTimezone=GMT%2B8
username={username}
password={password}

send_full_script=false
```

**注意**：
- `url` 使用冒号 `:` 而不是等号 `=`（MyBatis Migration 支持两种格式，但 URL 中含 `=` 时建议用 `:`）
- `send_full_script=false` 表示逐条发送 SQL，便于定位错误
- 每个环境一个文件，如 `dev.properties`、`local.properties`、`prod.properties`

### 4. Bootstrap 脚本模板

文件路径: `migrations/{module}/scripts/bootstrap.sql`

```sql
-- bootstrap.sql - 用于初始化数据库基础结构

-- 创建迁移历史表(MyBatis Migration自动管理)
-- 注意：不需要手动创建，工具会自动创建CHANGELOG表
```

### 5. Shell 脚本模板

所有脚本需要 `chmod +x script/migration_*.sh` 添加执行权限。

#### migration_init.sh — 初始化迁移环境

```bash
#!/bin/bash

MODULE=${MODULE:-sensevision}
ENV=${ENV:-dev}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

mvn -N migration:init -Dmigration.path="${PROJECT_ROOT}/migrations/${MODULE}/" -Dmigration.env=${ENV}
```

#### migration_bootstrap.sh — 引导迁移（首次初始化新库）

```bash
#!/bin/bash

MODULE=${MODULE:-sensevision}
ENV=${ENV:-dev}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

mvn -N migration:bootstrap -Dmigration.path="${PROJECT_ROOT}/migrations/${MODULE}/" -Dmigration.env=${ENV}
```

#### migration_new.sh — 创建新迁移脚本

```bash
#!/bin/bash

if [ $# -ne 1 ]; then
  echo '用法: MODULE=sensevision ENV=dev migration_new.sh "create_table_example"'
  exit 1
fi

MODULE=${MODULE:-sensevision}
ENV=${ENV:-dev}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

mvn -N migration:new -Dmigration.path="${PROJECT_ROOT}/migrations/${MODULE}/" -Dmigration.env=${ENV} -Dmigration.description="$1"
```

#### migration_up.sh — 执行迁移

```bash
#!/bin/bash

MODULE=${MODULE:-sensevision}
ENV=${ENV:-dev}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

mvn -N migration:up -Dmigration.path="${PROJECT_ROOT}/migrations/${MODULE}/" -Dmigration.env=${ENV}
```

#### migration_down.sh — 回滚最近一次迁移

```bash
#!/bin/bash

MODULE=${MODULE:-sensevision}
ENV=${ENV:-dev}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

mvn -N migration:down -Dmigration.path="${PROJECT_ROOT}/migrations/${MODULE}/" -Dmigration.env=${ENV}
```

#### migration_status.sh — 查看迁移状态

```bash
#!/bin/bash

MODULE=${MODULE:-sensevision}
ENV=${ENV:-dev}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

mvn -N migration:status -Dmigration.path="${PROJECT_ROOT}/migrations/${MODULE}/" -Dmigration.env=${ENV}
```

### 6. 从零搭建步骤

```bash
# 1. 在根 pom.xml 中添加 migration 插件配置（见上方 Maven 插件配置）

# 2. 创建 script/ 目录并添加所有 shell 脚本
mkdir -p script
# ... 创建上述 6 个脚本文件 ...
chmod +x script/migration_*.sh

# 3. 初始化迁移环境（自动创建 migrations/{module}/ 目录结构）
MODULE=sensevision ENV=dev ./script/migration_init.sh

# 4. 手动创建/编辑环境配置文件，填入数据库连接信息
# 编辑 migrations/sensevision/environments/dev.properties

# 5. 引导迁移（在数据库中创建 CHANGELOG 表）
MODULE=sensevision ENV=dev ./script/migration_bootstrap.sh

# 6. 创建第一个迁移脚本
MODULE=sensevision ENV=dev ./script/migration_new.sh "create_first_table"

# 7. 编辑生成的 SQL 文件，然后执行迁移
MODULE=sensevision ENV=dev ./script/migration_up.sh
```

## 空白迁移脚本模板

创建脚本时建议直接使用如下模板（同样适用于 `migration_new.sh` 生成后修改）：

```sql
-- // {一句话描述变更内容}
-- Migration SQL that makes the change goes here.

-- TODO: 写具体变更SQL

-- //@UNDO
-- SQL to undo the change goes here.

-- TODO: 写回滚SQL（精确逆操作）
```

## JSON 字段

当需要存储复杂结构时使用 JSON 类型：

```sql
`agent_ids`    JSON NOT NULL COMMENT '智能体ID数组',
`config_json`  JSON          COMMENT '配置信息（webhook、token等）',
`coordinates`  TEXT NOT NULL COMMENT '多边形坐标点JSON数组',
```

**权衡**: JSON 字段灵活性高但查询性能低，不适合频繁查询的字段。

## 最佳实践

1. **一次一变更**: 每个脚本只做一个变更（创建表、添加字段等）
2. **不可修改已发布脚本**: 已部署的脚本不能修改，只能创建新脚本
3. **测试回滚**: 在非生产环境测试 `@UNDO` 脚本
4. **备份数据**: 生产环境执行前备份数据库
