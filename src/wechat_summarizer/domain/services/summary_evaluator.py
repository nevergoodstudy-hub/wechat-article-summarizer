"""摘要质量评估服务

实现多种评估指标：
- ROUGE: 词汇覆盖评估
- BERTScore: 语义相似度评估
- 幻觉检测: 检测摘要中不存在于原文的信息
- LLM-as-Judge: 使用 LLM 进行多维度评估
- 信息密度: 评估摘要的信息压缩率

可选依赖：
- rouge-score: pip install rouge-score
- bert-score: pip install bert-score (GPU 推荐)
- jieba: pip install jieba (中文分词)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from ...application.ports.outbound import SummarizerPort

# 检查 rouge-score 是否可用
_rouge_available = False
try:
    from rouge_score import rouge_scorer

    _rouge_available = True
except ImportError:
    pass

# 检查 bert-score 是否可用
_bert_score_available = False
try:
    from bert_score import score as bert_score_fn

    _bert_score_available = True
except ImportError:
    pass

# 检查 jieba 是否可用
_jieba_available = False
try:
    import jieba

    _jieba_available = True
except ImportError:
    pass


@dataclass
class HallucinationInfo:
    """幻觉检测结果"""

    has_hallucination: bool = False
    """是否检测到幻觉"""

    hallucination_ratio: float = 0.0
    """幻觉比例（不在原文中的实体比例）"""

    suspicious_entities: tuple[str, ...] = field(default_factory=tuple)
    """可疑实体（出现在摘要但不在原文中）"""

    suspicious_numbers: tuple[str, ...] = field(default_factory=tuple)
    """可疑数字（摘要中的数字与原文不匹配）"""


@dataclass
class EvaluationResult:
    """评估结果"""

    # ROUGE 分数（F1）
    rouge_1: float = 0.0  # ROUGE-1 (unigram)
    rouge_2: float = 0.0  # ROUGE-2 (bigram)
    rouge_l: float = 0.0  # ROUGE-L (longest common subsequence)

    # BERTScore 分数
    bert_precision: float | None = None  # BERTScore 精确率
    bert_recall: float | None = None  # BERTScore 召回率
    bert_f1: float | None = None  # BERTScore F1

    # 幻觉检测
    hallucination: HallucinationInfo | None = None

    # 信息密度指标
    compression_ratio: float | None = None  # 压缩比（原文长度/摘要长度）
    keyword_coverage: float | None = None  # 关键词覆盖率
    info_density: float | None = None  # 信息密度（关键词数/摘要长度）

    # LLM 评估分数（0-10）
    coverage: float | None = None  # 覆盖度：摘要是否覆盖原文关键信息
    coherence: float | None = None  # 连贯性：摘要是否流畅连贯
    conciseness: float | None = None  # 简洁性：摘要是否简洁无冗余
    accuracy: float | None = None  # 准确性：摘要是否有事实错误/幻觉

    # LLM 评估反馈
    llm_feedback: str | None = None

    @property
    def overall(self) -> float:
        """综合评分（0-1）"""
        scores: list[float] = []
        weights: list[float] = []

        # ROUGE 分数 (20%)
        rouge_scores = [self.rouge_1, self.rouge_l]
        if any(s > 0 for s in rouge_scores):
            scores.append(sum(rouge_scores) / len(rouge_scores))
            weights.append(0.2)

        # BERTScore (20%)
        if self.bert_f1 is not None:
            scores.append(self.bert_f1)
            weights.append(0.2)

        # 幻觉惩罚 (-10% ~ 0)
        hallucination_penalty = 0.0
        if self.hallucination and self.hallucination.has_hallucination:
            hallucination_penalty = min(self.hallucination.hallucination_ratio * 0.5, 0.3)

        # LLM 评估 (40%)
        llm_scores = [
            s / 10.0 for s in [self.coverage, self.coherence, self.conciseness, self.accuracy]
            if s is not None
        ]
        if llm_scores:
            scores.append(sum(llm_scores) / len(llm_scores))
            weights.append(0.4)

        if not scores:
            return 0.0

        # 归一化权重
        total_weight = sum(weights)
        weighted_score = sum(s * w / total_weight for s, w in zip(scores, weights))

        # 应用幻觉惩罚
        return max(0.0, weighted_score - hallucination_penalty)

    @property
    def grade(self) -> str:
        """评分等级"""
        score = self.overall
        if score >= 0.8:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "中等"
        else:
            return "需改进"

    @property
    def has_quality_issues(self) -> bool:
        """是否有质量问题"""
        if self.hallucination and self.hallucination.has_hallucination:
            return True
        if self.accuracy is not None and self.accuracy < 5:
            return True
        if self.overall < 0.4:
            return True
        return False


class SummaryEvaluator:
    """
    摘要质量评估器

    支持多种评估方式：
    - ROUGE: 词汇覆盖评估
    - BERTScore: 语义相似度评估
    - 幻觉检测: 检测摘要中不存在于原文的信息
    - LLM-as-Judge: 使用 LLM 进行多维度评估
    """

    # LLM 评估提示词
    LLM_EVALUATION_PROMPT = """请评估以下摘要的质量。

