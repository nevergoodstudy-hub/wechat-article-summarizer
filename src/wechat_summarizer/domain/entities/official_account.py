"""公众号实体

表示微信公众号账号的领域实体，包含账号基本信息和元数据。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class ServiceType(IntEnum):
    """公众号服务类型
    
    微信公众号分为订阅号和服务号两种类型。
    """

    SUBSCRIPTION = 0  # 订阅号
    SERVICE = 1  # 服务号（具有更多API权限）


@dataclass
class OfficialAccount:
    """
    公众号实体
    
    表示一个微信公众号账号，是搜索结果的核心数据结构。
    
    Attributes:
        fakeid: 公众号唯一标识（微信内部ID，用于API调用）
        nickname: 公众号名称（显示名）
        alias: 公众号微信号（可选，用户自定义的ID）
        round_head_img: 公众号头像URL
        service_type: 服务类型（订阅号/服务号）
        signature: 公众号简介/签名
        searched_at: 搜索获取时间
    """

    fakeid: str
    nickname: str
    alias: str = ""
    round_head_img: str = ""
    service_type: ServiceType = ServiceType.SUBSCRIPTION
    signature: str = ""
    searched_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """验证实体数据"""
        if not self.fakeid:
            raise ValueError("fakeid不能为空")
        if not self.nickname:
            raise ValueError("公众号名称不能为空")

    @property
    def display_name(self) -> str:
        """获取显示名称（带微信号）"""
        if self.alias:
            return f"{self.nickname} ({self.alias})"
        return self.nickname

    @property
    def service_type_name(self) -> str:
        """获取服务类型名称"""
        return "订阅号" if self.service_type == ServiceType.SUBSCRIPTION else "服务号"

    @classmethod
    def from_api_response(cls, data: dict) -> "OfficialAccount":
        """从微信API响应创建实体
        
        Args:
            data: 微信搜索API返回的公众号数据
            
        Returns:
            OfficialAccount实体实例
        """
        return cls(
            fakeid=data.get("fakeid", ""),
            nickname=data.get("nickname", ""),
            alias=data.get("alias", ""),
            round_head_img=data.get("round_head_img", ""),
            service_type=ServiceType(data.get("service_type", 0)),
            signature=data.get("signature", ""),
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "fakeid": self.fakeid,
            "nickname": self.nickname,
            "alias": self.alias,
            "round_head_img": self.round_head_img,
            "service_type": self.service_type.value,
            "service_type_name": self.service_type_name,
            "signature": self.signature,
            "searched_at": self.searched_at.isoformat(),
        }

    def __str__(self) -> str:
        return f"OfficialAccount({self.display_name})"

    def __repr__(self) -> str:
        return (
            f"OfficialAccount(fakeid={self.fakeid!r}, "
            f"nickname={self.nickname!r}, alias={self.alias!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OfficialAccount):
            return NotImplemented
        return self.fakeid == other.fakeid

    def __hash__(self) -> int:
        return hash(self.fakeid)
