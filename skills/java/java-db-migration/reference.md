# MyBatis Migration 详细参考

当你需要在一个新项目中从零搭建 MyBatis Migration，或需要复制完整模板时，再读取本文件。

## 独立使用指南

以下模板可以让 MyBatis Migration 在任何新项目中独立使用，无需依赖已有项目。

### 1. 目录结构

```text
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
