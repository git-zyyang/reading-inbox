#!/usr/bin/env python3
"""阅读收件箱统一处理管线 v1.0

用法:
  python process_inbox.py fetch     # Phase 1: 读取inbox→去重→批量抓取→输出JSON
  python process_inbox.py finalize  # Phase 3: 更新reading_log + 清空inbox

Phase 2 (生成笔记卡片) 由 Claude 完成，读取 fetch 输出的 JSON。
"""
import re
import json
import subprocess
import html as htmlmod
import sys
import time
import os
from datetime import date

# === 路径配置 ===
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(BASE, "inbox.md")
LOG = os.path.join(BASE, "reading_log.md")
ARCHIVE = os.path.join(BASE, "archive")
FETCH_OUTPUT = "/tmp/inbox_fetched.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TODAY = date.today().strftime("%Y-%m-%d")
MMDD = date.today().strftime("%m%d")


# === Phase 0: 解析 inbox.md ===
def parse_inbox():
    """从 inbox.md 提取 URL 列表"""
    with open(INBOX, "r") as f:
        content = f.read()
    urls = re.findall(r'https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_\-]+(?:\?[^\s]*)?', content)
    # 也支持非微信 URL
    other = re.findall(r'https?://(?!mp\.weixin\.qq\.com)\S+', content)
    # 去掉 HTML 注释中的示例 URL
    urls = [u for u in urls if 'xxxxx' not in u and 'yyyyy' not in u]
    return urls, other


def get_processed_urls():
    """从 reading_log.md 提取已处理的 URL"""
    if not os.path.exists(LOG):
        return set()
    with open(LOG, "r") as f:
        content = f.read()
    # 从笔记链接中提取文件名，从 archive 文件中提取 URL
    processed = set()
    for fname in os.listdir(ARCHIVE):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(ARCHIVE, fname)
        with open(fpath, "r") as f:
            text = f.read(500)  # 只读前 500 字符找 URL
        m = re.search(r'url:\s*"?(https?://[^\s"]+)', text)
        if m:
            processed.add(m.group(1).split('?')[0])
    return processed


# === Phase 1: 批量抓取 ===
def fetch_article(url, retries=2):
    """抓取单篇微信文章，含重试"""
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                ["curl", "-sL", "-H", f"User-Agent: {UA}", url],
                capture_output=True, text=True, timeout=20
            )
            h = result.stdout
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            return {"url": url, "status": "fetch_failed", "error": str(e)}

        if not h or len(h) < 500:
            if attempt < retries:
                time.sleep(1)
                continue
            return {"url": url, "status": "fetch_failed", "error": "empty_response"}

        if '环境异常' in h and 'js_content' not in h:
            return {"url": url, "status": "blocked", "error": "verification_wall"}

        data = {"url": url, "status": "ok"}

        # 提取元数据
        for pat, key in [
            (r'og:title.*?content="(.*?)"', "title"),
            (r'og:description.*?content="(.*?)"', "description"),
            (r'var nickname\s*=\s*"(.*?)";', "author"),
            (r'var publish_time\s*=\s*"(.*?)";', "publish_time"),
        ]:
            m = re.search(pat, h, re.DOTALL)
            if m:
                data[key] = htmlmod.unescape(m.group(1).strip())

        # 提取正文 — 改进版：去除 script/style 标签
        content_match = re.search(
            r'id="js_content"[^>]*>(.*?)(?:<div class="rich_media_tool"|$)',
            h, re.DOTALL
        )
        if content_match:
            raw = content_match.group(1)
            # 先移除 script 和 style 标签及内容
            raw = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL)
            raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)
            # 移除所有 HTML 标签
            text = re.sub(r'<[^>]+>', '\n', raw)
            text = htmlmod.unescape(text)
            # 清理：去空行、去 JS 残留
            lines = []
            for l in text.split('\n'):
                l = l.strip()
                if not l:
                    continue
                # 跳过 JS 代码残留
                if any(kw in l for kw in [
                    'document.', 'function(', 'var ', 'window.',
                    'addEventListener', 'getElementById', '.style.',
                    'console.', 'return false', '});', 'try{', 'catch('
                ]):
                    continue
                lines.append(l)
            data["body"] = '\n'.join(lines)
        else:
            data["body"] = ""
            data["status"] = "metadata_only" if data.get("title") else "fetch_failed"

        return data

    return {"url": url, "status": "fetch_failed", "error": "max_retries"}


