"""安全存储工具（已废弃）

.. deprecated:: 2.4.0
    此模块使用 XOR 混淆，安全性不足。
    请使用 ``shared.utils.security`` 模块中基于 Fernet 的实现：
    ``from wechat_summarizer.shared.utils.security import encrypt_credential, decrypt_credential``

旧实现策略：
1. 优先使用 Windows DPAPI (仅 Windows)
2. 降级使用基于机器指纹的 XOR 混淆（非真正加密）
"""

from __future__ import annotations

import base64
import hashlib
import os
import platform
import secrets
import warnings
from pathlib import Path

from loguru import logger

warnings.warn(
    "shared.secure_storage 已废弃，请迁移到 shared.utils.security（基于 Fernet 加密）。"
    " 此模块将在 v3.0 中移除。",
    DeprecationWarning,
    stacklevel=2,
)


class SecureStorage:
    """安全存储管理器
    
    提供跨平台的敏感数据加密存储功能。
    """
    
    _instance: SecureStorage | None = None
    _key_file: Path | None = None
    
    def __new__(cls) -> SecureStorage:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """初始化安全存储"""
        self._key_file = Path.home() / ".wechat_summarizer" / ".secure_key"
        self._machine_key = self._get_machine_key()
        self._use_dpapi = self._check_dpapi_available()
        
        if self._use_dpapi:
            logger.debug("使用 Windows DPAPI 进行加密")
        else:
            logger.debug("使用机器指纹混淆进行加密")
    
    def _check_dpapi_available(self) -> bool:
        """检查 Windows DPAPI 是否可用"""
        if platform.system() != "Windows":
            return False
        try:
            import win32crypt  # noqa: F401
            return True
        except ImportError:
            return False
    
    def _get_machine_key(self) -> bytes:
        """获取基于机器信息的密钥"""
        # 收集机器特征
        features = [
            platform.node(),  # 机器名
            platform.machine(),  # CPU 架构
            str(Path.home()),  # 用户目录
        ]
        
        # 尝试获取更多唯一信息
        try:
            # 获取磁盘序列号（Windows）
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "diskdrive", "get", "serialnumber"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    features.append(result.stdout.strip())
        except Exception:
            pass
        
        # 生成密钥
        combined = "|".join(features)
        return hashlib.sha256(combined.encode()).digest()
    
    def _get_encryption_key(self) -> bytes:
        """获取加密密钥（使用或创建随机盐）"""
        salt_file = self._key_file
        
        if salt_file and salt_file.exists():
            try:
                salt = salt_file.read_bytes()
            except Exception:
                salt = secrets.token_bytes(32)
        else:
            salt = secrets.token_bytes(32)
            if salt_file:
                try:
                    salt_file.parent.mkdir(parents=True, exist_ok=True)
                    salt_file.write_bytes(salt)
                    # 设置文件权限（仅用户可读写）
                    if platform.system() != "Windows":
                        os.chmod(salt_file, 0o600)
                except Exception as e:
                    logger.warning(f"无法保存加密盐: {e}")
        
        # 使用 PBKDF2 派生密钥
        return hashlib.pbkdf2_hmac(
            "sha256",
            self._machine_key,
            salt,
            iterations=100000,
            dklen=32,
        )
    
    def encrypt(self, plaintext: str) -> str:
        """加密字符串
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            加密后的 base64 编码字符串
        """
        if not plaintext:
            return ""
        
        # 使用 Windows DPAPI
        if self._use_dpapi:
            try:
                import win32crypt
                encrypted = win32crypt.CryptProtectData(
                    plaintext.encode("utf-8"),
                    None,
                    None,
                    None,
                    None,
                    0,
                )
                return "DPAPI:" + base64.b64encode(encrypted).decode("ascii")
            except Exception as e:
                logger.warning(f"DPAPI 加密失败，降级使用混淆: {e}")
        
        # 使用 XOR 混淆（注意：这不是真正的加密，只是混淆）
        key = self._get_encryption_key()
        data = plaintext.encode("utf-8")
        
        # 添加随机前缀防止相同明文产生相同密文
        prefix = secrets.token_bytes(16)
        data = prefix + data
        
        # XOR 混淆
        encrypted = bytes(d ^ key[i % len(key)] for i, d in enumerate(data))
        
        return "XOR:" + base64.b64encode(encrypted).decode("ascii")
    
    def decrypt(self, ciphertext: str) -> str:
        """解密字符串
        
        Args:
            ciphertext: 加密后的字符串
            
        Returns:
            解密后的明文
        """
        if not ciphertext:
            return ""
        
        # 检查加密类型
        if ciphertext.startswith("DPAPI:"):
            if not self._use_dpapi:
                logger.warning("DPAPI 不可用，无法解密")
                return ""
            try:
                import win32crypt
                encrypted = base64.b64decode(ciphertext[6:])
                decrypted = win32crypt.CryptUnprotectData(
                    encrypted,
                    None,
                    None,
                    None,
                    0,
                )
                return decrypted[1].decode("utf-8")
            except Exception as e:
                logger.warning(f"DPAPI 解密失败: {e}")
                return ""
        
        elif ciphertext.startswith("XOR:"):
            try:
                key = self._get_encryption_key()
                encrypted = base64.b64decode(ciphertext[4:])
                
                # XOR 解密
                decrypted = bytes(d ^ key[i % len(key)] for i, d in enumerate(encrypted))
                
                # 移除随机前缀
                return decrypted[16:].decode("utf-8")
            except Exception as e:
                logger.warning(f"XOR 解密失败: {e}")
                return ""
        
        # 未知格式，可能是明文（兼容旧数据）
        return ciphertext
    
    def is_encrypted(self, value: str) -> bool:
        """检查值是否已加密"""
        return value.startswith("DPAPI:") or value.startswith("XOR:")


def get_secure_storage() -> SecureStorage:
    """获取安全存储实例"""
    return SecureStorage()


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """掩码敏感信息
    
    Args:
        value: 敏感值
        visible_chars: 保留可见字符数
        
    Returns:
        掩码后的字符串，如 "sk-****1234"
    """
    if not value:
        return ""
    
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    
    return value[:visible_chars] + "*" * (len(value) - visible_chars * 2) + value[-visible_chars:]
