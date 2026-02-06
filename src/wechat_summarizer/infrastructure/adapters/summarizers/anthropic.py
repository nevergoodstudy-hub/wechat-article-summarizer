"""Anthropic 摘要器

使用 anthropic 官方 SDK 调用 Claude 系列模型生成摘要。

该适配器为可选依赖：未安装 anthropic 时，构造函数会抛 ImportError，
容器层会捕获并降级。
"""

from __future__ import annotations

import re

from loguru import logger

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ....shared.prompts import SUMMARY_PROMPT_TEMPLATE
from ....shared.exceptions import SummarizerAPIError, SummarizerError
from .base import BaseSummarizer

# 延迟导入 Anthropic
_anthropic_available = True
try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    _anthropic_available = False


class AnthropicSummarizer(BaseSummarizer):
    """Anthropic/Claude 摘要器"""

    def __init__(self, api_key: str, model: str, timeout: int = 60):
        if not _anthropic_available:
            raise ImportError("Anthropic 未安装，请运行: pip install anthropic")

        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._client: Anthropic | None = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.ANTHROPIC

    def is_available(self) -> bool:
        return bool(self._api_key) and _anthropic_available

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        if not self.is_available():
            raise SummarizerError("Anthropic API Key 未配置或依赖不可用")

        prompt = self._build_prompt(content.text, max_length=max_length)

        try:
            text, usage = self._call_api(prompt)
        except Exception as e:
            raise SummarizerAPIError(f"Anthropic API 调用失败: {e}") from e

        parsed = self._parse_response(text, style)

        return Summary(
            content=parsed.content,
            key_points=parsed.key_points,
            tags=parsed.tags,
            method=SummaryMethod.ANTHROPIC,
            style=style,
            model_name=self._model,
            input_tokens=int(usage.get("input", 0)),
            output_tokens=int(usage.get("output", 0)),
        )

    def _get_client(self) -> Anthropic:
        if self._client is None:
            self._client = Anthropic(api_key=self._api_key)
        return self._client

    def _build_prompt(self, text: str, max_length: int) -> str:
        # 适配器层只做轻量保护；长文本分块逻辑由 UseCase 负责
        if len(text) > 30000:
            text = text[:30000] + "..."

        return SUMMARY_PROMPT_TEMPLATE.format(max_length=max_length, content=text)

    def _call_api(self, prompt: str) -> tuple[str, dict]:
        client = self._get_client()

        logger.debug(f"调用 Anthropic API: {self._model}")

        # 经验值：中文 500 字摘要通常不会超过 1000 tokens
        message = client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        # message.content 是文本块数组
        blocks = getattr(message, "content", [])
        text_parts: list[str] = []
        for b in blocks:
            t = getattr(b, "text", None)
            if t:
                text_parts.append(str(t))
        text = "\n".join(text_parts).strip()

        usage_obj = getattr(message, "usage", None)
        usage = {
            "input": getattr(usage_obj, "input_tokens", 0) if usage_obj else 0,
            "output": getattr(usage_obj, "output_tokens", 0) if usage_obj else 0,
        }

        return text, usage

    def _parse_response(self, response_text: str, style: SummaryStyle) -> Summary:
        summary_content = response_text

        summary_match = re.search(r"##\s*摘要\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if summary_match:
            summary_content = summary_match.group(1).strip()

        key_points: list[str] = []
        points_match = re.search(r"##\s*关键要点\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if points_match:
            points_text = points_match.group(1)
            key_points = [
                p.strip().lstrip("-•*").strip()
                for p in points_text.split("\n")
                if p.strip() and p.strip().startswith(("-", "•", "*"))
            ]

        tags: list[str] = []
        tags_match = re.search(r"##\s*标签\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if tags_match:
            tags_text = tags_match.group(1)
            tags = re.findall(r"#(\w+)", tags_text)

        return Summary(
            content=summary_content,
            key_points=tuple(key_points),
            tags=tuple(tags),
            method=SummaryMethod.ANTHROPIC,
            style=style,
            model_name=self._model,
        )
