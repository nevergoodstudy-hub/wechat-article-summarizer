"""远程资源下载安全测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from wechat_summarizer.infrastructure.adapters.exporters.word import WordExporter
from wechat_summarizer.infrastructure.adapters.exporters.zip_exporter import ZipExporter


def test_word_preprocess_images_uses_safe_client(tmp_path: Path) -> None:
    """Word 导出预处理图片时应通过安全客户端下载远程资源。"""
    exporter = WordExporter(output_dir=str(tmp_path))
    response = MagicMock()
    response.content = b"fake-image"
    response.headers = {"content-type": "image/png"}
    response.raise_for_status = MagicMock()

    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get.return_value = response

    html = '<div><img src="https://example.com/image.png" /></div>'
    with patch(
        "wechat_summarizer.infrastructure.adapters.exporters.word.create_safe_client",
        return_value=client,
    ) as mock_factory:
        processed = exporter._preprocess_images(html, "https://example.com/article")

    mock_factory.assert_called_once()
    client.get.assert_called_once()
    assert "data:image/png;base64," in processed


def test_zip_process_images_uses_safe_client(tmp_path: Path) -> None:
    """ZIP 导出下载图片时应通过安全客户端下载远程资源。"""
    exporter = ZipExporter(output_dir=str(tmp_path), download_images=True)
    response = MagicMock()
    response.content = b"zip-image"
    response.headers = {"content-type": "image/png"}
    response.raise_for_status = MagicMock()

    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.get.return_value = response

    with patch(
        "wechat_summarizer.infrastructure.adapters.exporters.zip_exporter.create_safe_client",
        return_value=client,
    ) as mock_factory:
        html, image_files = exporter._process_images(
            '<img src="https://example.com/image.png" />',
            ("https://example.com/image.png",),
            "article_001",
        )

    mock_factory.assert_called_once()
    client.get.assert_called_once_with("https://example.com/image.png")
    assert "images/article_001_img_1.png" in html
    assert "article_001_img_1.png" in image_files
