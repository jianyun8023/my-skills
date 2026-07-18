---
name: calibre-library
description: >-
  Use when browsing, searching, or downloading books from a Calibre library
  through its read-only AJAX API. Covers search, category browsing, book
  details, downloads, and the explicit no-write boundary.
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

实际使用时，先读配置文件得到 `BASE_URL`、`LIB_ID`、`USERNAME`、`PASSWORD`，再按是否启用 Basic Auth 拼接 curl 请求。

**禁止将密码写入 SKILL.md 或提交到版本控制。**

## API 参考

详细接口、查询参数、高级搜索语法和响应字段见 [reference.md](reference.md)。主技能只保留高频工作流：

- 搜索书籍：`/ajax/search`
- 获取单本 / 批量详情：`/ajax/book/{id}/{library}`、`/ajax/books?ids=...`
- 分类浏览：`/ajax/categories/{library}`、`/ajax/category/{hex}/{library}`
- 最新入库：基于 `date:` 搜索过滤
- 下载与封面：`/get/{format}/{id}/{library}`、`/get/cover/...`

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

1. 搜索：`curl -sL $AUTH "$BASE_URL/ajax/search?query=date:>7daysago&num=20&sort=date&sort_order=desc&library_id=$LIB_ID"`
2. 提取 `book_ids`，批量获取详情并展示
3. 根据用户需求调整时间范围（`7daysago`、`30daysago`、具体日期等）

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
