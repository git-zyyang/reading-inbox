---
name: reading-inbox
version: "2.0"
description: 阅读收件箱处理系统 — 批量处理微信收藏的文章链接，自动提取摘要、分类、归档到知识库。支持YAML frontmatter、去重检测、多源URL解析。
triggers:
  - "处理阅读收件箱"
  - "处理inbox"
  - "消化文章"
  - "处理收藏的文章"
---

# Reading Inbox Processor v2.0

## 系统定位

解决"转发即遗忘"的信息浪费问题。将微信文件传输助手中收藏的文章，转化为结构化的知识卡片，融入现有知识体系。

## 文件依赖

```
00_个人知识库/阅读笔记/
├── config.yaml           ← 用户配置（研究兴趣、标签体系）
├── inbox.md              ← 用户粘贴URL/标题的入口
├── reading_log.md        ← 处理日志（索引）
├── archive/              ← 归档的笔记卡片
│   └── MMDD_来源_标题缩写.md
├── scripts/
│   ├── capture.py        ← 剪贴板快捷捕获
│   └── fetch.py          ← 多策略文章抓取
└── templates/
    └── note_card.md      ← 笔记卡片模板
```

## 工作流程

### Phase 0: 读取收件箱 + 去重检测

1. 读取 `00_个人知识库/阅读笔记/inbox.md`
2. 解析URL（见下方URL解析规则）
3. 对每个URL检查 `reading_log.md` 是否已有相同URL或相似标题
4. 跳过重复条目，告知用户
5. 若收件箱为空或全部重复，告知用户并退出

### URL解析规则

用户粘贴的格式可能不规范（URL和标题连在一起、无分隔符等），需要鲁棒解析：

```
# 格式1：纯URL
https://mp.weixin.qq.com/s/XpCUeqzSPCN4GHlvczUZRA

# 格式2：URL+标题（无分隔符，中文字符作为分界）
https://mp.weixin.qq.com/s/XpCUeqzSPCN4GHlvczUZRA财富积累与共同富裕

# 格式3：URL + 标题（有分隔符）
https://mp.weixin.qq.com/s/XpCUeqzSPCN4GHlvczUZRA | 财富积累与共同富裕

# 格式4：纯标题 + 备注
某篇文章标题 | 关于数字经济的
```

解析逻辑：
1. 用正则 `https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+` 提取微信URL
2. URL后的中文/非ASCII字符视为标题提示
3. 其他URL用通用正则 `https?://\S+` 提取
4. 无URL的行视为纯标题，用WebSearch搜索

### Phase 1: 逐条处理

对每个条目执行：

#### 1.1 内容获取

微信文章抓取策略链（按优先级）：
1. `curl` + JS内容提取（提取 `id="js_content"` 内的文本）
2. 若curl失败 → 用 `WebFetch` 尝试
3. 若WebFetch失败 → 用 `WebSearch` 搜索文章标题获取缓存
4. 全部失败 → 记录URL，标记为 `fetch_failed`，跳过

#### 1.2 信息提取

从文章内容中提取（忠实原文，不过度解读）：

```yaml
title: 文章标题
authors: [作者列表]
source: 期刊/公众号
year: 发表年份
doi: DOI（如有）
tags: [主题标签]
date: 发布日期
body_summary: 核心论点（忠实原文）
data_and_method: 数据与方法
findings: 核心发现
contributions: 边际贡献
references: 提到的论文
```

#### 1.3 分类标签

从 `config.yaml` 的 `tag_categories` 读取标签体系，自动匹配。若config不存在，使用默认标签：

| 一级分类 | 二级标签示例 |
|----------|-------------|
| 宏观经济 | #产业政策 #区域发展 #国际贸易 #经济增长 |
| 数字经济 | #数字基础设施 #平台经济 #数据要素 #AI |
| 劳动经济 | #技能溢价 #外包 #就业 #工资不平等 |
| 实证方法 | #因果推断 #DID #IV #RDD #面板数据 |

### Phase 2: 生成笔记卡片（YAML frontmatter格式）

每篇文章生成一个归档文件，必须包含YAML frontmatter：

```markdown
---
title: "文章标题"
authors: ["作者1", "作者2"]
source: "期刊/公众号"
year: 2025
doi: "10.xxxx/xxxxx"
tags: ["标签1", "标签2"]
status: archived
relevance: medium
processed_date: 2026-02-22
url: "https://..."
---

# 文章标题

> 来源：... | 作者：...

## 研究问题
...
## 核心机制/论点
...
## 数据与方法
...
## 核心发现
...
## 边际贡献
...
## 提到的论文
...

<!-- AI-generated: 以下内容由AI根据config.yaml中的研究兴趣自动生成 -->
## 与我的研究关联
...

## 原文链接
...
```

文件命名：`archive/MMDD_{来源缩写}_{标题关键词}.md`

### Phase 3: 更新日志

将每篇处理结果追加到 `reading_log.md` 的表格中。更新累计处理数。

### Phase 4: 知识库联动（可选）

处理完所有条目后，汇总检查：
- 若发现值得追踪的论文 → 提示用户
- 若发现与当前在写论文直接相关的内容 → 高亮提示

### Phase 5: 清空收件箱

处理完成后，将 inbox.md 中已处理的条目移除，保留文件头部说明。

## 输出规范

```
✓ 阅读收件箱处理完成
- 本次处理：{N}篇（跳过{M}篇重复）
- 分类分布：学术{x}篇 / 科技{y}篇 / 其他{z}篇
- 发现论文线索：{n}条
- 笔记归档：archive/ 下 {N} 个文件
```

## 模型路由

- 内容抓取+信息提取：Sonnet（结构化提取任务）
- 研究关联判断：主会话 Opus（需要理解用户研究方向）

## 注意事项

- 微信文章链接有时效性，尽早处理
- WebFetch 对微信文章可能被拦截，优先用 Bash curl 抓取
- 笔记内容必须忠实原文，AI生成的关联分析部分用HTML注释标注
- "与我的研究关联"部分基于 config.yaml 中的研究兴趣生成
