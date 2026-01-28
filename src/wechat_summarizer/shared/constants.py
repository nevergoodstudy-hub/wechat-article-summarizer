"""全局常量"""

# 版本信息
VERSION = "2.1.1"
APP_NAME = "WeChat Article Summarizer"

# 默认配置
DEFAULT_TIMEOUT = 30  # 秒
DEFAULT_MAX_RETRIES = 3
DEFAULT_CHUNK_SIZE = 4000  # Token

# User-Agent池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# 微信相关
WECHAT_DOMAIN = "mp.weixin.qq.com"
WECHAT_CONTENT_SELECTORS = [
    "#js_content",
    ".rich_media_content",
    "#page-content",
]

# LLM默认配置
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"  # DeepSeek V3
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_ANTHROPIC_MODEL = "claude-3-haiku-20240307"
DEFAULT_ZHIPU_MODEL = "glm-4-flash"

# Token限制
MAX_TOKENS_OLLAMA = 8000
MAX_TOKENS_OPENAI = 128000
MAX_TOKENS_DEEPSEEK = 64000  # DeepSeek 支持 64K 上下文
MAX_TOKENS_ANTHROPIC = 100000
MAX_TOKENS_ZHIPU = 128000

# 摘要Prompt模板 - 基于全网最佳实践优化
SUMMARY_PROMPT_TEMPLATE = """# 角色设定
你是一位资深的内容分析专家，拥有10年以上的新媒体内容策划与文章分析经验。
你擅长快速提炼文章核心观点、识别关键信息、并以结构化方式呈现摘要。

# 任务目标
请对以下微信公众号文章进行深度分析与摘要，帮助读者快速理解文章核心价值。

# 分析要求
1. **核心观点提取**：识别文章的主旨论点和作者的核心主张
2. **关键信息提炼**：提取数据、案例、引用等支撑性内容
3. **逻辑结构梳理**：分析文章的论证逻辑和行文脉络
4. **价值判断**：评估文章的信息价值和适用场景
5. **字数控制**：摘要部分严格控制在{max_length}字以内

# 输出规范
- 使用简洁、准确的中文表述
- 避免冗余描述和重复信息
- 保持客观中立的分析视角
- 确保关键数据和观点的准确性

# 待分析文章
---
{content}
---

# 输出格式（请严格按照以下结构输出）

## 📝 文章摘要
[用2-3段话概括文章的核心内容和主要观点，突出最有价值的信息]

## 💡 核心观点
1. [最重要的核心观点]
2. [第二重要的观点]
3. [其他关键观点...]

## 🔑 关键要点
- **要点一**：[具体描述]
- **要点二**：[具体描述]
- **要点三**：[具体描述]
- [更多要点...]

## 📊 数据与案例（如有）
- [文章中提到的关键数据或案例]

## 🎯 适用场景
- [这篇文章对哪类读者或场景最有价值]

## 🏷️ 标签
#标签1 #标签2 #标签3 [3-5个相关标签]

## 💭 一句话总结
[用一句话概括全文精髓，便于分享]
"""

# 简洁版摘要Prompt模板 - 适合快速浏览
SUMMARY_PROMPT_CONCISE = """你是一位高效的内容提炼专家。请用最精炼的语言总结以下文章。

要求：
- 总字数控制在{max_length}字以内
- 只保留最核心的信息
- 使用简洁的中文表述

文章内容：
{content}

请输出：
【摘要】[2-3句话概括核心内容]
【要点】3-5个关键要点，每个一句话
【标签】2-3个关键词标签
"""

# 深度分析Prompt模板 - 带Chain-of-Thought推理
SUMMARY_PROMPT_DEEP_ANALYSIS = """# 角色
你是一位资深的内容分析师，擅长通过系统性思维深度解析文章。

# 任务
请对以下文章进行深度分析。在分析过程中，请逐步思考：

## 思考步骤（内部推理，无需输出）
1. 首先，识别文章的主题和写作目的
2. 然后，梳理文章的逻辑结构和论证路径
3. 接着，提取核心论点和支撑证据
4. 最后，评估文章的价值和局限性

# 待分析文章
```
{content}
```

# 输出格式（控制在{max_length}字内）

## 📚 文章定位
- **文章类型**：[资讯/观点/教程/故事/其他]
- **写作目的**：[作者想达到什么目的]
- **目标受众**：[适合什么样的读者]

## 🧠 核心观点解析
[深入分析文章的核心主张，包括论证逻辑和支撑证据]

## 📝 内容摘要
[概括文章的主要内容]

## 🎯 关键要点
1. [要点1及其重要性]
2. [要点2及其重要性]
3. [要点3及其重要性]

## 💡 独特见解
[文章中最有价值、最新颖的观点或视角]

## ⚖️ 价值评估
- **优势**：[文章的亮点和价值]
- **局限**：[文章可能存在的不足或偏见]

## 📌 行动建议
[读者可以采取的具体行动]

## 🏷️ 标签
#标签1 #标签2 #标签3
"""

