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

## 积累的复利

笔记卡片的真正价值不在于生成的那一刻，而在于日积月累之后。

当你的 `archive/` 里攒了几百张卡片，它就不再只是一个笔记文件夹，而是一个结构化的个人素材库。每张卡片都带有标题、作者、来源、标签、核心论点、关键发现——这些元数据让它们可以被精准检索。

关键在于：Claude Code 能直接读取这些卡片。当你在写论文、备课、做研究综述时，它会自动从你的素材库中找到相关材料，引用你读过的文章、调用你积累的数据和观点。你不需要记住"上个月读过一篇关于 AI 主权的报告"，Claude Code 会帮你找到它。

每天花两分钟粘贴链接，半年后你就拥有了一个只属于自己的、AI 可检索的知识库。你的日常阅读，变成了可复用的研究资产。

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

#### 方式B：三步命令行

```bash
# Step 1: 批量抓取文章内容（输出 JSON 到 /tmp/inbox_fetched.json）
python scripts/process_inbox.py fetch

# Step 2: Claude 根据抓取结果生成笔记卡片（在 Claude Code 中执行）

# Step 3: 更新日志 + 清空收件箱
python scripts/process_inbox.py finalize
```

#### 方式C：旧版命令行

```bash
python scripts/fetch.py  # 批量抓取并生成笔记卡片（v2.0 兼容）
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
│   ├── process_inbox.py         # 统一处理管线（v3.0）
│   ├── capture.py               # 剪贴板快捷捕获
│   └── fetch.py                 # 多策略文章抓取（v2.0 兼容）
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

## 示例输出

以下是实际处理后生成的笔记卡片。一篇顶刊论文，一篇政策报告，展示不同来源的处理效果。

### 学术论文 → 笔记卡片

> Acemoglu & Loebbing, *Journal of Political Economy*, 2026

```yaml
---
title: "学术 | JPE 从任务分配看自动化与劳动力市场结构的两端分红"
authors: ["Acemoglu D", "Loebbing J"]
source: "Journal of Political Economy"
year: 2026
tags: ["#劳动经济", "#AI", "#实证方法", "#宏观经济"]
relevance: high
url: "https://doi.org/10.1086/739330"
---
```

**核心论点**：自动化并非平均冲击劳动市场，而是内生集中于中等复杂度任务，从而引发就业与工资的结构性极化。低技能岗位早期"幸存"并非技术不可替代，而是因为劳动成本足够低，构成了自动化的经济性屏障。

**核心发现**：
- 自动化首先集中发生在中等复杂度任务上，内生引发就业与工资的结构性分化
- 中间任务被自动化接管后，劳动者被迫向两端重新分配，造成就业"中间塌陷"和工资"两端分化"
- 抬高低技能劳动成本的政策（如最低工资）可能削弱阻止自动化进入低端任务的经济约束，反而诱发更广泛的岗位替代

**边际贡献**：在统一的经济成本与比较优势框架下，系统回答了为何自动化长期集中冲击中等技能岗位而非低技能岗位。

<details>
<summary>📄 政策报告 → 笔记卡片（世界经济论坛 & 贝恩公司）</summary>

```yaml
---
title: "世界经济论坛 | 重新思考人工智能主权：通过战略性投资实现竞争力的路径"
authors: ["世界经济论坛", "贝恩公司"]
source: "世界经济论坛"
year: 2026
tags: ["#AI", "#产业政策", "#国际贸易", "#科技前沿"]
relevance: medium
url: "https://mp.weixin.qq.com/s/AHq7koP_Si7SFlDpueTkkg"
---
```

**核心论点**：AI主权不应等同于自给自足，而应是战略性相互依存。各经济体应专注于自身比较优势，通过战略性投资和国际合作构建竞争力，而非试图掌控整个AI价值链。

**核心发现**：
- 2010-2024年间，全球超过50%的AI投资流向基础设施和应用服务领域，AI基础设施投资超6000亿美元
- 美国和中国合计吸收全球AI价值链总投资的约65%
- 新加坡采取均衡发展路径，韩国聚焦芯片硬件优势，证明通往AI竞争力的路径不止一条

**边际贡献**：挑战了"AI主权=全价值链控制"的传统认知，提出战略性相互依存框架，为中小经济体提供了基于比较优势的差异化竞争路径。

</details>

更多示例见 [examples/](examples/) 目录。

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

## 支持作者

如果这个工具对你有帮助，欢迎请作者喝杯咖啡 :coffee:

<img src="assets/donate_alipay.jpg" width="200" alt="支付宝赞赏码">

## License

MIT
