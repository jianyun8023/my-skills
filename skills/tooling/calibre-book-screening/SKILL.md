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

### 规则 1：非中文书籍（硬性淘汰）

检查字段：`languages`

- **不合格**：`languages` 不包含 `zho` 或 `chi`
- 即使书名是中文，只要语言标记非中文即判定不合格（说明元数据有误）

```python
langs = info.get('languages', [])
is_chinese = any(lang in ['zho', 'chi'] for lang in langs)
if not is_chinese:
    fail("非中文", langs)
```

### 规则 2：色情/成人内容（硬性淘汰）

检查字段：`title`, `tags`, `comments`, `publisher`

- **标签黑名单**：`18禁`, `成人`, `色情`, `エロ`, `R18`, `R-18`, `adult`, `erotica`, `hentai`, `NSFW`
- **出版社黑名单**：已知成人内容出版源
- **书名/简介关键词**：明显色情暗示性词汇

```python
adult_tags = {'18禁', '成人', '色情', 'エロ', 'R18', 'R-18', 'adult', 'erotica', 'hentai', 'NSFW'}
book_tags = set(t.lower() for t in info.get('tags', []))
if adult_tags & book_tags:
    fail("色情/成人内容", matched_tags)
```

### 规则 3：日系漫画/轻小说（硬性淘汰）

检查字段：`title`, `authors`, `publisher`

- **出版社黑名单**：`株式会社`, `集英社`, `講談社`, `小学館`, `角川`, `KADOKAWA`, `スクウェア・エニックス`, `白泉社`
- **书名特征**：全片假名/平假名标题、含 `巻`, `コミック`, `マンガ`, `ライトノベル`
- **排序名特征**：`title_sort` 为全片假名

```python
jp_publishers = ['株式会社', '集英社', '講談社', '小学館', '角川', 'KADOKAWA']
publisher = info.get('publisher', '') or ''
if any(kw in publisher for kw in jp_publishers):
    fail("日系出版社", publisher)

import re
title = info.get('title', '')
title_sort = info.get('title_sort', '')
katakana_re = re.compile(r'^[\u30A0-\u30FF\u3040-\u309Fー・\s\d]+$')
if katakana_re.match(title_sort):
    fail("日系漫画(片假名标题)", title)
```

### 规则 4：作者/出版社含邮箱或垃圾信息（硬性淘汰）

检查字段：`authors`, `publisher`

- 作者/出版社含邮箱 → 硬性淘汰
- 作者/出版社含垃圾关键词 → 硬性淘汰

**作者/出版社黑名单关键词**：`Administer`, `Administrator`, `admin`

**垃圾信息关键词**（匹配 `authors`, `publisher`）：

`关注`, `微信`, `送书`, `公众号`, `书舍`, `书群`, `免费`, `加群`, `扫码`, `QQ群`

```python
import re
email_re = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
spam_author_kw = ['administer', 'administrator', 'admin']
spam_info_kw = ['关注', '微信', '送书', '公众号', '书舍', '书群', '免费', '加群', '扫码', 'QQ群']

authors = info.get('authors', [])
publisher = info.get('publisher', '') or ''
author_pub_text = [str(a) for a in authors] + [publisher]

for author in authors:
    if email_re.search(str(author)):
        fail("作者含邮箱", author)
if email_re.search(publisher):
    fail("出版社含邮箱", publisher)

for text in author_pub_text:
    if any(kw in text.lower() for kw in spam_author_kw):
        fail("垃圾作者名", text)
    if any(kw in text for kw in spam_info_kw):
        fail("垃圾推广信息", text)
```

### 规则 4b：标签含推广水印（警告 — 建议清理标签）

检查字段：`tags`

仅标签含推广关键词，但作者/出版社正常 → 书籍本身可能合格，标签被污染。

**判定**：标记为 `⚠️ 警告`，建议清理标签而非删除书籍。

