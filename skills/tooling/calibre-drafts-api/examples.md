# Calibre 草稿 API 请求示例

## 配置要求

**在执行任何请求前，必须先配置服务端基址**。

配置文件：`~/.config/calibre-drafts-api/config.json`

常见配置：
```json
# Docker Compose 部署（默认）
{"base_url": "http://localhost:3000"}

# 直接运行后端
{"base_url": "http://localhost:8080"}

# 生产环境
{"base_url": "https://calibre-api.example.com"}
```

以下示例使用 `http://localhost:3000` 作为基址（从配置文件读取）。所有路径均相对于 `base_url` 拼接。

---

## 场景 1：清理垃圾推广标签

```http
POST /api/drafts/update
Content-Type: application/json
```

```json
{
  "updates": [
    { "id": "274785", "data": { "tags": [] } },
    { "id": "274781", "data": { "tags": [] } },
    { "id": "274776", "data": { "tags": [] } }
  ]
}
```

## 场景 2：补全缺失元数据

```json
{
  "updates": [
    {
      "id": "123456",
      "data": {
        "publisher": "人民文学出版社",
        "isbn": "9787020123456"
      }
    }
  ]
}
```

## 场景 3：同时清空标签并补全其他字段

```json
{
  "updates": [
    {
      "id": "274782",
      "data": {
        "publisher": "上海译文出版社",
        "tags": [],
        "isbn": "9787532778956"
      }
    }
  ]
}
```

## 场景 4：搜索并补全元数据

**步骤 1**：搜索元数据

```http
GET http://localhost:3000/api/metadata/search?query=三体
```

或使用 curl：

```bash
curl "http://localhost:3000/api/metadata/search?query=三体"
```

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "douban:6518605",
      "title": "三体",
      "authors": ["刘慈欣"],
      "publisher": "重庆出版社",
      "pubdate": "2008-1",
      "isbn": "9787536692930",
      "tags": ["科幻", "小说", "刘慈欣"],
      "rating": 9.3,
      "comments": "文化大革命如火如荼进行的同时..."
    }
  ]
}
```

**步骤 2**：使用搜索结果补全草稿

```http
POST http://localhost:3000/api/drafts/update
Content-Type: application/json
```

或使用 curl：

```bash
curl -X POST http://localhost:3000/api/drafts/update \
  -H "Content-Type: application/json" \
  -d '...'
```

```json
{
  "updates": [
    {
      "id": "123456",
      "data": {
        "title": "三体",
        "authors": ["刘慈欣"],
        "publisher": "重庆出版社",
        "isbn": "9787536692930",
        "tags": ["科幻", "小说", "刘慈欣"],
        "comments": "文化大革命如火如荼进行的同时..."
      }
    }
  ]
}
```

**其他搜索示例**：

```bash
# 按作者搜索
curl "http://localhost:3000/api/metadata/search?query=刘慈欣"

# 按 ISBN 搜索
curl "http://localhost:3000/api/metadata/search?query=9787536692930"

# 组合搜索（注意 URL 编码）
curl "http://localhost:3000/api/metadata/search?query=三体%20刘慈欣"
```

## 删除草稿

`ids` 为 **Calibre 书籍 ID**（与 `POST /api/drafts/update` 里每条 `updates[].id` 含义相同），不是草稿记录 ID。

```http
POST /api/drafts/delete
Content-Type: application/json
```

```json
{
  "ids": ["123", "456", "789"]
}
```

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "received": 3
  }
}
```

## 撤销草稿

`ids` 为 **Calibre 书籍 ID**，与删除草稿接口一致。

```http
POST /api/drafts/cancel
Content-Type: application/json
```

```json
{
  "ids": ["123", "456"]
}
```

**响应示例**（与删除接口形态一致时）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "received": 2
  }
}
```
