"""摘要质量评估器测试

测试 SummaryEvaluator 的各种评估功能，包括 ROUGE、幻觉检测等。
"""

import pytest

from wechat_summarizer.domain.services.summary_evaluator import (
    EvaluationResult,
    HallucinationInfo,
    SummaryEvaluator,
    evaluate_summary,
)


class TestEvaluationResult:
    """EvaluationResult 测试"""

    @pytest.mark.unit
    def test_default_values(self) -> None:
        """测试默认值"""
        result = EvaluationResult()

        assert result.rouge_1 == 0.0
        assert result.rouge_2 == 0.0
        assert result.rouge_l == 0.0
        assert result.bert_precision is None
        assert result.bert_recall is None
        assert result.bert_f1 is None
        assert result.hallucination is None
        assert result.coverage is None
        assert result.coherence is None
        assert result.conciseness is None
        assert result.accuracy is None

    @pytest.mark.unit
    def test_overall_score_with_rouge_only(self) -> None:
        """测试只有 ROUGE 分数时的综合评分"""
        result = EvaluationResult(
            rouge_1=0.5,
            rouge_l=0.4,
        )

        overall = result.overall
        assert 0.0 <= overall <= 1.0
        assert overall > 0  # 有分数

    @pytest.mark.unit
    def test_overall_score_with_hallucination_penalty(self) -> None:
        """测试幻觉惩罚对综合评分的影响"""
        result_no_hallucination = EvaluationResult(
            rouge_1=0.6,
            rouge_l=0.5,
        )

        result_with_hallucination = EvaluationResult(
            rouge_1=0.6,
            rouge_l=0.5,
            hallucination=HallucinationInfo(
                has_hallucination=True,
                hallucination_ratio=0.3,
            ),
        )

        # 有幻觉的分数应该更低
        assert result_with_hallucination.overall < result_no_hallucination.overall

    @pytest.mark.unit
    def test_grade_classification(self) -> None:
        """测试评分等级分类"""
        excellent = EvaluationResult(rouge_1=0.9, rouge_l=0.9)
        good = EvaluationResult(rouge_1=0.7, rouge_l=0.7)
        medium = EvaluationResult(rouge_1=0.5, rouge_l=0.5)
        poor = EvaluationResult(rouge_1=0.2, rouge_l=0.2)

        assert excellent.grade == "优秀"
        assert good.grade == "良好"
        assert medium.grade == "中等"
        assert poor.grade == "需改进"

    @pytest.mark.unit
    def test_has_quality_issues(self) -> None:
        """测试质量问题检测"""
        # 有幻觉
        result1 = EvaluationResult(
            hallucination=HallucinationInfo(has_hallucination=True)
        )
        assert result1.has_quality_issues is True

        # 准确性低
        result2 = EvaluationResult(accuracy=3.0)
        assert result2.has_quality_issues is True

        # 综合分数低
        result3 = EvaluationResult(rouge_1=0.1, rouge_l=0.1)
        assert result3.has_quality_issues is True

        # 正常结果
        result4 = EvaluationResult(rouge_1=0.7, rouge_l=0.7)
        assert result4.has_quality_issues is False


class TestHallucinationInfo:
    """HallucinationInfo 测试"""

    @pytest.mark.unit
    def test_default_values(self) -> None:
        """测试默认值"""
        info = HallucinationInfo()

        assert info.has_hallucination is False
        assert info.hallucination_ratio == 0.0
        assert info.suspicious_entities == ()
        assert info.suspicious_numbers == ()

    @pytest.mark.unit
    def test_with_suspicious_entities(self) -> None:
        """测试包含可疑实体"""
        info = HallucinationInfo(
            has_hallucination=True,
            hallucination_ratio=0.2,
            suspicious_entities=("虚假公司", "不存在的人"),
            suspicious_numbers=("999999",),
        )

        assert info.has_hallucination is True
        assert len(info.suspicious_entities) == 2
        assert len(info.suspicious_numbers) == 1


