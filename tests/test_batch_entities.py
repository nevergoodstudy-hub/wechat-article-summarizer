"""批量获取相关实体和值对象的单元测试"""

import pytest
from datetime import datetime, timedelta

from src.wechat_summarizer.domain.entities.official_account import (
    OfficialAccount,
    ServiceType,
)
from src.wechat_summarizer.domain.entities.article_list import (
    ArticleListItem,
    ArticleList,
)
from src.wechat_summarizer.domain.value_objects.article_filter import ArticleFilter
from src.wechat_summarizer.domain.value_objects.batch_export_options import (
    BatchExportOptions,
    ExportFormat,
    LinkFormat,
)


class TestOfficialAccount:
    """公众号实体测试"""

    def test_create_account(self):
        """测试创建公众号实体"""
        account = OfficialAccount(
            fakeid="MzI1234567890",
            nickname="测试公众号",
            alias="test_account",
            service_type=ServiceType.SUBSCRIPTION,
        )
        
        assert account.fakeid == "MzI1234567890"
        assert account.nickname == "测试公众号"
        assert account.alias == "test_account"
        assert account.service_type == ServiceType.SUBSCRIPTION

    def test_display_name_with_alias(self):
        """测试带微信号的显示名称"""
        account = OfficialAccount(
            fakeid="test",
            nickname="测试号",
            alias="test_id",
        )
        assert account.display_name == "测试号 (test_id)"

    def test_display_name_without_alias(self):
        """测试不带微信号的显示名称"""
        account = OfficialAccount(
            fakeid="test",
            nickname="测试号",
        )
        assert account.display_name == "测试号"

    def test_service_type_name(self):
        """测试服务类型名称"""
        sub = OfficialAccount(fakeid="1", nickname="订阅号", service_type=ServiceType.SUBSCRIPTION)
        svc = OfficialAccount(fakeid="2", nickname="服务号", service_type=ServiceType.SERVICE)
        
        assert sub.service_type_name == "订阅号"
        assert svc.service_type_name == "服务号"

    def test_from_api_response(self):
        """测试从API响应创建"""
        data = {
            "fakeid": "MzI1234567890",
            "nickname": "Python之禅",
            "alias": "VTalk",
            "service_type": 0,
            "signature": "分享Python技术",
        }
        
        account = OfficialAccount.from_api_response(data)
        
        assert account.fakeid == "MzI1234567890"
        assert account.nickname == "Python之禅"
        assert account.alias == "VTalk"

    def test_to_dict(self):
        """测试转换为字典"""
        account = OfficialAccount(
            fakeid="test",
            nickname="测试",
        )
        
        d = account.to_dict()
        
        assert d["fakeid"] == "test"
        assert d["nickname"] == "测试"
        assert "searched_at" in d

    def test_equality(self):
        """测试相等性比较（基于fakeid）"""
        a1 = OfficialAccount(fakeid="same", nickname="名称1")
        a2 = OfficialAccount(fakeid="same", nickname="名称2")
        a3 = OfficialAccount(fakeid="diff", nickname="名称1")
        
        assert a1 == a2
        assert a1 != a3

    def test_hash(self):
        """测试哈希（用于集合和字典）"""
        a1 = OfficialAccount(fakeid="test", nickname="测试")
        a2 = OfficialAccount(fakeid="test", nickname="测试")
        
        s = {a1, a2}
        assert len(s) == 1

    def test_invalid_fakeid(self):
        """测试无效fakeid"""
        with pytest.raises(ValueError, match="fakeid不能为空"):
            OfficialAccount(fakeid="", nickname="测试")

    def test_invalid_nickname(self):
        """测试无效名称"""
        with pytest.raises(ValueError, match="公众号名称不能为空"):
            OfficialAccount(fakeid="test", nickname="")


class TestArticleListItem:
    """文章列表项测试"""

    def test_create_item(self):
        """测试创建文章列表项"""
        item = ArticleListItem(
            aid="123",
            title="测试文章",
            link="https://mp.weixin.qq.com/s/test",
            digest="这是摘要",
            update_time=1704067200,  # 2024-01-01
        )
        
        assert item.aid == "123"
        assert item.title == "测试文章"
        assert item.link == "https://mp.weixin.qq.com/s/test"
        assert item.digest == "这是摘要"

    def test_publish_datetime(self):
        """测试发布时间转换"""
        item = ArticleListItem(
            aid="1",
            title="测试",
            link="http://test",
            update_time=1704067200,
        )
        
        dt = item.publish_datetime
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1

    def test_publish_date_str(self):
        """测试发布日期字符串"""
        item = ArticleListItem(
            aid="1",
            title="测试",
            link="http://test",
            update_time=1704067200,
        )
        
        assert item.publish_date_str == "2024-01-01"

    def test_from_api_response(self):
        """测试从API响应创建"""
        data = {
            "aid": "123456",
            "title": "Python 3.12新特性",
            "link": "https://mp.weixin.qq.com/s/xxx",
            "digest": "介绍Python 3.12的新特性",
            "cover": "http://cover.jpg",
            "update_time": 1704067200,
            "is_original": 1,
        }
        
        item = ArticleListItem.from_api_response(data)
        
        assert item.aid == "123456"
        assert item.title == "Python 3.12新特性"
        assert item.is_original is True

    def test_to_dict(self):
        """测试转换为字典"""
        item = ArticleListItem(
            aid="1",
            title="测试",
            link="http://test",
        )
        
        d = item.to_dict()
        
        assert d["aid"] == "1"
        assert d["title"] == "测试"
        assert "publish_date" in d

    def test_equality(self):
        """测试相等性（基于link）"""
        i1 = ArticleListItem(aid="1", title="标题1", link="http://same")
        i2 = ArticleListItem(aid="2", title="标题2", link="http://same")
        i3 = ArticleListItem(aid="1", title="标题1", link="http://diff")
        
        assert i1 == i2
        assert i1 != i3

    def test_invalid_title(self):
        """测试无效标题"""
        with pytest.raises(ValueError, match="文章标题不能为空"):
            ArticleListItem(aid="1", title="", link="http://test")

    def test_invalid_link(self):
        """测试无效链接"""
        with pytest.raises(ValueError, match="文章链接不能为空"):
            ArticleListItem(aid="1", title="测试", link="")


