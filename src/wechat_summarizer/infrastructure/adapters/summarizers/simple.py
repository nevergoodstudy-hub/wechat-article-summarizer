"""简单规则摘要器 - 无需AI"""

import re
from collections import Counter

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from .base import BaseSummarizer


class SimpleSummarizer(BaseSummarizer):
    """
    简单规则摘要器

    基于规则提取文章摘要，无需调用AI API。
    适用于快速预览或API不可用时的回退方案。
    """

    @property
    def name(self) -> str:
        return "simple"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.SIMPLE

    def is_available(self) -> bool:
        """始终可用"""
        return True

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """
        基于规则生成摘要

        策略：
        1. 提取前几段作为摘要
        2. 提取关键句（包含关键词的句子）
        3. 自动提取关键词作为标签
        """
        text = content.text

        # 分段
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

        # 生成摘要内容
        if style == SummaryStyle.BULLET_POINTS:
            summary_content = self._extract_key_sentences(paragraphs, max_length)
        else:
            summary_content = self._extract_first_paragraphs(paragraphs, max_length)

        # 提取关键点
        key_points = self._extract_key_points(paragraphs)

        # 提取标签
        tags = self._extract_tags(text)

        return Summary(
            content=summary_content,
            key_points=tuple(key_points),
            tags=tuple(tags),
            method=SummaryMethod.SIMPLE,
            style=style,
        )

    def _extract_first_paragraphs(self, paragraphs: list[str], max_length: int) -> str:
        """提取前几段作为摘要"""
        result: list[str] = []
        current_length = 0

        for para in paragraphs:
            if current_length + len(para) > max_length:
                # 如果第一段就超长，截断它
                if not result:
                    result.append(para[:max_length] + "...")
                break
            result.append(para)
            current_length += len(para)

        return "\n\n".join(result)

    def _extract_key_sentences(self, paragraphs: list[str], max_length: int) -> str:
        """提取关键句子"""
        # 关键词列表
        keywords = ["重要", "关键", "核心", "总结", "结论", "因此", "所以", "总之", "首先", "其次"]

        key_sentences = []

        for para in paragraphs:
            # 分句
            sentences = re.split(r"[。！？]", para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                # 检查是否包含关键词
                if any(kw in sentence for kw in keywords):
                    key_sentences.append(sentence + "。")

        # 如果没找到关键句，取前几段
        if not key_sentences:
            return self._extract_first_paragraphs(paragraphs, max_length)

        # 组合关键句
        result: list[str] = []
        current_length = 0

        for sentence in key_sentences:
            if current_length + len(sentence) > max_length:
                break
            result.append(sentence)
            current_length += len(sentence)

        return "\n".join(result)

    def _extract_key_points(self, paragraphs: list[str], max_points: int = 5) -> list[str]:
        """提取关键要点"""
        key_points = []

        for para in paragraphs[:10]:  # 只看前10段
            # 查找列表项（以数字或符号开头）
            if re.match(r"^[\d一二三四五六七八九十①②③④⑤][\.\、\)]", para):
                point = re.sub(r"^[\d一二三四五六七八九十①②③④⑤][\.\、\)]", "", para).strip()
                if point and len(point) < 100:
                    key_points.append(point)

            if len(key_points) >= max_points:
                break

        # 如果没找到列表项，提取首句
        if not key_points:
            for para in paragraphs[:max_points]:
                sentences = re.split(r"[。！？]", para)
                if sentences and sentences[0].strip():
                    first_sentence = sentences[0].strip()
                    if len(first_sentence) < 100:
                        key_points.append(first_sentence)

        return key_points[:max_points]

    def _extract_tags(self, text: str, max_tags: int = 5) -> list[str]:
        """提取标签（基于词频）"""
        # 简单的中文分词（基于连续中文字符）
        words = re.findall(r"[\u4e00-\u9fff]{2,4}", text)

        # 停用词
        stopwords = {"的", "是", "在", "有", "和", "与", "了", "等", "也", "都", "而", "及", "或"}

        # 统计词频
        word_counts = Counter(w for w in words if w not in stopwords)

        # 返回高频词
        return [word for word, _ in word_counts.most_common(max_tags)]
