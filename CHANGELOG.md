# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.0] - 2026-01-28

### Added
- 🎨 **2026 GUI现代化重构** - 全面升级视觉设计系统
  - 💧 液态玻璃效果 (Liquid Glass) - 半透明模糊背景
  - 🎨 动态渐变色系统 - 支持线性/径向渐变动画
  - 🔘 ModernButton - Ripple水波纹/Loading状态/4种变体
  - 📋 ModernInput - 现代化输入框组件
  - 🎴 ModernCard - 4级阴影深度 + hover微动画
  - 📢 ToastManager - 堆叠管理/自动消失/多种类型
  - 📊 LinearProgress - 流畅进度指示
- ⌨️ **无障碍与交互增强**
  - KeyboardShortcutManager - 全局快捷键管理
  - BreakpointManager - 响应式布局支持
  - PerformanceMonitor - FPS/内存实时监控
- 📦 **Windows 可执行文件** - PyInstaller 6.18.0 打包
  - 单文件便携版 (~100MB)
  - 包含所有依赖和资源文件

### Changed
- GUI 组件全面替换为现代化组件库
- ToastManager 改为懒加载创建，避免黑色区域问题
- ModernInput 修复 pack 方法继承问题
- 导出功能增加目录配置检查提示

### Fixed
- 修复 ModernButton `_on_leave` 方法参数错误
- 修复 ModernInput 不显示问题
- 修复 Toast 容器初始化时的黑色区域

## [2.0.0] - 2026-01-17

### Added
- 🏗️ **企业级架构重构** - 采用 DDD + 六边形架构
- 📝 **智能摘要** - 支持 simple/Ollama/OpenAI/Anthropic/智谱 多种方式
- 📤 **多平台导出** - HTML/Markdown/Obsidian/Notion/OneNote
- 🎨 **现代化 GUI** - 基于 CustomTkinter，支持深色/浅色主题
- ⌨️ **CLI 工具** - 基于 Click，支持批量处理
- 💾 **本地缓存** - 避免重复抓取
- 🔒 **安全增强** - URL 验证、SSRF 防护、敏感信息保护
- ✅ **测试覆盖** - 单元测试、集成测试

### Changed
- 配置管理迁移至 Pydantic Settings
- 日志系统使用 Loguru
- HTTP 客户端使用 httpx

### Security
- API 密钥使用 SecretStr 保护
- 添加 URL 长度限制和协议白名单
- 添加 SSRF 防护（禁止内网地址）
- 日志脱敏处理

## [1.0.0] - 2025-12-19

### Added
- 初始版本发布
- 微信公众号文章抓取
- 简单摘要生成
- HTML 导出

[Unreleased]: https://github.com/your-username/wechat-article-summarizer/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/your-username/wechat-article-summarizer/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/your-username/wechat-article-summarizer/releases/tag/v1.0.0