# 技术文章摘要Prompt模板
SUMMARY_PROMPT_TECHNICAL = """你是一位资深的技术文档分析专家，具备软件开发、数据科学和AI等领域的专业背景。

请分析以下技术文章，提取核心技术要点。

文章内容：
```
{content}
```

请按以下格式输出（控制在{max_length}字内）：

## 🛠️ 技术概述
[用简洁的语言概括技术主题和背景]

## 💻 核心技术点
1. **技术点1**：[详细描述]
2. **技术点2**：[详细描述]
3. **技术点3**：[详细描述]

## 📦 涉及技术栈
- [列出文章涉及的技术、工具、框架等]

## 💡 关键实现思路
[描述核心的实现方案或架构设计]

## ⚠️ 注意事项/常见问题
- [潜在的坑点或需要注意的地方]

## 📊 性能/效果指标（如有）
- [文章中提到的关键数据指标]

## 🚀 应用场景
[这项技术适合什么场景使用]

## 📖 延伸阅读建议
[推荐进一步学习的方向或资源]

## 🏷️ 标签
#技术领域 #具体技术 #应用场景
"""

# 新闻资讯摘要Prompt模板
SUMMARY_PROMPT_NEWS = """你是一位资深的新闻编辑，擅长快速提取新闻要素和核心信息。

请分析以下新闻/资讯文章，提取关键信息。

文章内容：
```
{content}
```

请按以下格式输出（控制在{max_length}字内）：

## 📰 新闻要素
- **什么事**：[事件核心内容]
- **谁**：[涉及的关键人物/机构]
- **何时**：[时间点或时间范围]
- **何地**：[地点信息]
- **为何**：[原因或背景]
- **如何**：[进展或方式]

## 📝 事件摘要
[用一段话概括整个事件]

## 🔑 关键数据
- [文章中的关键数字和数据]

## 🔗 相关背景
[理解这个新闻需要了解的背景信息]

## 💡 影响分析
[这个事件可能产生的影响]

## 🏷️ 标签
#新闻类别 #关键词1 #关键词2
"""

# 观点评论文章摘要Prompt模板
SUMMARY_PROMPT_OPINION = """你是一位客观中立的内容分析师，擅长分析观点类文章的论证逻辑。

请分析以下观点/评论文章。

文章内容：
```
{content}
```

请按以下格式输出（控制在{max_length}字内）：

## 🎯 作者核心观点
[明确陈述作者的主要观点和立场]

## 🧩 论证结构
1. **论点一**：[观点] → **论据**：[支撑证据]
2. **论点二**：[观点] → **论据**：[支撑证据]
3. **论点三**：[观点] → **论据**：[支撑证据]

## 📝 论证摘要
[概括文章的主要论证逻辑]

## ⚖️ 观点评估
- **观点深度**：[分析观点的深度和原创性]
- **论据强度**：[评估支撑证据的充分程度]
- **逻辑严密性**：[评估论证过程的逻辑性]

## 🔄 另一种视角
[客观分析可能存在的不同观点或反驳意见]

## 💡 讨论价值
[这篇文章为相关讨论带来了什么价值]

## 🏷️ 标签
#话题领域 #观点类型 #关键词
"""

# 教程/实操类文章摘要Prompt模板
SUMMARY_PROMPT_TUTORIAL = """你是一位经验丰富的知识整理专家，擅长提炼教程和实操类内容的核心步骤。

请分析以下教程/实操文章。

文章内容：
```
{content}
```

请按以下格式输出（控制在{max_length}字内）：

## 🎯 学习目标
[完成本教程后你能掌握什么]

## 📝 教程摘要
[简要概括教程内容]

## 📋 步骤概览
1. **步骤1**：[步骤名称和简要说明]
2. **步骤2**：[步骤名称和简要说明]
3. **步骤3**：[步骤名称和简要说明]
...

## 🛠️ 所需工具/前置条件
- [完成教程需要的工具、材料或前置知识]

## ⚠️ 注意事项
- [容易出错的地方或关键提示]

## 💡 实用技巧
- [文章中分享的有用技巧]

## 📖 适用人群
[这个教程适合什么水平的读者]

## 🏷️ 标签
#技能领域 #难度级别 #关键词
"""

