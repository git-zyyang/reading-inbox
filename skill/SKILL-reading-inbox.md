---
name: reading-inbox
version: "3.0"
description: 阅读收件箱处理系统 — 批量处理微信收藏的文章链接，自动提取摘要、分类、归档到知识库。v3.0 使用统一 Python 脚本处理机械步骤，Claude 专注智能摘要。
triggers:
  - "处理阅读收件箱"
  - "处理inbox"
  - "消化文章"
  - "处理收藏的文章"
---

# Reading Inbox Processor v3.0

## 系统定位

解决"转发即遗忘"的信息浪费问题。将微信文件传输助手中收藏的文章，转化为结构化的知识卡片，融入现有知识体系。

## 架构：脚本 + Claude 分工

```
process_inbox.py fetch    → 机械步骤（读取inbox、去重、curl抓取）
Claude                    → 智能步骤（摘要、分类、标签、关联判断）
process_inbox.py finalize → 机械步骤（更新日志、清空收件箱）
```

## 文件依赖

```
00_个人知识库/阅读笔记/
├── config.yaml           ← 用户配置（研究兴趣、标签体系）
├── inbox.md              ← 用户粘贴URL的入口
├── reading_log.md        ← 处理日志（索引表格）
├── archive/              ← 归档的笔记卡片
│   └── MMDD_来源_标题缩写.md
└── scripts/
    ├── process_inbox.py  ← 统一处理管线（v1.0）
    └── batch_fetch.py    ← 旧版抓取脚本（已被process_inbox.py取代）
```

## 工作流程（3步）

### Step 1: 运行抓取脚本

```bash
python3 00_个人知识库/阅读笔记/scripts/process_inbox.py fetch > /tmp/inbox_fetched.json 2>/tmp/inbox_progress.txt
```

脚本自动完成：
- 读取 inbox.md 提取 URL
- 对比 archive/ 已有文件去重
- curl + 浏览器 UA 批量抓取（含重试、JS代码过滤）
- 输出结构化 JSON 到 /tmp/inbox_fetched.json

### Step 2: Claude 生成笔记卡片

读取 /tmp/inbox_fetched.json，对每篇 status=ok 的文章：

1. 根据 body 内容生成笔记卡片（格式见下方模板）
2. 串行写入 archive/ 目录（禁止并行 sub-agent 写同一目录）
3. 文件命名：`MMDD_{来源}_{标题前10字}.md`

**关键规则**：
- 禁止并行 sub-agent 写 archive/ 目录（v2.0 教训：文件冲突导致丢失）
- 可以用 2 个串行 sub-agent（每个处理一半），但不能同时写
- 或者用 1 个 sub-agent 全部处理（更安全）
- 摘要必须从 body 文本提取，不能写"待提取"
- 检查摘要是否包含 JS 代码残留（document.、function(等），若有则重新提取

### Step 3: 运行收尾脚本

```bash
python3 00_个人知识库/阅读笔记/scripts/process_inbox.py finalize 2>&1
```

脚本自动完成：
- 扫描 archive/ 中今天的文件
- 提取 YAML 元数据生成日志条目
- 追加到 reading_log.md
- 清空 inbox.md 中的 URL

## 笔记卡片模板

```markdown
---
title: "文章标题"
authors: ["作者1"]
source: "公众号/期刊名"
year: 2026
tags: ["#标签1", "#标签2", "#标签3"]
status: archived
relevance: high/medium/low
processed_date: 2026-02-23
url: "https://..."
---

# 文章标题

> 来源：XX | 作者：XX

## 核心论点
（2-4句话概括，忠实原文）

## 数据与方法
（学术文章描述方法；评论/资讯写"评论/资讯类文章"）

## 核心发现
- 发现1
- 发现2
- 发现3

## 边际贡献
（1-2句话）

## 提到的论文
- （列出明确引用的论文，无则写"未发现明确引用"）

## 原文链接
[原文](URL)
```

## 分类标签体系

从 config.yaml 读取，默认：

| 一级分类 | 标签 |
|----------|------|
| 宏观经济 | #产业政策 #区域发展 #国际贸易 #宏观经济 |
| 数字经济 | #数字经济 #数字基础设施 #平台经济 #AI |
| 劳动经济 | #劳动经济 #就业 #工资不平等 #技能溢价 |
| 实证方法 | #实证方法 #因果推断 #DID #IV |
| 科技前沿 | #科技前沿 #创新 #知识管理 |

relevance 判断（基于 config.yaml 研究兴趣）：
- high: 直接相关（数字经济、劳动经济、产业组织）
- medium: 间接相关或方法论参考
- low: 一般性资讯

## 来源分类规则

文件名前缀：
- 标题含"JPE/AER/QJE/ECMA/RES/JDE/JIE/JIBS"等 → `学术`
- 标题含"管理世界/经济研究/中国社会科学"等 → 对应期刊名
- 其他 → `公众号`

## 输出规范

```
✓ 阅读收件箱处理完成
- 本次处理：{N}篇（跳过{M}篇重复）
- 成功/失败：{ok}/{fail}
- 笔记归档：archive/ 下 {N} 个文件
```

## 模型路由

- process_inbox.py: 无需模型（纯 Python）
- 笔记卡片生成: Sonnet sub-agent（结构化提取）
- 研究关联判断: 主会话 Opus

## 微信抓取注意事项

- 必须用 curl + 浏览器 UA，WebFetch 会被微信验证墙拦截
- process_inbox.py 已内置正确的 UA 和 JS 代码过滤
- 抓取失败的文章标记为 fetch_failed，不生成卡片

## Zotero 自动导入（可选）

处理完成后，如果 config.yaml 中 `zotero.enabled: true`，运行：

```bash
python3 00_个人知识库/阅读笔记/scripts/zotero_sync.py
```

自动将带 DOI 的笔记卡片导入 Zotero，并在 frontmatter 中标记 `zotero_synced: true`。
已同步的卡片不会重复导入。
