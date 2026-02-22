# Reading Inbox

> 你转发到微信文件传输助手的文章，后来真的读了吗？

一个轻量的个人知识捕获工具。把微信公众号里随手转发的文章，自动变成带元数据的结构化笔记卡片。

不需要数据库，不需要服务器，不需要注册账号。只要一个 Markdown 文件夹和 Claude Code。

## 为什么做这个

做学术的人每天在微信公众号上刷到不少好文章，顺手转发到文件传输助手，想着"回头看"。但回头就忘了。

这些零散的阅读素材，如果能持续积累、分类检索，其实是很有价值的个人知识库。

Reading Inbox 做的事情很简单：

- 把链接粘贴到 `inbox.md`
- 说一句"处理阅读收件箱"
- 自动抓取全文、提取关键信息、生成笔记卡片、更新索引

从"转发即遗忘"变成"转发即入库"。

## 快速开始

### 1. 安装

将本项目复制到你的知识库目录：

```bash
git clone https://github.com/git-zyyang/reading-inbox.git
cd reading-inbox
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入你的研究兴趣
```

### 2. 捕获文章

在电脑端微信看到文件传输助手里的文章，复制链接粘贴到 `inbox.md`：

```markdown
https://mp.weixin.qq.com/s/xxxxx
https://mp.weixin.qq.com/s/yyyyy
```

或使用快捷捕获脚本（macOS）：

```bash
python scripts/capture.py  # 监听剪贴板，自动追加微信链接
```

### 3. 处理

#### 方式A：Claude Code Skill（推荐）

将 `skill/SKILL-reading-inbox.md` 复制到你的 `.claude/skills/` 目录，然后对 Claude 说：

> 处理阅读收件箱

#### 方式B：命令行

```bash
python scripts/fetch.py  # 批量抓取并生成笔记卡片
```

## 项目结构

```
reading-inbox/
├── README.md                    # 本文件
├── config.yaml                  # 用户配置
├── inbox.md                     # 文章链接入口
├── reading_log.md               # 处理日志（索引）
├── archive/                     # 归档的笔记卡片
│   └── MMDD_来源_标题.md
├── skill/
│   └── SKILL-reading-inbox.md   # Claude Code Skill
├── scripts/
│   ├── capture.py               # 剪贴板快捷捕获
│   └── fetch.py                 # 多策略文章抓取
├── templates/
│   ├── note_card.md             # 笔记卡片模板
│   └── weekly_digest.md         # 周报模板
└── examples/
    └── ...                      # 示例输出
```

## 笔记卡片格式

每篇文章生成一个 Markdown 文件，包含 YAML frontmatter：

```yaml
---
title: "文章标题"
authors: ["作者1", "作者2"]
source: "期刊/公众号"
year: 2025
doi: "10.xxxx/xxxxx"
tags: ["标签1", "标签2"]
status: archived   # inbox | processing | archived | read | cited
relevance: medium  # low | medium | high
processed_date: 2026-02-22
url: "https://..."
---
```

## 状态流转

```
inbox → processing → archived → read → cited
                                  ↓
                              deep-read
```

## 配置

编辑 `config.yaml` 自定义：
- 研究兴趣和标签体系
- 笔记详细程度（minimal / standard / rich）
- 是否生成AI关联分析
- 文章抓取策略

## 支持的文章来源

| 来源 | 状态 | 说明 |
|------|------|------|
| 微信公众号 | ✅ | 通过 curl + JS内容提取 |
| arXiv | 🔜 | 计划中 |
| NBER | 🔜 | 计划中 |
| SSRN | 🔜 | 计划中 |

## License

MIT
