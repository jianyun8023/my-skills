#!/usr/bin/env python3
"""
Calibre 书籍质量筛选脚本

按优化顺序执行 6 条规则：规则4 → 规则5 → 规则3 → 规则2 → 规则1 → 规则6
使用短路逻辑，首个"删除"规则命中后立即返回，提升筛选效率。
"""

import re
import json
import argparse
import os
from collections import Counter
from typing import Dict, List, Tuple, Optional

# ============================================================================
# 规则配置
# ============================================================================

# 邮箱正则
EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

# 片假名正则
KATAKANA_RE = re.compile(r'^[\u30A0-\u30FF\u3040-\u309Fー・\s\d]+$')

# 中文字符正则
CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')

# 规则 4: 垃圾信息黑名单
SPAM_AUTHOR_KW = ['administer', 'administrator', 'admin', '未知']
SPAM_INFO_KW = ['关注', '微信', '送书', '公众号', '书舍', '书群', '免费', '加群', '扫码', 'QQ群']

# 规则 5: 低质出版源黑名单
BAD_PUBLISHERS = {'epub掌上书苑', 'Unknown', 'calibre'}

# 规则 3: 日系特征黑名单
JP_PUBLISHERS = {'株式会社', '集英社', '講談社', '小学館', '角川', 'KADOKAWA', 
                 'スクウェア・エニックス', '白泉社', 'MediaFactory'}
JP_AUTHORS = {'榎宫佑', '伏见司', '西尾维新', '川原砾', '晓佳奈'}
LN_TITLES = {'no game no life', 'sword art online', 're:zero', 'overlord'}
JP_KEYWORDS = {'コミック', 'マンガ', 'ライトノベル'}

# 规则 2: 色情/成人内容黑名单
ADULT_TAGS = {'18禁', '成人', '色情', 'エロ', 'r18', 'r-18', 'adult', 'erotica', 'hentai', 'nsfw'}


# ============================================================================
# 工具函数
# ============================================================================

def contains_chinese(text: str) -> bool:
    """检测文本是否包含中文字符"""
    return bool(CHINESE_RE.search(str(text)))


# ============================================================================
# 规则检查函数（按优化顺序：4 → 5 → 3 → 2 → 1 → 6）
# ============================================================================

