from __future__ import annotations

import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from wechat_summarizer.infrastructure.config import paths as paths_module
from wechat_summarizer.infrastructure.config import settings as settings_module
from wechat_summarizer.infrastructure.config.settings import (
    AppSettings,
    _get_env_value,
    _parse_dotenv_file,
    get_config_path,
    get_settings,
    reset_settings,
)
from wechat_summarizer.shared import constants as constants_module


@pytest.mark.unit
def test_parse_dotenv_file_supports_comments_export_and_quotes(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# ignored",
                "export OPENAI_API_KEY='sk-test'",
                'OPENAI_BASE_URL="https://example.test/v1"',
                "OUTPUT_DIR= ./output ",
                "INVALID_LINE",
            ]
        ),
        encoding="utf-8",
    )

    parsed = _parse_dotenv_file(env_file)

    assert parsed == {
        "OPENAI_API_KEY": "sk-test",
        "OPENAI_BASE_URL": "https://example.test/v1",
        "OUTPUT_DIR": "./output",
    }


@pytest.mark.unit
def test_parse_dotenv_file_retries_with_ignored_decode_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"\xff")
    calls: list[str | None] = []

    def fake_read_text(self: Path, *, encoding: str, errors: str | None = None) -> str:
        if self == env_file and errors is None:
            calls.append("strict")
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "boom")
        if self == env_file and errors == "ignore":
            calls.append("ignore")
            return "OPENAI_API_KEY=retry-success\n"
        raise AssertionError(f"unexpected path: {self}")

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    parsed = _parse_dotenv_file(env_file)

    assert parsed == {"OPENAI_API_KEY": "retry-success"}
    assert calls == ["strict", "ignore"]


@pytest.mark.unit
def test_get_env_value_prefers_os_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "from-os")

    assert _get_env_value("OPENAI_API_KEY", {"OPENAI_API_KEY": "from-dotenv"}) == "from-os"


@pytest.mark.unit
def test_app_settings_warns_when_llm_method_lacks_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(
        settings_module._logger, "warning", lambda message: warnings.append(message)
    )

    AppSettings(default_summary_method="openai")

    assert warnings
    assert "openai" in warnings[0]


@pytest.mark.unit
def test_get_settings_backfills_all_supported_legacy_variables(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=sk-openai",
                "OPENAI_BASE_URL=https://proxy.example/v1",
                "DEEPSEEK_API_KEY=sk-deepseek",
                "ANTHROPIC_API_KEY=sk-anthropic",
                "ZHIPU_API_KEY=sk-zhipu",
                "OUTPUT_DIR=./legacy-output",
                "NOTION_API_KEY=secret-notion",
                "NOTION_DATABASE_ID=db123",
                "OBSIDIAN_VAULT_PATH=D:/vault",
                "ONENOTE_CLIENT_ID=client-123",
                "ONENOTE_TENANT=tenant-456",
                "ONENOTE_NOTEBOOK=Notebook",
                "ONENOTE_SECTION=Section",
            ]
        ),
        encoding="utf-8",
    )

    for key in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_API_KEY",
        "ZHIPU_API_KEY",
        "OUTPUT_DIR",
        "NOTION_API_KEY",
        "NOTION_DATABASE_ID",
        "OBSIDIAN_VAULT_PATH",
        "ONENOTE_CLIENT_ID",
        "ONENOTE_TENANT",
        "ONENOTE_NOTEBOOK",
        "ONENOTE_SECTION",
    ]:
        monkeypatch.delenv(key, raising=False)

    monkeypatch.setattr(settings_module, "get_env_file_candidates", lambda: (env_file,))

    reset_settings()
    settings = get_settings()

    assert settings.openai.api_key.get_secret_value() == "sk-openai"
    assert settings.openai.base_url == "https://proxy.example/v1"
    assert settings.deepseek.api_key.get_secret_value() == "sk-deepseek"
    assert settings.anthropic.api_key.get_secret_value() == "sk-anthropic"
    assert settings.zhipu.api_key.get_secret_value() == "sk-zhipu"
    assert settings.export.default_output_dir == "./legacy-output"
    assert settings.export.notion_api_key.get_secret_value() == "secret-notion"
    assert settings.export.notion_database_id == "db123"
    assert settings.export.obsidian_vault_path == "D:/vault"
    assert settings.export.onenote_client_id == "client-123"
    assert settings.export.onenote_tenant == "tenant-456"
    assert settings.export.onenote_notebook == "Notebook"
    assert settings.export.onenote_section == "Section"

    reset_settings()


