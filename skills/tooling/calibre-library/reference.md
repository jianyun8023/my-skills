# Calibre Library API 详细参考

当需要精确查接口参数、分类 hex ID、响应字段或高级搜索语法时，再读取本文件。

所有 AJAX 端点返回 JSON。以下用 `{BASE}` 代替 `base_url`，`{LIB}` 代替 `library_id`。

## 认证与 curl 模式

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

## 1. 搜索书籍

```text
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

### 高级搜索语法

```text
author:"刘慈欣"
tags:"科幻"
publisher:"重庆出版社"
series:"冰与火之歌"
isbn:9787229042066
date:>2025-01-01                     # 2025年之后入库（timestamp，非出版日期）
date:>30daysago                      # 最近30天入库
date:>yesterday                      # 昨天及之后入库
author:"刘慈欣" AND tags:"科幻"
author:"刘慈欣" AND date:>7daysago   # 组合：某作者最近7天入库
```

## 2. 书籍详情

单本：

```text
GET {BASE}/ajax/book/{book_id}/{LIB}
```

批量（逗号分隔 ID）：

```text
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

## 3. 分类列表

获取书库支持的所有分类：

```text
GET {BASE}/ajax/categories/{LIB}
```

返回数组，每项包含 `name`、`url`、`is_category`。

## 4. 分类浏览

浏览某一分类下的条目：

```text
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

## 5. 分类内书籍

获取某个作者/出版社/标签/丛书下的所有书籍 ID：

```text
GET {BASE}{item_url}?num={count}&offset={offset}
```

`item_url` 来自分类浏览响应中 `items[].url`，或书籍详情的 `category_urls` 字段。

响应与搜索接口相同，返回 `book_ids` 数组。

## 6. 最新入库

通过搜索接口的 `date:` 过滤器按添加时间查询，`date:` 对应书籍的 `timestamp`（入库时间），而非 `pubdate`（出版日期）。

```text
GET {BASE}/ajax/search?query=date:>{date_expr}&num={count}&sort=date&sort_order=desc&library_id={LIB}
```

`date_expr` 支持两种格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| 绝对日期 | `date:>2025-03-01` | 指定日期之后入库的书籍 |
| 相对日期 | `date:>30daysago` | 最近 30 天入库 |
| 相对日期 | `date:>7daysago` | 最近 7 天入库 |
| 相对日期 | `date:>yesterday` | 昨天及之后入库 |

配合 `sort=date&sort_order=desc` 按入库时间倒序排列。

响应示例：

```json
{
  "total_num": 112,
  "sort_order": "desc",
  "sort": "date",
  "book_ids": [274770, 274769, 274768],
  "query": "date:>30daysago"
}
```

## 7. 下载与封面

下载书籍文件：

```text
GET {BASE}/get/{format}/{book_id}/{LIB}
```

`format` 小写：epub, mobi, pdf, azw3, txt 等。返回二进制文件。

建议保存到 `~/Downloads/`，并通过 `format_metadata.{format}.size` 校验文件大小。

封面与缩略图：

```text
GET {BASE}/get/cover/{book_id}/{LIB}
GET {BASE}/get/thumb/{book_id}/{LIB}
```