原文（部分）：
{original}

摘要：
{summary}

请从以下四个维度进行评分（0-10分）：
1. 覆盖度（Coverage）：摘要是否覆盖了原文的关键信息和主要观点
2. 连贯性（Coherence）：摘要是否流畅、逻辑清晰、易于理解
3. 简洁性（Conciseness）：摘要是否简洁、无冗余信息
4. 准确性（Accuracy）：摘要是否准确、无事实错误或幻觉

请按以下 JSON 格式返回评估结果：
{{
    "coverage": <分数>,
    "coherence": <分数>,
    "conciseness": <分数>,
    "accuracy": <分数>,
    "feedback": "<简短的改进建议>"
}}

只返回 JSON，不要有其他内容。"""

    # 中文实体正则（用于幻觉检测）
    _ENTITY_PATTERNS = [
        r'[一-龥]{2,4}公司',  # 公司名
        r'[一-龥]{2,3}(?:市|省|区|县)',  # 地名
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # 英文人名/专有名词
        r'\d{4}年\d{1,2}月\d{1,2}日',  # 日期
        r'\d+(?:\.\d+)?(?:%|万|亿|元)',  # 数字+单位
    ]

    def __init__(
        self,
        summarizer: "SummarizerPort | None" = None,
        use_rouge: bool = True,
        use_bert_score: bool = False,
        use_hallucination_detection: bool = True,
        use_llm: bool = False,
        bert_model: str = "bert-base-chinese",
    ):
        """
        Args:
            summarizer: 用于 LLM 评估的摘要器（可选）
            use_rouge: 是否使用 ROUGE 评估
            use_bert_score: 是否使用 BERTScore 评估
            use_hallucination_detection: 是否进行幻觉检测
            use_llm: 是否使用 LLM 评估
            bert_model: BERTScore 使用的模型
        """
        self._summarizer = summarizer
        self._use_rouge = use_rouge and _rouge_available
        self._use_bert_score = use_bert_score and _bert_score_available
        self._use_hallucination = use_hallucination_detection
        self._use_llm = use_llm and summarizer is not None
        self._bert_model = bert_model

        if self._use_rouge:
            self._rouge_scorer = rouge_scorer.RougeScorer(
                ["rouge1", "rouge2", "rougeL"],
                use_stemmer=False,  # 中文不需要词干提取
            )
        else:
            self._rouge_scorer = None

    def is_available(self) -> bool:
        """检查评估器是否可用"""
        return self._use_rouge or self._use_bert_score or self._use_llm or self._use_hallucination

    def evaluate(
        self,
        original: str,
        summary: str,
        use_llm: bool | None = None,
        use_bert_score: bool | None = None,
    ) -> EvaluationResult:
        """
        评估摘要质量

        Args:
            original: 原文内容
            summary: 摘要内容
            use_llm: 是否使用 LLM 评估（覆盖初始化设置）
            use_bert_score: 是否使用 BERTScore（覆盖初始化设置）

        Returns:
            评估结果
        """
        result = EvaluationResult()

        # 计算信息密度指标
        result = self._evaluate_info_density(original, summary, result)

        # ROUGE 评估
        if self._use_rouge and self._rouge_scorer:
            result = self._evaluate_rouge(original, summary, result)

        # BERTScore 评估
        should_use_bert = use_bert_score if use_bert_score is not None else self._use_bert_score
        if should_use_bert and _bert_score_available:
            result = self._evaluate_bert_score(original, summary, result)

        # 幻觉检测
        if self._use_hallucination:
            result = self._detect_hallucination(original, summary, result)

        # LLM 评估
        should_use_llm = use_llm if use_llm is not None else self._use_llm
        if should_use_llm and self._summarizer:
            result = self._evaluate_llm(original, summary, result)

        return result

    def _evaluate_info_density(
        self,
        original: str,
        summary: str,
        result: EvaluationResult,
    ) -> EvaluationResult:
        """计算信息密度指标"""
        try:
            # 压缩比
            if len(summary) > 0:
                result.compression_ratio = len(original) / len(summary)
            else:
                result.compression_ratio = 0.0

            # 关键词覆盖率（需要 jieba）
            if _jieba_available:
                # 提取原文关键词
                original_words = set(jieba.analyse.extract_tags(original, topK=20))
                summary_words = set(jieba.analyse.extract_tags(summary, topK=20))

                if original_words:
                    covered = len(original_words & summary_words)
                    result.keyword_coverage = covered / len(original_words)

                    # 信息密度 = 覆盖的关键词数 / 摘要长度 * 100
                    if len(summary) > 0:
                        result.info_density = (covered / len(summary)) * 100

            logger.debug(
                f"信息密度: compression={result.compression_ratio:.1f}x, "
                f"keyword_coverage={result.keyword_coverage:.2%}" if result.keyword_coverage else ""
            )
        except Exception as e:
            logger.warning(f"信息密度计算失败: {e}")

        return result

    def _evaluate_rouge(
        self,
        original: str,
        summary: str,
        result: EvaluationResult,
    ) -> EvaluationResult:
        """ROUGE 评估"""
        try:
            scores = self._rouge_scorer.score(original, summary)

            result.rouge_1 = scores["rouge1"].fmeasure
            result.rouge_2 = scores["rouge2"].fmeasure
            result.rouge_l = scores["rougeL"].fmeasure

            logger.debug(
                f"ROUGE 评估: R1={result.rouge_1:.3f}, R2={result.rouge_2:.3f}, RL={result.rouge_l:.3f}"
            )
        except Exception as e:
            logger.warning(f"ROUGE 评估失败: {e}")

        return result

    def _evaluate_bert_score(
        self,
        original: str,
        summary: str,
        result: EvaluationResult,
    ) -> EvaluationResult:
        """BERTScore 评估（语义相似度）"""
        try:
            # 截断文本（BERTScore 对长文本耗时）
            max_len = 1000
            original_truncated = original[:max_len]
            summary_truncated = summary[:max_len]

            # 计算 BERTScore
            P, R, F1 = bert_score_fn(
                [summary_truncated],
                [original_truncated],
                model_type=self._bert_model,
                lang="zh",
                verbose=False,
            )

            result.bert_precision = float(P[0])
            result.bert_recall = float(R[0])
            result.bert_f1 = float(F1[0])

            logger.debug(
                f"BERTScore: P={result.bert_precision:.3f}, R={result.bert_recall:.3f}, F1={result.bert_f1:.3f}"
            )
        except Exception as e:
            logger.warning(f"BERTScore 评估失败: {e}")

        return result

    def _detect_hallucination(
        self,
        original: str,
        summary: str,
        result: EvaluationResult,
    ) -> EvaluationResult:
        """幻觉检测：检测摘要中不存在于原文的实体和数字"""
        try:
            suspicious_entities: list[str] = []
            suspicious_numbers: list[str] = []

            # 提取原文中的实体
            original_entities: set[str] = set()
            for pattern in self._ENTITY_PATTERNS:
                original_entities.update(re.findall(pattern, original))

            # 提取原文中的数字
            original_numbers = set(re.findall(r'\d+(?:\.\d+)?', original))

            # 检查摘要中的实体
            for pattern in self._ENTITY_PATTERNS:
                summary_entities = re.findall(pattern, summary)
                for entity in summary_entities:
                    # 检查实体是否在原文中出现
                    if entity not in original and entity not in original_entities:
                        # 模糊匹配：检查是否部分匹配
                        if not any(entity in e or e in entity for e in original_entities):
                            suspicious_entities.append(entity)

            # 检查摘要中的数字
            summary_numbers = re.findall(r'\d+(?:\.\d+)?', summary)
            for num in summary_numbers:
                if num not in original_numbers and len(num) > 1:  # 忽略单个数字
                    suspicious_numbers.append(num)

            # 计算幻觉比例
            total_entities = len(re.findall(r'[\u4e00-\u9fa5]{2,}', summary)) + len(summary_numbers)
            hallucination_count = len(suspicious_entities) + len(suspicious_numbers)

            hallucination_ratio = (
                hallucination_count / max(total_entities, 1)
            )

            result.hallucination = HallucinationInfo(
                has_hallucination=len(suspicious_entities) > 0 or len(suspicious_numbers) > 0,
                hallucination_ratio=hallucination_ratio,
                suspicious_entities=tuple(suspicious_entities[:10]),  # 限制数量
                suspicious_numbers=tuple(suspicious_numbers[:10]),
            )

            if result.hallucination.has_hallucination:
                logger.warning(
                    f"检测到可能的幻觉: 实体={suspicious_entities[:3]}, 数字={suspicious_numbers[:3]}"
                )

        except Exception as e:
            logger.warning(f"幻觉检测失败: {e}")

        return result

    def _evaluate_llm(
        self,
        original: str,
        summary: str,
        result: EvaluationResult,
    ) -> EvaluationResult:
        """LLM 评估"""
        import json

        try:
            # 截断原文（避免超出 token 限制）
            max_original_len = 3000
            truncated_original = original[:max_original_len]
            if len(original) > max_original_len:
                truncated_original += "...[已截断]"

            prompt = self.LLM_EVALUATION_PROMPT.format(
                original=truncated_original,
                summary=summary,
            )

            # 使用摘要器生成评估
            llm_result = self._summarizer.summarize(prompt)
            response_text = llm_result.content if hasattr(llm_result, "content") else str(llm_result)

            # 解析 JSON 响应
            # 尝试提取 JSON
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)

                result.coverage = float(data.get("coverage", 0))
                result.coherence = float(data.get("coherence", 0))
                result.conciseness = float(data.get("conciseness", 0))
                result.accuracy = float(data.get("accuracy", 0))
                result.llm_feedback = data.get("feedback", "")

                logger.debug(
                    f"LLM 评估: coverage={result.coverage}, coherence={result.coherence}, "
                    f"conciseness={result.conciseness}, accuracy={result.accuracy}"
                )

        except json.JSONDecodeError as e:
            logger.warning(f"LLM 评估响应解析失败: {e}")
        except Exception as e:
            logger.warning(f"LLM 评估失败: {e}")

        return result

    def get_improvement_suggestions(self, result: EvaluationResult) -> list[str]:
        """根据评估结果生成改进建议"""
        suggestions: list[str] = []

        # ROUGE 相关
        if result.rouge_1 < 0.3:
            suggestions.append("摘要与原文词汇重叠度低，建议提取更多原文关键词")

        if result.rouge_l < 0.2:
            suggestions.append("摘要结构与原文差异较大，建议保持更多原文的表达方式")

        # BERTScore 相关
        if result.bert_f1 is not None and result.bert_f1 < 0.6:
            suggestions.append("语义相似度较低，建议摘要更准确地反映原文含义")

        # 幻觉检测相关
        if result.hallucination and result.hallucination.has_hallucination:
            suggestions.append(
                f"⚠️ 检测到可能的幻觉内容，请核实以下信息："
            )
            if result.hallucination.suspicious_entities:
                suggestions.append(
                    f"  - 可疑实体: {', '.join(result.hallucination.suspicious_entities[:5])}"
                )
            if result.hallucination.suspicious_numbers:
                suggestions.append(
                    f"  - 可疑数字: {', '.join(result.hallucination.suspicious_numbers[:5])}"
                )

        # 信息密度相关
        if result.keyword_coverage is not None and result.keyword_coverage < 0.3:
            suggestions.append("关键词覆盖率低，建议纳入更多原文核心关键词")

        if result.compression_ratio is not None and result.compression_ratio < 3:
            suggestions.append("摘要压缩比低，建议进一步精简内容")

        # LLM 评估相关
        if result.coverage is not None and result.coverage < 6:
            suggestions.append("覆盖度不足，建议确保摘要包含原文的核心观点")

        if result.coherence is not None and result.coherence < 6:
            suggestions.append("连贯性不足，建议优化摘要的逻辑结构和过渡")

        if result.conciseness is not None and result.conciseness < 6:
            suggestions.append("简洁性不足，建议删除冗余信息，精简表达")

        if result.accuracy is not None and result.accuracy < 6:
            suggestions.append("准确性不足，建议核实摘要内容是否与原文一致")

        if result.llm_feedback:
            suggestions.append(f"LLM 建议：{result.llm_feedback}")

        return suggestions


# 便捷函数
def evaluate_summary(
    original: str,
    summary: str,
    use_llm: bool = False,
    summarizer: "SummarizerPort | None" = None,
) -> EvaluationResult:
    """快捷评估函数"""
    evaluator = SummaryEvaluator(summarizer=summarizer, use_llm=use_llm)
    return evaluator.evaluate(original, summary)