@pytest.mark.unit
def test_get_settings_preserves_explicit_nested_values_over_legacy_fallbacks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "WECHAT_SUMMARIZER_OPENAI__API_KEY=sk-nested",
                "WECHAT_SUMMARIZER_OPENAI__MODEL=nested-model",
                "OPENAI_API_KEY=sk-legacy",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "get_env_file_candidates", lambda: (env_file,))

    reset_settings()
    settings = get_settings()

    assert settings.openai.api_key == SecretStr("sk-nested")
    assert settings.openai.model == "nested-model"

    reset_settings()


@pytest.mark.unit
def test_get_config_path_uses_platform_config_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config-home"
    monkeypatch.setattr(settings_module, "get_config_dir", lambda: config_dir)

    assert get_config_path() == config_dir / "config.yaml"


@pytest.mark.unit
def test_get_platformdirs_paths_prefers_platformdirs_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_platformdirs = SimpleNamespace(
        user_config_dir=lambda app_name, app_author: f"/config/{app_name}/{app_author}",
        user_cache_dir=lambda app_name, app_author: f"/cache/{app_name}/{app_author}",
        user_data_dir=lambda app_name, app_author: f"/data/{app_name}/{app_author}",
    )
    monkeypatch.setitem(sys.modules, "platformdirs", fake_platformdirs)

    config_dir, cache_dir, data_dir = paths_module._get_platformdirs_paths()

    assert config_dir == Path("/config/WechatSummarizer/WechatSummarizer")
    assert cache_dir == Path("/cache/WechatSummarizer/WechatSummarizer")
    assert data_dir == Path("/data/WechatSummarizer/WechatSummarizer")


@pytest.mark.unit
def test_get_platformdirs_paths_falls_back_when_import_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import builtins

    original_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "platformdirs":
            raise ImportError("simulated missing dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "platformdirs", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(paths_module.sys, "platform", "linux")

    config_dir, cache_dir, data_dir = paths_module._get_platformdirs_paths()

    assert config_dir == tmp_path / ".config" / "wechatsummarizer"
    assert cache_dir == tmp_path / ".cache" / "wechatsummarizer"
    assert data_dir == tmp_path / ".local" / "share" / "wechatsummarizer"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("platform_name", "local_app_data", "expected"),
    [
        (
            "win32",
            r"C:\Users\Test\AppData\Local",
            (Path(r"C:\Users\Test\AppData\Local") / "WechatSummarizer", "Cache", "Data"),
        ),
        (
            "darwin",
            None,
            (
                Path("/Users/test/Library/Application Support/WechatSummarizer"),
                "Caches",
                "Application Support",
            ),
        ),
        ("linux", None, (Path("/home/test/.config/wechatsummarizer"), ".cache", ".local/share")),
    ],
)
def test_get_fallback_paths_returns_platform_specific_locations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    platform_name: str,
    local_app_data: str | None,
    expected: tuple[Path, str, str],
) -> None:
    if platform_name == "win32":
        monkeypatch.setenv("LOCALAPPDATA", local_app_data or "")
    else:
        monkeypatch.delenv("LOCALAPPDATA", raising=False)

    home = Path("/Users/test") if platform_name == "darwin" else Path("/home/test")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(paths_module.sys, "platform", platform_name)

    config_dir, cache_dir, data_dir = paths_module._get_fallback_paths()

    if platform_name == "win32":
        assert config_dir == expected[0]
        assert cache_dir == expected[0] / expected[1]
        assert data_dir == expected[0] / expected[2]
    elif platform_name == "darwin":
        assert config_dir == expected[0]
        assert cache_dir == Path("/Users/test/Library/Caches/WechatSummarizer")
        assert data_dir == expected[0]
    else:
        assert config_dir == expected[0]
        assert cache_dir == Path("/home/test/.cache/wechatsummarizer")
        assert data_dir == Path("/home/test/.local/share/wechatsummarizer")


@pytest.mark.unit
def test_standard_directory_helpers_create_directories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config"
    cache_dir = tmp_path / "cache"
    data_dir = tmp_path / "data"
    monkeypatch.setattr(
        paths_module, "_get_platformdirs_paths", lambda: (config_dir, cache_dir, data_dir)
    )

    assert paths_module.get_config_dir().is_dir()
    assert paths_module.get_cache_dir().is_dir()
    assert paths_module.get_data_dir().is_dir()
    assert paths_module.get_log_dir() == data_dir / "logs"
    assert (data_dir / "logs").is_dir()


@pytest.mark.unit
def test_get_legacy_config_dir_only_returns_existing_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy_dir = tmp_path / ".wechat_summarizer"
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert paths_module.get_legacy_config_dir() is None

    legacy_dir.mkdir()

    assert paths_module.get_legacy_config_dir() == legacy_dir


