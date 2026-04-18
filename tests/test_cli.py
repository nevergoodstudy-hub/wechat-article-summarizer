"""CLI 单元测试

测试 CLI 命令：
- cli --version
- cli --help
- fetch 命令 with mocked container
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from rich.console import Console

from wechat_summarizer.presentation.cli.app import _display_article, _process_single, cli
from wechat_summarizer.shared.constants import VERSION


class _EncodingGuardStream:
    """模拟 GBK 控制台，遇到不可编码字符时直接抛错。"""

    encoding = "gbk"

    def __init__(self) -> None:
        self._buffer: list[str] = []

    def write(self, text: str) -> int:
        text.encode(self.encoding)
        self._buffer.append(text)
        return len(text)

    def flush(self) -> None:
        return None

    def isatty(self) -> bool:
        return True

    def getvalue(self) -> str:
        return "".join(self._buffer)


@pytest.mark.unit
class TestCLIBasic:
    """CLI 基础命令测试"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """创建 CliRunner 实例"""
        return CliRunner()

    def test_cli_version(self, runner: CliRunner) -> None:
        """测试 --version 选项"""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert VERSION in result.output

    def test_cli_help(self, runner: CliRunner) -> None:
        """测试 --help 选项"""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "微信公众号文章总结器" in result.output
        # 应该显示可用命令
        assert "fetch" in result.output
        assert "batch" in result.output
        assert "config" in result.output

    def test_cli_debug_flag(self, runner: CliRunner) -> None:
        """测试 --debug 标志"""
        result = runner.invoke(cli, ["--debug", "--help"])

        assert result.exit_code == 0

    def test_fetch_help(self, runner: CliRunner) -> None:
        """测试 fetch --help"""
        result = runner.invoke(cli, ["fetch", "--help"])

        assert result.exit_code == 0
        assert "抓取并处理单篇文章" in result.output
        assert "--method" in result.output
        assert "--no-summary" in result.output
        assert "--export" in result.output
        assert "html" in result.output
        assert "markdown" in result.output
        assert "word" in result.output
        assert "obsidian" in result.output
        assert "notion" in result.output
        assert "onenote" in result.output
        assert "zip" in result.output

    def test_batch_help(self, runner: CliRunner) -> None:
        """测试 batch --help"""
        result = runner.invoke(cli, ["batch", "--help"])

        assert result.exit_code == 0
        assert "批量处理多篇文章" in result.output
        assert "--input-file" in result.output
        assert "--from-clipboard" in result.output
        assert "html" in result.output
        assert "markdown" in result.output
        assert "word" in result.output
        assert "obsidian" in result.output
        assert "notion" in result.output
        assert "onenote" in result.output
        assert "zip" in result.output

    def test_batch_async_help(self, runner: CliRunner) -> None:
        """测试 batch-async --help"""
        result = runner.invoke(cli, ["batch-async", "--help"])

        assert result.exit_code == 0
        assert "异步批量处理多篇文章" in result.output
        assert "--concurrency" in result.output
        assert "--export" in result.output
        assert "html" in result.output
        assert "markdown" in result.output
        assert "word" in result.output
        assert "obsidian" in result.output
        assert "notion" in result.output
        assert "onenote" in result.output
        assert "zip" in result.output

    def test_config_help(self, runner: CliRunner) -> None:
        """测试 config --help"""
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "显示当前配置" in result.output


@pytest.mark.unit
class TestFetchCommand:
    """fetch 命令测试"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """创建 CliRunner 实例"""
        return CliRunner()

    @pytest.fixture
    def mock_article(self, sample_article):
        """使用 conftest 的 sample_article fixture"""
        return sample_article

    @pytest.fixture
    def mock_summary(self, sample_summary):
        """使用 conftest 的 sample_summary fixture"""
        return sample_summary

    def test_fetch_success(
        self,
        runner: CliRunner,
        mock_article,
        mock_summary,
    ) -> None:
        """测试成功抓取文章"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = mock_article
        mock_container.summarize_use_case.execute.return_value = mock_summary

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["fetch", "https://mp.weixin.qq.com/s/test123"])

            # 应该成功（exit_code 为 0）
            assert result.exit_code == 0
            # 应该显示文章标题
            assert "测试文章标题" in result.output

    def test_fetch_with_no_summary(
        self,
        runner: CliRunner,
        mock_article,
    ) -> None:
        """测试 --no-summary 选项"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = mock_article

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(
                cli, ["fetch", "https://mp.weixin.qq.com/s/test123", "--no-summary"]
            )

            assert result.exit_code == 0
            # 不应调用摘要用例
            mock_container.summarize_use_case.execute.assert_not_called()

    def test_fetch_with_method(
        self,
        runner: CliRunner,
        mock_article,
        mock_summary,
    ) -> None:
        """测试 --method 选项"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = mock_article
        mock_container.summarize_use_case.execute.return_value = mock_summary

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(
                cli,
                ["fetch", "https://mp.weixin.qq.com/s/test123", "-m", "ollama"],
            )

            assert result.exit_code == 0
            # 应该以指定的 method 调用
            mock_container.summarize_use_case.execute.assert_called_once()
            call_kwargs = mock_container.summarize_use_case.execute.call_args
            assert call_kwargs[1]["method"] == "ollama"

    def test_fetch_scrape_failure(self, runner: CliRunner) -> None:
        """测试抓取失败"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.side_effect = Exception("网络错误")

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["fetch", "https://mp.weixin.qq.com/s/test123"])

            # 应该失败
            assert result.exit_code == 1
            assert "抓取失败" in result.output

    def test_process_single_fetch_failure_is_safe_on_gbk_console(self) -> None:
        """GBK 控制台下的抓取失败路径不应因为 Rich spinner 再次崩溃。"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.side_effect = Exception("网络错误")

        stream = _EncodingGuardStream()
        gbk_console = Console(
            file=stream,
            force_terminal=True,
            color_system=None,
            width=120,
        )

        with (
            patch(
                "wechat_summarizer.presentation.cli.app.get_container",
                return_value=mock_container,
            ),
            patch("wechat_summarizer.presentation.cli.app.console", gbk_console),
            pytest.raises(SystemExit) as exc_info,
        ):
            _process_single("https://mp.weixin.qq.com/s/test123")

        assert exc_info.value.code == 1
        assert "抓取失败" in stream.getvalue()

    def test_display_article_is_safe_on_gbk_console(self) -> None:
        """GBK 控制台下展示文章结果时不应因 Rich Panel 或特殊字符崩溃。"""
        article = MagicMock()
        article.title = "What’s new in Python 3.14"
        article.account_name = None
        article.word_count = 123
        article.url = "https://docs.python.org/3/whatsnew/3.14.html"
        article.content_text = "Preview body"
        article.summary = MagicMock(
            content="What’s new in Python 3.14",
            key_points=("alpha",),
            tags=("python",),
        )

        stream = _EncodingGuardStream()
        gbk_console = Console(
            file=stream,
            force_terminal=True,
            color_system=None,
            width=120,
        )

        with patch("wechat_summarizer.presentation.cli.app.console", gbk_console):
            _display_article(article)

        rendered = stream.getvalue()
        assert "标题:" in rendered
        assert "内容预览:" in rendered

    def test_fetch_summary_failure_continues(
        self,
        runner: CliRunner,
        mock_article,
    ) -> None:
        """测试摘要失败但继续执行"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = mock_article
        mock_container.summarize_use_case.execute.side_effect = Exception("API 错误")

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["fetch", "https://mp.weixin.qq.com/s/test123"])

            # 即使摘要失败，也应该显示文章信息
            assert result.exit_code == 0
            assert "摘要生成失败" in result.output


@pytest.mark.unit
class TestConfigCommand:
    """config 命令测试"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """创建 CliRunner 实例"""
        return CliRunner()

    def test_config_display(self, runner: CliRunner) -> None:
        """测试配置显示"""
        mock_settings = MagicMock()
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.default_summary_method = "simple"
        mock_settings.ollama.host = "http://localhost:11434"
        mock_settings.ollama.model = "qwen2.5:7b"
        mock_settings.openai.model = "gpt-4o-mini"
        mock_settings.export.default_output_dir = "./output"

        with patch(
            "wechat_summarizer.presentation.cli.app.get_settings",
            return_value=mock_settings,
        ):
            result = runner.invoke(cli, ["config"])

            assert result.exit_code == 0
            assert "当前配置" in result.output
            # 应该显示配置项
            assert "日志级别" in result.output

    def test_config_json_output(self, runner: CliRunner) -> None:
        """测试 --json 输出"""
        mock_settings = MagicMock()
        mock_settings.debug = False
        mock_settings.log_level = "INFO"
        mock_settings.default_summary_method = "simple"
        mock_settings.ollama.host = "http://localhost:11434"
        mock_settings.ollama.model = "qwen2.5:7b"
        mock_settings.openai.model = "gpt-4o-mini"
        mock_settings.export.default_output_dir = "./output"

        with patch(
            "wechat_summarizer.presentation.cli.app.get_settings",
            return_value=mock_settings,
        ):
            result = runner.invoke(cli, ["config", "--json"])

            assert result.exit_code == 0
            # JSON 输出应包含 { 和 }
            assert "{" in result.output
            assert "}" in result.output


@pytest.mark.unit
class TestCheckCommand:
    """check 命令测试"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """创建 CliRunner 实例"""
        return CliRunner()

    def test_check_components(self, runner: CliRunner) -> None:
        """测试组件检查"""
        mock_scraper = MagicMock()
        mock_scraper.name = "wechat_httpx"

        mock_summarizer = MagicMock()
        mock_summarizer.is_available.return_value = True

        mock_exporter = MagicMock()
        mock_exporter.is_available.return_value = True

        mock_container = MagicMock()
        mock_container.scrapers = [mock_scraper]
        mock_container.summarizers = {"simple": mock_summarizer}
        mock_container.exporters = {"markdown": mock_exporter}
        mock_container.storage = MagicMock()

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["check"])

            assert result.exit_code == 0
            assert "检查组件状态" in result.output
            assert "抓取器" in result.output
            assert "摘要器" in result.output
            assert "导出器" in result.output

    def test_check_output_is_console_safe(self, runner: CliRunner) -> None:
        """check 输出不应包含会触发 GBK 控制台崩溃的符号。"""
        mock_scraper = MagicMock()
        mock_scraper.name = "wechat_httpx"

        mock_summarizer = MagicMock()
        mock_summarizer.is_available.return_value = True

        mock_exporter = MagicMock()
        mock_exporter.is_available.return_value = True

        mock_container = MagicMock()
        mock_container.scrapers = [mock_scraper]
        mock_container.summarizers = {"simple": mock_summarizer}
        mock_container.exporters = {"markdown": mock_exporter}
        mock_container.storage = MagicMock()

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["check"])

        assert result.exit_code == 0
        assert "•" not in result.output
        assert "✓" not in result.output
        assert "✗" not in result.output


@pytest.mark.unit
class TestInfoCommand:
    """info 命令测试"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """创建 CliRunner 实例"""
        return CliRunner()

    def test_info_command(self, runner: CliRunner, sample_article) -> None:
        """测试 info 命令（只抓取不摘要）"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = sample_article

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["info", "https://mp.weixin.qq.com/s/test123"])

            assert result.exit_code == 0
            # 不应调用摘要用例
            mock_container.summarize_use_case.execute.assert_not_called()


