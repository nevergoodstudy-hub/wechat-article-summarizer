"""跨平台路径管理

遵循各平台标准路径规范：
- Windows: AppData/Local, AppData/Roaming
- macOS: ~/Library/Application Support, ~/Library/Caches
- Linux: ~/.local/share, ~/.cache (XDG规范)

使用 platformdirs 库实现跨平台支持（如不可用则回退到用户目录）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass

# 应用标识
APP_NAME = "WechatSummarizer"
APP_AUTHOR = "WechatSummarizer"

# 旧版路径（用于迁移）
LEGACY_CONFIG_DIR_NAME = ".wechat_summarizer"


def _get_platformdirs_paths() -> tuple[Path, Path, Path]:
    """使用 platformdirs 获取标准路径"""
    try:
        import platformdirs

        config_dir = Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR))
        cache_dir = Path(platformdirs.user_cache_dir(APP_NAME, APP_AUTHOR))
        data_dir = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
        return config_dir, cache_dir, data_dir
    except ImportError:
        # platformdirs 不可用，回退到用户目录
        logger.debug("platformdirs not available, using fallback paths")
        return _get_fallback_paths()


def _get_fallback_paths() -> tuple[Path, Path, Path]:
    """回退路径（当 platformdirs 不可用时）"""
    if sys.platform == "win32":
        # Windows: 使用 LOCALAPPDATA
        import os

        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            base = Path(local_app_data) / APP_NAME
        else:
            base = Path.home() / "AppData" / "Local" / APP_NAME
        return base, base / "Cache", base / "Data"
    else:
        # Unix-like: 使用 XDG 规范或 macOS 标准路径
        if sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / APP_NAME
            cache = Path.home() / "Library" / "Caches" / APP_NAME
            return base, cache, base
        else:
            # Linux/Other Unix
            config = Path.home() / ".config" / APP_NAME.lower()
            cache = Path.home() / ".cache" / APP_NAME.lower()
            data = Path.home() / ".local" / "share" / APP_NAME.lower()
            return config, cache, data


def get_config_dir() -> Path:
    """获取配置目录

    Windows: C:/Users/<user>/AppData/Local/WechatSummarizer
    macOS: ~/Library/Application Support/WechatSummarizer
    Linux: ~/.config/wechatsummarizer
    """
    config_dir, _, _ = _get_platformdirs_paths()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """获取缓存目录

    Windows: C:/Users/<user>/AppData/Local/WechatSummarizer/Cache
    macOS: ~/Library/Caches/WechatSummarizer
    Linux: ~/.cache/wechatsummarizer
    """
    _, cache_dir, _ = _get_platformdirs_paths()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_data_dir() -> Path:
    """获取数据目录

    Windows: C:/Users/<user>/AppData/Local/WechatSummarizer/Data
    macOS: ~/Library/Application Support/WechatSummarizer
    Linux: ~/.local/share/wechatsummarizer
    """
    _, _, data_dir = _get_platformdirs_paths()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir() -> Path:
    """获取日志目录"""
    log_dir = get_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_legacy_config_dir() -> Path | None:
    """获取旧版配置目录（如果存在）"""
    legacy_dir = Path.home() / LEGACY_CONFIG_DIR_NAME
    if legacy_dir.exists() and legacy_dir.is_dir():
        return legacy_dir
    return None


def migrate_legacy_config() -> bool:
    """迁移旧版配置到新位置

    Returns:
        True if migration was performed, False otherwise
    """
    legacy_dir = get_legacy_config_dir()
    if legacy_dir is None:
        return False

    new_cache_dir = get_cache_dir()

    # 检查是否已迁移
    migration_marker = new_cache_dir / ".migrated_from_legacy"
    if migration_marker.exists():
        return False

    logger.info(f"Migrating legacy config from {legacy_dir} to {new_cache_dir}")

    try:
        import shutil

        # 迁移缓存目录
        legacy_cache = legacy_dir / "cache"
        if legacy_cache.exists():
            for item in legacy_cache.iterdir():
                dest = new_cache_dir / item.name
                if not dest.exists():
                    if item.is_file():
                        shutil.copy2(item, dest)
                    elif item.is_dir():
                        shutil.copytree(item, dest)

        # 创建迁移标记
        migration_marker.write_text(str(legacy_dir))

        logger.info("Migration completed successfully")
        return True

    except Exception as e:
        logger.warning(f"Migration failed: {e}")
        return False


def get_env_file_path() -> Path:
    """获取 .env 文件路径（项目目录或配置目录）"""
    # 优先使用当前工作目录
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env

    # 其次使用配置目录
    config_env = get_config_dir() / ".env"
    return config_env


# 模块初始化时自动迁移
def _init_paths() -> None:
    """初始化路径并执行必要的迁移"""
    try:
        migrate_legacy_config()
    except Exception as e:
        logger.debug(f"Path initialization warning: {e}")


_init_paths()
