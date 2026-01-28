# 🚀 微信公众号文章总结器 - 新手入门教程

本教程将帮助你从零开始使用微信公众号文章总结器。即使你是编程新手，也能轻松上手！

---

## 📋 目录

1. [这个工具能做什么？](#1-这个工具能做什么)
2. [准备工作](#2-准备工作)
3. [安装步骤](#3-安装步骤)
4. [第一次使用（GUI 图形界面）](#4-第一次使用gui-图形界面)
5. [命令行使用（CLI）](#5-命令行使用cli)
6. [配置 AI 摘要功能](#6-配置-ai-摘要功能)
7. [导出到各种平台](#7-导出到各种平台)
8. [常见问题解答](#8-常见问题解答)
9. [进阶技巧](#9-进阶技巧)

---

## 1. 这个工具能做什么？

**微信公众号文章总结器** 可以帮你：

- 📥 **抓取文章**：输入微信公众号文章链接，自动获取文章内容
- 📝 **生成摘要**：用 AI 或简单规则自动生成文章摘要
- 📤 **导出保存**：将文章导出为 HTML、Markdown、Word 等格式
- 🔗 **同步笔记**：直接写入 Obsidian、Notion、OneNote 等笔记软件

**使用场景示例：**
- 看到一篇好文章，想快速了解核心内容
- 批量整理收藏的公众号文章
- 把文章保存到你的笔记系统中

---

## 2. 准备工作

### 2.1 安装 Python

本工具需要 **Python 3.10 或更高版本**。

**检查是否已安装 Python：**

打开命令提示符（Windows 搜索 `cmd`）或 PowerShell，输入：

```bash
python --version
```

如果显示 `Python 3.10.x` 或更高版本，说明已安装。

**如果未安装，请下载安装：**

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载最新版本（推荐 Python 3.11 或 3.12）
3. 安装时 **务必勾选** "Add Python to PATH"（添加到环境变量）
4. 安装完成后重新打开命令行，验证安装

### 2.2 获取项目代码

**方式一：直接下载**
- 下载项目压缩包并解压到你想要的位置（如 `D:\wechat-summarizer`）

**方式二：使用 Git**
```bash
git clone https://github.com/your-repo/wechat-summarizer.git
cd wechat-summarizer
```

---

## 3. 安装步骤

### 3.1 打开项目目录

```bash
# Windows 示例
cd D:\Newidea-warp

# 或者你的项目所在目录
cd /path/to/wechat-summarizer
```

### 3.2 创建虚拟环境（推荐）

虚拟环境可以隔离项目依赖，避免与其他 Python 项目冲突：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.\.venv\Scripts\Activate.ps1

# 激活虚拟环境（Windows CMD）
.\.venv\Scripts\activate.bat

# 激活虚拟环境（Mac/Linux）
source .venv/bin/activate
```

> 💡 **提示**：激活成功后，命令行开头会显示 `(.venv)`

### 3.3 安装项目

```bash
# 基础安装（包含核心功能）
pip install -e .

# 安装 GUI 图形界面支持
pip install -e .[gui]

# 安装 AI 摘要功能（OpenAI、Anthropic 等）
pip install -e .[ai]

# 一次性安装全部功能
pip install -e .[full,gui]
```

> 💡 **提示**：如果下载慢，可以使用国内镜像源：
> ```bash
> pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 3.4 验证安装

```bash
# 查看版本号
wechat-summarizer --version

# 查看帮助信息
wechat-summarizer --help
```

如果显示版本号和帮助信息，恭喜你，安装成功！🎉

---

## 4. 第一次使用（GUI 图形界面）

对于新手来说，**图形界面是最简单的使用方式**。

### 4.1 启动 GUI

有三种方式启动：

**方式一：双击启动文件**
- Windows 用户可以双击项目根目录的 `启动文章助手.bat` 或 `run_gui.pyw`

**方式二：命令行启动**
```bash
python -m wechat_summarizer
```

**方式三：使用命令**
```bash
wechat-summarizer gui
```

### 4.2 使用 GUI

启动后你会看到一个现代化的界面：

1. **粘贴链接**：复制微信公众号文章链接，粘贴到输入框
2. **选择摘要方式**：
   - `simple` - 简单规则摘要（无需配置，立即可用）
   - `ollama` - 本地 AI 模型（需要安装 Ollama）
   - `openai` - OpenAI GPT（需要 API Key）
   - 其他 AI 选项...
3. **点击处理**：等待抓取和生成摘要
4. **查看结果**：在界面中预览文章内容和摘要
5. **导出保存**：选择格式导出到本地

### 4.3 获取微信文章链接

1. 在微信中打开公众号文章
2. 点击右上角 **「...」** → **「复制链接」**
3. 链接格式通常为：`https://mp.weixin.qq.com/s/xxxxx`

---

## 5. 命令行使用（CLI）

命令行适合批量处理或自动化场景。

### 5.1 基础命令

```bash
# 抓取文章（使用简单摘要）
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx"

# 只查看文章信息，不生成摘要
wechat-summarizer info "https://mp.weixin.qq.com/s/xxx"

# 抓取并导出为 Markdown
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -e markdown

# 抓取并导出为 HTML，保存到指定路径
wechat-summarizer fetch "https://mp.weixin.qq.com/s/xxx" -e html -o article.html
```

### 5.2 选择摘要方式

```bash
# 使用简单规则摘要（默认，无需配置）
wechat-summarizer fetch URL -m simple

# 使用 Ollama 本地模型
wechat-summarizer fetch URL -m ollama

# 使用 OpenAI（需要配置 API Key）
wechat-summarizer fetch URL -m openai

# 使用 Anthropic Claude（需要配置 API Key）
wechat-summarizer fetch URL -m anthropic

# 使用智谱 AI（需要配置 API Key）
wechat-summarizer fetch URL -m zhipu
```

### 5.3 批量处理

```bash
# 处理多个链接
wechat-summarizer batch URL1 URL2 URL3

# 从文件读取链接（每行一个 URL）
wechat-summarizer batch -f urls.txt -e markdown -o ./output

# 从剪贴板读取链接
wechat-summarizer batch --from-clipboard
```

**urls.txt 文件格式示例：**
```
# 这是注释行，会被忽略
https://mp.weixin.qq.com/s/article1
https://mp.weixin.qq.com/s/article2
https://mp.weixin.qq.com/s/article3
```

---

## 6. 配置 AI 摘要功能

默认的 `simple` 摘要方式无需配置，但效果有限。如果你想要更好的摘要效果，可以配置 AI 服务。

### 6.1 创建配置文件

在项目根目录创建 `.env` 文件（可以复制 `.env.example` 并重命名）：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# 然后用记事本编辑
notepad .env
```

### 6.2 配置 OpenAI

如果你有 OpenAI API Key：

```env
WECHAT_SUMMARIZER_OPENAI__API_KEY=sk-your-api-key-here
WECHAT_SUMMARIZER_OPENAI__BASE_URL=https://api.openai.com/v1
WECHAT_SUMMARIZER_OPENAI__MODEL=gpt-4o-mini
```

**获取 API Key：** 访问 [OpenAI 官网](https://platform.openai.com/api-keys) 注册并创建 Key

### 6.3 配置国产 AI（推荐国内用户）

**智谱 AI（GLM）：**
```env
WECHAT_SUMMARIZER_ZHIPU__API_KEY=your-zhipu-api-key
WECHAT_SUMMARIZER_ZHIPU__MODEL=glm-4-flash
```
获取 Key：[智谱开放平台](https://open.bigmodel.cn/)

### 6.4 配置本地 AI（Ollama）

Ollama 可以在本地运行 AI 模型，完全免费且无需联网：

1. 下载安装 [Ollama](https://ollama.com/)
2. 下载模型：`ollama pull qwen2.5:7b`
3. 配置（可选，使用默认值即可）：
```env
WECHAT_SUMMARIZER_OLLAMA__HOST=http://localhost:11434
WECHAT_SUMMARIZER_OLLAMA__MODEL=qwen2.5:7b
```

---

## 7. 导出到各种平台

### 7.1 导出为本地文件

```bash
# 导出为 HTML
wechat-summarizer fetch URL -e html -o article.html

# 导出为 Markdown
wechat-summarizer fetch URL -e markdown -o article.md

# 导出为 Word 文档
wechat-summarizer fetch URL -e word -o article.docx
```

### 7.2 导出到 Obsidian

Obsidian 是一款流行的 Markdown 笔记软件。

配置 `.env`：
```env
WECHAT_SUMMARIZER_EXPORT__OBSIDIAN_VAULT_PATH=D:/MyObsidianVault
```

使用：
```bash
wechat-summarizer fetch URL -e obsidian
```

### 7.3 导出到 Notion

1. 创建 Notion Integration 并获取 API Key
2. 获取目标数据库 ID
3. 配置 `.env`：
```env
WECHAT_SUMMARIZER_EXPORT__NOTION_API_KEY=secret_xxx
WECHAT_SUMMARIZER_EXPORT__NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```
4. 使用：
```bash
wechat-summarizer fetch URL -e notion
```

### 7.4 导出到 OneNote

1. 在 Azure 注册应用获取 Client ID
2. 配置 `.env`：
```env
WECHAT_SUMMARIZER_EXPORT__ONENOTE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
WECHAT_SUMMARIZER_EXPORT__ONENOTE_NOTEBOOK=我的笔记本
WECHAT_SUMMARIZER_EXPORT__ONENOTE_SECTION=微信文章
```
3. 首次使用需要授权：
```bash
wechat-summarizer onenote-auth
```
4. 使用：
```bash
wechat-summarizer fetch URL -e onenote
```

---

## 8. 常见问题解答

### Q1: 安装时提示 "pip 不是内部命令"
**原因**：Python 未正确添加到环境变量  
**解决**：重新安装 Python，确保勾选 "Add Python to PATH"

### Q2: 运行时提示 "ModuleNotFoundError"
**原因**：依赖未正确安装  
**解决**：
```bash
# 确保在项目目录下
cd D:\Newidea-warp

# 重新安装
pip install -e .[full,gui]
```

### Q3: 抓取失败，提示超时或网络错误
**原因**：网络问题或微信反爬限制  
**解决**：
1. 检查网络连接
2. 稍等几分钟后重试
3. 尝试配置代理：
```env
WECHAT_SUMMARIZER_SCRAPER__PROXY=http://127.0.0.1:7890
```

### Q4: GUI 启动失败
**原因**：GUI 依赖未安装  
**解决**：
```bash
pip install -e .[gui]
```

### Q5: OpenAI 提示 API Key 无效
**原因**：API Key 配置错误或过期  
**解决**：
1. 检查 `.env` 文件中的 Key 是否正确（无多余空格）
2. 到 OpenAI 官网确认 Key 是否有效
3. 检查账户是否有余额

### Q6: 缓存占用空间太大
**解决**：清理缓存
```bash
# 查看缓存状态
wechat-summarizer cache-stats

# 清理过期缓存
wechat-summarizer cache-clean
```

---

## 9. 进阶技巧

### 9.1 调试模式

遇到问题时，开启调试模式查看详细日志：
```bash
wechat-summarizer --debug fetch URL
```

### 9.2 使用 Playwright 抓取

部分文章需要 JavaScript 渲染，可以启用 Playwright：

```bash
# 安装 Playwright
pip install -e .[playwright]
playwright install chromium

# 配置启用
# 在 .env 中设置：
WECHAT_SUMMARIZER_SCRAPER__USE_PLAYWRIGHT=true
```

### 9.3 自定义输出目录

```env
WECHAT_SUMMARIZER_EXPORT__DEFAULT_OUTPUT_DIR=D:/我的文章
```

### 9.4 批处理脚本示例

创建 `process_articles.bat`：
```batch
@echo off
cd /d D:\Newidea-warp
call .venv\Scripts\activate.bat
wechat-summarizer batch -f urls.txt -m simple -e markdown -o ./output
pause
```

---

## 🎉 恭喜！

你已经学会了微信公众号文章总结器的基本使用方法。

**下一步建议：**
- 尝试处理几篇文章，熟悉工具
- 配置 AI 摘要，体验智能摘要效果
- 设置导出到你常用的笔记软件

**需要帮助？**
- 查看 [README.md](../README.md) 了解更多功能
- 查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何参与开发

祝你使用愉快！📰✨
