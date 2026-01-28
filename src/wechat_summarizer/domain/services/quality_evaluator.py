"""摘要质量评估器"""

from __future__ import annotations

from dataclasses import dataclass

from ..entities import Article, Summary


@dataclass
class QualityScore:
    """摘要质量评分"""

    completeness: float  # 完整性 0-1
    conciseness: float  # 简洁性 0-1
    coherence: float  # 连贯性 0-1
    overall: float  # 总分 0-1

    def to_dict(self) -> dict[str, float]:
        return {
            "completeness": self.completeness,
            "conciseness": self.conciseness,
            "coherence": self.coherence,
            "overall": self.overall,
        }


class SummaryQualityEvaluator:
    """
    摘要质量评估器

    使用启发式规则评估摘要质量。
    """

    def evaluate(self, article: Article, summary: Summary) -> QualityScore:
        """
        评估摘要质量

        Args:
            article: 原始文章
            summary: 生成的摘要

        Returns:
            质量评分
        """
        completeness = self._evaluate_completeness(article.content_text, summary.content)
        conciseness = self._evaluate_conciseness(article.content_text, summary.content)
        coherence = self._evaluate_coherence(summary.content)

        overall = (completeness + conciseness + coherence) / 3

        return QualityScore(
            completeness=completeness,
            conciseness=conciseness,
            coherence=coherence,
            overall=overall,
        )

    def _evaluate_completeness(self, original: str, summary: str) -> float:
        """
        评估完整性

        基于关键词覆盖率评估摘要是否涵盖了原文的主要内容。
        """
        if not original or not summary:
            return 0.0

        # 提取原文关键词（简单实现：高频词）
        original_words = set(self._extract_keywords(original))
        summary_words = set(self._extract_keywords(summary))

        if not original_words:
            return 1.0

        # 计算覆盖率
        coverage = len(original_words & summary_words) / len(original_words)
        return min(coverage * 2, 1.0)  # 放大覆盖率，50%覆盖=1.0

    def _evaluate_conciseness(self, original: str, summary: str) -> float:
        """
        评估简洁性

        基于压缩比评估摘要是否足够简洁。
        """
        if not original:
            return 1.0

        original_len = len(original)
        summary_len = len(summary)

        if summary_len == 0:
            return 0.0

        # 理想压缩比在 5%-20% 之间
        ratio = summary_len / original_len

        if ratio <= 0.05:
            return 0.5  # 太短
        elif ratio <= 0.20:
            return 1.0  # 理想
        elif ratio <= 0.40:
            return 0.7  # 稍长
        else:
            return 0.3  # 太长

    def _evaluate_coherence(self, summary: str) -> float:
        """
        评估连贯性

        基于句子结构评估摘要是否通顺连贯。
        """
        if not summary:
            return 0.0

        # 简单实现：检查是否有完整句子
        sentences = [s.strip() for s in summary.split("。") if s.strip()]

        if not sentences:
            return 0.5

        # 检查句子平均长度（太短或太长都不好）
        avg_len = sum(len(s) for s in sentences) / len(sentences)

        if 10 <= avg_len <= 100:
            return 1.0
        elif 5 <= avg_len <= 150:
            return 0.7
        else:
            return 0.4

    def _extract_keywords(self, text: str, top_n: int = 20) -> list[str]:
        """
        提取关键词（简单实现）

        过滤停用词，按词频排序取前N个。
        """
        # 简单分词（按非汉字/字母分割）
        import re

        words = re.findall(r"[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}", text)

        # 简单停用词列表
        stopwords = {
            "的", "是", "在", "了", "和", "与", "或", "但", "而", "这", "那",
            "有", "为", "以", "及", "等", "也", "都", "就", "对", "到", "被",
            "让", "把", "从", "向", "于", "给", "上", "下", "中", "内", "外",
            "the", "is", "are", "was", "were", "and", "or", "but", "for",
        }

        # 过滤停用词并统计词频
        word_freq: dict[str, int] = {}
        for word in words:
            if word.lower() not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 按词频排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return [word for word, _ in sorted_words[:top_n]]
