"""Browser activity detection for WeChat article pages."""

from __future__ import annotations

import subprocess

from loguru import logger


class BrowserDetector:
    """浏览器探测器 - 检测当前浏览器是否在浏览微信公众号页面"""

    @staticmethod
    def get_active_browser_url() -> str | None:
        """获取当前活动浏览器窗口的URL（仅Windows）"""
        try:
            ps_script = """
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            using System.Text;
            public class Win32 {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll")]
                public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                [DllImport("user32.dll")]
                public static extern int GetWindowTextLength(IntPtr hWnd);
            }
"@
            $hwnd = [Win32]::GetForegroundWindow()
            $len = [Win32]::GetWindowTextLength($hwnd)
            $sb = New-Object System.Text.StringBuilder($len + 1)
            [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity)
            $sb.ToString()
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                ),
            )
            window_title = result.stdout.strip()

            if window_title and any(
                keyword in window_title.lower() for keyword in ["微信", "wechat", "mp.weixin"]
            ):
                logger.debug(f"检测到微信相关窗口: {window_title}")
                return window_title

            return None

        except Exception as exc:
            logger.debug(f"浏览器探测失败: {exc}")
            return None

    @staticmethod
    def check_wechat_browser_activity() -> bool:
        """检查是否有微信公众号相关浏览器活动"""
        window_title = BrowserDetector.get_active_browser_url()
        return window_title is not None


__all__ = ["BrowserDetector"]
