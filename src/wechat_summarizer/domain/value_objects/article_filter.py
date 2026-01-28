"""文章筛选条件值对象

定义文章列表的筛选条件，支持多种筛选维度组合。
值对象是不可变的，包含筛选逻辑。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.article_list import ArticleListItem


@dataclass(frozen=True)
class ArticleFilter:
    """
    文章筛选条件值对象
    
    支持多种筛选条件的组合，用于从文章列表中筛选符合条件的文章。
    所有条件之间是 AND 关系（同时满足）。
    
    Attributes:
        keyword: 关键词筛选（标题或摘要包含）
        start_date: 起始日期（包含）
        end_date: 结束日期（包含）
        original_only: 是否只看原创
        min_count: 最少返回数量（0表示不限）
        max_count: 最多返回数量（0表示不限）
    """

    keyword: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    original_only: bool = False
    min_count: int = 0
    max_count: int = 0

    def __post_init__(self) -> None:
        """验证筛选条件"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("开始日期不能晚于结束日期")
        
        if self.min_count < 0:
            raise ValueError("min_count不能为负数")
        
        if self.max_count < 0:
            raise ValueError("max_count不能为负数")
        
        if self.min_count > 0 and self.max_count > 0:
            if self.min_count > self.max_count:
                raise ValueError("min_count不能大于max_count")

    def matches(self, item: "ArticleListItem") -> bool:
        """判断文章是否符合筛选条件
        
        Args:
            item: 待检查的文章
            
        Returns:
            是否符合所有筛选条件
        """
        # 关键词筛选
        if self.keyword:
            keyword_lower = self.keyword.lower()
            if (
                keyword_lower not in item.title.lower()
                and keyword_lower not in item.digest.lower()
            ):
                return False

        # 日期筛选
        pub_time = item.publish_datetime
        if self.start_date and pub_time < self.start_date:
            return False
        if self.end_date and pub_time > self.end_date:
            return False

        # 原创筛选
        if self.original_only and not item.is_original:
            return False

        return True

    def apply(self, items: list["ArticleListItem"]) -> list["ArticleListItem"]:
        """应用筛选条件到文章列表
        
        Args:
            items: 待筛选的文章列表
            
        Returns:
            符合条件的文章列表
        """
        # 应用筛选条件
        filtered = [item for item in items if self.matches(item)]

        # 应用数量限制
        if self.max_count > 0:
            filtered = filtered[: self.max_count]

        return filtered

    @property
    def is_empty(self) -> bool:
        """是否为空筛选条件（无任何限制）"""
        return (
            self.keyword is None
            and self.start_date is None
            and self.end_date is None
            and not self.original_only
            and self.max_count == 0
        )

    @property
    def description(self) -> str:
        """获取筛选条件的文字描述"""
        parts = []
        
        if self.keyword:
            parts.append(f"关键词: {self.keyword}")
        
        if self.start_date:
            parts.append(f"从: {self.start_date.strftime('%Y-%m-%d')}")
        
        if self.end_date:
            parts.append(f"到: {self.end_date.strftime('%Y-%m-%d')}")
        
        if self.original_only:
            parts.append("仅原创")
        
        if self.max_count > 0:
            parts.append(f"最多: {self.max_count}篇")

        return ", ".join(parts) if parts else "无筛选条件"

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "keyword": self.keyword,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "original_only": self.original_only,
            "min_count": self.min_count,
            "max_count": self.max_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArticleFilter":
        """从字典创建实例"""
        return cls(
            keyword=data.get("keyword"),
            start_date=(
                datetime.fromisoformat(data["start_date"])
                if data.get("start_date")
                else None
            ),
            end_date=(
                datetime.fromisoformat(data["end_date"])
                if data.get("end_date")
                else None
            ),
            original_only=data.get("original_only", False),
            min_count=data.get("min_count", 0),
            max_count=data.get("max_count", 0),
        )

    @classmethod
    def by_keyword(cls, keyword: str) -> "ArticleFilter":
        """创建仅关键词筛选"""
        return cls(keyword=keyword)

    @classmethod
    def by_date_range(
        cls,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> "ArticleFilter":
        """创建日期范围筛选"""
        return cls(start_date=start_date, end_date=end_date)

    @classmethod
    def recent_days(cls, days: int) -> "ArticleFilter":
        """创建最近N天筛选"""
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return cls(start_date=start_date, end_date=end_date)

    @classmethod
    def top_n(cls, n: int) -> "ArticleFilter":
        """创建获取前N篇筛选"""
        return cls(max_count=n)

    def __str__(self) -> str:
        return f"ArticleFilter({self.description})"

    def __repr__(self) -> str:
        return (
            f"ArticleFilter(keyword={self.keyword!r}, "
            f"start_date={self.start_date}, end_date={self.end_date}, "
            f"original_only={self.original_only}, max_count={self.max_count})"
        )
