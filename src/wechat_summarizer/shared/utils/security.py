"""安全工具模块

提供加密、解密、密钥管理等安全相关功能。
使用 Fernet (对称加密) 保护敏感凭证。
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

# 密钥文件存储位置（在用户主目录）
KEY_FILE_DIR = Path.home() / ".wechat_summarizer"
KEY_FILE_NAME = ".keyfile"
KEY_FILE_PATH = KEY_FILE_DIR / KEY_FILE_NAME


def _ensure_key_dir() -> None:
    """确保密钥目录存在"""
    KEY_FILE_DIR.mkdir(parents=True, exist_ok=True)
    # 在 Windows 上设置为隐藏目录
    if os.name == "nt":
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(KEY_FILE_DIR), FILE_ATTRIBUTE_HIDDEN)
        except Exception:
            pass  # 如果设置隐藏失败，不影响功能


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
    # 这确保了即使机器ID泄露，也需要很大的计算成本才能破解
    salt = b"wechat_summarizer_v2"  # 固定盐值，确保同一机器生成相同密钥
    key = hashlib.pbkdf2_hmac("sha256", machine_id.encode(), salt, 100000)
    return base64.urlsafe_b64encode(key)


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
        with open(KEY_FILE_PATH, "wb") as f:
            f.write(key)
        # 设置文件权限（仅用户可读写）
        if os.name != "nt":  # Unix-like systems
            KEY_FILE_PATH.chmod(0o600)
    except Exception as e:
        logger.error(f"无法保存密钥文件: {e}")
    
    return key


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
    
    try:
        key = _get_or_create_key()
        f = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_text)
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except InvalidToken:
        logger.error("凭证解密失败：无效的加密数据或密钥已更改")
        raise ValueError("无法解密凭证，密钥可能已更改")
    except Exception as e:
        logger.error(f"解密凭证失败: {e}")
        raise


def is_encrypted(text: str) -> bool:
    """检查文本是否为加密格式
    
    Args:
        text: 待检查的文本
        
    Returns:
        True 如果看起来像加密文本
    """
    if not text:
        return False
    
    # 简单启发式检查：加密文本是base64编码的，通常很长且包含特定字符
    try:
        # 尝试base64解码
        decoded = base64.b64decode(text)
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


def sanitize_error_message(error_msg: str, sensitive_keys: Optional[list[str]] = None) -> str:
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
    for char in suspicious_chars:
        if char in api_key:
            return False
    
    return True


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
    MAX_IMAGE_SIZE = 5 * 1024 * 1024    # 5MB
