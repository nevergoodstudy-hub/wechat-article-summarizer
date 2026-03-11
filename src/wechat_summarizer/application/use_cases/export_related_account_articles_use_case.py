"""公众号相关文章导出用例。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ...domain.entities.article import Article
from ...domain.entities.article_list import ArticleListItem
from ...domain.entities.summary import Summary
from ...domain.value_objects.batch_export_options import BatchExportOptions, ExportFormat, LinkFormat
from ...shared.exceptions import ValidationError
from .preview_related_account_articles_use_case import RelatedAccountArticlesPreview

if TYPE_CHECKING:
    from .fetch_article import FetchArticleUseCase
    from .summarize_article import SummarizeArticleUseCase


class LinkExporterProtocol(Protocol):
    """链接导出器协议。"""

    def export_links(
        self,
        items: list[ArticleListItem],
        options: BatchExportOptions,
        account_name: str | None = None,
    ) -> Path:
        """导出链接列表。"""
        ...


class ArticlePackageExporterProtocol(Protocol):
    """文章打包导出器协议。"""

    def export(
        self,
        articles: list[Article],
        output_path: str | Path,
        manifest: dict,
    ) -> Path:
        """打包导出文章内容。"""
        ...


@dataclass(frozen=True)
class RelatedAccountArticleExportFailure:
    """单条相关文章导出失败记录。"""

    title: str
    link: str
    stage: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "link": self.link,
            "stage": self.stage,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RelatedAccountArticlesExportResult:
    """公众号相关文章导出结果。"""

    output_dir: Path
    matched_count: int
    exported_count: int
    link_exports: dict[str, Path]
    search_result_path: Path
    export_report_path: Path
    package_path: Path
    failures: list[RelatedAccountArticleExportFailure]

    @property
    def failed_count(self) -> int:
        return len(self.failures)


class ExportRelatedAccountArticlesUseCase:
    """导出公众号相关文章的链接清单与内容包。"""

    def __init__(
        self,
        *,
        fetch_use_case: FetchArticleUseCase,
        summarize_use_case: SummarizeArticleUseCase,
        link_exporter: LinkExporterProtocol,
        package_exporter: ArticlePackageExporterProtocol,
        output_root: str | Path = "output",
    ) -> None:
        self._fetch_use_case = fetch_use_case
        self._summarize_use_case = summarize_use_case
        self._link_exporter = link_exporter
        self._package_exporter = package_exporter
        self._output_root = Path(output_root)

    def execute(
        self,
        *,
        preview: RelatedAccountArticlesPreview,
        summarizer_method: str | None = None,
    ) -> RelatedAccountArticlesExportResult:
        if preview.matched_count == 0:
            raise ValidationError("没有可导出的相关文章")

        output_dir = self._create_output_dir(preview)
        output_dir.mkdir(parents=True, exist_ok=True)

        link_exports = self._export_links(preview.matched_articles, preview.account.nickname, output_dir)
        search_result_path = self._write_search_result(preview, output_dir)

        exported_articles: list[Article] = []
        failures: list[RelatedAccountArticleExportFailure] = []
        for item in preview.matched_articles:
            article = self._fetch_article(item, failures)
            if article is None:
                continue
            if summarizer_method:
                summary = self._summarize_article(item, article, summarizer_method, failures)
                if summary is None:
                    continue
                article.attach_summary(summary)
            exported_articles.append(article)

        manifest = self._build_manifest(preview, exported_articles, failures)
        package_path = self._package_exporter.export(
            articles=exported_articles,
            output_path=output_dir / "articles.zip",
            manifest=manifest,
        )
        export_report_path = self._write_export_report(
            preview=preview,
            output_dir=output_dir,
            link_exports=link_exports,
            package_path=package_path,
            exported_articles=exported_articles,
            failures=failures,
        )
        return RelatedAccountArticlesExportResult(
            output_dir=output_dir,
            matched_count=preview.matched_count,
            exported_count=len(exported_articles),
            link_exports=link_exports,
            search_result_path=search_result_path,
            export_report_path=export_report_path,
            package_path=package_path,
            failures=failures,
        )

    def _fetch_article(
        self,
        item: ArticleListItem,
        failures: list[RelatedAccountArticleExportFailure],
    ) -> Article | None:
        try:
            return self._fetch_use_case.execute(item.link)
        except Exception as exc:
            failures.append(
                RelatedAccountArticleExportFailure(
                    title=item.title,
                    link=item.link,
                    stage="fetch",
                    reason=str(exc),
                )
            )
            return None

    def _summarize_article(
        self,
        item: ArticleListItem,
        article: Article,
        summarizer_method: str,
        failures: list[RelatedAccountArticleExportFailure],
    ) -> Summary | None:
        try:
            return self._summarize_use_case.execute(article, method=summarizer_method)
        except Exception as exc:
            failures.append(
                RelatedAccountArticleExportFailure(
                    title=item.title,
                    link=item.link,
                    stage="summarize",
                    reason=str(exc),
                )
            )
            return None

    def _export_links(
        self,
        items: list[ArticleListItem],
        account_name: str,
        output_dir: Path,
    ) -> dict[str, Path]:
        csv_path = self._link_exporter.export_links(
            items,
            BatchExportOptions(
                export_format=ExportFormat.CSV,
                output_path=output_dir / "matched_links.csv",
                include_metadata=True,
                include_digest=True,
                timestamp_filename=False,
            ),
            account_name=account_name,
        )
        markdown_path = self._link_exporter.export_links(
            items,
            BatchExportOptions(
                export_format=ExportFormat.MARKDOWN,
                link_format=LinkFormat.MARKDOWN,
                output_path=output_dir / "matched_links.md",
                include_metadata=True,
                include_digest=True,
                timestamp_filename=False,
            ),
            account_name=account_name,
        )
        return {
            "csv": csv_path,
            "markdown": markdown_path,
        }

    def _write_search_result(
        self,
        preview: RelatedAccountArticlesPreview,
        output_dir: Path,
    ) -> Path:
        path = output_dir / "search_result.json"
        path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now().isoformat(),
                    **preview.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def _write_export_report(
        self,
        *,
        preview: RelatedAccountArticlesPreview,
        output_dir: Path,
        link_exports: dict[str, Path],
        package_path: Path,
        exported_articles: list[Article],
        failures: list[RelatedAccountArticleExportFailure],
    ) -> Path:
        path = output_dir / "export_report.json"
        path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now().isoformat(),
                    "account": preview.account.to_dict(),
                    "keyword": preview.keyword,
                    "matched_count": preview.matched_count,
                    "exported_count": len(exported_articles),
                    "failed_count": len(failures),
                    "link_exports": {name: str(export_path) for name, export_path in link_exports.items()},
                    "package_path": str(package_path),
                    "failures": [failure.to_dict() for failure in failures],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _build_manifest(
        preview: RelatedAccountArticlesPreview,
        articles: list[Article],
        failures: list[RelatedAccountArticleExportFailure],
    ) -> dict:
        return {
            "generated_at": datetime.now().isoformat(),
            "account": preview.account.to_dict(),
            "keyword": preview.keyword,
            "matched_count": preview.matched_count,
            "exported_count": len(articles),
            "articles": [
                {
                    "title": article.title,
                    "link": str(article.url),
                    "account_name": article.account_name,
                    "has_summary": article.summary is not None,
                }
                for article in articles
            ],
            "failures": [failure.to_dict() for failure in failures],
        }

    def _create_output_dir(self, preview: RelatedAccountArticlesPreview) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_account = self._sanitize_path_fragment(
            preview.account.alias or preview.account.nickname or preview.account.fakeid
        )
        safe_keyword = self._sanitize_path_fragment(preview.keyword)
        return self._output_root / f"{timestamp}_{safe_account}_{safe_keyword}"

    @staticmethod
    def _sanitize_path_fragment(value: str) -> str:
        sanitized = re.sub(r"[\\/*?:\"<>|]+", "", value).strip()
        sanitized = re.sub(r"\s+", "_", sanitized)
        return sanitized or "untitled"
