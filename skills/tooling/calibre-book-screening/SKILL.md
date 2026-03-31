---
name: calibre-book-screening
description: >-
  Calibre 书库入库质量筛选。通过元数据检查识别不合格书籍：非中文、色情内容、
  日系漫画、作者/出版社含邮箱、低质出版源、元数据缺失等。
  Use when the user mentions 书籍筛选, 书库清理, 不合格书籍, 质量检查,
  书籍审核, or wants to screen/filter/review books in Calibre library.
---

# Calibre 书库质量筛选

依赖 `calibre-library` 技能提供的 API 访问能力，对入库书籍进行质量审核。

**目标：只保留中文正规出版书籍。**

## 适用场景

- 定期审核最近入库的书籍质量
- 批量筛选不合格书籍并输出清单
- 对单本书籍进行详细质量核查

## 筛选规则

**执行顺序**：规则4 → 规则5 → 规则3 → 规则2 → 规则1 → 规则6（高频问题优先，使用短路逻辑）

### 规则 4: 作者/出版社含垃圾信息（优先检查，高频问题）

**检查字段**：`authors`, `publisher`

**判定标准**：
- 含邮箱地址 → 删除
- 含黑名单关键词（admin, administrator, 关注, 微信, 送书, 公众号等） → 删除

**关键逻辑**：
```python
email_re = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
spam_kw = ['admin', 'administrator', '关注', '微信', '送书', '公众号', '书舍']

if email_re.match(author) or any(kw in author for kw in spam_kw):
    return 'DELETE'
```

完整实现见 [scripts/screen.py](scripts/screen.py)

### 规则 5: 低质出版源（高频问题）

**检查字段**：`publisher`

**判定标准**：
- 出版社为 `epub掌上书苑`, `Unknown`, `calibre` → 删除
- 出版社为纯数字（如 `2000`） → 删除

**关键逻辑**：
```python
bad_publishers = {'epub掌上书苑', 'Unknown', 'calibre'}
if publisher in bad_publishers or re.match(r'^\d+$', publisher):
    return 'DELETE'
```

### 规则 3: 日系漫画/轻小说

**检查字段**：`title`, `authors`, `publisher`, `title_sort`

**判定标准**：
- 出版社含：株式会社、集英社、講談社、小学館、角川、KADOKAWA 等 → 删除
- 作者为：榎宫佑、伏见司、西尾维新、川原砾、晓佳奈 等 → 删除
- 书名含日文"巻"（注意：不检测中文"卷"） → 删除
- 书名含：コミック、マンガ、ライトノベル → 删除
- 知名轻小说标题：NO GAME NO LIFE, Sword Art Online, Re:Zero 等 → 删除
- `title_sort` 为全片假名 → 删除

**注意事项**：
- 不检测中文"卷"，因学术丛书常用"第X卷"
- 不检测 `Vol.`/`Volume`，因正规出版物也使用

### 规则 2: 色情/成人内容

**检查字段**：`tags`

**判定标准**：
- 标签含：18禁、成人、色情、エロ、R18、adult、erotica、hentai、NSFW → 删除

**关键逻辑**：
```python
adult_tags = {'18禁', '成人', '色情', 'エロ', 'r18', 'adult', 'erotica', 'hentai', 'nsfw'}
if adult_tags & {t.lower() for t in book_tags}:
    return 'DELETE'
```

### 规则 1: 非中文书籍（智能判断）

**检查字段**：`languages`, `title`, `authors`

**判定标准**：
- `languages` 不含 `zho` 或 `chi` 且书名/作者也不含中文 → 删除
- `languages` 不含 `zho` 或 `chi` 但书名/作者含中文 → 合格（忽略语言标记问题）

**智能判断逻辑**：以书名/作者的实际语言为准，忽略元数据中的语言标记错误

**关键逻辑**：
```python
def contains_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))

is_chinese = any(lang in ['zho', 'chi'] for lang in langs)
if not is_chinese:
    has_chinese_content = contains_chinese(title) or any(contains_chinese(a) for a in authors)
    return 'PASS' if has_chinese_content else 'DELETE'
```

### 规则 4b: 标签含推广水印（警告级）

**检查字段**：`tags`

**判定标准**：
- 仅标签含推广关键词，但作者/出版社正常 → 更新（清理标签）

**说明**：书籍本身可能合格，仅标签被污染，建议清理标签而非删除书籍。

### 规则 6: 元数据严重缺失（警告级）

**检查字段**：`publisher`, `comments`, `tags`

**判定标准**：
- 同时满足：无出版社 AND 无简介 AND 无标签 → 更新（补充元数据）

## 操作流程

### 批量筛选

1. 准备书籍元数据 JSON 文件：

```bash
# 使用 calibre-library 技能获取书籍数据
# 将书籍元数据保存为 books.json
# 格式：{"book_id": {"title": "...", "authors": [...], ...}, ...}
```

2. 运行筛选脚本：

```bash
cd skills/tooling/calibre-book-screening
python scripts/screen.py --input books.json --output report.md
```

3. 脚本会自动：
   - 按优化顺序（4→5→3→2→1→6）执行规则检查
   - 使用短路逻辑（首个"删除"规则命中后立即返回）
   - 统计高频问题源（TOP 不合格出版社/作者/标签）
   - 生成分组报告（按来源分组，批量问题优先展示）

### 单本核查

对单本书籍进行全部 6 条规则检查，输出详细核查报告。

## 输出格式

报告包含三个部分：

### 1. 高频问题源统计（当前批次）

展示 TOP 不合格出版社、作者、标签及其出现频率。

### 2. 待删除清单

按来源分组（高频问题优先展示）：
- 低质出版源: epub掌上书苑（X本）
- 作者含邮箱: xxx@xxx.com（X本）
- 日系出版社: 株式会社 集英社（X本）
- 非中文书籍（X本）
- ...

### 3. 待更新清单

按问题类型分组：
- 语言标记错误（修正为 zho）
- 标签含推广水印（清理标签）
- 元数据缺失（补充信息）

详细输出示例见 [examples.md](examples.md)

## 判定结果

每本书只能是以下之一：

| 判定结果 | 说明 | 操作建议 |
|---------|------|---------|
| **待删除** | 触发硬性淘汰规则（规则1非中文、规则2色情、规则3日系、规则4垃圾、规则5低质出版源） | 删除书籍 |
| **待更新** | 触发警告规则（规则4b标签水印、规则6元数据缺失） | 修正元数据 |
| **合格** | 通过全部检查（包括语言标记错误但书名/作者为中文的情况） | 保留 |

## Checklist

使用前：
- [ ] `calibre-library` 技能的配置已就绪
- [ ] 确认操作为只读，不修改书库数据
- [ ] 准备好书籍元数据 JSON 文件

使用后：
- [ ] 所有书籍均经过全部 6 条规则检查
- [ ] 输出包含频率统计、待删除清单、待更新清单
- [ ] 未执行任何写入操作

## 常见陷阱

- ❌ 仅凭 `languages` 字段判断 → ✅ 以书名/作者实际语言为准（忽略语言标记错误）
- ❌ 检测中文"卷"字 → ✅ 只检测日文"巻"（学术丛书常用"第X卷"）
- ❌ 不按优化顺序检查 → ✅ 使用短路逻辑，高频问题优先（规则4→5→3→2→1→6）
- ❌ 一次请求100+ ID → ✅ 批量接口每次 ≤ 50 个
