"""Domain-owned exceptions.

The domain layer must not import shared/application/infrastructure modules.
Keep domain errors here and let outer layers re-export them when compatibility
with older import paths is needed.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base class for domain validation and invariant errors."""

    code: int = 1000
    error_type: str = "DOMAIN_ERROR"
    default_message: str = "领域错误"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        self._message = message or self.default_message
        self._details = details or {}
        self._cause = cause
        super().__init__(self._message)

    @property
    def user_message(self) -> str:
        """User-facing message kept compatible with shared exceptions."""
        return self._message

    @property
    def details(self) -> dict[str, Any]:
        """Additional structured details."""
        return self._details

    @property
    def cause(self) -> Exception | None:
        """Original exception, if wrapped."""
        return self._cause

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable error payload."""
        return {
            "error_code": self.code,
            "error_type": self.error_type,
            "message": self._message,
            "details": self._details,
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self._message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self._message!r})"


class InvalidURLError(DomainError):
    """Invalid article URL."""

    code = 1002
    error_type = "INVALID_URL"
    default_message = "无效的URL"


class InvalidContentError(DomainError):
    """Invalid article content."""

    code = 1003
    error_type = "INVALID_CONTENT"
    default_message = "无效的内容"


class ArticleNotFoundError(DomainError):
    """Article not found."""

    code = 2004
    error_type = "ARTICLE_NOT_FOUND"
    default_message = "文章未找到"
