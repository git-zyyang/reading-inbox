#!/usr/bin/env python3
"""
capture.py - 剪贴板快捷捕获工具
监听剪贴板，检测到微信公众号链接时自动追加到 inbox.md
"""

import subprocess
import time
import os
import re
from datetime import datetime
from pathlib import Path

# 配置
INBOX_PATH = Path(__file__).parent.parent / "inbox.md"
CHECK_INTERVAL = 1.0  # 秒
URL_PATTERNS = [
    r'https?://mp\.weixin\.qq\.com/s/\S+',
    r'https?://arxiv\.org/abs/\S+',
    r'https?://papers\.ssrn\.com/\S+',
    r'https?://www\.nber\.org/papers/\S+',
]

def get_clipboard():
    """获取macOS剪贴板内容"""
    try:
        result = subprocess.run(
            ['pbpaste'], capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip()
    except Exception:
        return ""

def extract_url(text):
    """从文本中提取支持的URL"""
    for pattern in URL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

def is_duplicate(url):
    """检查URL是否已在inbox中"""
    if not INBOX_PATH.exists():
        return False
    content = INBOX_PATH.read_text(encoding='utf-8')
    return url in content

def append_to_inbox(url):
    """追加URL到inbox.md"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"\n{url}  <!-- captured: {timestamp} -->\n"
    with open(INBOX_PATH, 'a', encoding='utf-8') as f:
        f.write(line)
    print(f"[{timestamp}] Captured: {url}")

def main():
    print(f"Monitoring clipboard for article URLs...")
    print(f"Inbox: {INBOX_PATH}")
    print("Press Ctrl+C to stop.\n")

    last_url = None

    try:
        while True:
            text = get_clipboard()
            url = extract_url(text)

            if url and url != last_url:
                if not is_duplicate(url):
                    append_to_inbox(url)
                    last_url = url
                else:
                    print(f"[skip] Already in inbox: {url[:60]}...")
                    last_url = url

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