class TestArticleList:
    """文章列表聚合根测试"""

    def test_create_list(self):
        """测试创建文章列表"""
        article_list = ArticleList(
            fakeid="test",
            account_name="测试公众号",
            total_count=100,
        )
        
        assert article_list.fakeid == "test"
        assert article_list.account_name == "测试公众号"
        assert article_list.total_count == 100
        assert article_list.count == 0

    def test_add_item(self):
        """测试添加文章"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        item = ArticleListItem(aid="1", title="文章1", link="http://1")
        
        article_list.add_item(item)
        
        assert article_list.count == 1
        assert article_list[0] == item

    def test_add_item_deduplicate(self):
        """测试添加文章去重"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        item = ArticleListItem(aid="1", title="文章1", link="http://same")
        
        article_list.add_item(item)
        article_list.add_item(item)
        
        assert article_list.count == 1

    def test_add_items_batch(self):
        """测试批量添加文章"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        items = [
            ArticleListItem(aid="1", title="文章1", link="http://1"),
            ArticleListItem(aid="2", title="文章2", link="http://2"),
            ArticleListItem(aid="3", title="文章3", link="http://3"),
        ]
        
        added = article_list.add_items(items)
        
        assert added == 3
        assert article_list.count == 3

    def test_links_property(self):
        """测试获取所有链接"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        article_list.add_item(ArticleListItem(aid="1", title="文章1", link="http://1"))
        article_list.add_item(ArticleListItem(aid="2", title="文章2", link="http://2"))
        
        links = article_list.links
        
        assert links == ["http://1", "http://2"]

    def test_get_by_keyword(self):
        """测试按关键词筛选"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        article_list.add_item(ArticleListItem(aid="1", title="Python教程", link="http://1"))
        article_list.add_item(ArticleListItem(aid="2", title="Java教程", link="http://2"))
        article_list.add_item(ArticleListItem(aid="3", title="Python进阶", link="http://3"))
        
        results = article_list.get_by_keyword("Python")
        
        assert len(results) == 2

    def test_get_original_only(self):
        """测试获取原创文章"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        article_list.add_item(ArticleListItem(aid="1", title="原创1", link="http://1", is_original=True))
        article_list.add_item(ArticleListItem(aid="2", title="转载", link="http://2", is_original=False))
        article_list.add_item(ArticleListItem(aid="3", title="原创2", link="http://3", is_original=True))
        
        originals = article_list.get_original_only()
        
        assert len(originals) == 2

    def test_iterator(self):
        """测试迭代器"""
        article_list = ArticleList(fakeid="test", account_name="测试")
        article_list.add_item(ArticleListItem(aid="1", title="文章1", link="http://1"))
        article_list.add_item(ArticleListItem(aid="2", title="文章2", link="http://2"))
        
        titles = [item.title for item in article_list]
        
        assert titles == ["文章1", "文章2"]

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        article_list = ArticleList(fakeid="test", account_name="测试", total_count=10)
        article_list.add_item(ArticleListItem(aid="1", title="文章1", link="http://1"))
        
        d = article_list.to_dict()
        restored = ArticleList.from_dict(d)
        
        assert restored.fakeid == "test"
        assert restored.account_name == "测试"
        assert restored.count == 1