def check_rule4_spam_info(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则4: 作者/出版社含邮箱或垃圾信息（优先检查，高频问题）
    
    Returns:
        None: 通过检查
        Tuple: ('DELETE', 原因类别, 详细信息)
    """
    authors = info.get('authors', [])
    publisher = info.get('publisher', '') or ''
    
    # 检查作者邮箱
    for author in authors:
        if EMAIL_RE.search(str(author)):
            return ('DELETE', '作者含邮箱', f'{author}')
    
    # 检查出版社邮箱
    if EMAIL_RE.search(publisher):
        return ('DELETE', '出版社含邮箱', f'{publisher}')
    
    # 检查垃圾关键词
    author_pub_text = [str(a) for a in authors] + [publisher]
    for text in author_pub_text:
        text_lower = text.lower()
        # 检查黑名单作者名
        for kw in SPAM_AUTHOR_KW:
            if kw in text_lower:
                return ('DELETE', '垃圾作者/出版社名', f'{text}')
        # 检查推广信息
        for kw in SPAM_INFO_KW:
            if kw in text:
                return ('DELETE', '垃圾推广信息', f'{text}')
    
    return None


def check_rule4b_tag_spam(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则4b: 仅标签含推广水印（警告级，不删除）
    
    Returns:
        None: 通过检查
        Tuple: ('UPDATE', 原因类别, 详细信息)
    """
    tags = info.get('tags', [])
    spam_tags = []
    
    for tag in tags:
        for kw in SPAM_INFO_KW:
            if kw in tag:
                spam_tags.append(tag)
                break
    
    if spam_tags:
        return ('UPDATE', '标签含推广水印', ', '.join(spam_tags))
    
    return None


def check_rule5_bad_publisher(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则5: 低质出版源（高频问题）
    
    Returns:
        None: 通过检查
        Tuple: ('DELETE', 原因类别, 详细信息)
    """
    publisher = info.get('publisher', '') or ''
    
    # 检查黑名单出版社
    if publisher in BAD_PUBLISHERS:
        return ('DELETE', '低质出版源', f'{publisher}')
    
    # 检查纯数字出版社
    if publisher.strip() and re.match(r'^\d+$', publisher.strip()):
        return ('DELETE', '低质出版源(纯数字)', f'{publisher}')
    
    return None


def check_rule3_japanese(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则3: 日系漫画/轻小说
    
    Returns:
        None: 通过检查
        Tuple: ('DELETE', 原因类别, 详细信息)
    """
    publisher = info.get('publisher', '') or ''
    authors = set(info.get('authors', []))
    title = info.get('title', '')
    title_lower = title.lower()
    title_sort = info.get('title_sort', '')
    
    # 检查日系出版社
    for kw in JP_PUBLISHERS:
        if kw in publisher:
            return ('DELETE', '日系出版社', f'{publisher}')
    
    # 检查日系作者
    matched_authors = authors & JP_AUTHORS
    if matched_authors:
        return ('DELETE', '日系作者', ', '.join(matched_authors))
    
    # 检查知名轻小说标题
    for ln_title in LN_TITLES:
        if ln_title in title_lower:
            return ('DELETE', '日系轻小说标题', f'{title}')
    
    # 检查日系关键词
    for kw in JP_KEYWORDS:
        if kw in title:
            return ('DELETE', '日系书名关键词', f'{title}')
    
    # 检查日文"巻"
    if '巻' in title:
        return ('DELETE', '日系书名特征(含巻)', f'{title}')
    
    # 检查片假名标题
    if KATAKANA_RE.match(title_sort):
        return ('DELETE', '片假名标题', f'{title}')
    
    return None


def check_rule2_adult(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则2: 色情/成人内容
    
    Returns:
        None: 通过检查
        Tuple: ('DELETE', 原因类别, 详细信息)
    """
    tags = info.get('tags', [])
    book_tags = {t.lower() for t in tags}
    
    matched = ADULT_TAGS & book_tags
    if matched:
        return ('DELETE', '色情/成人内容', ', '.join(matched))
    
    return None


def check_rule1_language(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则1: 非中文书籍（智能判断）
    
    Returns:
        None: 通过检查
        Tuple: ('DELETE', 原因类别, 详细信息)
    """
    langs = info.get('languages', [])
    
    # 检查语言标记
    is_chinese = any(lang in ['zho', 'chi'] for lang in langs)
    
    if not is_chinese:
        # 智能判断：检查书名/作者是否含中文
        title = info.get('title', '')
        authors = info.get('authors', [])
        
        has_chinese_title = contains_chinese(title)
        has_chinese_author = any(contains_chinese(a) for a in authors)
        
        if has_chinese_title or has_chinese_author:
            # 语言标记错误，但内容是中文 → 忽略标记问题，视为合格
            return None
        else:
            # 确实是非中文书籍 → 删除
            lang_str = ', '.join(langs) if langs else '无语言标记'
            return ('DELETE', '非中文书籍', lang_str)
    
    return None


def check_rule6_metadata(info: Dict) -> Optional[Tuple[str, str, str]]:
    """
    规则6: 元数据严重缺失
    
    Returns:
        None: 通过检查
        Tuple: ('UPDATE', 原因类别, 详细信息)
    """
    no_publisher = not info.get('publisher')
    no_comments = not info.get('comments')
    no_tags = not info.get('tags')
    
    if no_publisher and no_comments and no_tags:
        return ('UPDATE', '元数据缺失', '无出版社/简介/标签')
    
    return None


def check_book(book_id: str, info: Dict) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """
    按优化顺序检查书籍，使用短路逻辑
    
    检查顺序：规则4 → 规则5 → 规则3 → 规则2 → 规则1 → 规则4b → 规则6
    
    Returns:
        Tuple: (状态, 原因类别, 详细信息, 分组键)
        - 状态: 'PASS', 'DELETE', 'UPDATE'
        - 原因类别: 如 '作者含邮箱', '低质出版源'
        - 详细信息: 具体的邮箱/出版社等
        - 分组键: 用于按来源分组展示
    """
    # 规则4: 垃圾信息（高频，优先检查）
    result = check_rule4_spam_info(info)
    if result:
        action, category, detail = result
        # 分组键：提取关键信息作为分组依据
        if '邮箱' in category:
            group_key = f"作者含邮箱: {detail}"
        else:
            group_key = f"{category}: {detail[:20]}"
        return (action, category, detail, group_key)
    
    # 规则5: 低质出版源（高频）
    result = check_rule5_bad_publisher(info)
    if result:
        action, category, detail = result
        group_key = f"低质出版源: {detail}"
        return (action, category, detail, group_key)
    
    # 规则3: 日系
    result = check_rule3_japanese(info)
    if result:
        action, category, detail = result
        if '出版社' in category:
            group_key = f"日系出版社: {detail}"
        elif '作者' in category:
            group_key = f"日系作者: {detail}"
        else:
            group_key = f"{category}"
        return (action, category, detail, group_key)
    
    # 规则2: 色情
    result = check_rule2_adult(info)
    if result:
        action, category, detail = result
        group_key = "色情/成人内容"
        return (action, category, detail, group_key)
    
    # 规则1: 语言
    result = check_rule1_language(info)
    if result:
        action, category, detail = result
        group_key = "非中文书籍"
        return (action, category, detail, group_key)
    
    # 规则4b: 标签推广（警告级）
    result = check_rule4b_tag_spam(info)
    if result:
        action, category, detail = result
        group_key = "标签含推广水印"
        return (action, category, detail, group_key)
    
    # 规则6: 元数据缺失（最后检查）
    result = check_rule6_metadata(info)
    if result:
        action, category, detail = result
        group_key = "元数据缺失"
        return (action, category, detail, group_key)
    
    # 全部通过
    return ('PASS', None, None, None)


# ============================================================================
# 频率统计
# ============================================================================

def calculate_frequency(results: List[Dict]) -> Dict:
    """
    统计当前批次的高频问题源
    
    Args:
        results: 筛选结果列表
        
    Returns:
        包含 publishers, authors, tags 的频率统计
    """
    publishers = Counter()
    authors = Counter()
    tags = Counter()
    
    for item in results:
        if item['action'] == 'DELETE':
            info = item['info']
            pub = info.get('publisher', '') or ''
            if pub:
                publishers[pub] += 1
            
            for author in info.get('authors', []):
                authors[author] += 1
            
            for tag in info.get('tags', []):
                # 仅统计问题标签
                if any(kw in tag for kw in SPAM_INFO_KW) or any(kw in tag.lower() for kw in ADULT_TAGS):
                    tags[tag] += 1
    
    return {
        'publishers': publishers.most_common(10),
        'authors': authors.most_common(10),
        'tags': tags.most_common(10)
    }


# ============================================================================
# 报告生成
# ============================================================================

def format_report(results: List[Dict], frequency: Dict) -> str:
    """
    生成分组筛选报告
    
    Args:
        results: 筛选结果列表
        frequency: 频率统计数据
        
    Returns:
        Markdown 格式的报告
    """
    lines = []
    
    # 标题
    lines.append("# Calibre 书籍筛选报告\n")
    
    # 频率统计
    total_books = len(results)
    delete_books = [r for r in results if r['action'] == 'DELETE']
    update_books = [r for r in results if r['action'] == 'UPDATE']
    pass_books = [r for r in results if r['action'] == 'PASS']
    
    lines.append("## 高频问题源统计（当前批次）\n")
    
    # TOP 不合格出版社
    if frequency['publishers']:
        lines.append("### TOP 不合格出版社\n")
        lines.append("| 出版社 | 书籍数 | 占比 |")
        lines.append("|--------|--------|------|")
        total_del = len(delete_books)
        for pub, count in frequency['publishers']:
            pct = f"{count * 100 / total_del:.1f}%" if total_del > 0 else "0%"
            lines.append(f"| {pub} | {count} | {pct} |")
        lines.append("")
    
    # TOP 不合格作者
    if frequency['authors']:
        lines.append("### TOP 不合格作者\n")
        lines.append("| 作者 | 书籍数 | 占比 |")
        lines.append("|------|--------|------|")
        total_del = len(delete_books)
        for author, count in frequency['authors']:
            pct = f"{count * 100 / total_del:.1f}%" if total_del > 0 else "0%"
            lines.append(f"| {author} | {count} | {pct} |")
        lines.append("")
    
    # TOP 问题标签
    if frequency['tags']:
        lines.append("### TOP 问题标签\n")
        lines.append("| 标签 | 出现次数 |")
        lines.append("|------|----------|")
        for tag, count in frequency['tags']:
            lines.append(f"| {tag} | {count} |")
        lines.append("")
    
    # 按分组展示待删除清单
    if delete_books:
        lines.append(f"## 待删除清单（{len(delete_books)}本）\n")
        
        # 按 group_key 分组
        grouped = {}
        for item in delete_books:
            key = item['group_key']
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)
        
        # 按组内书籍数量排序（高频问题优先展示）
        sorted_groups = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
        
        for group_key, books in sorted_groups:
            lines.append(f"### {group_key}（{len(books)}本）\n")
            # 按 ID 降序排列（最新在前）
            books_sorted = sorted(books, key=lambda x: int(x['book_id']), reverse=True)
            for book in books_sorted:
                info = book['info']
                title = info.get('title', '未知')
                authors = ', '.join(info.get('authors', ['未知']))
                book_id = book['book_id']
                lines.append(f"- **{title}** (ID: {book_id}) — {authors}")
            lines.append("")
    
    # 按分组展示待更新清单
    if update_books:
        lines.append(f"## 待更新清单（{len(update_books)}本）\n")
        
        # 按 group_key 分组
        grouped = {}
        for item in update_books:
            key = item['group_key']
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)
        
        for group_key, books in grouped.items():
            lines.append(f"### {group_key}（{len(books)}本）\n")
            books_sorted = sorted(books, key=lambda x: int(x['book_id']), reverse=True)
            for book in books_sorted:
                info = book['info']
                title = info.get('title', '未知')
                authors = ', '.join(info.get('authors', ['未知']))
                book_id = book['book_id']
                detail = book['detail']
                lines.append(f"- **{title}** (ID: {book_id}) — {authors} | {detail}")
            lines.append("")
    
    # 汇总统计
    lines.append("## 汇总统计\n")
    lines.append(f"共检查 {total_books} 本")
    
    if delete_books:
        pct = f"{len(delete_books) * 100 / total_books:.1f}%" if total_books > 0 else "0%"
        lines.append(f"❌ 待删除 {len(delete_books)} 本 (占比 {pct})")
    
    if update_books:
        pct = f"{len(update_books) * 100 / total_books:.1f}%" if total_books > 0 else "0%"
        lines.append(f"⚠️ 待更新 {len(update_books)} 本 (占比 {pct})")
    
    if pass_books:
        pct = f"{len(pass_books) * 100 / total_books:.1f}%" if total_books > 0 else "0%"
        lines.append(f"✅ 合格 {len(pass_books)} 本 (占比 {pct})")
    
    return '\n'.join(lines)


# ============================================================================
# CLI 接口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Calibre 书籍质量筛选')
    parser.add_argument('--input', '-i', required=True, help='输入 JSON 文件（书籍元数据）')
    parser.add_argument('--output', '-o', help='输出报告文件（默认：输出到 stdout）')
    
    args = parser.parse_args()
    
    # 读取输入数据
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 筛选书籍
    results = []
    for book_id, info in data.items():
        action, category, detail, group_key = check_book(book_id, info)
        results.append({
            'book_id': book_id,
            'action': action,
            'category': category,
            'detail': detail,
            'group_key': group_key,
            'info': info
        })
    
    # 计算频率统计
    frequency = calculate_frequency(results)
    
    # 生成报告
    report = format_report(results, frequency)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
