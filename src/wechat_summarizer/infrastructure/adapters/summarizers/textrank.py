"""TextRank摘要器 - 基于图算法的抽取式摘要"""

import math
import re
from collections import Counter

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent
from .base import BaseSummarizer


class TextRankSummarizer(BaseSummarizer):
    """
    TextRank摘要器

    基于TextRank算法实现的抽取式文本摘要。
    TextRank是一种基于图的排序算法，类似于PageRank，
    通过计算句子之间的相似度来确定句子的重要性。

    优点：
    - 无需训练数据
    - 无需调用外部API
    - 保持原文表述
    - 适合中文文本
    """

    def __init__(self, damping: float = 0.85, max_iterations: int = 100, threshold: float = 0.0001):
        """
        初始化TextRank摘要器

        Args:
            damping: 阻尼系数，默认0.85（与PageRank相同）
            max_iterations: 最大迭代次数
            threshold: 收敛阈值
        """
        self.damping = damping
        self.max_iterations = max_iterations
        self.threshold = threshold

    @property
    def name(self) -> str:
        return "textrank"

    @property
    def method(self) -> SummaryMethod:
        return SummaryMethod.TEXTRANK

    def is_available(self) -> bool:
        """始终可用（纯Python实现）"""
        return True

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """
        使用TextRank算法生成摘要

        算法步骤：
        1. 将文本分割成句子
        2. 对每个句子进行分词
        3. 计算句子间的相似度（基于词重叠）
        4. 构建相似度图
        5. 运行TextRank迭代
        6. 选择得分最高的句子
        """
        text = content.text

        # 句子分割
        sentences = self._split_sentences(text)
        if not sentences:
            return Summary(
                content="",
                method=SummaryMethod.TEXTRANK,
                style=style,
            )

        # 如果句子太少，直接返回
        if len(sentences) <= 3:
            return Summary(
                content="\n".join(sentences),
                key_points=tuple(sentences),
                method=SummaryMethod.TEXTRANK,
                style=style,
            )

        # 分词
        tokenized_sentences = [self._tokenize(s) for s in sentences]

        # 计算TF-IDF权重
        idf = self._compute_idf(tokenized_sentences)

        # 构建相似度矩阵
        similarity_matrix = self._build_similarity_matrix(tokenized_sentences, idf)

        # 运行TextRank
        scores = self._textrank(similarity_matrix)

        # 选择摘要句子
        summary_content, key_points = self._select_summary_sentences(
            sentences, scores, max_length, style
        )

        # 提取标签
        tags = self._extract_tags(text)

        return Summary(
            content=summary_content,
            key_points=tuple(key_points),
            tags=tuple(tags),
            method=SummaryMethod.TEXTRANK,
            style=style,
        )

    def _split_sentences(self, text: str) -> list[str]:
        """分割句子"""
        # 中文句子分隔符
        pattern = r'[。！？；\n]+'
        sentences = re.split(pattern, text)

        # 清理并过滤
        result = []
        for s in sentences:
            s = s.strip()
            if s and len(s) >= 5:  # 过滤太短的句子
                result.append(s)
        return result

    def _tokenize(self, text: str) -> list[str]:
        """
        简单分词

        使用基于规则的方法：
        1. 提取连续的中文字符（2-4个字符组成的词）
        2. 提取英文单词
        """
        # 中文词（2-4字）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)

        # 英文词
        english_words = re.findall(r'[a-zA-Z]+', text.lower())

        words = chinese_words + english_words

        # 停用词
        stopwords = {
            "的", "是", "在", "有", "和", "与", "了", "等", "也", "都",
            "而", "及", "或", "但", "如", "这", "那", "个", "一", "不",
            "就", "为", "到", "被", "把", "让", "给", "从", "向", "能",
            "会", "可以", "可能", "应该", "需要", "已经", "正在", "将",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "can", "could", "may", "might", "must", "shall", "should",
            "of", "to", "in", "for", "on", "with", "at", "by", "from",
        }

        return [w for w in words if w not in stopwords]

    def _compute_idf(self, tokenized_sentences: list[list[str]]) -> dict[str, float]:
        """计算IDF（逆文档频率）"""
        n_sentences = len(tokenized_sentences)
        if n_sentences == 0:
            return {}

        # 统计每个词出现在多少个句子中
        doc_freq: dict[str, int] = {}
        for tokens in tokenized_sentences:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # 计算IDF
        idf = {}
        for token, freq in doc_freq.items():
            # 使用平滑的IDF公式
            idf[token] = math.log((n_sentences + 1) / (freq + 1)) + 1

        return idf

    def _build_similarity_matrix(
        self, tokenized_sentences: list[list[str]], idf: dict[str, float]
    ) -> list[list[float]]:
        """构建句子相似度矩阵"""
        n = len(tokenized_sentences)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                sim = self._sentence_similarity(
                    tokenized_sentences[i],
                    tokenized_sentences[j],
                    idf
                )
                matrix[i][j] = sim
                matrix[j][i] = sim

        return matrix

    def _sentence_similarity(
        self, sent1: list[str], sent2: list[str], idf: dict[str, float]
    ) -> float:
        """
        计算两个句子的相似度

        使用基于TF-IDF加权的余弦相似度
        """
        if not sent1 or not sent2:
            return 0.0

        # 构建词汇表
        all_words = set(sent1) | set(sent2)

        # 计算TF-IDF向量
        def tfidf_vector(sentence: list[str]) -> dict[str, float]:
            tf = Counter(sentence)
            total = len(sentence)
            return {
                word: (tf.get(word, 0) / total) * idf.get(word, 1.0)
                for word in all_words
            }

        vec1 = tfidf_vector(sent1)
        vec2 = tfidf_vector(sent2)

        # 计算余弦相似度
        dot_product = sum(vec1[w] * vec2[w] for w in all_words)
        norm1 = math.sqrt(sum(v * v for v in vec1.values()))
        norm2 = math.sqrt(sum(v * v for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _textrank(self, similarity_matrix: list[list[float]]) -> list[float]:
        """
        运行TextRank算法

        类似PageRank，通过迭代计算每个句子的重要性分数
        """
        n = len(similarity_matrix)
        if n == 0:
            return []

        # 初始化分数（均匀分布）
        scores = [1.0 / n] * n

        # 计算出度（用于归一化）
        out_sum = []
        for i in range(n):
            s = sum(similarity_matrix[i])
            out_sum.append(s if s > 0 else 1.0)

        # 迭代直到收敛
        for _ in range(self.max_iterations):
            prev_scores = scores[:]

            for i in range(n):
                # 计算入度贡献
                rank_sum = 0.0
                for j in range(n):
                    if i != j and similarity_matrix[j][i] > 0:
                        rank_sum += similarity_matrix[j][i] * prev_scores[j] / out_sum[j]

                # TextRank公式
                scores[i] = (1 - self.damping) / n + self.damping * rank_sum

            # 检查收敛
            diff = sum(abs(scores[i] - prev_scores[i]) for i in range(n))
            if diff < self.threshold:
                break

        return scores

    def _select_summary_sentences(
        self,
        sentences: list[str],
        scores: list[float],
        max_length: int,
        style: SummaryStyle
    ) -> tuple[str, list[str]]:
        """选择摘要句子"""
        # 将句子与分数配对，并按分数排序
        scored_sentences = list(zip(range(len(sentences)), scores, sentences))
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # 根据风格确定要选择的句子数量
        if style == SummaryStyle.CONCISE:
            target_ratio = 0.2  # 选择20%的句子
        elif style == SummaryStyle.DETAILED:
            target_ratio = 0.4  # 选择40%的句子
        else:
            target_ratio = 0.3  # 默认30%

        max_sentences = max(3, int(len(sentences) * target_ratio))

        # 选择句子（按原文顺序重排）
        selected = []
        current_length = 0
        key_points = []

        for idx, score, sentence in scored_sentences:
            if len(selected) >= max_sentences:
                break
            if current_length + len(sentence) > max_length:
                if not selected:  # 确保至少有一个句子
                    selected.append((idx, sentence[:max_length] + "..."))
                    key_points.append(sentence[:50] + "...")
                break

            selected.append((idx, sentence))
            key_points.append(sentence if len(sentence) <= 50 else sentence[:47] + "...")
            current_length += len(sentence) + 1  # +1 for newline

        # 按原文顺序排序
        selected.sort(key=lambda x: x[0])

        # 组装摘要
        if style == SummaryStyle.BULLET_POINTS:
            summary_content = "\n".join(f"• {s}" for _, s in selected)
        else:
            summary_content = "。".join(s for _, s in selected)
            if summary_content and not summary_content.endswith("。"):
                summary_content += "。"

        return summary_content, key_points[:5]  # 最多5个关键点

    def _extract_tags(self, text: str, max_tags: int = 5) -> list[str]:
        """提取标签（基于词频和位置）"""
        words = self._tokenize(text)
        if not words:
            return []

        # 统计词频
        word_counts = Counter(words)

        # 给出现在开头的词更高权重
        first_words = set(words[:min(50, len(words))])
        weighted_counts = {}
        for word, count in word_counts.items():
            weight = 1.5 if word in first_words else 1.0
            weighted_counts[word] = count * weight

        # 按加权频率排序
        sorted_words = sorted(weighted_counts.items(), key=lambda x: x[1], reverse=True)

        return [word for word, _ in sorted_words[:max_tags]]