# 学术/研究文章摘要Prompt模板
SUMMARY_PROMPT_ACADEMIC = """# 角色
你是一位严谨的学术论文审阅专家，具备广泛的跨学科研究背景。

# 任务
请对以下学术/研究文章进行专业摘要。

文章内容：
```
{content}
```

请按以下格式输出（控制在{max_length}字内）：

## 📚 研究概述
- **研究领域**：[学科领域]
- **研究问题**：[研究试图解决的问题]
- **研究目的**：[主要研究目标]

## 🧪 研究方法
[描述采用的研究方法、实验设计或分析框架]

## 📊 核心发现
1. [主要发现一]
2. [主要发现二]
3. [主要发现三]

## 💡 研究贡献
[这项研究的创新点和学术价值]

## ⚠️ 局限性
[研究的局限性和待改进之处]

## 🔮 未来方向
[可能的后续研究方向]

## 🏷️ 标签
#研究领域 #研究方法 #关键词
"""

# 多语言/双语摘要Prompt模板
SUMMARY_PROMPT_BILINGUAL = """你是一位精通中英双语的内容分析专家。

请对以下文章进行中英双语摘要。

文章内容：
```
{content}
```

请按以下格式输出（每种语言控制在{max_length}字内）：

## 🇨🇳 中文摘要

### 核心观点
[用中文描述核心观点]

### 关键要点
- 要点一
- 要点二
- 要点三

### 一句话总结
[中文一句话摘要]

---

## 🇺🇸 English Summary

### Core Insights
[Describe core insights in English]

### Key Points
- Point 1
- Point 2
- Point 3

### One-line Summary
[One-line summary in English]

## 🏷️ 标签/Tags
#中文标签 #EnglishTag #关键词
"""

# 摘要模板索引（用于代码中动态选择）
SUMMARY_TEMPLATES = {
    "standard": SUMMARY_PROMPT_TEMPLATE,
    "concise": SUMMARY_PROMPT_CONCISE,
    "deep": SUMMARY_PROMPT_DEEP_ANALYSIS,
    "technical": SUMMARY_PROMPT_TECHNICAL,
    "news": SUMMARY_PROMPT_NEWS,
    "opinion": SUMMARY_PROMPT_OPINION,
    "tutorial": SUMMARY_PROMPT_TUTORIAL,
    "academic": SUMMARY_PROMPT_ACADEMIC,
    "bilingual": SUMMARY_PROMPT_BILINGUAL,
}

# 模板描述（用于GUI显示）
SUMMARY_TEMPLATE_DESCRIPTIONS = {
    "standard": "标准摘要 - 适合大多数文章，结构化输出",
    "concise": "简洁摘要 - 快速浏览，精炼输出",
    "deep": "深度分析 - 包含价值评估和行动建议",
    "technical": "技术文章 - 提取技术要点和实现思路",
    "news": "新闻资讯 - 5W1H结构，新闻要素提取",
    "opinion": "观点评论 - 分析论证逻辑和观点强度",
    "tutorial": "教程实操 - 提取步骤和注意事项",
    "academic": "学术研究 - 研究方法和发现摘要",
    "bilingual": "双语摘要 - 中英文对照输出",
}

# GUI相关
GUI_WINDOW_TITLE = "微信公众号文章总结器 v2.1"
GUI_WINDOW_SIZE = "1200x800"
GUI_MIN_SIZE = (800, 600)

# 主题颜色
THEME_COLORS = {
    "primary": "#07C160",  # 微信绿
    "secondary": "#576B95",  # 微信蓝
    "success": "#91d5ff",
    "warning": "#faad14",
    "error": "#ff4d4f",
    "background": "#f5f5f5",
    "text": "#333333",
}

# 文件路径
CONFIG_DIR_NAME = ".wechat_summarizer"
CONFIG_FILE_NAME = "config.yaml"
CACHE_DIR_NAME = "cache"
LOG_FILE_NAME = "app.log"