```python
tags = info.get('tags', [])
for tag in tags:
    if any(kw in tag for kw in spam_info_kw):
        warn("标签含推广水印", tag)
```

### 规则 5：低质出版源（硬性淘汰）

检查字段：`publisher`

**出版社黑名单**：

| 出版社 | 原因 |
|--------|------|
| `epub掌上书苑` | 非正规出版，通常为网络抓取 |
| `Unknown` | 元数据缺失 |
| `calibre` | Calibre 默认值，未修正 |

```python
bad_publishers = {'epub掌上书苑', 'Unknown', 'calibre'}
publisher = info.get('publisher', '') or ''
if publisher in bad_publishers:
    fail("低质出版源", publisher)
```

### 规则 6：元数据严重缺失（警告）

同时满足以下全部条件时判定不合格：

- `publisher` 为空或 null
- `comments` 为空或 null
- `tags` 为空列表

```python
no_publisher = not info.get('publisher')
no_comments = not info.get('comments')
no_tags = not info.get('tags')
if no_publisher and no_comments and no_tags:
    fail("元数据缺失(无出版社/简介/标签)")
```

## 操作流程

### 批量筛选（推荐）

1. 使用 `calibre-library` 技能的搜索接口拉取目标书籍 ID

```bash
curl -sL "$BASE_URL/ajax/search?query=date:>14daysago&num=100&sort=date&sort_order=desc&library_id=$LIB_ID"
```

2. 批量获取详情（每批不超过 50 个 ID）

```bash
curl -sL "$BASE_URL/ajax/books?ids=ID1,ID2,...&library_id=$LIB_ID"
```

3. 使用 Python 脚本批量筛选，将结果写入临时文件

```python
import json, re

email_re = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
katakana_re = re.compile(r'^[\u30A0-\u30FF\u3040-\u309Fー・\s\d]+$')

bad_publishers = {'epub掌上书苑', 'Unknown', 'calibre'}
jp_publishers = ['株式会社', '集英社', '講談社', '小学館', '角川', 'KADOKAWA',
                 'スクウェア・エニックス', '白泉社']
adult_tags = {'18禁', '成人', '色情', 'エロ', 'r18', 'r-18', 'adult',
              'erotica', 'hentai', 'nsfw'}
spam_author_kw = ['administer', 'administrator', 'admin']
spam_info_kw = ['关注', '微信', '送书', '公众号', '书舍', '书群', '免费', '加群', '扫码', 'QQ群']

def check_book(book_id, info):
    """返回 (reasons, warnings)，reasons 为硬性淘汰，warnings 为警告"""
    reasons = []
    warnings = []
    langs = info.get('languages', [])
    publisher = info.get('publisher', '') or ''
    authors = info.get('authors', [])
    title = info.get('title', '')
    title_sort = info.get('title_sort', '')
    tags = info.get('tags', [])
    comments = info.get('comments', '') or ''
    author_pub_text = [str(a) for a in authors] + [publisher]

    # 规则 1: 非中文
    if not any(l in ['zho', 'chi'] for l in langs):
        reasons.append(f'非中文({langs})')

    # 规则 2: 色情/成人
    book_tags_lower = {t.lower() for t in tags}
    matched = adult_tags & book_tags_lower
    if matched:
        reasons.append(f'色情/成人内容({matched})')

    # 规则 3: 日系漫画
    if any(kw in publisher for kw in jp_publishers):
        reasons.append(f'日系出版社({publisher})')
    if katakana_re.match(title_sort):
        reasons.append(f'日系漫画(片假名标题)')

    # 规则 4: 作者/出版社邮箱 + 垃圾信息 (硬性淘汰)
    for a in authors:
        if email_re.search(str(a)):
            reasons.append(f'作者含邮箱({a})')
    if email_re.search(publisher):
        reasons.append(f'出版社含邮箱({publisher})')
    for text in author_pub_text:
        if any(kw in text.lower() for kw in spam_author_kw):
            reasons.append(f'垃圾作者名({text})')
            break
    for text in author_pub_text:
        if any(kw in text for kw in spam_info_kw):
            reasons.append(f'垃圾推广信息({text})')
            break

    # 规则 4b: 仅标签含推广水印 (警告)
    for tag in tags:
        if any(kw in tag for kw in spam_info_kw):
            warnings.append(f'标签含推广水印({tag})')

    # 规则 5: 低质出版源
    if publisher in bad_publishers:
        reasons.append(f'低质出版源({publisher})')

    # 规则 6: 元数据缺失
    if not publisher and not comments and not tags:
        reasons.append('元数据缺失(无出版社/简介/标签)')

    return reasons, warnings
```

