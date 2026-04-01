---
name: calibre-drafts-api
description: >-
  Use when the user mentions Calibre 草稿、元数据草稿、drafts API、批量更新元数据、
  批量提交元数据、清理标签草稿、撤销草稿、删除草稿、元数据搜索、在线元数据、
  /api/drafts、/api/drafts/update、/api/drafts/cancel、/api/drafts/delete、
  /api/metadata/search，或需要向 Calibre 配套服务提交待审核的元数据修改或搜索在线元数据。
---

# Calibre 书籍草稿 API

用于向本地 Calibre 配套服务提交**待审核**元数据草稿；生效需管理员审核。

## 配置

配置文件路径：`~/.config/calibre-drafts-api/config.json`

**首次使用前**，检查配置文件是否存在：

```bash
cat ~/.config/calibre-drafts-api/config.json
```

若不存在，提示用户创建：

```bash
mkdir -p ~/.config/calibre-drafts-api
cat > ~/.config/calibre-drafts-api/config.json << 'EOF'
{
  "base_url": "http://localhost:3000"
}
EOF
```

### 配置说明

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `base_url` | 是 | Calibre API 服务基址，**不包含** `/api` 后缀 | `http://localhost:3000` |

### 常见配置示例

```json
# Docker Compose 部署（默认）
{"base_url": "http://localhost:3000"}

# 直接运行后端
{"base_url": "http://localhost:8080"}

# 生产环境
{"base_url": "https://calibre-api.example.com"}
```

### 地址使用规则

- 配置的 `base_url` **不应包含**尾随的 `/api`
- 所有接口路径由 `base_url` + `/api/...` 拼接
- ✅ 正确: 配置 `http://localhost:3000`，使用 `http://localhost:3000/api/drafts/update`
- ❌ 错误: 配置 `http://localhost:3000/api`，导致 `http://localhost:3000/api/api/drafts/update`

## 何时使用

**使用此技能当：**
- 需要批量提交 Calibre 书籍元数据更新草稿
- 清理垃圾标签、补全缺失元数据
- 搜索在线元数据（豆瓣等源）以获取正确的书籍信息
- 撤销或删除已提交的待审核草稿
- 调用本地 Calibre 配套服务的草稿 API

**不使用此技能当：**
- 只读访问 Calibre 书库（使用 `calibre-library` 技能）
- 直接修改 Calibre 数据库（不推荐，应通过官方 API）

## ID 约定（重要）

- **`updates[].id`**（`POST /api/drafts/update`）：Calibre **书籍 ID**（字符串，与书库/API 中书籍主键一致）。
- **`ids`**（`POST /api/drafts/delete`、`POST /api/drafts/cancel`）：**书籍 ID** 的数组，与上相同；**不是**草稿表主键或其它内部 ID。

## 批量更新草稿

- **方法/路径**: `POST /api/drafts/update`
- **Content-Type**: `application/json`

### 请求体结构

- `updates`: 数组，每项含 `id`（书籍 ID 字符串）与 `data`（要修改的字段对象）。

### 字段更新规则（必须遵守）

| 字段类型 | 包含字段 | 不传 / `null` | `[]` 或 `""` | 非空值 |
|----------|----------|---------------|--------------|--------|
| **Tags** | `tags` | 不更新 | **清空全部标签**（唯一允许「清空」的字段） | 设为该标签列表 |
| **Authors** | `authors` | 不更新 | **拒绝**（不可清空作者） | 更新作者列表 |
| **字符串** | `title`, `publisher`, `comments`, `isbn` | 不更新 | **拒绝**（不可清空） | 更新为该值 |

### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "received": 3
  }
}
```

### 注意事项

1. **同一本书多次提交会合并**：已有待审核草稿时，新提交会更新该草稿而非新建。
2. **只传需要改的字段**：未出现的字段表示不更新。
3. **违规字段单独忽略**：某字段违反规则时该字段被丢弃，其余合法字段仍保存；可查服务端日志确认。
4. **批量**：一次请求可包含多本书。

更多 JSON 请求示例见 [examples.md](examples.md)。

## 列出草稿

```http
GET /api/drafts?limit=50&offset=0
```

（完整 URL：`{基址}/api/drafts?...`）

## 元数据搜索

- **方法/路径**: `GET /api/metadata/search`
- **用途**: 搜索在线元数据源（如豆瓣），获取书籍的标准元数据信息

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | 是 | 搜索关键词：书名、作者、ISBN 等 |

### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "douban:123456",
      "title": "三体",
      "authors": ["刘慈欣"],
      "publisher": "重庆出版社",
      "pubdate": "2008-1",
      "isbn": "9787536692930",
      "tags": ["科幻", "小说"],
      "rating": 9.3,
      "cover": "https://...",
      "comments": "文化大革命如火如荼..."
    }
  ]
}
```

### 使用场景

1. **补全缺失元数据前查询**：搜索正确的书籍信息，然后通过 `POST /api/drafts/update` 提交草稿
2. **验证 ISBN**：通过 ISBN 搜索，确认书籍信息是否正确
3. **查找标准出版信息**：获取规范的出版社名称、出版日期等

### 注意事项

- 搜索结果来自在线源（如豆瓣），需要网络连接
- 返回的是候选列表，需要人工确认选择正确的条目
- `id` 字段（如 `douban:123456`）是元数据源的内部标识，**不是** Calibre 书籍 ID

## 撤销草稿

- **方法/路径**: `POST /api/drafts/cancel`
- **Content-Type**: `application/json`

用于**撤销已提交、尚未审核通过**的草稿：放弃本次待合并的修改，该书不再保留对应待审核草稿。

**请求体**（与删除接口相同形态；`ids` 为**书籍 ID**）：

```json
{
  "ids": ["123", "456", "789"]
}
```

- `ids`（必填）：要撤销草稿的 **Calibre 书籍 ID** 列表。

**响应**：与更新接口类似，`data.received` 表示处理条数。

## 删除草稿

- **方法/路径**: `POST /api/drafts/delete`
- **Content-Type**: `application/json`

**请求体**（`ids` 为**书籍 ID**）：

```json
{
  "ids": ["123", "456", "789"]
}
```

- `ids`（必填）：待删除草稿对应的 **Calibre 书籍 ID** 列表。

**响应**：与更新接口类似，`data.received` 表示处理条数。

**说明**：服务端会对重复删除等场景做去重/兼容，避免无意义重复操作。

**与 `cancel` 的区分**：`cancel` 侧重「撤回已提交的待审核修改」；`delete` 侧重「删除草稿记录」。若你方实现中二者等价，可只暴露其一；以实际服务文档为准。

## 常见错误

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| 未创建配置文件 | 请求失败，找不到服务地址 | 首次使用前检查并创建 `~/.config/calibre-drafts-api/config.json` |
| 配置的 `base_url` 包含 `/api` 后缀 | 路径重复（如 `/api/api/drafts`） | `base_url` 应为 `http://localhost:3000`，不包含 `/api` |
| 传 `authors: []` | 请求被拒绝 | Authors 不可清空，需要非空数组 |
| 传 `""` 清空字符串字段 | 字段被忽略 | 字符串字段（title、publisher 等）不可清空，只有 `tags: []` 可清空 |
| 误用草稿表 ID | 找不到书籍 | `id` 和 `ids` 均为 **Calibre 书籍 ID**，不是草稿记录内部 ID |
| 误用元数据源 ID | 找不到书籍 | 元数据搜索返回的 `id`（如 `douban:123456`）不是 Calibre 书籍 ID |
| 忘记 Content-Type | 请求失败 | 必须设置 `Content-Type: application/json` |
| 重复提交同一书 | 草稿被合并而非新建 | 同一书多次提交会更新现有草稿，这是预期行为 |
| 传 `null` 值 | 字段被忽略 | `null` 等同于不传，表示"不更新该字段" |
| 直接使用搜索结果 | 可能信息不准确 | 元数据搜索返回候选列表，需人工确认后再提交草稿 |

## 与书库只读技能的关系

浏览/搜索书库仍用 `calibre-library`（只读）。本技能仅描述**草稿写入、撤销与删除** HTTP 契约；调用前需确认服务已启动且基址正确。
