#!/usr/bin/env python3
"""
fetch.py - 多策略文章抓取工具
从 inbox.md 读取URL，抓取文章内容，生成结构化笔记卡片
"""

import re
import html
import json
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INBOX_PATH = BASE_DIR / "inbox.md"
ARCHIVE_DIR = BASE_DIR / "archive"
LOG_PATH = BASE_DIR / "reading_log.md"

def parse_inbox():
    """解析inbox.md，提取待处理条目"""
    if not INBOX_PATH.exists():
        return []
    content = INBOX_PATH.read_text(encoding='utf-8')
    entries = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('>'):
            continue
        if line.startswith('<!--') or line.startswith('---'):
            continue
        # 提取URL（支持URL和标题连在一起的情况）
        url_match = re.match(
            r'(https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+)', line
        )
        if url_match:
            url = url_match.group(1)
            title_hint = line[len(url):].strip().lstrip('-').strip()
            entries.append({'url': url, 'title_hint': title_hint})
            continue
        # 其他URL
        url_match = re.match(r'(https?://\S+)', line)
        if url_match:
            url = url_match.group(1)
            title_hint = line[len(url):].strip()
            entries.append({'url': url, 'title_hint': title_hint})
            continue
        # 纯标题
        if '|' in line:
            title, note = line.split('|', 1)
            entries.append({
                'url': None,
                'title_hint': title.strip(),
                'note': note.strip()
            })
    return entries

def fetch_wechat(url):
    """抓取微信公众号文章"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        return {'error': str(e)}

    result = {}

    # 提取发布日期
    time_match = re.search(r'var ct = "(\d+)"', raw)
    if time_match:
        ts = int(time_match.group(1))
        result['date'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

    # 提取正文
    body_match = re.search(
        r'id="js_content"[^>]*>(.*?)</div>\s*<script', raw, re.DOTALL
    )
    if body_match:
        body = body_match.group(1)
        body = re.sub(r'<[^>]+>', '', body)
        body = html.unescape(body)
        body = re.sub(r'\s+', ' ', body).strip()
        result['body'] = body

    return result

def check_duplicate(url):
    """检查URL是否已处理过"""
    if not LOG_PATH.exists():
        return False
    content = LOG_PATH.read_text(encoding='utf-8')
    return url in content

def main():
    entries = parse_inbox()
    if not entries:
        print("Inbox is empty.")
        return

    print(f"Found {len(entries)} entries to process.\n")

    for i, entry in enumerate(entries, 1):
        url = entry.get('url')
        if not url:
            print(f"[{i}] Skipping (no URL): {entry.get('title_hint')}")
            continue

        if check_duplicate(url):
            print(f"[{i}] Skipping (duplicate): {url[:60]}...")
            continue

        print(f"[{i}] Fetching: {url[:60]}...")

        if 'mp.weixin.qq.com' in url:
            result = fetch_wechat(url)
        else:
            print(f"  Unsupported source, skipping.")
            continue

        if 'error' in result:
            print(f"  Error: {result['error']}")
            continue

        if 'body' in result:
            print(f"  Fetched {len(result['body'])} chars")
            print(f"  Date: {result.get('date', 'unknown')}")
            print(f"  Title hint: {entry.get('title_hint', 'none')}")
            # 保存原始内容供后续处理
            out_path = ARCHIVE_DIR / f"raw_{i}.txt"
            out_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"  Saved raw content to: {out_path}")
        else:
            print(f"  No content extracted.")

    print(f"\nDone. Use Claude Code skill for full processing with AI analysis.")

if __name__ == "__main__":
    main()
