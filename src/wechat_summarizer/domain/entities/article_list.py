"""文章列表实体

表示公众号的文章列表，包含文章列表项和文章列表聚合根。
与 Article 实体不同，ArticleListItem 是轻量级的列表项，
用于批量展示和筛选，不包含文章完整内容。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator


@dataclass
class ArticleListItem:
    """
    文章列表项
    
    表示公众号文章列表中的一条记录，是轻量级的文章元数据。
    用于批量获取和筛选场景，不包含文章正文内容。
    
    Attributes:
        aid: 文章ID（微信内部标识）
        title: 文章标题
        link: 文章永久链接
        digest: 文章摘要/描述
        cover: 封面图片URL
        update_time: 发布/更新时间戳（Unix时间戳）
        create_time: 创建时间戳（可能与update_time相同）
        item_show_type: 显示类型
        is_original: 是否原创
        copyright_type: 版权类型
    """

    aid: str
    title: str
    link: str
    digest: str = ""
    cover: str = ""
    update_time: int = 0
    create_time: int = 0
    item_show_type: int = 0
    is_original: bool = False
    copyright_type: int = 0

    def __post_init__(self) -> None:
        """验证数据"""
        if not self.title:
            raise ValueError("文章标题不能为空")
        if not self.link:
            raise ValueError("文章链接不能为空")

    @property
    def publish_datetime(self) -> datetime:
        """获取发布时间（datetime对象）"""
        if self.update_time:
            return datetime.fromtimestamp(self.update_time)
        return datetime.now()

    @property
    def publish_date_str(self) -> str:
        """获取发布日期字符串（YYYY-MM-DD格式）"""
        return self.publish_datetime.strftime("%Y-%m-%d")

    @property
    def has_cover(self) -> bool:
        """是否有封面图"""
        return bool(self.cover)

    @classmethod
    def from_api_response(cls, data: dict) -> "ArticleListItem":
        """从微信API响应创建实体
        
        Args:
            data: 微信appmsg API返回的文章数据
            
        Returns:
            ArticleListItem实例
        """
        return cls(
            aid=str(data.get("aid", "")),
            title=data.get("title", ""),
            link=data.get("link", ""),
            digest=data.get("digest", ""),
            cover=data.get("cover", ""),
            update_time=data.get("update_time", 0),
            create_time=data.get("create_time", 0),
            item_show_type=data.get("item_show_type", 0),
            is_original=data.get("is_original", 0) == 1,
            copyright_type=data.get("copyright_type", 0),
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "aid": self.aid,
            "title": self.title,
            "link": self.link,
            "digest": self.digest,
            "cover": self.cover,
            "update_time": self.update_time,
            "create_time": self.create_time,
            "publish_date": self.publish_date_str,
            "is_original": self.is_original,
            "copyright_type": self.copyright_type,
        }

    def __str__(self) -> str:
        return f"[{self.publish_date_str}] {self.title}"

    def __repr__(self) -> str:
        return f"ArticleListItem(aid={self.aid!r}, title={self.title!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArticleListItem):
            return NotImplemented
        # 使用link作为唯一标识（比aid更可靠）
        return self.link == other.link

    def __hash__(self) -> int:
        return hash(self.link)


@dataclass
class ArticleList:
    """
    文章列表聚合根
    
    管理公众号的文章列表集合，提供分页、筛选等功能。
    
    Attributes:
        fakeid: 所属公众号的fakeid
        account_name: 公众号名称
        items: 文章列表项集合
        total_count: 文章总数（来自API）
        fetched_at: 获取时间
    """

    fakeid: str
    account_name: str
    items: list[ArticleListItem] = field(default_factory=list)
    total_count: int = 0
    fetched_at: datetime = field(default_factory=datetime.now)

    @property
    def count(self) -> int:
        """当前已获取的文章数量"""
        return len(self.items)

    @property
    def is_complete(self) -> bool:
        """是否已获取全部文章"""
        return self.count >= self.total_count

    @property
    def links(self) -> list[str]:
        """获取所有文章链接"""
        return [item.link for item in self.items]

    @property
    def titles(self) -> list[str]:
        """获取所有文章标题"""
        return [item.title for item in self.items]

    def add_item(self, item: ArticleListItem) -> None:
        """添加文章项（去重）"""
        if item not in self.items:
            self.items.append(item)

    def add_items(self, items: list[ArticleListItem]) -> int:
        """批量添加文章项
        
        Returns:
            实际新增的数量
        """
        added = 0
        for item in items:
            if item not in self.items:
                self.items.append(item)
                added += 1
        return added

    def get_by_date_range(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ArticleListItem]:
        """按日期范围筛选文章
        
        Args:
            start_date: 开始日期（包含）
            end_date: 结束日期（包含）
            
        Returns:
            符合条件的文章列表
        """
        result = []
        for item in self.items:
            pub_time = item.publish_datetime
            if start_date and pub_time < start_date:
                continue
            if end_date and pub_time > end_date:
                continue
            result.append(item)
        return result

    def get_by_keyword(self, keyword: str) -> list[ArticleListItem]:
        """按关键词筛选文章（标题和摘要）
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            符合条件的文章列表
        """
        keyword_lower = keyword.lower()
        return [
            item
            for item in self.items
            if keyword_lower in item.title.lower()
            or keyword_lower in item.digest.lower()
        ]

    def get_original_only(self) -> list[ArticleListItem]:
        """获取原创文章"""
        return [item for item in self.items if item.is_original]

    def sort_by_time(self, ascending: bool = False) -> list[ArticleListItem]:
        """按时间排序
        
        Args:
            ascending: 是否升序（默认降序，最新在前）
            
        Returns:
            排序后的文章列表
        """
        return sorted(
            self.items,
            key=lambda x: x.update_time,
            reverse=not ascending,
        )

    def slice(self, start: int, end: int | None = None) -> list[ArticleListItem]:
        """获取指定范围的文章
        
        Args:
            start: 起始索引
            end: 结束索引（不包含）
            
        Returns:
            指定范围的文章列表
        """
        return self.items[start:end]

    def __iter__(self) -> Iterator[ArticleListItem]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> ArticleListItem:
        return self.items[index]

    def __str__(self) -> str:
        return (
            f"ArticleList({self.account_name}: "
            f"{self.count}/{self.total_count} articles)"
        )

    def __repr__(self) -> str:
        return (
            f"ArticleList(fakeid={self.fakeid!r}, "
            f"account_name={self.account_name!r}, "
            f"count={self.count}, total={self.total_count})"
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "fakeid": self.fakeid,
            "account_name": self.account_name,
            "total_count": self.total_count,
            "fetched_count": self.count,
            "is_complete": self.is_complete,
            "fetched_at": self.fetched_at.isoformat(),
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArticleList":
        """从字典创建实例（用于缓存恢复）"""
        article_list = cls(
            fakeid=data["fakeid"],
            account_name=data["account_name"],
            total_count=data.get("total_count", 0),
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
        )
        for item_data in data.get("items", []):
            article_list.items.append(
                ArticleListItem(
                    aid=item_data["aid"],
                    title=item_data["title"],
                    link=item_data["link"],
                    digest=item_data.get("digest", ""),
                    cover=item_data.get("cover", ""),
                    update_time=item_data.get("update_time", 0),
                    create_time=item_data.get("create_time", 0),
                    is_original=item_data.get("is_original", False),
                    copyright_type=item_data.get("copyright_type", 0),
                )
            )
        return article_list
