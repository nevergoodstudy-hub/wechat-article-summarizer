"""安全工具模块

提供加密、解密、密钥管理等安全相关功能。
使用 Fernet (对称加密) 保护敏感凭证。
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

# 密钥文件存储位置（在用户主目录）
KEY_FILE_DIR = Path.home() / ".wechat_summarizer"
KEY_FILE_NAME = ".keyfile"
KEY_FILE_PATH = KEY_FILE_DIR / KEY_FILE_NAME
SALT_FILE_NAME = ".salt"

# PBKDF2-HMAC-SHA256 policy. OWASP currently recommends 600,000+ iterations for
# PBKDF2-HMAC-SHA256 when PBKDF2 is required.
PBKDF2_HASH_NAME = "sha256"
PBKDF2_ITERATIONS = 600_000
PBKDF2_KEY_LENGTH = 32
MIN_SALT_BYTES = 16
SALT_BYTES = 32
LEGACY_CREDENTIAL_PREFIXES = ("DPAPI:", "XOR:")

LegacyCredentialDecryptor = Callable[[str], str]


@dataclass(frozen=True)
class CredentialMigrationResult:
    """Result of reading or migrating a stored credential."""

    plaintext: str = field(repr=False)
    encrypted_text: str = field(repr=False)
    migrated: bool
    legacy_format: str | None = None


def _ensure_key_dir() -> None:
    """确保密钥目录存在"""
    KEY_FILE_DIR.mkdir(parents=True, exist_ok=True)
    # 在 Windows 上设置为隐藏目录
    if os.name == "nt":
        try:
            import ctypes

            file_attribute_hidden = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(KEY_FILE_DIR), file_attribute_hidden)
        except Exception:
            pass  # 如果设置隐藏失败，不影响功能


def _get_salt_path() -> Path:
    """返回盐值文件路径"""
    return KEY_FILE_DIR / SALT_FILE_NAME


def _is_valid_salt(salt: bytes) -> bool:
    """校验 PBKDF2 盐值长度"""
    return len(salt) >= MIN_SALT_BYTES


def _write_private_bytes(path: Path, data: bytes) -> None:
    """以仅当前用户可读写的方式原子写入二进制数据"""
    _ensure_key_dir()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp-{secrets.token_hex(4)}")

    try:
        temp_path.write_bytes(data)
        _set_file_permissions(temp_path)
        temp_path.replace(path)
        _set_file_permissions(path)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError as e:
            logger.debug(f"清理临时安全文件失败 ({temp_path.name}): {e}")


def _create_salt(salt_path: Path | None = None) -> bytes:
    """创建并保存新的随机盐值"""
    path = salt_path or _get_salt_path()
    salt = secrets.token_bytes(SALT_BYTES)
    try:
        _write_private_bytes(path, salt)
    except Exception as e:
        logger.warning(f"无法保存盐值文件: {e}")
    return salt


def _generate_key_from_machine() -> bytes:
    """基于机器特征生成确定性密钥

    注意：这不是最安全的方式，但对于本地桌面应用是可接受的平衡。
    更安全的方式需要用户输入密码或使用操作系统密钥存储。
    """
    # 获取机器唯一标识（跨平台）
    machine_id = ""

    try:
        # Windows: 使用计算机名和用户名
        if os.name == "nt":
            machine_id = f"{os.environ.get('COMPUTERNAME', '')}{os.environ.get('USERNAME', '')}"
        else:
            # Unix/Linux/Mac: 使用hostname和用户名
            import socket

            machine_id = f"{socket.gethostname()}{os.environ.get('USER', '')}"
    except Exception:
        # 如果获取失败，使用随机值（将存储到文件）
        machine_id = secrets.token_hex(32)

    # 使用 PBKDF2 派生密钥
    # 使用随机盐值（存储在 salt 文件中），比固定盐更安全
    salt = _get_or_create_salt()
    key = hashlib.pbkdf2_hmac(
        PBKDF2_HASH_NAME,
        machine_id.encode(),
        salt,
        PBKDF2_ITERATIONS,
        dklen=PBKDF2_KEY_LENGTH,
    )
    return base64.urlsafe_b64encode(key)


def _get_or_create_salt() -> bytes:
    """获取或创建随机盐值

    盐值存储在密钥目录中，每台机器生成一次。
    """
    salt_path = _get_salt_path()

    if salt_path.exists():
        try:
            salt = salt_path.read_bytes()
            if _is_valid_salt(salt):
                return salt
            logger.warning("盐值文件长度不足，将重新生成随机盐值")
        except Exception as e:
            logger.warning(f"无法读取盐值文件，将重新生成: {e}")

    # 生成新的随机盐值
    return _create_salt(salt_path)


def _get_or_create_key() -> bytes:
    """获取或创建加密密钥

    Returns:
        Fernet兼容的密钥 (32字节，base64编码)
    """
    _ensure_key_dir()

    # 如果密钥文件已存在，读取它
    if KEY_FILE_PATH.exists():
        try:
            with open(KEY_FILE_PATH, "rb") as f:
                key = f.read()
            # 验证密钥格式
            Fernet(key)
            return key
        except Exception as e:
            logger.warning(f"无法读取现有密钥文件，将生成新密钥: {e}")

    # 生成新密钥
    key = _generate_key_from_machine()

    # 保存到文件
    try:
        _write_private_bytes(KEY_FILE_PATH, key)
    except Exception as e:
        logger.error(f"无法保存密钥文件: {e}")

    return key


def _set_file_permissions(path: Path) -> None:
    """设置文件权限为仅当前用户可读写"""
    try:
        if os.name == "nt":
            # Windows: 使用 icacls 限制为当前用户
            import subprocess

            username = os.environ.get("USERNAME", "")
            if username:
                subprocess.run(
                    ["icacls", str(path), "/inheritance:r", "/grant:r", f"{username}:(R,W)"],
                    capture_output=True,
                    stdin=subprocess.DEVNULL,
                    timeout=10,
                )
        else:
            path.chmod(0o600)
    except Exception as e:
        logger.debug(f"设置文件权限失败 ({path.name}): {e}")


def encrypt_credential(plaintext: str) -> str:
    """加密凭证

    Args:
        plaintext: 明文凭证

    Returns:
        Base64编码的加密文本
    """
    if not plaintext:
        return ""

    try:
        key = _get_or_create_key()
        f = Fernet(key)
        encrypted = f.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"加密凭证失败: {e}")
        raise


def decrypt_credential(encrypted_text: str) -> str:
    """解密凭证

    Args:
        encrypted_text: Base64编码的加密文本

    Returns:
        明文凭证
    """
    if not encrypted_text:
        return ""

    if is_legacy_encrypted(encrypted_text):
        raise ValueError("检测到旧版凭据格式，请先使用 migrate_legacy_credential() 迁移")

    try:
        key = _get_or_create_key()
        f = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_text, validate=True)
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except InvalidToken as err:
        logger.error("凭证解密失败：无效的加密数据或密钥已更改")
        raise ValueError("无法解密凭证，密钥可能已更改") from err
    except Exception as e:
        logger.error(f"解密凭证失败: {e}")
        raise


def is_legacy_encrypted(text: str) -> bool:
    """检查文本是否为旧版加密格式"""
    return bool(text) and text.startswith(LEGACY_CREDENTIAL_PREFIXES)


def migrate_legacy_credential(
    encrypted_text: str,
    legacy_decryptor: LegacyCredentialDecryptor | None = None,
) -> CredentialMigrationResult:
    """兼容读取并迁移旧版凭据格式。

    旧 ``DPAPI:`` / ``XOR:`` 数据需要调用方提供历史解密器；本模块不会重新
    引入已废弃的 XOR 混淆实现。迁移成功后返回新的 Fernet 加密文本，调用方
    可将其写回原配置位置。
    """
    if not encrypted_text:
        return CredentialMigrationResult(
            plaintext="",
            encrypted_text="",
            migrated=False,
        )

    if not is_legacy_encrypted(encrypted_text):
        return CredentialMigrationResult(
            plaintext=decrypt_credential(encrypted_text),
            encrypted_text=encrypted_text,
            migrated=False,
        )

    if legacy_decryptor is None:
        raise ValueError("检测到旧版凭据格式，需要提供 legacy_decryptor 完成迁移")

    plaintext = legacy_decryptor(encrypted_text)
    return CredentialMigrationResult(
        plaintext=plaintext,
        encrypted_text=encrypt_credential(plaintext),
        migrated=True,
        legacy_format=encrypted_text.split(":", 1)[0],
    )


def is_encrypted(text: str) -> bool:
    """检查文本是否为加密格式

    Args:
        text: 待检查的文本

    Returns:
        True 如果看起来像加密文本
    """
    if not text:
        return False

    if is_legacy_encrypted(text):
        return True

    # 简单启发式检查：加密文本是base64编码的，通常很长且包含特定字符
    try:
        # 尝试base64解码
        decoded = base64.b64decode(text, validate=True)
        # 加密文本通常至少几十字节
        return len(decoded) >= 32 and len(text) > 40
    except Exception:
        return False


def secure_compare(a: str, b: str) -> bool:
    """时间恒定的字符串比较，防止时序攻击

    Args:
        a: 第一个字符串
        b: 第二个字符串

    Returns:
        True 如果相等
    """
    if not isinstance(a, str) or not isinstance(b, str):
        return False

    # Python 3.3+ 的 secrets 模块提供时间恒定比较
    return secrets.compare_digest(a, b)


def sanitize_error_message(error_msg: str, sensitive_keys: list[str] | None = None) -> str:
    """清理错误消息中的敏感信息

    Args:
        error_msg: 原始错误消息
        sensitive_keys: 需要过滤的敏感关键词列表

    Returns:
        清理后的错误消息
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "api_key",
            "api-key",
            "apikey",
            "token",
            "secret",
            "password",
            "passwd",
            "pwd",
            "credential",
        ]

    sanitized = error_msg
    for key in sensitive_keys:
        # 替换可能包含密钥的部分
        if key.lower() in sanitized.lower():
            # 简单替换策略：将可能的值部分隐藏
            import re

            # 匹配 key=value 或 key: value 格式
            pattern = rf"{key}[\s:=]+['\"]?([^\s'\"]+)['\"]?"
            sanitized = re.sub(
                pattern,
                f"{key}=***REDACTED***",
                sanitized,
                flags=re.IGNORECASE,
            )

    return sanitized


def generate_secure_random_string(length: int = 32) -> str:
    """生成密码学安全的随机字符串

    Args:
        length: 字符串长度

    Returns:
        随机十六进制字符串
    """
    return secrets.token_hex(length // 2)


def validate_api_key_format(api_key: str, min_length: int = 16) -> bool:
    """验证 API 密钥格式

    Args:
        api_key: API 密钥
        min_length: 最小长度

    Returns:
        True 如果格式有效
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # 基本长度检查
    if len(api_key.strip()) < min_length:
        return False

    # 检查是否包含可疑字符（可能是注入攻击）
    suspicious_chars = [";", "|", "&", "$", "`", "\n", "\r"]
    return all(char not in api_key for char in suspicious_chars)


# 安全配置常量
class SecurityConfig:
    """安全配置常量"""

    # 密钥最小长度
    MIN_API_KEY_LENGTH = 16

    # 最大重试次数（防止暴力破解）
    MAX_AUTH_RETRIES = 3

    # 超时设置（秒）
    REQUEST_TIMEOUT = 30
    MAX_REQUEST_TIMEOUT = 120

    # URL 验证
    MAX_URL_LENGTH = 2048
    ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

    # 文件大小限制
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
