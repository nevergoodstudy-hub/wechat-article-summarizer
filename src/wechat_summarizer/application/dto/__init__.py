"""数据传输对象"""

from .article_dto import (
    ArticleDTO,
    BatchProcessRequest,
    BatchProcessResponse,
    ExportRequest,
    ExportResponse,
    FetchArticleRequest,
    FetchArticleResponse,
    SummarizeRequest,
    SummarizeResponse,
    SummaryDTO,
)

__all__ = [
    "ArticleDTO",
    "SummaryDTO",
    "FetchArticleRequest",
    "FetchArticleResponse",
    "SummarizeRequest",
    "SummarizeResponse",
    "ExportRequest",
    "ExportResponse",
    "BatchProcessRequest",
    "BatchProcessResponse",
]