def cmd_fetch():
    """Phase 1: 读取inbox → 去重 → 批量抓取 → 输出JSON"""
    urls, other_urls = parse_inbox()
    if not urls and not other_urls:
        print(json.dumps({"status": "empty", "message": "收件箱为空"}, ensure_ascii=False))
        return

    processed = get_processed_urls()
    new_urls = [u for u in urls if u.split('?')[0] not in processed]
    skipped = len(urls) - len(new_urls)

    print(f"收件箱: {len(urls)} 条微信链接, 去重后: {len(new_urls)} 条新链接, 跳过: {skipped} 条",
          file=sys.stderr)

    results = []
    for i, url in enumerate(new_urls):
        sys.stderr.write(f"[{i+1}/{len(new_urls)}] 抓取中...")
        article = fetch_article(url)
        results.append(article)
        title = article.get("title", "N/A")[:30]
        sys.stderr.write(f" {article['status']} | {title}\n")
        if i < len(new_urls) - 1:
            time.sleep(0.5)

    # 统计
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = sum(1 for r in results if r["status"] != "ok")
    print(f"\n完成: {ok} 成功, {fail} 失败", file=sys.stderr)

    # 输出 JSON
    output = {
        "fetch_date": TODAY,
        "total": len(new_urls),
        "skipped": skipped,
        "ok": ok,
        "failed": fail,
        "articles": results
    }
    with open(FETCH_OUTPUT, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 {FETCH_OUTPUT}", file=sys.stderr)

    # 同时输出到 stdout 供 Claude 读取
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)


# === Phase 3: 更新日志 + 清空收件箱 ===
def cmd_finalize():
    """读取 archive 中今天的文件，更新 reading_log.md，清空 inbox.md"""
    # 收集今天的笔记卡片
    today_files = sorted(f for f in os.listdir(ARCHIVE) if f.startswith(f"{MMDD}_"))
    if not today_files:
        print("没有找到今天的笔记卡片", file=sys.stderr)
        return

    # 读取已有 log 中的文件名，避免重复
    with open(LOG, "r") as f:
        log_content = f.read()
    existing_files = set(re.findall(r'archive/([^\)]+\.md)', log_content))

    new_entries = []
    for fname in today_files:
        if fname in existing_files:
            continue
        fpath = os.path.join(ARCHIVE, fname)
        with open(fpath, "r") as f:
            content = f.read(1500)

        # 提取 YAML 字段
        title_m = re.search(r'^title:\s*"(.+?)"', content, re.M)
        source_m = re.search(r'^source:\s*"(.+?)"', content, re.M)
        tags_m = re.search(r'^tags:\s*\[(.+?)\]', content, re.M)

        title = title_m.group(1)[:40] if title_m else fname.replace(".md", "")
        source = source_m.group(1)[:20] if source_m else "公众号"

        tags_str = ""
        if tags_m:
            tag_list = re.findall(r'"(#[^"]+)"', tags_m.group(1))
            if not tag_list:
                tag_list = re.findall(r"'(#[^']+)'", tags_m.group(1))
            tags_str = " ".join(tag_list[:3])

        # 提取一句话摘要
        summary = ""
        core_m = re.search(r'## 核心论点\s*\n(.+?)(?:\n\n|\n##)', content, re.S)
        if core_m:
            first_sent = re.split(r'[。！？\n]', core_m.group(1).strip())[0]
            summary = first_sent[:80]

        entry = (f"| {TODAY} | {title} | {source} | {tags_str} | "
                 f"{summary} | [笔记](archive/{fname}) |")
        new_entries.append(entry)

    if not new_entries:
        print("所有卡片已在日志中，无需更新", file=sys.stderr)
        return

    # 插入到 reading_log.md
    marker = "<!-- 新条目插入在这里 -->"
    new_text = "\n".join(new_entries) + "\n" + marker
    log_content = log_content.replace(marker, new_text)

    # 更新累计数
    count_m = re.search(r'累计处理：(\d+)篇', log_content)
    if count_m:
        old_count = int(count_m.group(1))
        new_count = old_count + len(new_entries)
        log_content = log_content.replace(
            f'累计处理：{old_count}篇', f'累计处理：{new_count}篇')

    # 更新日期
    log_content = re.sub(r'最后更新：\d{4}-\d{2}-\d{2}', f'最后更新：{TODAY}', log_content)

    with open(LOG, "w") as f:
        f.write(log_content)
    print(f"reading_log.md 已更新，新增 {len(new_entries)} 条", file=sys.stderr)

    # 清空 inbox.md 中的 URL
    with open(INBOX, "r") as f:
        inbox_content = f.read()

    # 移除所有 http 开头的行
    lines = inbox_content.split('\n')
    cleaned = []
    removed = 0
    for line in lines:
        if line.strip().startswith('http'):
            removed += 1
        else:
            cleaned.append(line)

    # 添加处理记录注释
    comment = f"<!-- {TODAY} 已处理{removed}条 -->"
    # 在已有注释后或 --> 后插入
    final = '\n'.join(cleaned)
    if removed > 0 and comment not in final:
        final = final.replace(
            "<!-- 2026-02-23 已处理37条，36成功/1失败(UVcJGzfMP6b2x7c3jJftMQ) -->",
            f"<!-- 2026-02-23 已处理37条，36成功/1失败(UVcJGzfMP6b2x7c3jJftMQ) -->\n{comment}"
        )

    with open(INBOX, "w") as f:
        f.write(final)
    print(f"inbox.md 已清空 {removed} 条链接", file=sys.stderr)


# === 入口 ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "fetch":
        cmd_fetch()
    elif cmd == "finalize":
        cmd_finalize()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)