@pytest.mark.unit
class TestBatchCommand:
    """batch 命令测试"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """创建 CliRunner 实例"""
        return CliRunner()

    def test_batch_no_urls_error(self, runner: CliRunner) -> None:
        """测试没有提供 URL 时的错误"""
        mock_container = MagicMock()

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(cli, ["batch"])

            assert result.exit_code == 1
            assert "没有提供 URL" in result.output

    def test_batch_with_urls(self, runner: CliRunner, sample_article) -> None:
        """测试批量处理多个 URL"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = sample_article
        mock_container.summarize_use_case.execute.return_value = MagicMock(
            content="摘要内容",
            key_points=(),
            tags=(),
            method=MagicMock(value="simple"),
        )

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(
                cli,
                [
                    "batch",
                    "https://mp.weixin.qq.com/s/test1",
                    "https://mp.weixin.qq.com/s/test2",
                ],
            )

            assert result.exit_code == 0
            assert "处理完成" in result.output

    def test_batch_from_file(self, runner: CliRunner, sample_article) -> None:
        """测试从文件读取 URL"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = sample_article
        mock_container.summarize_use_case.execute.return_value = MagicMock(
            content="摘要内容",
            key_points=(),
            tags=(),
            method=MagicMock(value="simple"),
        )

        with (
            patch(
                "wechat_summarizer.presentation.cli.app.get_container",
                return_value=mock_container,
            ),
            runner.isolated_filesystem(),
        ):
            url_file = Path("urls.txt")
            url_file.write_text(
                "https://mp.weixin.qq.com/s/test1\nhttps://mp.weixin.qq.com/s/test2",
                encoding="utf-8",
            )
            result = runner.invoke(cli, ["batch", "-f", str(url_file)])

            assert result.exit_code == 0
            # 应该处理 2 篇文章
            assert mock_container.fetch_use_case.execute.call_count == 2

    def test_batch_json_output(self, runner: CliRunner, sample_article) -> None:
        """测试 JSON 输出格式"""
        mock_container = MagicMock()
        mock_container.fetch_use_case.execute.return_value = sample_article
        mock_container.summarize_use_case.execute.return_value = MagicMock(
            content="摘要内容",
            key_points=(),
            tags=(),
            method=MagicMock(value="simple"),
        )

        with patch(
            "wechat_summarizer.presentation.cli.app.get_container",
            return_value=mock_container,
        ):
            result = runner.invoke(
                cli,
                [
                    "batch",
                    "https://mp.weixin.qq.com/s/test1",
                    "--output-format",
                    "json",
                ],
            )

            assert result.exit_code == 0
            # JSON 输出
            assert "{" in result.output
            assert "success_count" in result.output
