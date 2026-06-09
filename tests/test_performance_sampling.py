"""Performance sampling tests for application and GUI paths."""

from __future__ import annotations

from dataclasses import dataclass

from wechat_summarizer.application.use_cases.batch_process import BatchProcessUseCase
from wechat_summarizer.application.use_cases.performance_sampling import PerformanceSampler
from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.presentation.gui import runtime_batch


def test_performance_sampler_records_duration_and_memory() -> None:
    with PerformanceSampler("sampled", metadata={"items": 2}) as sampler:
        _payload = ["x" * 10 for _ in range(5)]

    assert sampler.sample.name == "sampled"
    assert sampler.sample.duration_ms >= 0
    assert sampler.sample.peak_memory_kb >= 0
    assert sampler.sample.to_dict()["metadata"] == {"items": 2}


@dataclass
class _FetchUseCase:
    def execute(self, url: str) -> Article:
        return Article(
            url=ArticleURL.from_string(url),
            title=url.rsplit("/", 1)[-1],
            content=ArticleContent.from_text("content"),
        )


@dataclass
class _SummaryUseCase:
    def execute(self, article: Article, method: str = "simple"):
        return None


@dataclass
class _ExportUseCase:
    def execute(self, article: Article, target: str, path: str | None = None) -> str:
        return f"{target}:{article.title}:{path or ''}"


def test_sync_batch_process_records_performance_sample() -> None:
    use_case = BatchProcessUseCase(_FetchUseCase(), _SummaryUseCase(), _ExportUseCase())

    articles = list(
        use_case.process_urls(
            ["https://mp.weixin.qq.com/s/1", "https://mp.weixin.qq.com/s/2"],
            summarize=False,
        )
    )

    assert len(articles) == 2
    assert use_case.last_process_sample is not None
    assert use_case.last_process_sample.name == "batch_process_urls"
    assert use_case.last_process_sample.metadata["url_count"] == 2
    assert use_case.last_process_sample.metadata["success_count"] == 2
    assert use_case.last_process_sample.duration_ms >= 0


def test_sync_batch_export_records_performance_sample() -> None:
    use_case = BatchProcessUseCase(_FetchUseCase(), _SummaryUseCase(), _ExportUseCase())
    article = Article(
        url=ArticleURL.from_string("https://mp.weixin.qq.com/s/1"),
        title="one",
        content=ArticleContent.from_text("content"),
    )

    result = use_case.export_batch([article], target="markdown", output_dir="out")

    assert result == ["markdown:one:out"]
    assert use_case.last_export_sample is not None
    assert use_case.last_export_sample.name == "batch_export_articles"
    assert use_case.last_export_sample.metadata["article_count"] == 1


class _FakeTimer:
    def __init__(self, calls: list[str]) -> None:
        self._calls = calls

    def __enter__(self) -> _FakeTimer:
        self._calls.append("enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._calls.append("exit")
        return False


class _FakeMonitor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def timer(self, name: str) -> _FakeTimer:
        self.calls.append(name)
        return _FakeTimer(self.calls)


class _FakeVar:
    def get(self) -> str:
        return "simple"


class _FakeRoot:
    def after(self, _delay: int, callback) -> None:
        callback()


class _FakeTracker:
    def __init__(self) -> None:
        self.finished = False

    def finish(self) -> None:
        self.finished = True


class _FakeGUI:
    def __init__(self) -> None:
        self._perf_monitor = _FakeMonitor()
        self.batch_method_var = _FakeVar()
        self.batch_urls: list[str] = []
        self._batch_progress_tracker = _FakeTracker()
        self.root = _FakeRoot()
        self.completed = False

    def _batch_process_complete(self) -> None:
        self.completed = True


def test_gui_batch_worker_records_operation_sample_for_empty_batch() -> None:
    gui = _FakeGUI()

    runtime_batch.batch_process_worker(gui)

    assert gui._perf_monitor.calls == ["gui_batch_process_worker", "enter", "exit"]
    assert gui._batch_progress_tracker.finished is True
    assert gui.completed is True
