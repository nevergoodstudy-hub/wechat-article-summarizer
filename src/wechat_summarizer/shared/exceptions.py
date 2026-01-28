"""自定义异常类

包含：
- 错误码枚举 (ErrorCode)
- 分层异常类（领域层、应用层、基础设施层）
- 用户友好的错误消息
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(Enum):
    """错误码枚举

    错误码范围：
    - 1xxx: 通用错误
    - 2xxx: 网络/抓取错误
    - 3xxx: 摘要生成错误
    - 4xxx: 导出错误
    - 5xxx: 存储错误
    - 6xxx: 配置错误
    """

    # 通用错误 1xxx
    UNKNOWN_ERROR = (1000, "未知错误")
    INVALID_INPUT = (1001, "输入无效")
    INVALID_URL = (1002, "无效的URL")
    INVALID_CONTENT = (1003, "无效的内容")
    OPERATION_CANCELLED = (1004, "操作已取消")

    # 网络/抓取错误 2xxx
    NETWORK_ERROR = (2000, "网络连接失败")
    SCRAPER_ERROR = (2001, "抓取失败")
    SCRAPER_TIMEOUT = (2002, "抓取超时")
    SCRAPER_BLOCKED = (2003, "被反爬机制封禁")
    ARTICLE_NOT_FOUND = (2004, "文章未找到")
    UNSUPPORTED_SOURCE = (2005, "不支持的来源")

    # 摘要生成错误 3xxx
    SUMMARIZER_ERROR = (3000, "摘要生成失败")
    SUMMARIZER_API_ERROR = (3001, "摘要API调用失败")
    SUMMARIZER_TOKEN_LIMIT = (3002, "内容超出Token限制")
    SUMMARIZER_NOT_AVAILABLE = (3003, "摘要服务不可用")

    # 导出错误 4xxx
    EXPORT_ERROR = (4000, "导出失败")
    EXPORT_AUTH_ERROR = (4001, "导出认证失败")
    EXPORT_PATH_ERROR = (4002, "导出路径无效")
    EXPORT_FORMAT_ERROR = (4003, "不支持的导出格式")

    # 存储错误 5xxx
    STORAGE_ERROR = (5000, "存储操作失败")
    STORAGE_READ_ERROR = (5001, "读取数据失败")
    STORAGE_WRITE_ERROR = (5002, "写入数据失败")
    CACHE_ERROR = (5003, "缓存操作失败")

    # 配置错误 6xxx
    CONFIG_ERROR = (6000, "配置错误")
    CONFIG_MISSING = (6001, "缺少必要配置")
    CONFIG_INVALID = (6002, "配置值无效")

    def __init__(self, code: int, message: str):
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        """错误码"""
        return self._code

    @property
    def message(self) -> str:
        """错误消息"""
        return self._message

    def __str__(self) -> str:
        return f"[{self._code}] {self._message}"


class WechatSummarizerError(Exception):
    """基础异常类

    所有自定义异常的基类，支持错误码和详细信息。
    """

    error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: ErrorCode | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        self._error_code = error_code or self.error_code
        self._message = message or self._error_code.message
        self._details = details or {}
        self._cause = cause

        super().__init__(self._message)

    @property
    def code(self) -> int:
        """错误码"""
        return self._error_code.code

    @property
    def user_message(self) -> str:
        """用户友好的错误消息"""
        return self._message

    @property
    def details(self) -> dict[str, Any]:
        """详细信息"""
        return self._details

    @property
    def cause(self) -> Exception | None:
        """原始异常"""
        return self._cause

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于API响应或日志）"""
        return {
            "error_code": self._error_code.code,
            "error_type": self._error_code.name,
            "message": self._message,
            "details": self._details,
        }

    def __str__(self) -> str:
        return f"[{self._error_code.code}] {self._message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self._error_code.code}, message={self._message!r})"


# ============ 领域层异常 ============


class DomainError(WechatSummarizerError):
    """领域异常基类"""


class InvalidURLError(DomainError):
    """无效URL异常"""

    error_code = ErrorCode.INVALID_URL


class InvalidContentError(DomainError):
    """无效内容异常"""

    error_code = ErrorCode.INVALID_CONTENT


class ArticleNotFoundError(DomainError):
    """文章未找到异常"""

    error_code = ErrorCode.ARTICLE_NOT_FOUND


# ============ 应用层异常 ============


class ApplicationError(WechatSummarizerError):
    """应用层异常基类"""


class UseCaseError(ApplicationError):
    """用例执行异常"""


class ValidationError(ApplicationError):
    """验证异常"""

    error_code = ErrorCode.INVALID_INPUT


class OperationCancelledError(ApplicationError):
    """操作取消异常"""

    error_code = ErrorCode.OPERATION_CANCELLED


# ============ 基础设施层异常 ============


class InfrastructureError(WechatSummarizerError):
    """基础设施异常基类"""


class ScraperError(InfrastructureError):
    """抓取器异常"""

    error_code = ErrorCode.SCRAPER_ERROR


class ScraperTimeoutError(ScraperError):
    """抓取超时异常"""

    error_code = ErrorCode.SCRAPER_TIMEOUT


class ScraperBlockedError(ScraperError):
    """被反爬封禁异常"""

    error_code = ErrorCode.SCRAPER_BLOCKED


class NetworkError(InfrastructureError):
    """网络连接异常"""

    error_code = ErrorCode.NETWORK_ERROR


class SummarizerError(InfrastructureError):
    """摘要器异常"""

    error_code = ErrorCode.SUMMARIZER_ERROR


class SummarizerAPIError(SummarizerError):
    """摘要API调用异常"""

    error_code = ErrorCode.SUMMARIZER_API_ERROR


class SummarizerTokenLimitError(SummarizerError):
    """Token超限异常"""

    error_code = ErrorCode.SUMMARIZER_TOKEN_LIMIT


class SummarizerNotAvailableError(SummarizerError):
    """摘要服务不可用异常"""

    error_code = ErrorCode.SUMMARIZER_NOT_AVAILABLE


class ExporterError(InfrastructureError):
    """导出器异常"""

    error_code = ErrorCode.EXPORT_ERROR


class ExporterAuthError(ExporterError):
    """导出认证异常"""

    error_code = ErrorCode.EXPORT_AUTH_ERROR


class ExporterPathError(ExporterError):
    """导出路径异常"""

    error_code = ErrorCode.EXPORT_PATH_ERROR


class StorageError(InfrastructureError):
    """存储异常"""

    error_code = ErrorCode.STORAGE_ERROR


class StorageReadError(StorageError):
    """存储读取异常"""

    error_code = ErrorCode.STORAGE_READ_ERROR


class StorageWriteError(StorageError):
    """存储写入异常"""

    error_code = ErrorCode.STORAGE_WRITE_ERROR


class ConfigError(InfrastructureError):
    """配置异常"""

    error_code = ErrorCode.CONFIG_ERROR


class ConfigMissingError(ConfigError):
    """配置缺失异常"""

    error_code = ErrorCode.CONFIG_MISSING


class PluginError(InfrastructureError):
    """插件异常"""


# ============ 工具函数 ============


def wrap_exception(
    exc: Exception,
    error_class: type[WechatSummarizerError] = WechatSummarizerError,
    message: str | None = None,
) -> WechatSummarizerError:
    """将普通异常包装为 WechatSummarizerError

    Args:
        exc: 原始异常
        error_class: 目标异常类
        message: 自定义消息（可选）

    Returns:
        包装后的异常
    """
    if isinstance(exc, WechatSummarizerError):
        return exc

    return error_class(
        message=message or str(exc),
        cause=exc,
    )
