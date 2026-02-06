"""Ollama本地LLM摘要器"""

import re

import httpx
from loguru import logger

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ....shared.prompts import SUMMARY_PROMPT_TEMPLATE
from ....shared.exceptions import SummarizerAPIError, SummarizerError
from .base import BaseSummarizer


class OllamaSummarizer(BaseSummarizer):
    """
    Ollama本地LLM摘要器

    使用本地部署的Ollama服务生成摘要。
    支持qwen2.5、llama3、mistral等模型。
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout: int = 120,
    ):
        self._host = host.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._api_url = f"{self._host}/api/generate"

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.OLLAMA

    def is_available(self) -> bool:
        """检查Ollama服务是否在线"""
        try:
            response = httpx.get(f"{self._host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """使用Ollama生成摘要"""
        if not self.is_available():
            raise SummarizerError("Ollama服务不可用")

        # 构建prompt
        prompt = self._build_prompt(content.text, style, max_length)

        # 调用API
        try:
            response_text = self._call_api(prompt)
        except Exception as e:
            raise SummarizerAPIError(f"Ollama API调用失败: {e}") from e

        # 解析响应
        return self._parse_response(response_text, style)

    def _build_prompt(self, text: str, style: SummaryStyle, max_length: int) -> str:
        """构建prompt"""
        # 截断过长的文本
        if len(text) > 8000:
            text = text[:8000] + "..."

        return SUMMARY_PROMPT_TEMPLATE.format(
            max_length=max_length,
            content=text,
        )

    def _call_api(self, prompt: str) -> str:
        """调用Ollama API"""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
            },
        }

        logger.debug(f"调用Ollama API: {self._model}")

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(self._api_url, json=payload)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, dict):
                return str(data.get("response", "") or "")
            return ""

    def _parse_response(self, response_text: str, style: SummaryStyle) -> Summary:
        """解析LLM响应"""
        # 提取摘要部分
        summary_content = response_text

        # 尝试提取结构化内容
        summary_match = re.search(r"##\s*摘要\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if summary_match:
            summary_content = summary_match.group(1).strip()

        # 提取关键要点
        key_points = []
        points_match = re.search(r"##\s*关键要点\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if points_match:
            points_text = points_match.group(1)
            key_points = [
                p.strip().lstrip("-•*").strip()
                for p in points_text.split("\n")
                if p.strip() and p.strip().startswith(("-", "•", "*"))
            ]

        # 提取标签
        tags = []
        tags_match = re.search(r"##\s*标签\s*\n(.*?)(?=##|$)", response_text, re.DOTALL)
        if tags_match:
            tags_text = tags_match.group(1)
            tags = re.findall(r"#(\w+)", tags_text)

        return Summary(
            content=summary_content,
            key_points=tuple(key_points),
            tags=tuple(tags),
            method=SummaryMethod.OLLAMA,
            style=style,
            model_name=self._model,
        )
