"""Composition tests for split Windows GUI integration utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui.utils import windows_integration as integration_module
from wechat_summarizer.presentation.gui.utils.windows_integration import (
    Windows11StyleHelper,
    WindowsIntegration,
    windows,
)
from wechat_summarizer.presentation.gui.utils.windows_platform import (
    get_windows_version,
    is_windows,
    powershell_quote,
)
from wechat_summarizer.presentation.gui.utils.windows_shell import build_shortcut_script
from wechat_summarizer.presentation.gui.utils.windows_style import (
    Windows11StyleHelper as SplitWindows11StyleHelper,
)
from wechat_summarizer.presentation.gui.utils.windows_taskbar import WindowsTaskbarProgress


@pytest.mark.unit
def test_windows_integration_module_keeps_compatibility_exports() -> None:
    assert integration_module.Windows11StyleHelper is SplitWindows11StyleHelper
    assert Windows11StyleHelper is SplitWindows11StyleHelper
    assert isinstance(windows, WindowsIntegration)
    assert WindowsIntegration.is_windows() is is_windows()
    assert WindowsIntegration.get_windows_version() == get_windows_version()


@pytest.mark.unit
def test_windows_integration_facade_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    integration = WindowsIntegration()
    calls: list[tuple[str, object]] = []

    class FakeTaskbar:
        taskbar_list = "taskbar"

        def set_progress(self, progress: float, hwnd: int | None = None) -> None:
            calls.append(("taskbar", (progress, hwnd)))

    monkeypatch.setattr(
        integration_module,
        "open_windows_folder",
        lambda path: calls.append(("folder", path)) or True,
    )
    monkeypatch.setattr(
        integration_module, "open_windows_file", lambda path: calls.append(("file", path)) or True
    )
    monkeypatch.setattr(
        integration_module,
        "create_windows_shortcut",
        lambda target, shortcut_path, description="", icon=None, working_dir=None: (
            calls.append(("shortcut", shortcut_path)) or True
        ),
    )
    monkeypatch.setattr(
        integration_module, "get_windows_documents_folder", lambda: Path("Documents")
    )
    monkeypatch.setattr(integration_module, "get_windows_desktop_folder", lambda: Path("Desktop"))
    integration._taskbar_progress = FakeTaskbar()

    integration.set_taskbar_progress(0.25, hwnd=123)

    assert integration._taskbar_list == "taskbar"
    assert integration.open_folder("out") is True
    assert integration.open_file("report.pdf") is True
    assert integration.create_shortcut("app.exe", "app.lnk") is True
    assert integration.get_documents_folder() == Path("Documents")
    assert integration.get_desktop_folder() == Path("Desktop")
    assert calls == [
        ("taskbar", (0.25, 123)),
        ("folder", "out"),
        ("file", "report.pdf"),
        ("shortcut", "app.lnk"),
    ]


@pytest.mark.unit
def test_powershell_helpers_escape_single_quotes() -> None:
    assert powershell_quote("Bob's App") == "'Bob''s App'"

    script = build_shortcut_script(
        "C:/Apps/Bob's/app.exe",
        "C:/Users/Bob/Desktop/Bob's App.lnk",
        description="Bob's desktop shortcut",
        icon="C:/Icons/Bob's.ico",
        working_dir="C:/Apps/Bob's",
    )

    assert "$Shortcut.TargetPath = 'C:/Apps/Bob''s/app.exe'" in script
    assert "$Shortcut.Description = 'Bob''s desktop shortcut'" in script
    assert "$Shortcut.IconLocation = 'C:/Icons/Bob''s.ico'" in script
    assert "$Shortcut.WorkingDirectory = 'C:/Apps/Bob''s'" in script


@pytest.mark.unit
def test_taskbar_progress_noops_outside_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    from wechat_summarizer.presentation.gui.utils import (
        windows_platform,
        windows_taskbar,
    )

    monkeypatch.setattr(windows_platform.sys, "platform", "linux")
    monkeypatch.setattr(windows_taskbar, "is_windows", lambda: False)

    taskbar = WindowsTaskbarProgress()
    taskbar.set_progress(0.5)

    assert not is_windows()
    assert taskbar.taskbar_list is None


@pytest.mark.unit
def test_windows_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_integration.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_platform.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_taskbar.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_notifications.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_shell.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_paths.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/windows_style.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
