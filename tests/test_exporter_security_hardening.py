from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from wechat_summarizer.infrastructure.adapters.exporters.word import WordExporter
from wechat_summarizer.infrastructure.adapters.exporters.zip_exporter import ZipExporter


@pytest.mark.unit
def test_zip_index_escapes_article_titles(sample_article) -> None:
    object.__setattr__(sample_article, "title", '<script>alert("xss")</script>')
    exporter = ZipExporter()

    index_html = exporter._generate_index([sample_article])

    assert '<script>alert("xss")</script>' not in index_html
    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;" in index_html


@pytest.mark.unit
def test_zip_exporter_uses_safe_fetch_for_remote_images(sample_article) -> None:
    exporter = ZipExporter(download_images=True)
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b"fake-image"
    mock_response.headers = {"content-type": "image/png"}

    with patch(
        "wechat_summarizer.infrastructure.adapters.exporters.zip_exporter.safe_fetch_sync",
        return_value=mock_response,
    ) as mock_fetch:
        html_content, image_files = exporter._process_images(
            '<img src="https://example.com/image1.jpg">',
            sample_article.content.images,
            "001_test",
            base_url=str(sample_article.url),
        )

    assert "images/001_test_img_1.png" in html_content
    assert "001_test_img_1.png" in image_files
    mock_fetch.assert_called_once()


@pytest.mark.unit
def test_word_exporter_uses_safe_fetch_for_remote_images() -> None:
    exporter = WordExporter()
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b"\x89PNG\r\n\x1a\n"
    mock_response.headers = {"content-type": "image/png"}

    html_content = '<html><body><img src="https://example.com/image.png" /></body></html>'

    with patch(
        "wechat_summarizer.infrastructure.adapters.exporters.word.safe_fetch_sync",
        return_value=mock_response,
    ) as mock_fetch:
        result = exporter._preprocess_images(html_content, "https://mp.weixin.qq.com/s/test")

    assert "data:image/png;base64," in result
    mock_fetch.assert_called_once()
