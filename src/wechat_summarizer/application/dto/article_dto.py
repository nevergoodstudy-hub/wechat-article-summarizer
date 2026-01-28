"""文章数据传输对象"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ArticleDTO:
    """文章DTO - 用于在层之间传输数据"""

    url: str
    title: str = ""
    author: str | None = None
    account_name: str | None = None
    publish_time: str | None = None

    # 内容
    content_text: str = ""
    content_html: str = ""
    word_count: int = 0
    image_count: int = 0

    # 来源
    source_type: str = "web"
    source_platform: str = ""

    # 摘要（如果有）
    summary: "SummaryDTO | None" = None

    # 元数据
    id: str | None = None
    created_at: str | None = None


@dataclass
class SummaryDTO:
    """摘要DTO"""

    content: str
    key_points: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    method: str = "simple"
    style: str = "concise"
    model_name: str | None = None

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class FetchArticleRequest:
    """抓取文章请求"""

    url: str
    use_playwright: bool = False  # 是否使用Playwright渲染


@dataclass
class FetchArticleResponse:
    """抓取文章响应"""

    success: bool
    article: ArticleDTO | None = None
    error: str | None = None


@dataclass
class SummarizeRequest:
    """生成摘要请求"""

    article: ArticleDTO
    method: str = "simple"
    style: str = "concise"
    max_length: int = 500


@dataclass
class SummarizeResponse:
    """生成摘要响应"""

    success: bool
    summary: SummaryDTO | None = None
    error: str | None = None


@dataclass
class ExportRequest:
    """导出请求"""

    article: ArticleDTO
    target: str  # html, markdown, onenote, notion, obsidian
    path: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResponse:
    """导出响应"""

    success: bool
    result: str | None = None  # 文件路径或成功消息
    error: str | None = None


@dataclass
class BatchProcessRequest:
    """批量处理请求"""

    urls: list[str]
    summarize: bool = True
    method: str = "simple"
    export_target: str | None = None
    export_dir: str | None = None


@dataclass
class BatchProcessResponse:
    """批量处理响应"""

    total: int
    success: int
    failed: int
    articles: list[ArticleDTO] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (url, error)
