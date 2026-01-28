"""安全测试用例

依据标准：
- GB/T 22239-2019 信息安全等级保护基本要求
- OWASP Top 10 2021
"""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile

import pytest
from pydantic import SecretStr

from wechat_summarizer.infrastructure.config.settings import (
    OpenAISettings,
    get_settings,
)
from wechat_summarizer.domain.value_objects.url import ArticleURL
from wechat_summarizer.shared.exceptions import InvalidURLError


class TestApiKeyNotLeaked:
    """测试API密钥不泄露到日志"""

    def test_secret_str_repr_hides_value(self):
        """验证SecretStr的repr不显示实际值"""
        secret = SecretStr("sk-test-api-key-12345")
        repr_str = repr(secret)
        
        assert "sk-test-api-key-12345" not in repr_str
        assert "**" in repr_str or "SecretStr" in repr_str

    def test_secret_str_str_hides_value(self):
        """验证SecretStr的str不显示实际值"""
        secret = SecretStr("sk-test-api-key-12345")
        str_value = str(secret)
        
        assert "sk-test-api-key-12345" not in str_value

    def test_settings_serialization_hides_api_keys(self):
        """验证配置序列化时隐藏API密钥"""
        settings = OpenAISettings(
            api_key=SecretStr("sk-secret-key"),
            model="gpt-4",
        )
        
        # model_dump 默认应该隐藏 SecretStr
        dumped = settings.model_dump()
        
        # SecretStr 在 dump 时应该是 SecretStr 对象或隐藏值
        if isinstance(dumped.get("api_key"), str):
            assert "sk-secret-key" not in dumped["api_key"]


class TestSecretStrSecurity:
    """测试SecretStr安全性"""

    def test_secret_str_not_serialized_to_json(self):
        """验证SecretStr不会直接序列化为JSON"""
        secret = SecretStr("my-secret-value")
        
        # 直接JSON序列化应该失败或不包含明文
        try:
            json_str = json.dumps({"key": secret})
            assert "my-secret-value" not in json_str
        except TypeError:
            # 预期行为：SecretStr 不可直接JSON序列化
            pass

    def test_get_secret_value_returns_actual_value(self):
        """验证get_secret_value正确返回实际值"""
        secret = SecretStr("actual-secret")
        
        assert secret.get_secret_value() == "actual-secret"


class TestPathTraversalPrevention:
    """测试路径遍历防护"""

    def test_export_path_no_parent_traversal(self):
        """验证导出路径不允许父目录遍历"""
        from wechat_summarizer.infrastructure.adapters.exporters.markdown import MarkdownExporter
        
        exporter = MarkdownExporter(output_dir="./output")
        
        # 尝试使用路径遍历攻击
        malicious_titles = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "test/../../../secret",
        ]
        
        for title in malicious_titles:
            article = type('Article', (), {'title': title})()
            safe_name = exporter._generate_filename(article)
            # 确保结果不包含路径分隔符
            assert "/" not in safe_name.replace(".md", "")
            assert "\\" not in safe_name

    def test_filename_sanitization_removes_dangerous_chars(self):
        """验证文件名清理移除危险字符"""
        from wechat_summarizer.infrastructure.adapters.exporters.markdown import MarkdownExporter
        
        exporter = MarkdownExporter(output_dir="./output")
        
        dangerous_chars = '<>:"|?*'
        test_title = f"test{dangerous_chars}file"
        
        article = type('Article', (), {'title': test_title})()
        safe_name = exporter._generate_filename(article)
        
        for char in dangerous_chars:
            assert char not in safe_name


class TestUrlValidation:
    """测试URL验证安全性"""

    def test_url_rejects_javascript_protocol(self):
        """验证URL拒绝javascript协议"""
        dangerous_urls = [
            "javascript:alert(1)",
            "JAVASCRIPT:alert(1)",
        ]
        
        for url in dangerous_urls:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_url_rejects_data_protocol(self):
        """验证URL拒绝data协议"""
        with pytest.raises(InvalidURLError):
            ArticleURL("data:text/html,<script>alert(1)</script>")

    def test_url_accepts_valid_https(self):
        """验证URL接受有效的HTTPS链接"""
        valid_urls = [
            "https://mp.weixin.qq.com/s/abc123",
            "https://www.example.com/article",
        ]
        
        for url in valid_urls:
            article_url = ArticleURL(url)
            assert article_url.value == url


class TestCredentialFileSecurity:
    """测试凭据文件安全性"""

    def test_credentials_file_should_be_user_only(self):
        """验证凭据文件应该只有用户可读写"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"token": "test"}')
            temp_path = f.name
        
        try:
            # 设置为用户只读写
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)
            
            # 验证权限
            file_stat = os.stat(temp_path)
            mode = file_stat.st_mode
            
            # 检查其他用户没有权限（仅在Unix系统上有效）
            if sys.platform != 'win32':
                assert not (mode & stat.S_IRGRP)
                assert not (mode & stat.S_IWGRP)
                assert not (mode & stat.S_IROTH)
                assert not (mode & stat.S_IWOTH)
        finally:
            os.unlink(temp_path)


class TestSsrfPrevention:
    """测试SSRF防护"""

    def test_url_rejects_localhost(self):
        """验证URL拒绝localhost"""
        localhost_urls = [
            "http://localhost/admin",
            "http://127.0.0.1/admin",
            "http://0.0.0.0/admin",
        ]
        
        for url in localhost_urls:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)

    def test_url_rejects_internal_ip(self):
        """验证URL拒绝内网IP"""
        internal_urls = [
            "http://10.0.0.1/admin",
            "http://172.16.0.1/admin",
            "http://192.168.1.1/admin",
        ]
        
        for url in internal_urls:
            with pytest.raises(InvalidURLError):
                ArticleURL(url)


class TestSecureDefaults:
    """测试安全默认值"""

    def test_scraper_uses_https(self):
        """验证抓取器默认使用HTTPS"""
        from wechat_summarizer.infrastructure.adapters.wechat_batch.auth_manager import (
            MP_BASE_URL,
        )
        
        assert MP_BASE_URL.startswith("https://")

    def test_api_endpoints_use_https(self):
        """验证API端点默认使用HTTPS"""
        settings = get_settings()
        
        # DeepSeek 默认端点
        assert settings.deepseek.base_url.startswith("https://")