class TestArticleFilter:
    """文章筛选条件测试"""

    def test_empty_filter(self):
        """测试空筛选条件"""
        f = ArticleFilter()
        assert f.is_empty is True

    def test_keyword_filter(self):
        """测试关键词筛选"""
        f = ArticleFilter.by_keyword("Python")
        
        assert f.keyword == "Python"
        assert f.is_empty is False

    def test_date_range_filter(self):
        """测试日期范围筛选"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        
        f = ArticleFilter.by_date_range(start, end)
        
        assert f.start_date == start
        assert f.end_date == end

    def test_recent_days_filter(self):
        """测试最近N天筛选"""
        f = ArticleFilter.recent_days(7)
        
        assert f.start_date is not None
        assert f.end_date is not None

    def test_top_n_filter(self):
        """测试前N篇筛选"""
        f = ArticleFilter.top_n(10)
        
        assert f.max_count == 10

    def test_matches_keyword(self):
        """测试关键词匹配"""
        f = ArticleFilter(keyword="Python")
        
        item1 = ArticleListItem(aid="1", title="Python教程", link="http://1")
        item2 = ArticleListItem(aid="2", title="Java教程", link="http://2")
        item3 = ArticleListItem(aid="3", title="学习", link="http://3", digest="Python进阶")
        
        assert f.matches(item1) is True
        assert f.matches(item2) is False
        assert f.matches(item3) is True  # 匹配摘要

    def test_matches_original_only(self):
        """测试原创筛选"""
        f = ArticleFilter(original_only=True)
        
        item1 = ArticleListItem(aid="1", title="原创", link="http://1", is_original=True)
        item2 = ArticleListItem(aid="2", title="转载", link="http://2", is_original=False)
        
        assert f.matches(item1) is True
        assert f.matches(item2) is False

    def test_apply_filter(self):
        """测试应用筛选条件"""
        f = ArticleFilter(keyword="Python", max_count=2)
        
        items = [
            ArticleListItem(aid="1", title="Python基础", link="http://1"),
            ArticleListItem(aid="2", title="Java入门", link="http://2"),
            ArticleListItem(aid="3", title="Python进阶", link="http://3"),
            ArticleListItem(aid="4", title="Python高级", link="http://4"),
        ]
        
        filtered = f.apply(items)
        
        assert len(filtered) == 2  # max_count限制
        assert all("Python" in item.title for item in filtered)

    def test_description(self):
        """测试筛选条件描述"""
        f = ArticleFilter(keyword="Python", original_only=True, max_count=10)
        
        desc = f.description
        
        assert "Python" in desc
        assert "仅原创" in desc
        assert "最多" in desc

    def test_invalid_date_range(self):
        """测试无效日期范围"""
        with pytest.raises(ValueError, match="开始日期不能晚于结束日期"):
            ArticleFilter(
                start_date=datetime(2024, 12, 31),
                end_date=datetime(2024, 1, 1),
            )


class TestBatchExportOptions:
    """批量导出选项测试"""

    def test_default_options(self):
        """测试默认选项"""
        opts = BatchExportOptions()
        
        assert opts.export_format == ExportFormat.TXT
        assert opts.link_format == LinkFormat.RAW
        assert opts.deduplicate is True

    def test_simple_txt(self):
        """测试简单TXT导出"""
        opts = BatchExportOptions.simple_txt()
        
        assert opts.export_format == ExportFormat.TXT
        assert opts.include_metadata is False

    def test_markdown_with_titles(self):
        """测试Markdown导出"""
        opts = BatchExportOptions.markdown_with_titles()
        
        assert opts.export_format == ExportFormat.MARKDOWN
        assert opts.link_format == LinkFormat.MARKDOWN
        assert opts.include_digest is True

    def test_full_json(self):
        """测试完整JSON导出"""
        opts = BatchExportOptions.full_json()
        
        assert opts.export_format == ExportFormat.JSON
        assert opts.include_metadata is True

    def test_csv_for_analysis(self):
        """测试分析用CSV导出"""
        opts = BatchExportOptions.csv_for_analysis()
        
        assert opts.export_format == ExportFormat.CSV
        assert opts.group_by_account is True

    def test_get_file_extension(self):
        """测试获取文件扩展名"""
        assert BatchExportOptions(export_format=ExportFormat.TXT).get_file_extension() == ".txt"
        assert BatchExportOptions(export_format=ExportFormat.CSV).get_file_extension() == ".csv"
        assert BatchExportOptions(export_format=ExportFormat.JSON).get_file_extension() == ".json"
        assert BatchExportOptions(export_format=ExportFormat.MARKDOWN).get_file_extension() == ".md"

    def test_generate_filename(self):
        """测试生成文件名"""
        opts = BatchExportOptions(timestamp_filename=False)
        
        filename = opts.generate_filename(account_name="测试号")
        
        assert filename.startswith("wechat_articles")
        assert "测试号" in filename
        assert filename.endswith(".txt")

    def test_generate_filename_with_timestamp(self):
        """测试生成带时间戳的文件名"""
        opts = BatchExportOptions(timestamp_filename=True)
        
        filename = opts.generate_filename()
        
        assert "20" in filename  # 年份

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        opts = BatchExportOptions(
            export_format=ExportFormat.JSON,
            link_format=LinkFormat.MARKDOWN,
            group_by_account=True,
        )
        
        d = opts.to_dict()
        restored = BatchExportOptions.from_dict(d)
        
        assert restored.export_format == ExportFormat.JSON
        assert restored.link_format == LinkFormat.MARKDOWN
        assert restored.group_by_account is True
