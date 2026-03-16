---
name: calibre-library
description: >-
  只读访问个人 Calibre 书库，通过 AJAX API 搜索、浏览、下载书籍。支持按
  标题/作者/标签/ISBN 搜索，按作者/出版社/标签/丛书分类浏览，获取书籍详情与
  元数据，下载 epub/mobi/pdf 等格式。Use when the user mentions Calibre,
  书库, 找书, 下载书籍, 搜书, or wants to browse/search/download books.
  FORBIDDEN: Any write/modify/delete operations.
---

# Calibre 书库（只读）

通过 Calibre Content Server AJAX API 搜索、浏览和下载书籍。

**严禁任何写入、修改、删除操作。仅允许搜索、浏览和下载。**

## 适用场景

- 按关键词搜索书籍（标题、作者、标签、ISBN）
- 按作者、出版社、标签、丛书分类浏览
- 获取书籍详情和元数据
- 下载书籍文件（epub、mobi、pdf 等）
- 查看最新入库书籍

## 不适用

- 添加、删除、修改书籍或元数据
- 管理书库设置或用户权限
- 上传文件到书库

## 配置

配置文件路径：`~/.config/calibre-library/config.json`

**首次使用前**，检查配置文件是否存在：

```bash
cat ~/.config/calibre-library/config.json
```

若不存在，提示用户创建：

```bash
mkdir -p ~/.config/calibre-library
cat > ~/.config/calibre-library/config.json << 'EOF'
{
  "base_url": "https://lib.pve.icu",
  "library_id": "library",
  "username": "",
  "password": ""
}
EOF
```

| 字段 | 说明 |
|------|------|
| `base_url` | Calibre Content Server 地址，不带尾部斜杠 |
| `library_id` | 书库 ID，通常为 `library` |
| `username` | Basic Auth 用户名，无认证留空 |
| `password` | Basic Auth 密码，无认证留空 |

### 认证模式

读取配置后根据 `username`/`password` 决定认证方式：

- **无认证**：两个字段均为空 → 直接请求
- **Basic Auth**：任一字段非空 → curl 附加 `-u username:password`

构建 curl 命令的模式：

```bash
# 读取配置
CONFIG=$(cat ~/.config/calibre-library/config.json)
BASE_URL=$(echo "$CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin)['base_url'])")
LIB_ID=$(echo "$CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin)['library_id'])")
USERNAME=$(echo "$CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('username',''))")
PASSWORD=$(echo "$CONFIG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('password',''))")

# 构建 auth 参数
AUTH=""
if [ -n "$USERNAME" ]; then AUTH="-u $USERNAME:$PASSWORD"; fi

# 示例请求
curl -sL $AUTH "$BASE_URL/ajax/search?query=三体&num=10&library_id=$LIB_ID"
```

实际使用中直接将读取到的值替换进 curl 命令即可，无需每次都执行完整脚本。

**禁止将密码写入 SKILL.md 或提交到版本控制。**

## API 参考

所有 AJAX 端点返回 JSON。以下用 `{BASE}` 代替 `base_url`，`{LIB}` 代替 `library_id`。

### 1. 搜索书籍

