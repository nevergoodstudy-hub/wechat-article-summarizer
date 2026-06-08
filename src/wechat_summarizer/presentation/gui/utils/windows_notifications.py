"""Windows notification helpers."""

from __future__ import annotations

import subprocess

from loguru import logger

from .windows_platform import is_windows, powershell_quote


def show_notification(
    title: str,
    message: str,
    icon: str = "info",
    duration: int = 5000,
) -> None:
    """Show a Windows notification when supported."""
    if not is_windows():
        return

    try:
        if _show_winotify_notification(title, message, icon, duration):
            return
        _show_powershell_notification(title, message)
    except Exception as exc:
        logger.debug(f"Failed to show notification: {exc}")


def _show_winotify_notification(
    title: str,
    message: str,
    icon: str,
    duration: int,
) -> bool:
    try:
        from winotify import Notification, audio
    except ImportError:
        return False

    toast = Notification(
        app_id="微信公众号文章总结器",
        title=title,
        msg=message,
        duration="short" if duration <= 5000 else "long",
    )
    icon_map = {
        "info": audio.Default,
        "warning": audio.Reminder,
        "error": audio.IM,
    }
    toast.set_audio(icon_map.get(icon, audio.Default), loop=False)
    toast.show()
    return True


def _show_powershell_notification(title: str, message: str) -> None:
    script = build_notification_script(title, message)
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        timeout=5,
    )


def build_notification_script(title: str, message: str) -> str:
    """Build the PowerShell fallback script with safe string quoting."""
    return f"""
$title = {powershell_quote(title)}
$message = {powershell_quote(message)}
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode($title)) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode($message)) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("WechatSummarizer").Show($toast)
"""


__all__ = ["build_notification_script", "show_notification"]