4. 输出筛选结果

### 单本核查

对用户指定的 book_id 获取详情后，逐条执行全部 6 条规则，输出详细核查报告。

## 输出格式

### 批量筛选结果

按不合格原因分组，每组内按 ID 降序（最新在前）：

```
### 非中文书籍
- **Kairos** (ID: 274750) — Jenny Erpenbeck | 语言: deu, eng
- **Technofeudalism** (ID: 274724) — Yanis Varoufakis | 语言: eng

### 日系出版社
- **タメ口後輩ギャル...** (ID: 274767) — 緒二葉 | 出版社: 株式会社 集英社

### 低质出版源 (epub掌上书苑)
- **推背图（金圣叹版）** (ID: 274737) — 李淳风 袁天罡

### 作者/出版社含邮箱或垃圾信息
- **一个人的朝圣** (ID: 274764) — asd44858@163.com
- **某书名** (ID: XXXXX) — Administer

### 元数据缺失
- **欧·亨利短篇小说精选** (ID: 274735) — 欧·亨利 | 无出版社/简介/标签

### ⚠️ 标签含推广水印（警告，建议清理标签）
- **巴比松大饭店** (ID: 274752) — 保利娜·布伦 | 标签: 公众号：绿悠书舍
```

末尾附汇总：

```
共检查 N 本
❌ 不合格 M 本 (占比 X%)
  - 非中文: A 本
  - 色情/成人: B 本
  - 日系漫画: C 本
  - 邮箱/垃圾信息: D 本
  - 低质出版源: E 本
  - 元数据缺失: F 本
⚠️ 警告 W 本（标签推广水印，建议清理标签）
```

### 单本核查报告

```
## 书籍核查：《书名》(ID: XXXXX)

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 中文书籍 | ✅/❌ | languages: [...] |
| 色情/成人 | ✅/❌ | tags: [...] |
| 非日系漫画 | ✅/❌ | publisher: ... |
| 作者/出版社无邮箱 | ✅/❌ | ... |
| 作者/出版社无垃圾信息 | ✅/❌ | 作者/出版社是否含推广关键词 |
| 标签无推广水印 | ✅/⚠️ | tags 是否含推广关键词（警告级） |
| 出版源合规 | ✅/❌ | publisher: ... |
| 元数据完整 | ✅/❌ | publisher/comments/tags |

**结论**: 合格 / 不合格（原因: ...）/ 合格但有警告（标签需清理）
```

## Checklist

使用前：
- [ ] `calibre-library` 技能的配置已就绪
- [ ] 确认操作为只读，不修改书库数据

使用后：
- [ ] 所有书籍均经过全部 6 条规则检查
- [ ] 输出格式按分组呈现，附汇总统计
- [ ] 未执行任何写入操作

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 仅凭书名语种判断 | 以 `languages` 字段为准，书名中文但标记 eng 仍判不合格 |
| 忽略 `title_sort` 字段 | 用 `title_sort` 检测片假名标题更准确 |
| 只检查部分规则 | 每本书必须经过全部 6 条规则 |
| 一次请求过多详情 | 批量接口每次不超过 50 个 ID |
| 未统计汇总 | 始终在末尾附上汇总数据 |