```
GET {BASE}/ajax/search?query={keyword}&num={count}&library_id={LIB}
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | 是 | - | 搜索关键词 |
| `num` | 否 | 50 | 返回数量 |
| `offset` | 否 | 0 | 分页偏移量 |
| `sort` | 否 | title | 排序字段：title, author, date, rating, size, tags, series |
| `sort_order` | 否 | asc | asc 或 desc |

响应示例：

```json
{
  "total_num": 59,
  "book_ids": [165522, 38336],
  "num": 2,
  "offset": 0
}
```

仅返回 `book_ids`，需用详情接口获取完整信息。翻页：设置 `offset` = 上一页 `offset` + `num`。

#### 高级搜索语法

```
author:"刘慈欣"
tags:"科幻"
publisher:"重庆出版社"
series:"冰与火之歌"
isbn:9787229042066
author:"刘慈欣" AND tags:"科幻"
```

### 2. 书籍详情

单本：

```
GET {BASE}/ajax/book/{book_id}/{LIB}
```

批量（逗号分隔 ID）：

```
GET {BASE}/ajax/books?ids={id1},{id2}&library_id={LIB}
```

关键响应字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | string | 书名 |
| `authors` | string[] | 作者列表 |
| `publisher` | string | 出版社 |
| `pubdate` | string | 出版日期 (ISO 8601) |
| `tags` | string[] | 标签列表 |
| `series` | string | 丛书名 |
| `series_index` | number | 丛书序号 |
| `rating` | number | 评分 (0-5) |
| `comments` | string | 书籍简介 (HTML) |
| `formats` | string[] | 可用格式，如 `["epub", "mobi"]` |
| `main_format` | object | 主格式下载路径，如 `{"epub": "/get/epub/{id}/{LIB}"}` |
| `identifiers` | object | 标识符，如 `{"isbn": "978...", "douban": "123"}` |
| `format_metadata` | object | 每种格式的文件大小和修改时间 |
| `category_urls` | object | 关联分类 URL（作者、标签、出版社、丛书） |

### 3. 分类列表

获取书库支持的所有分类：

```
GET {BASE}/ajax/categories/{LIB}
```

返回数组，每项包含 `name`、`url`、`is_category`。

### 4. 分类浏览

浏览某一分类下的条目：

```
GET {BASE}/ajax/category/{category_hex}/{LIB}?num={count}&offset={offset}
```

常用分类 hex ID：

| 分类 | Hex ID | 条目数 |
|------|--------|--------|
| 作者 | `617574686f7273` | ~70,000+ |
| 出版社 | `7075626c6973686572` | ~3,000+ |
| 标签 | `74616773` | ~13,000+ |
| 丛书 | `736572696573` | ~300+ |
| 评分 | `726174696e67` | - |
| 语言 | `6c616e677561676573` | - |

响应示例（作者分类）：

```json
{
  "category_name": "作者",
  "total_num": 70780,
  "offset": 0,
  "num": 3,
  "items": [
    {
      "name": "刘慈欣",
      "count": 110,
      "average_rating": 0.0,
      "url": "/ajax/books_in/617574686f7273/313336/library"
    }
  ]
}
```

每个 `item` 的 `url` 可直接用于获取该条目下的书籍。

### 5. 分类内书籍

获取某个作者/出版社/标签/丛书下的所有书籍 ID：

```
GET {BASE}{item_url}?num={count}&offset={offset}
```

`item_url` 来自分类浏览响应中 `items[].url`，或书籍详情的 `category_urls` 字段。

响应与搜索接口相同，返回 `book_ids` 数组。

### 6. 最新书籍

```
GET {BASE}/ajax/books_in/6e6577657374/30/{LIB}?num={count}
```

按入库时间倒序返回 `book_ids`。

### 7. 下载与封面

下载书籍文件：

```
GET {BASE}/get/{format}/{book_id}/{LIB}
```

`format` 小写：epub, mobi, pdf, azw3, txt 等。返回二进制文件。

建议保存到 `~/Downloads/`，并通过 `format_metadata.{format}.size` 校验文件大小。

封面与缩略图：

```
GET {BASE}/get/cover/{book_id}/{LIB}
GET {BASE}/get/thumb/{book_id}/{LIB}
```

## 操作步骤

### 搜索并查看

1. 读取配置获取 `BASE_URL` 和 `LIB_ID`
2. 搜索：`curl -sL $AUTH "$BASE_URL/ajax/search?query=关键词&num=10&library_id=$LIB_ID"`
3. 提取 `book_ids`
4. 批量获取详情：`curl -sL $AUTH "$BASE_URL/ajax/books?ids=ID1,ID2&library_id=$LIB_ID"`
5. 向用户展示结果

### 按作者/出版社/标签浏览

1. 搜索 `author:"刘慈欣"` 找到书籍
2. 从书籍详情的 `category_urls.authors` 获取作者 URL
3. 请求该 URL 获取该作者全部 `book_ids`
4. 批量获取详情

或直接浏览分类：

1. 请求分类浏览接口列出作者/出版社列表
2. 从 `items[].url` 获取目标条目的书籍列表
3. 批量获取详情

### 下载书籍

1. 获取书籍详情，确认可用 `formats` 和 `main_format` 路径
2. 下载：`curl -sL $AUTH "$BASE_URL/get/epub/{book_id}/$LIB_ID" -o ~/Downloads/书名.epub`
3. 校验文件大小是否匹配 `format_metadata.{format}.size`

### 查看最新入库

1. 请求最新书籍接口获取 `book_ids`
2. 批量获取详情并展示

## 输出格式

列表展示使用 bullet list：

```
- **三体三部曲** — 刘慈欣 (ID: 267085)
  格式: epub | 标签: 科幻, 经典 | ISBN: 9787229042066
```

单本详情包含：书名、作者、出版社、出版日期、丛书、标签、可用格式、ISBN、评分，以及从 `comments` 截取的简介（过长时截断）。

## Checklist

使用前：
- [ ] 配置文件 `~/.config/calibre-library/config.json` 存在且内容正确
- [ ] `base_url` 可访问（curl 返回 HTTP 200）
- [ ] 确认操作为只读（搜索/浏览/下载），无任何写入意图

使用后：
- [ ] 下载的文件大小与 `format_metadata` 一致
- [ ] 未执行任何写入、修改、删除操作

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 在 SKILL.md 中硬编码 base_url 或密码 | 从 `~/.config/calibre-library/config.json` 读取 |
| 直接用 `/mobile` HTML 端点解析 | 用 `/ajax/` JSON 端点，结构化可靠 |
| 搜索后直接拼下载 URL | 先获取详情确认 `formats` 和 `main_format` 再下载 |
| 一次请求大量书籍详情 | 批量接口 `ids=` 每次不超过 50 个，分批请求 |
| 尝试通过 API 修改书籍元数据 | 严禁写操作，此技能仅支持只读访问 |
| 配置文件不存在时直接报错 | 提示用户创建配置文件并填写参数 |
