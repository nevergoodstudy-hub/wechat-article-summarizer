"""认证管理端口

定义微信公众平台认证的抽象接口。
支持扫码登录和token管理。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class AuthCredentials:
    """认证凭据
    
    存储登录后获取的认证信息。
    """

    token: str  # 访问令牌
    cookies: dict[str, str]  # Cookie信息
    fingerprint: str = ""  # 设备指纹
    expires_at: datetime | None = None  # 过期时间
    user_info: dict | None = None  # 用户信息（公众号信息）

    @property
    def is_expired(self) -> bool:
        """检查凭据是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    def to_dict(self) -> dict:
        """转换为字典（用于持久化）"""
        return {
            "token": self.token,
            "cookies": self.cookies,
            "fingerprint": self.fingerprint,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "user_info": self.user_info,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuthCredentials":
        """从字典创建实例"""
        return cls(
            token=data["token"],
            cookies=data["cookies"],
            fingerprint=data.get("fingerprint", ""),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            user_info=data.get("user_info"),
        )


@dataclass
class QRCodeData:
    """二维码数据"""

    qrcode_url: str  # 二维码图片URL
    uuid: str  # 二维码唯一标识
    expires_in: int = 300  # 有效期（秒）


class AuthPort(Protocol):
    """
    认证管理端口协议
    
    定义微信公众平台登录认证的接口规范。
    支持获取登录二维码和轮询扫码状态。
    """

    @abstractmethod
    async def get_qrcode(self) -> QRCodeData:
        """获取登录二维码
        
        Returns:
            二维码数据（URL和标识）
            
        Raises:
            NetworkError: 网络请求失败
        """
        ...

    @abstractmethod
    async def poll_scan_status(self, uuid: str) -> tuple[int, AuthCredentials | None]:
        """轮询扫码状态
        
        Args:
            uuid: 二维码唯一标识
            
        Returns:
            (状态码, 凭据) 元组
            状态码：0-等待扫码, 1-已扫码待确认, 2-登录成功, -1-已过期
            凭据：仅在登录成功时返回
            
        Raises:
            NetworkError: 网络请求失败
        """
        ...

    @abstractmethod
    async def refresh_credentials(
        self, credentials: AuthCredentials
    ) -> AuthCredentials | None:
        """刷新凭据
        
        Args:
            credentials: 当前凭据
            
        Returns:
            新凭据，如果刷新失败则返回None
        """
        ...

    @abstractmethod
    async def validate_credentials(self, credentials: AuthCredentials) -> bool:
        """验证凭据是否有效
        
        Args:
            credentials: 待验证的凭据
            
        Returns:
            凭据是否有效
        """
        ...

    @abstractmethod
    async def logout(self, credentials: AuthCredentials) -> bool:
        """登出
        
        Args:
            credentials: 当前凭据
            
        Returns:
            是否成功登出
        """
        ...


class CredentialStoragePort(Protocol):
    """
    凭据存储端口协议
    
    定义凭据的持久化存储接口。
    """

    @abstractmethod
    def save(self, credentials: AuthCredentials) -> None:
        """保存凭据
        
        Args:
            credentials: 要保存的凭据
        """
        ...

    @abstractmethod
    def load(self) -> AuthCredentials | None:
        """加载凭据
        
        Returns:
            保存的凭据，如果不存在则返回None
        """
        ...

    @abstractmethod
    def delete(self) -> None:
        """删除凭据"""
        ...

    @abstractmethod
    def exists(self) -> bool:
        """检查凭据是否存在
        
        Returns:
            凭据是否存在
        """
        ...
