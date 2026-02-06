"""Windows 系统集成

提供 Windows 特定功能：
- 任务栏进度显示
- 系统通知
- 文件资源管理器集成
- 快捷方式创建
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass


class WindowsIntegration:
    """Windows 系统集成类

    封装 Windows 特定的系统功能。
    在非 Windows 系统上，这些方法会静默失败。
    """

    _instance: WindowsIntegration | None = None

    def __new__(cls) -> WindowsIntegration:
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._taskbar_list = None
        self._hwnd = None
        self._is_windows = sys.platform == "win32"

    def set_taskbar_progress(self, progress: float, hwnd: int | None = None) -> None:
        """设置任务栏进度

        Args:
            progress: 进度值 (0.0 - 1.0)，设置为 -1 清除进度
            hwnd: 窗口句柄（可选，如果为 None 会尝试获取当前窗口）
        """
        if not self._is_windows:
            return

        try:
            # 延迟导入 Windows 特定模块
            import ctypes
            from ctypes import wintypes

            # 获取窗口句柄
            if hwnd is None:
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if not hwnd:
                    # 尝试获取前台窗口
                    hwnd = ctypes.windll.user32.GetForegroundWindow()

            if not hwnd:
                return

            # ITaskbarList3 接口
            CLSID_TaskbarList = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
            IID_ITaskbarList3 = "{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}"

            # 使用 comtypes 如果可用
            try:
                import comtypes.client as cc

                if self._taskbar_list is None:
                    self._taskbar_list = cc.CreateObject(
                        CLSID_TaskbarList,
                        interface=None,
                    )

                if progress < 0:
                    # 清除进度
                    self._taskbar_list.SetProgressState(hwnd, 0)  # TBPF_NOPROGRESS
                else:
                    # 设置进度
                    self._taskbar_list.SetProgressState(hwnd, 2)  # TBPF_NORMAL
                    self._taskbar_list.SetProgressValue(
                        hwnd,
                        int(progress * 100),
                        100,
                    )
            except ImportError:
                # comtypes 不可用，跳过
                pass

        except Exception as e:
            logger.debug(f"Failed to set taskbar progress: {e}")

    def clear_taskbar_progress(self, hwnd: int | None = None) -> None:
        """清除任务栏进度"""
        self.set_taskbar_progress(-1, hwnd)

    def show_notification(
        self,
        title: str,
        message: str,
        icon: str = "info",
        duration: int = 5000,
    ) -> None:
        """显示系统通知

        Args:
            title: 通知标题
            message: 通知内容
            icon: 图标类型 ("info", "warning", "error")
            duration: 显示时长（毫秒）
        """
        if not self._is_windows:
            return

        try:
            # 使用 Windows Toast 通知
            # 需要 win10toast 或 winotify
            try:
                from winotify import Notification, audio

                toast = Notification(
                    app_id="微信公众号文章总结器",
                    title=title,
                    msg=message,
                    duration="short" if duration <= 5000 else "long",
                )

                # 设置图标
                icon_map = {
                    "info": audio.Default,
                    "warning": audio.Reminder,
                    "error": audio.IM,
                }
                toast.set_audio(icon_map.get(icon, audio.Default), loop=False)

                toast.show()
                return
            except ImportError:
                pass

            # 回退：使用 PowerShell 显示通知
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("WechatSummarizer").Show($toast)
            '''

            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                timeout=5,
            )

        except Exception as e:
            logger.debug(f"Failed to show notification: {e}")

    def open_folder(self, path: str | Path) -> bool:
        """在文件资源管理器中打开文件夹

        Args:
            path: 文件夹路径

        Returns:
            是否成功
        """
        if not self._is_windows:
            return False

        try:
            path = Path(path)
            if path.is_file():
                # 如果是文件，打开其所在文件夹并选中
                subprocess.run(["explorer", "/select,", str(path)], check=True)
            elif path.is_dir():
                # 如果是文件夹，直接打开
                subprocess.run(["explorer", str(path)], check=True)
            else:
                return False
            return True
        except Exception as e:
            logger.debug(f"Failed to open folder: {e}")
            return False

    def open_file(self, path: str | Path) -> bool:
        """使用默认程序打开文件

        Args:
            path: 文件路径

        Returns:
            是否成功
        """
        if not self._is_windows:
            return False

        try:
            import os

            os.startfile(str(path))
            return True
        except Exception as e:
            logger.debug(f"Failed to open file: {e}")
            return False

    def create_shortcut(
        self,
        target: str | Path,
        shortcut_path: str | Path,
        description: str = "",
        icon: str | Path | None = None,
        working_dir: str | Path | None = None,
    ) -> bool:
        """创建快捷方式

        Args:
            target: 目标程序路径
            shortcut_path: 快捷方式路径（.lnk）
            description: 描述
            icon: 图标路径
            working_dir: 工作目录

        Returns:
            是否成功
        """
        if not self._is_windows:
            return False

        try:
            import win32com.client

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(target)
            shortcut.Description = description

            if icon:
                shortcut.IconLocation = str(icon)
            if working_dir:
                shortcut.WorkingDirectory = str(working_dir)

            shortcut.save()
            return True
        except ImportError:
            # pywin32 不可用，使用 PowerShell
            try:
                ps_script = f'''
                $WshShell = New-Object -comObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
                $Shortcut.TargetPath = "{target}"
                $Shortcut.Description = "{description}"
                $Shortcut.Save()
                '''
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    capture_output=True,
                    check=True,
                )
                return True
            except Exception as e:
                logger.debug(f"Failed to create shortcut via PowerShell: {e}")
                return False
        except Exception as e:
            logger.debug(f"Failed to create shortcut: {e}")
            return False

    def get_documents_folder(self) -> Path:
        """获取用户文档文件夹"""
        if self._is_windows:
            try:
                import ctypes
                from ctypes import wintypes

                CSIDL_PERSONAL = 0x0005
                buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(
                    None, CSIDL_PERSONAL, None, 0, buf
                )
                return Path(buf.value)
            except Exception:
                pass

        return Path.home() / "Documents"

    def get_desktop_folder(self) -> Path:
        """获取用户桌面文件夹"""
        if self._is_windows:
            try:
                import ctypes
                from ctypes import wintypes

                CSIDL_DESKTOPDIRECTORY = 0x0010
                buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(
                    None, CSIDL_DESKTOPDIRECTORY, None, 0, buf
                )
                return Path(buf.value)
            except Exception:
                pass

        return Path.home() / "Desktop"

    @staticmethod
    def is_windows() -> bool:
        """检查是否为 Windows 系统"""
        return sys.platform == "win32"

    @staticmethod
    def get_windows_version() -> tuple[int, int, int] | None:
        """获取 Windows 版本

        Returns:
            (major, minor, build) 或 None（非 Windows）
        """
        if sys.platform != "win32":
            return None

        try:
            import platform

            version = platform.version()
            parts = version.split(".")
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            return None


class Windows11StyleHelper:
    """应用 Windows 11 原生窗口样式

    使用 pywinstyles 库实现标题栏颜色和边框样式的原生适配。
    在非 Windows 11 或 pywinstyles 不可用时静默跳过。
    """

    _pywinstyles = None
    _checked: bool = False

    @classmethod
    def _ensure_pywinstyles(cls):
        """延迟导入 pywinstyles"""
        if not cls._checked:
            cls._checked = True
            try:
                import pywinstyles
                cls._pywinstyles = pywinstyles
            except ImportError:
                cls._pywinstyles = None

    @classmethod
    def is_windows_11(cls) -> bool:
        """检测是否为 Windows 11"""
        cls._ensure_pywinstyles()
        if cls._pywinstyles is None:
            return False
        try:
            version = sys.getwindowsversion()
            return version.major == 10 and version.build >= 22000
        except Exception:
            return False

    @classmethod
    def apply_window_style(cls, root, appearance_mode: str = 'dark'):
        """应用 Windows 11 窗口样式

        Args:
            root: CTk 根窗口
            appearance_mode: 'dark' 或 'light'
        """
        if not cls.is_windows_11():
            logger.debug('当前系统不是 Windows 11, 跳过样式应用')
            return

        try:
            from ..styles.colors import ModernColors

            pw = cls._pywinstyles
            if appearance_mode == 'dark':
                pw.change_header_color(root, ModernColors.DARK_BG)
                pw.change_border_color(root, ModernColors.DARK_BORDER)
            else:
                pw.change_header_color(root, ModernColors.LIGHT_BG)
                pw.change_border_color(root, ModernColors.LIGHT_BORDER)

            logger.info('✨ 已应用 Windows 11 窗口样式')
        except Exception as e:
            logger.debug(f'Windows 11 样式应用失败: {e}')

    @classmethod
    def update_titlebar_color(cls, root, appearance_mode: str):
        """更新标题栏颜色

        Args:
            root: CTk 根窗口
            appearance_mode: 'dark' 或 'light'
        """
        if not cls.is_windows_11():
            return

        try:
            from ..styles.colors import ModernColors

            pw = cls._pywinstyles
            if appearance_mode == 'dark':
                pw.change_header_color(root, ModernColors.DARK_BG)
                pw.change_border_color(root, ModernColors.DARK_BORDER)
            else:
                pw.change_header_color(root, ModernColors.LIGHT_BG)
                pw.change_border_color(root, ModernColors.LIGHT_BORDER)
            logger.debug(f'标题栏颜色已更新: {appearance_mode}')
        except Exception as e:
            logger.debug(f'标题栏颜色更新失败: {e}')


# 全局实例
windows = WindowsIntegration()