@pytest.mark.unit
def test_migrate_legacy_config_copies_cache_contents_and_writes_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy_dir = tmp_path / "legacy"
    legacy_cache = legacy_dir / "cache"
    legacy_cache.mkdir(parents=True)
    (legacy_cache / "entry.txt").write_text("cache", encoding="utf-8")
    nested_dir = legacy_cache / "nested"
    nested_dir.mkdir()
    (nested_dir / "child.txt").write_text("nested", encoding="utf-8")

    new_cache_dir = tmp_path / "new-cache"
    new_cache_dir.mkdir()

    monkeypatch.setattr(paths_module, "get_legacy_config_dir", lambda: legacy_dir)
    monkeypatch.setattr(paths_module, "get_cache_dir", lambda: new_cache_dir)

    assert paths_module.migrate_legacy_config() is True
    assert (new_cache_dir / "entry.txt").read_text(encoding="utf-8") == "cache"
    assert (new_cache_dir / "nested" / "child.txt").read_text(encoding="utf-8") == "nested"
    assert (new_cache_dir / ".migrated_from_legacy").read_text(encoding="utf-8") == str(legacy_dir)


@pytest.mark.unit
def test_migrate_legacy_config_handles_existing_marker_and_copy_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    legacy_dir = tmp_path / "legacy"
    legacy_cache = legacy_dir / "cache"
    legacy_cache.mkdir(parents=True)
    (legacy_cache / "entry.txt").write_text("cache", encoding="utf-8")

    new_cache_dir = tmp_path / "new-cache"
    new_cache_dir.mkdir()
    marker = new_cache_dir / ".migrated_from_legacy"
    marker.write_text("done", encoding="utf-8")

    monkeypatch.setattr(paths_module, "get_legacy_config_dir", lambda: legacy_dir)
    monkeypatch.setattr(paths_module, "get_cache_dir", lambda: new_cache_dir)

    assert paths_module.migrate_legacy_config() is False

    marker.unlink()
    monkeypatch.setattr(
        shutil, "copy2", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("copy failed"))
    )

    assert paths_module.migrate_legacy_config() is False


@pytest.mark.unit
def test_get_env_file_candidates_handles_checkout_override_and_resolution_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_env = tmp_path / "config" / ".env"
    config_env.parent.mkdir()
    config_env.write_text("", encoding="utf-8")
    cwd_dir = tmp_path / "repo"
    cwd_dir.mkdir()
    cwd_env = cwd_dir / ".env"
    cwd_env.write_text("", encoding="utf-8")

    monkeypatch.setattr(paths_module, "get_default_env_file_path", lambda: config_env)
    monkeypatch.chdir(cwd_dir)

    assert paths_module.get_env_file_candidates() == (config_env, cwd_env)

    monkeypatch.setattr(Path, "resolve", lambda self: (_ for _ in ()).throw(OSError("boom")))
    assert paths_module.get_env_file_candidates() == (config_env, cwd_env)

    cwd_env.unlink()
    assert paths_module.get_env_file_candidates() == (config_env,)
    assert paths_module.get_env_file_path() == config_env


def _set_fake_module_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    fake_module_file = tmp_path / "src" / "wechat_summarizer" / "shared" / "constants.py"
    fake_module_file.parent.mkdir(parents=True, exist_ok=True)
    fake_module_file.write_text("# placeholder", encoding="utf-8")
    monkeypatch.setattr(constants_module, "__file__", str(fake_module_file))
    return tmp_path / "pyproject.toml"


@pytest.mark.unit
def test_read_version_from_pyproject_returns_none_when_file_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_fake_module_file(monkeypatch, tmp_path)

    assert constants_module._read_version_from_pyproject() is None


@pytest.mark.unit
def test_read_version_from_pyproject_handles_read_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pyproject_path = _set_fake_module_file(monkeypatch, tmp_path)
    pyproject_path.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")

    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == pyproject_path:
            raise OSError("cannot read")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    assert constants_module._read_version_from_pyproject() is None


@pytest.mark.unit
def test_read_version_from_pyproject_falls_back_to_regex_when_tomllib_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pyproject_path = _set_fake_module_file(monkeypatch, tmp_path)
    pyproject_path.write_text(
        '[project]\nversion = "9.8.7"\ninvalid = [\n',
        encoding="utf-8",
    )

    assert constants_module._read_version_from_pyproject() == "9.8.7"


@pytest.mark.unit
def test_resolve_version_uses_metadata_then_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(constants_module, "_read_version_from_pyproject", lambda: None)
    monkeypatch.setattr(constants_module._metadata, "version", lambda _name: "8.7.6")
    assert constants_module._resolve_version() == "8.7.6"

    def raise_not_found(_name: str) -> str:
        raise constants_module._metadata.PackageNotFoundError

    monkeypatch.setattr(constants_module._metadata, "version", raise_not_found)
    assert constants_module._resolve_version() == "2.4.3"
