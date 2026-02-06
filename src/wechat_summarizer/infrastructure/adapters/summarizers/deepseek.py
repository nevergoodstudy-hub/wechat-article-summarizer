"""DeepSeek摘要器

DeepSeek 是国产高性能大语言模型，提供与 OpenAI 兼容的 API 接口。
支持 deepseek-chat (DeepSeek V3) 和 deepseek-coder 等模型。

API 文档：https://platform.deepseek.com/api-docs
"""

from __future__ import annotations

import re

from loguru import logger

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ....shared.constants import DEFAULT_DEEPSEEK_BASE_URL
from ....shared.prompts import SUMMARY_PROMPT_TEMPLATE
from ....shared.exceptions import SummarizerAPIError, SummarizerError
from .base import BaseSummarizer

# 延迟导入 OpenAI（DeepSeek 使用兼容的 OpenAI SDK）
_openai_available = True
try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    _openai_available = False


class DeepSeekSummarizer(BaseSummarizer):
    """
    DeepSeek摘要器

    使用 DeepSeek API 生成高质量摘要。
    DeepSeek 提供与 OpenAI 兼容的 API 接口，因此使用 OpenAI SDK 进行调用。
    
    特点：
    - 国产大模型，响应速度快
    - 支持 64K 上下文窗口
    - 性价比高（价格约为 GPT-4 的 1/10）
    - 中文理解能力出色
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = DEFAULT_DEEPSEEK_BASE_URL,
    ):
        if not _openai_available:
            raise ImportError("OpenAI未安装，请运行: pip install openai")

        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client: OpenAI | None = None

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.DEEPSEEK

    def is_available(self) -> bool:
        """检查API密钥是否配置"""
        return bool(self._api_key)

    def _get_client(self) -> OpenAI:
        """获取DeepSeek客户端（使用OpenAI SDK）"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        return self._client

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """使用DeepSeek生成摘要"""
        if not self.is_available():
            raise SummarizerError("DeepSeek API密钥未配置")

        # 构建prompt
        prompt = self._build_prompt(content.text, style, max_length)

        # 调用API
        try:
            response_text, tokens = self._call_api(prompt)
        except Exception as e:
            raise SummarizerAPIError(f"DeepSeek API调用失败: {e}") from e

        # 解析响应
        summary = self._parse_response(response_text, style)

        # 添加token信息
        return Summary(
            content=summary.content,
            key_points=summary.key_points,
            tags=summary.tags,
            method=SummaryMethod.DEEPSEEK,
            style=style,
            model_name=self._model,
            input_tokens=tokens.get("input", 0),
            output_tokens=tokens.get("output", 0),
        )

    def _build_prompt(self, text: str, style: SummaryStyle, max_length: int) -> str:
        """构建prompt"""
        # DeepSeek 支持 64K 上下文
        if len(text) > 50000:
            text = text[:50000] + "..."

        return SUMMARY_PROMPT_TEMPLATE.format(
            max_length=max_length,
            content=text,
        )

    def _call_api(self, prompt: str) -> tuple[str, dict]:
        """调用DeepSeek API"""
        client = self._get_client()

        logger.debug(f"调用DeepSeek API: {self._model}")

        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "你是一个专业的文章摘要助手，擅长提炼文章核心观点。"},
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
        # 与OpenAI类似的解析逻辑
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
            method=SummaryMethod.DEEPSEEK,
            style=style,
            model_name=self._model,
        )
