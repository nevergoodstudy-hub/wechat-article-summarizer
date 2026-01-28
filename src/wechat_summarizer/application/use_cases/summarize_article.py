"""生成摘要用例"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from ...domain.entities import Article, Summary, SummaryStyle
from ...domain.value_objects import ArticleContent
from ...shared.exceptions import UseCaseError
from ...shared.utils import chunk_text, truncate_text

if TYPE_CHECKING:
    from ..ports.outbound import SummarizerPort


class SummarizeArticleUseCase:
    """
    生成摘要用例

    负责协调摘要器来生成文章摘要。
    """

    def __init__(self, summarizers: dict[str, SummarizerPort]):
        """
        Args:
            summarizers: 摘要器字典 {method_name: summarizer}
        """
        self._summarizers = summarizers

    def execute(
        self,
        article: Article,
        method: str = "simple",
        style: str = "concise",
        max_length: int = 500,
    ) -> Summary:
        """
        执行生成摘要用例

        Args:
            article: 文章实体
            method: 摘要方法名称
            style: 摘要风格
            max_length: 最大字数

        Returns:
            生成的摘要

        Raises:
            UseCaseError: 摘要生成失败
        """
        if article.content is None:
            raise UseCaseError("文章内容为空，无法生成摘要")

        # 解析风格
        try:
            summary_style = SummaryStyle(style)
        except ValueError:
            logger.warning(f"未知的摘要风格: {style}, 使用默认值")
            summary_style = SummaryStyle.CONCISE

        # 获取摘要器
        summarizer = self._get_summarizer(method)
        if summarizer is None:
            raise UseCaseError(f"未找到摘要方法: {method}")

        if not summarizer.is_available():
            raise UseCaseError(f"摘要器 {method} 不可用")

        # 生成摘要
        logger.info(f"使用 {method} 生成摘要 (风格: {style})")

        try:
            if self._should_chunk(method, article.content.text):
                summary = self._summarize_chunked(
                    summarizer=summarizer,
                    content=article.content,
                    style=summary_style,
                    max_length=max_length,
                    method_name=method,
                )
            else:
                summary = summarizer.summarize(
                    content=article.content,
                    style=summary_style,
                    max_length=max_length,
                )

            logger.info(f"摘要生成成功 (Token: {summary.total_tokens})")
            return summary

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            raise UseCaseError(f"摘要生成失败: {e}") from e

    def _get_summarizer(self, method: str) -> SummarizerPort | None:
        """获取摘要器"""
        return self._summarizers.get(method)

    @staticmethod
    def _should_chunk(method_name: str, text: str) -> bool:
        """判断是否需要分块，避免适配器内部截断导致信息丢失。"""
        # 仅对会“截断输入文本”的 LLM 摘要器启用。
        # simple 摘要器属于规则提取，不需要。
        limits = {
            # 适配器内部目前按字符数截断：ollama 8000, 其余 LLM 约 30000
            "ollama": 8000,
            "openai": 30000,
            "anthropic": 30000,
            "zhipu": 30000,
        }
        limit = limits.get(method_name)
        return bool(limit and len(text) > limit)

    @staticmethod
    def _dedup_keep_order(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            item = item.strip()
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    def _summarize_chunked(
        self,
        summarizer: SummarizerPort,
        content: ArticleContent,
        style: SummaryStyle,
        max_length: int,
        method_name: str,
    ) -> Summary:
        """对长文本分块摘要，再合并并二次压缩到 max_length。"""
        # 预留一定余量给 prompt 模板等
        if method_name == "ollama":
            chunk_size = 6000
        elif method_name in ("openai", "anthropic", "zhipu"):
            chunk_size = 20000
        else:
            chunk_size = 8000

        overlap = 200
        chunk_max_length = min(300, max_length)

        summaries: list[Summary] = []
        total_in = 0
        total_out = 0

        for chunk in chunk_text(content.text, chunk_size=chunk_size, overlap=overlap):
            chunk_content = ArticleContent.from_text(chunk)
            s = summarizer.summarize(
                content=chunk_content, style=style, max_length=chunk_max_length
            )
            summaries.append(s)
            total_in += getattr(s, "input_tokens", 0)
            total_out += getattr(s, "output_tokens", 0)

        combined_text = "\n\n".join(s.content for s in summaries if s.content)

        combined_key_points = self._dedup_keep_order(
            [p for s in summaries for p in list(getattr(s, "key_points", ()))][:20]
        )[:5]
        combined_tags = self._dedup_keep_order(
            [t for s in summaries for t in list(getattr(s, "tags", ()))][:50]
        )[:8]

        # 二次压缩：把分块摘要再总结到用户目标长度
        if len(combined_text) > max_length:
            merged = summarizer.summarize(
                content=ArticleContent.from_text(combined_text),
                style=style,
                max_length=max_length,
            )

            # 以二次结果为主；如果二次结果没给 key_points/tags，就回退合并的
            key_points = (
                list(merged.key_points)
                if getattr(merged, "key_points", ())
                else combined_key_points
            )
            tags = list(merged.tags) if getattr(merged, "tags", ()) else combined_tags

            return Summary(
                content=merged.content,
                key_points=tuple(key_points),
                tags=tuple(tags),
                method=merged.method,
                style=merged.style,
                model_name=merged.model_name,
                input_tokens=total_in + getattr(merged, "input_tokens", 0),
                output_tokens=total_out + getattr(merged, "output_tokens", 0),
            )

        # 不需要二次压缩：直接合并并截断
        return Summary(
            content=truncate_text(combined_text, max_length=max_length),
            key_points=tuple(combined_key_points),
            tags=tuple(combined_tags),
            method=summarizer.method,
            style=style,
            model_name=getattr(summaries[-1], "model_name", None) if summaries else None,
            input_tokens=total_in,
            output_tokens=total_out,
        )

    def list_available_methods(self) -> list[str]:
        """列出可用的摘要方法"""
        return [name for name, summarizer in self._summarizers.items() if summarizer.is_available()]
