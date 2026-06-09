"""Local draft obfuscation helpers."""

from __future__ import annotations

import base64
import hashlib
import logging
import os

logger = logging.getLogger(__name__)


class SimpleEncryptor:
    """简单加密器 (用于本地草稿保护)."""

    def __init__(self, key: str | None = None):
        if key is None:
            import platform

            machine_id = f"{platform.node()}-{os.getlogin()}"
            key = hashlib.sha256(machine_id.encode()).hexdigest()[:32]
        self._key = key.encode()

    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            encrypted = bytes(
                left ^ right
                for left, right in zip(
                    data.encode("utf-8"),
                    (self._key * (len(data) // len(self._key) + 1))[: len(data.encode("utf-8"))],
                    strict=False,
                )
            )
            return base64.b64encode(encrypted).decode("ascii")
        except Exception as exc:
            logger.error("加密失败: %s", exc)
            return data

    def decrypt(self, data: str) -> str:
        """解密数据"""
        try:
            encrypted = base64.b64decode(data.encode("ascii"))
            decrypted = bytes(
                left ^ right
                for left, right in zip(
                    encrypted,
                    (self._key * (len(encrypted) // len(self._key) + 1))[: len(encrypted)],
                    strict=False,
                )
            )
            return decrypted.decode("utf-8")
        except Exception as exc:
            logger.error("解密失败: %s", exc)
            return data


__all__ = ["SimpleEncryptor"]
