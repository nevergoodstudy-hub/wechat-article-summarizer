"""智谱 AI（BigModel）摘要器

使用 BigModel 的 Chat Completions HTTP API 生成摘要。

参考：open.bigmodel.cn 文档（chat/completions）。
"""

from __future__ import annotations

import re

import httpx
from loguru import logger

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from ....shared.constants import SUMMARY_PROMPT_TEMPLATE
from ....shared.exceptions import SummarizerAPIError, SummarizerError
from .base import BaseSummarizer


class ZhipuSummarizer(BaseSummarizer):
    """智谱 AI 摘要器"""

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4-flash",
        base_url: str = "https://open.bigmodel.cn",
        timeout: int = 60,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "zhipu"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.ZHIPU

    def is_available(self) -> bool:
        return bool(self._api_key)

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        if not self.is_available():
            raise SummarizerError("智谱 API Key 未配置")

        prompt = self._build_prompt(content.text, max_length=max_length)

        try:
            response_text, usage = self._call_api(prompt)
        except Exception as e:
            raise SummarizerAPIError(f"智谱 API 调用失败: {e}") from e

        parsed = self._parse_response(response_text, style)

        return Summary(
            content=parsed.content,
            key_points=parsed.key_points,
            tags=parsed.tags,
            method=SummaryMethod.ZHIPU,
            style=style,
            model_name=self._model,
            input_tokens=int(usage.get("input", 0)),
            output_tokens=int(usage.get("output", 0)),
        )

    def _build_prompt(self, text: str, max_length: int) -> str:
        # 适配器层只做轻量保护；长文本分块由 UseCase 负责
        if len(text) > 30000:
            text = text[:30000] + "..."

        return SUMMARY_PROMPT_TEMPLATE.format(max_length=max_length, content=text)

    def _call_api(self, prompt: str) -> tuple[str, dict]:
        url = f"{self._base_url}/api/paas/v4/chat/completions"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "你是一个专业的文章摘要助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }

        logger.debug(f"调用智谱 API: {self._model}")

        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(url, headers=headers, json=payload)

        if resp.status_code in (401, 403):
            raise SummarizerError(f"智谱鉴权失败 (HTTP {resp.status_code})")

        if resp.status_code >= 400:
            raise SummarizerAPIError(f"智谱请求失败 (HTTP {resp.status_code}): {resp.text}")

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""

        usage_obj = data.get("usage") or {}
        usage = {
            "input": usage_obj.get("prompt_tokens", 0),
            "output": usage_obj.get("completion_tokens", 0),
        }

        return str(content), usage

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
            method=SummaryMethod.ZHIPU,
            style=style,
            model_name=self._model,
        )
