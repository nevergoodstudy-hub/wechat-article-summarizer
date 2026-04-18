"""System keyring-backed JSON secret storage."""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

from loguru import logger

_keyring: Any | None
_is_recommended_backend: Callable[[object], bool]


def _fallback_recommended_backend(_backend: object) -> bool:
    return False


try:
    import keyring as _imported_keyring
except ImportError:  # pragma: no cover - exercised in environments without keyring
    _keyring = None
    _is_recommended_backend = _fallback_recommended_backend
else:
    from keyring.core import recommended as _keyring_recommended

    _keyring = _imported_keyring
    _is_recommended_backend = cast(Callable[[object], bool], _keyring_recommended)


class JsonSecretStore:
    """Persist a JSON blob in the OS keyring, with safe in-memory fallback."""

    def __init__(
        self,
        *,
        service_name: str,
        entry_name: str,
        legacy_path: Path | None = None,
        label: str = "secret",
    ) -> None:
        self._service_name = service_name
        self._entry_name = entry_name
        self._legacy_path = legacy_path
        self._label = label
        self._memory_cache: dict[str, Any] | None = None
        self._warned_unavailable = False

    def load(self) -> dict[str, Any] | None:
        """Load the stored JSON payload."""
        if self._memory_cache is not None:
            return dict(self._memory_cache)

        if not self._backend_available():
            return None

        data = self._load_from_keyring()
        if data is not None:
            self._memory_cache = data
            return dict(data)

        legacy_data = self._load_legacy_json()
        if legacy_data is None:
            return None

        logger.warning(f"检测到旧版明文 {self._label} 缓存，正在迁移到系统密钥库")
        self.save(legacy_data)
        return dict(legacy_data)

    def save(self, data: dict[str, Any]) -> None:
        """Store the JSON payload."""
        self._memory_cache = dict(data)

        backend_module = _keyring
        if backend_module is None or not self._backend_available():
            self._warn_unavailable()
            return

        try:
            backend_module.set_password(
                self._service_name,
                self._entry_name,
                json.dumps(data, ensure_ascii=False),
            )
            self._delete_legacy_file()
        except Exception as exc:
            self._warn_unavailable(exc)

    def delete(self) -> None:
        """Delete the stored payload from both keyring and legacy file storage."""
        self._memory_cache = None

        backend_module = _keyring
        if backend_module is not None and self._backend_available():
            with suppress(Exception):
                backend_module.delete_password(self._service_name, self._entry_name)

        self._delete_legacy_file()

    def exists(self) -> bool:
        """Whether a payload exists in memory, keyring, or a migratable legacy file."""
        return self.load() is not None

    def _backend_available(self) -> bool:
        if _keyring is None:
            self._warn_unavailable()
            return False

        try:
            backend = _keyring.get_keyring()
        except Exception as exc:
            self._warn_unavailable(exc)
            return False

        try:
            is_recommended = bool(_is_recommended_backend(backend))
        except Exception as exc:
            self._warn_unavailable(exc)
            return False

        if not is_recommended:
            self._warn_unavailable()

        return is_recommended

    def _load_from_keyring(self) -> dict[str, Any] | None:
        if _keyring is None:
            return None

        try:
            raw = _keyring.get_password(self._service_name, self._entry_name)
        except Exception as exc:
            logger.warning(f"读取系统密钥库中的 {self._label} 失败: {exc}")
            return None

        if not raw:
            return None

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning(f"系统密钥库中的 {self._label} 数据损坏: {exc}")
            return None

        if not isinstance(data, dict):
            logger.warning(f"系统密钥库中的 {self._label} 数据格式无效")
            return None

        return {str(key): value for key, value in data.items()}

    def _load_legacy_json(self) -> dict[str, Any] | None:
        path = self._legacy_path
        if path is None or not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning(f"读取旧版 {self._label} 缓存失败: {exc}")
            return None

        if not isinstance(data, dict):
            logger.warning(f"旧版 {self._label} 缓存格式无效")
            return None

        return {str(key): value for key, value in data.items()}

    def _delete_legacy_file(self) -> None:
        path = self._legacy_path
        if path is None or not path.exists():
            return

        try:
            path.unlink()
        except Exception as exc:
            logger.warning(f"删除旧版 {self._label} 缓存失败: {exc}")

    def _warn_unavailable(self, exc: Exception | None = None) -> None:
        if self._warned_unavailable:
            return

        detail = f": {exc}" if exc is not None else ""
        logger.warning(
            f"系统密钥库不可用，{self._label} 将仅保存在当前进程内存中，不会写入磁盘{detail}"
        )
        self._warned_unavailable = True
