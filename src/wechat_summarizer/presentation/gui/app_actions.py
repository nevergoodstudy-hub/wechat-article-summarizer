"""Fetch, validation, and single-article interaction helpers for the GUI."""

from __future__ import annotations

import threading
from tkinter import messagebox
from typing import TYPE_CHECKING, Any

from loguru import logger

from .styles.colors import ModernColors
from .widgets.helpers import ExporterInfo, SummarizerInfo

if TYPE_CHECKING:
    from ...domain.entities import Article


class GUIActionsMixin:
    """Encapsulates service discovery, URL validation, and single-run actions."""

    def _get_summarizer_info(self: Any) -> dict[str, SummarizerInfo]:
        info: dict[str, SummarizerInfo] = {}
        info["simple"] = SummarizerInfo("simple", True, "基于规则的简单摘要")
        info["textrank"] = SummarizerInfo("textrank", True, "基于图算法的抽取式摘要")

        ollama_available = True
        ollama_reason = ""
        try:
            import httpx

            with httpx.Client(timeout=2) as client:
                client.get(f"{self.settings.ollama.host}/api/tags")
            ollama_reason = "本地Ollama服务"
        except Exception:
            ollama_available = False
            ollama_reason = f"无法连接到 {self.settings.ollama.host}"
        info["ollama"] = SummarizerInfo("ollama", ollama_available, ollama_reason)

        openai_key = (
            self.user_prefs.get_api_key("openai") or self.settings.openai.api_key.get_secret_value()
        )
        if openai_key:
            info["openai"] = SummarizerInfo("openai", True, "OpenAI GPT")
        else:
            info["openai"] = SummarizerInfo("openai", False, "需要配置 API Key")

        deepseek_key = (
            self.user_prefs.get_api_key("deepseek")
            or self.settings.deepseek.api_key.get_secret_value()
        )
        if deepseek_key:
            info["deepseek"] = SummarizerInfo("deepseek", True, "DeepSeek V3")
        else:
            info["deepseek"] = SummarizerInfo("deepseek", False, "需要配置 API Key")

        anthropic_key = (
            self.user_prefs.get_api_key("anthropic")
            or self.settings.anthropic.api_key.get_secret_value()
        )
        if anthropic_key:
            info["anthropic"] = SummarizerInfo("anthropic", True, "Claude AI")
        else:
            info["anthropic"] = SummarizerInfo("anthropic", False, "需要配置 API Key")

        zhipu_key = (
            self.user_prefs.get_api_key("zhipu") or self.settings.zhipu.api_key.get_secret_value()
        )
        if zhipu_key:
            info["zhipu"] = SummarizerInfo("zhipu", True, "智谱AI GLM")
        else:
            info["zhipu"] = SummarizerInfo("zhipu", False, "需要配置 API Key")

        return info

    def _get_exporter_info(self: Any) -> dict[str, ExporterInfo]:
        info: dict[str, ExporterInfo] = {}
        info["html"] = ExporterInfo("html", True)
        info["markdown"] = ExporterInfo("markdown", True)
        info["zip"] = ExporterInfo("zip", True)

        try:
            import docx  # noqa: F401

            info["word"] = ExporterInfo("word", True)
        except ImportError:
            info["word"] = ExporterInfo("word", False, "缺少 python-docx")

        return info

    def _is_valid_wechat_url(self: Any, url: str) -> bool:
        import re

        patterns = [
            "https?://mp\\.weixin\\.qq\\.com/s[/?]",
            "https?://mp\\.weixin\\.qq\\.com/s/[\\w\\-]+",
        ]
        return any(re.match(pattern, url.strip()) for pattern in patterns)

    def _on_url_input_change(self: Any, event: Any = None) -> None:
        url = self.single_page.url_entry.get().strip()
        if not url:
            self.url_status_label.configure(text="", text_color="gray")
            return None

        if self._is_valid_wechat_url(url):
            self.url_status_label.configure(
                text="✓ 有效的微信公众号链接",
                text_color=ModernColors.SUCCESS,
            )
        else:
            self.url_status_label.configure(
                text="✗ 请输入有效的微信公众号文章链接",
                text_color=ModernColors.ERROR,
            )

    def _on_batch_url_input_change(self: Any, event: Any = None) -> None:
        content = self.batch_page.batch_url_text.get("1.0", "end").strip()
        if not content:
            self.batch_url_status_label.configure(text="", text_color="gray")
            return None

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if not lines:
            self.batch_url_status_label.configure(text="", text_color="gray")
            return None

        valid_urls: list[str] = []
        invalid_urls: list[str] = []
        for url in lines:
            if self._is_valid_wechat_url(url):
                valid_urls.append(url)
            elif url.startswith("http"):
                invalid_urls.append(url)

        unique_urls: list[str] = []
        duplicate_count = 0
        seen: set[str] = set()
        for url in valid_urls:
            if url in seen:
                duplicate_count += 1
            else:
                seen.add(url)
                unique_urls.append(url)

        if duplicate_count > 0:
            self.batch_url_text.index("insert")
            self.batch_url_text.delete("1.0", "end")
            self.batch_url_text.insert("1.0", "\n".join(unique_urls))
            messagebox.showinfo(
                "已自动去重",
                f"检测到 {duplicate_count} 个重复链接\n已自动删除重复项",
            )
            logger.info(f"已自动删除 {duplicate_count} 个重复链接")

        total_count = len(unique_urls)
        invalid_count = len(invalid_urls)

        if total_count > 0 and invalid_count == 0:
            self.batch_url_status_label.configure(
                text=f"✓ 共 {total_count} 个有效链接",
                text_color=ModernColors.SUCCESS,
            )
            return None

        if total_count > 0 and invalid_count > 0:
            self.batch_url_status_label.configure(
                text=f"✓ {total_count} 个有效 | ✗ {invalid_count} 个无效",
                text_color=ModernColors.WARNING,
            )
        else:
            self.batch_url_status_label.configure(
                text="✗ 未找到有效的微信公众号链接",
                text_color=ModernColors.ERROR,
            )

    def _on_fetch(self: Any) -> None:
        url = self.single_page.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入文章URL")
            return None

        if not self._is_valid_wechat_url(url) and not messagebox.askyesno(
            "提示",
            "输入的链接可能不是有效的微信公众号链接\n\n是否继续处理？",
        ):
            return None

        self._single_processing_active = True
        self.single_page.fetch_btn.configure(state="disabled")
        self._set_status("正在抓取...", ModernColors.INFO, pulse=True)
        logger.info(f"开始抓取: {url}")
        threading.Thread(target=self._fetch_article, args=(url,), daemon=True).start()

    def _fetch_article(self: Any, url: str) -> None:
        try:
            article = self.container.fetch_use_case.execute(url)
            logger.info(f"抓取成功: {article.title}")

            if self.single_page.summarize_var.get():
                method = self.single_page.method_var.get()
                try:
                    logger.info(f"正在生成摘要 ({method})...")
                    summary = self.container.summarize_use_case.execute(article, method=method)
                    article.attach_summary(summary)
                    logger.success("摘要生成完成")
                except Exception as exc:
                    logger.warning(f"摘要生成失败: {exc}")

            self.current_article = article
            self.root.after(0, lambda: self._display_result(article))
        except Exception as exc:
            logger.error(f"处理失败: {exc}")
            error_msg = str(exc)
            self.root.after(0, lambda msg=error_msg: self._show_error(msg))

    def _display_result(self: Any, article: Article) -> None:
        self._single_processing_active = False

        single_page = self.single_page
        single_page.title_label.configure(text=f"标题: {article.title}")
        single_page.author_label.configure(text=f"公众号: {article.account_name or '未知'}")
        single_page.word_count_label.configure(text=f"字数: {article.word_count}")

        single_page.preview_text.delete("1.0", "end")
        preview = (
            article.content_text[:2000] + "..."
            if len(article.content_text) > 2000
            else article.content_text
        )
        single_page.preview_text.insert("1.0", preview)

        single_page.summary_text.delete("1.0", "end")
        if article.summary:
            single_page.summary_text.insert("1.0", article.summary.content)
            single_page.points_text.delete("1.0", "end")
            if article.summary.key_points:
                points = "\n".join(f"• {point}" for point in article.summary.key_points)
                single_page.points_text.insert("1.0", points)

        single_page.export_btn.configure(state="normal")
        single_page.fetch_btn.configure(state="normal")
        self._set_status("处理完成", ModernColors.SUCCESS, pulse=False)

    def _show_error(self: Any, message: str) -> None:
        self._single_processing_active = False
        self.single_page.fetch_btn.configure(state="normal")
        self._set_status("处理失败", ModernColors.ERROR, pulse=False)
        messagebox.showerror("错误", message)

    def _check_export_dir_configured(self: Any) -> bool:
        user_export_dir = self.user_prefs.export_dir
        default_export_dir = (
            self.settings.export.default_output_dir if hasattr(self.settings, "export") else None
        )

        if not user_export_dir and not default_export_dir:
            result = messagebox.askyesno(
                "导出目录未设置",
                "您尚未设置默认导出目录。\n\n"
                "建议在「设置」页面配置导出目录，这样每次导出时会自动定位到该目录。\n\n"
                "是否继续导出？\n"
                "\n· 点击「是」继续导出（每次需手动选择位置）"
                "\n· 点击「否」前往设置页配置导出目录",
                icon="warning",
            )

            if not result:
                self._show_page_animated(self.PAGE_SETTINGS)
                if hasattr(self, "_toast_manager") and self._toast_manager:
                    self._toast_manager.info("请在下方「导出设置」中配置默认导出目录")
                return False

        return True