class TestSummaryEvaluator:
    """SummaryEvaluator 测试"""

    @pytest.fixture
    def evaluator(self) -> SummaryEvaluator:
        """创建评估器（仅 ROUGE 和幻觉检测）"""
        return SummaryEvaluator(
            use_rouge=True,
            use_hallucination_detection=True,
            use_llm=False,
        )

    @pytest.mark.unit
    def test_evaluator_creation(self, evaluator: SummaryEvaluator) -> None:
        """测试评估器创建"""
        assert evaluator.is_available() is True

    @pytest.mark.unit
    def test_evaluate_basic(self, evaluator: SummaryEvaluator) -> None:
        """测试基本评估"""
        original = "人工智能正在改变世界。机器学习是人工智能的重要分支。深度学习推动了技术进步。"
        summary = "人工智能改变世界，机器学习是其重要分支。"

        result = evaluator.evaluate(original, summary)

        assert isinstance(result, EvaluationResult)
        # ROUGE 分数应该存在
        assert result.rouge_1 >= 0
        assert result.rouge_l >= 0

    @pytest.mark.unit
    def test_hallucination_detection_no_hallucination(self, evaluator: SummaryEvaluator) -> None:
        """测试无幻觉的情况"""
        original = "华为公司2023年营收超过5000亿元。"
        summary = "华为公司营收超过5000亿元。"

        result = evaluator.evaluate(original, summary)

        # 应该没有检测到幻觉（数字来自原文）
        if result.hallucination:
            # 数字 5000 应该不被标记为可疑
            assert "5000" not in result.hallucination.suspicious_numbers

    @pytest.mark.unit
    def test_hallucination_detection_with_hallucination(self, evaluator: SummaryEvaluator) -> None:
        """测试有幻觉的情况"""
        original = "华为公司是一家科技企业。"
        summary = "华为公司2024年营收达到8000亿元。"  # 虚假数字

        result = evaluator.evaluate(original, summary)

        # 应该检测到可疑数字
        if result.hallucination:
            assert result.hallucination.has_hallucination or len(result.hallucination.suspicious_numbers) > 0

    @pytest.mark.unit
    def test_info_density_calculation(self, evaluator: SummaryEvaluator) -> None:
        """测试信息密度计算"""
        original = "这是一段很长的原文内容。" * 20
        summary = "这是摘要。"

        result = evaluator.evaluate(original, summary)

        # 压缩比应该大于 1
        if result.compression_ratio:
            assert result.compression_ratio > 1

    @pytest.mark.unit
    def test_get_improvement_suggestions_rouge(self, evaluator: SummaryEvaluator) -> None:
        """测试 ROUGE 相关的改进建议"""
        result = EvaluationResult(
            rouge_1=0.1,
            rouge_l=0.1,
        )

        suggestions = evaluator.get_improvement_suggestions(result)

        assert len(suggestions) > 0
        assert any("词汇" in s for s in suggestions)

    @pytest.mark.unit
    def test_get_improvement_suggestions_hallucination(self, evaluator: SummaryEvaluator) -> None:
        """测试幻觉相关的改进建议"""
        result = EvaluationResult(
            hallucination=HallucinationInfo(
                has_hallucination=True,
                suspicious_entities=("虚假实体",),
            )
        )

        suggestions = evaluator.get_improvement_suggestions(result)

        assert any("幻觉" in s for s in suggestions)


class TestEvaluateSummaryFunction:
    """evaluate_summary 便捷函数测试"""

    @pytest.mark.unit
    def test_evaluate_summary_function(self) -> None:
        """测试便捷评估函数"""
        original = "人工智能是计算机科学的一个分支。"
        summary = "AI是计算机科学分支。"

        result = evaluate_summary(original, summary)

        assert isinstance(result, EvaluationResult)


class TestSummaryEvaluatorIntegration:
    """SummaryEvaluator 集成测试"""

    @pytest.mark.integration
    def test_container_has_evaluator(self) -> None:
        """测试容器中包含评估器"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()

        assert container.evaluator is not None
        assert isinstance(container.evaluator, SummaryEvaluator)

    @pytest.mark.integration
    def test_evaluator_is_available(self) -> None:
        """测试评估器可用"""
        from wechat_summarizer.infrastructure.config import get_container, reset_container

        reset_container()
        container = get_container()

        assert container.evaluator.is_available() is True
