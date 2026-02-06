"""OpenAI摘要器"""

from __future__ import annotations

import re

from loguru import logger

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ....shared.prompts import SUMMARY_PROMPT_TEMPLATE
from ....shared.exceptions import SummarizerAPIError, SummarizerError
from .base import BaseSummarizer

# 延迟导入 OpenAI（作为可选依赖）
_openai_available = True
try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    _openai_available = False


class OpenAISummarizer(BaseSummarizer):
    """
    OpenAI摘要器

    使用OpenAI API (GPT系列) 生成高质量摘要。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ):
        if not _openai_available:
            raise ImportError("OpenAI未安装，请运行: pip install openai")

        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client: OpenAI | None = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.OPENAI

    def is_available(self) -> bool:
        """检查API密钥是否配置"""
        return bool(self._api_key)

    def _get_client(self) -> OpenAI:
        """获取OpenAI客户端"""
        if self._client is None:
            kwargs = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """使用OpenAI生成摘要"""
        if not self.is_available():
            raise SummarizerError("OpenAI API密钥未配置")

        # 构建prompt
        prompt = self._build_prompt(content.text, style, max_length)

        # 调用API
        try:
            response_text, tokens = self._call_api(prompt)
        except Exception as e:
            raise SummarizerAPIError(f"OpenAI API调用失败: {e}") from e

        # 解析响应
        summary = self._parse_response(response_text, style)

        # 添加token信息
        return Summary(
            content=summary.content,
            key_points=summary.key_points,
            tags=summary.tags,
            method=SummaryMethod.OPENAI,
            style=style,
            model_name=self._model,
            input_tokens=tokens.get("input", 0),
            output_tokens=tokens.get("output", 0),
        )

    def _build_prompt(self, text: str, style: SummaryStyle, max_length: int) -> str:
        """构建prompt"""
        # OpenAI有更大的上下文窗口
        if len(text) > 30000:
            text = text[:30000] + "..."

        return SUMMARY_PROMPT_TEMPLATE.format(
            max_length=max_length,
            content=text,
        )

    def _call_api(self, prompt: str) -> tuple[str, dict]:
        """调用OpenAI API"""
        client = self._get_client()

        logger.debug(f"调用OpenAI API: {self._model}")

        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是一个专业的文章摘要助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""
        tokens = {
            "input": response.usage.prompt_tokens if response.usage else 0,
            "output": response.usage.completion_tokens if response.usage else 0,
        }

        return content, tokens

    def _parse_response(self, response_text: str, style: SummaryStyle) -> Summary:
        """解析LLM响应"""
        # 与Ollama类似的解析逻辑
        summary_content = response_text

        summary_match = re.search(r"##\s*摘要\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if summary_match:
            summary_content = summary_match.group(1).strip()

        key_points = []
        points_match = re.search(r"##\s*关键要点\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if points_match:
            points_text = points_match.group(1)
            key_points = [
                p.strip().lstrip("-•*").strip()
                for p in points_text.split("\n")
                if p.strip() and p.strip().startswith(("-", "•", "*"))
            ]

        tags = []
        tags_match = re.search(r"##\s*标签\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if tags_match:
            tags_text = tags_match.group(1)
            tags = re.findall(r"#(\w+)", tags_text)

        return Summary(
            content=summary_content,
            key_points=tuple(key_points),
            tags=tuple(tags),
            method=SummaryMethod.OPENAI,
            style=style,
            model_name=self._model,
        )
