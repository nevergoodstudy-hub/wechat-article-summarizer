"""剪贴板微信链接检测工具

自动检测剪贴板中的微信公众号文章链接，
支持浏览器当前页面探测。

2026年增强版:
- 批量URL识别(多行文本)
- 智能去重算法(基于核心参数)
- URL安全验证
- 支持更多URL格式

安全措施:
- URL白名单验证
- 最大URL数量限制
- 文本长度限制
- 恶意字符过滤
"""

from __future__ import annotations

import re
import subprocess
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict
from urllib.parse import urlparse, parse_qs, urlencode

from loguru import logger


# 安全限制常量
MAX_TEXT_LENGTH = 100000  # 最大文本长度 100KB
MAX_URLS = 50  # 最大URL数量
MAX_URL_LENGTH = 2048  # 单个URL最大长度


@dataclass
class DetectionResult:
    """检测结果"""
    links: List[str]  # 检测到的链接列表
    source: str  # 来源: "clipboard", "browser", "none"
    message: str  # 显示给用户的消息
    duplicates_removed: int = 0  # 去重移除的数量
    invalid_removed: int = 0  # 无效URL移除的数量


class WeChatLinkDetector:
    """微信公众号链接检测器
    
    增强版 (2026):
    - 支持更多URL格式
    - 智能去重(基于文章ID)
    - 安全验证
    """
    
    # 微信公众号文章URL模式 - 支持多种格式
    WECHAT_PATTERNS = [
        # 标准链接（带参数）- 使用非贪婪模式
        r'https?://mp\.weixin\.qq\.com/s\?[^\s\n\r<>"\'、。，！]+',
        # 短链接格式
        r'https?://mp\.weixin\.qq\.com/s/[A-Za-z0-9_-]+',
        # 带sn参数的链接
        r'https?://mp\.weixin\.qq\.com/s/[^\s\n\r<>"\']+__biz=[^\s\n\r<>"\']+',
        # 临时链接格式
        r'https?://mp\.weixin\.qq\.com/mp/appmsg/show\?[^\s\n\r<>"\']+',
    ]
    
    # 允许的域名白名单
    ALLOWED_DOMAINS = [
        'mp.weixin.qq.com',
        'weixin.qq.com',
    ]
    
    # 危险字符模式
    DANGEROUS_PATTERNS = [
        r'<script',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'on\w+\s*=',
    ]
    
    @classmethod
    def extract_links(
        cls, 
        text: str,
        smart_dedup: bool = True
    ) -> tuple[List[str], int, int]:
        """从文本中提取微信公众号链接
        
        Args:
            text: 要检测的文本
            smart_dedup: 是否启用智能去重（基于文章ID）
            
        Returns:
            (检测到的链接列表, 去重数量, 无效数量)
        """
        if not text:
            return [], 0, 0
        
        # 安全检查: 限制文本长度
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"文本过长({len(text)}字符)，截断至{MAX_TEXT_LENGTH}")
            text = text[:MAX_TEXT_LENGTH]
        
        logger.debug(f"检测文本长度: {len(text)} 字符")
        
        # 收集所有匹配
        raw_links = []
        for pattern in cls.WECHAT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            logger.debug(f"模式匹配到 {len(matches)} 个")
            raw_links.extend(matches)
        
        # 清理和验证链接
        cleaned_links = []
        invalid_count = 0
        
        for link in raw_links:
            cleaned = cls._clean_url(link)
            if cleaned and cls.is_valid_wechat_link(cleaned):
                if cls._is_safe_url(cleaned):
                    cleaned_links.append(cleaned)
                else:
                    invalid_count += 1
                    logger.warning(f"检测到不安全URL: {cleaned[:50]}...")
            else:
                invalid_count += 1
        
        # 智能去重
        if smart_dedup:
            unique_links, dup_count = cls._smart_deduplicate(cleaned_links)
        else:
            unique_links, dup_count = cls._simple_deduplicate(cleaned_links)
        
        # 限制最大数量
        if len(unique_links) > MAX_URLS:
            logger.warning(f"URL数量超限({len(unique_links)})，截断至{MAX_URLS}")
            unique_links = unique_links[:MAX_URLS]
        
        logger.debug(f"最终提取到 {len(unique_links)} 个唯一链接")
        return unique_links, dup_count, invalid_count
    
    @classmethod
    def _clean_url(cls, url: str) -> Optional[str]:
        """清理URL"""
        if not url:
            return None
        
        # 移除首尾空白
        url = url.strip()
        
        # 移除尾部标点
        url = url.rstrip('.,;:!?"\'\\)>、。，！？】」』')
        
        # 处理HTML实体
        url = url.replace('&amp;', '&')
        url = url.replace('&lt;', '<')
        url = url.replace('&gt;', '>')
        url = url.replace('&quot;', '"')
        
        # 长度检查
        if len(url) > MAX_URL_LENGTH:
            return None
        
        return url
    
    @classmethod
    def _is_safe_url(cls, url: str) -> bool:
        """检查URL是否安全"""
        # 检查危险模式
        url_lower = url.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, url_lower):
                return False
        
        # 检查域名白名单
        try:
            parsed = urlparse(url)
            if parsed.netloc not in cls.ALLOWED_DOMAINS:
                return False
        except Exception:
            return False
        
        return True
    
    @classmethod
    def _smart_deduplicate(cls, links: List[str]) -> tuple[List[str], int]:
        """智能去重 - 基于文章核心参数
        
        微信文章的唯一标识通常是 __biz + mid + idx 或 短链接ID
        """
        seen_ids: Set[str] = set()
        unique_links: List[str] = []
        dup_count = 0
        
        for link in links:
            article_id = cls._extract_article_id(link)
            
            if article_id not in seen_ids:
                seen_ids.add(article_id)
                unique_links.append(link)
            else:
                dup_count += 1
        
        return unique_links, dup_count
    
    @classmethod
    def _simple_deduplicate(cls, links: List[str]) -> tuple[List[str], int]:
        """简单去重 - 基于完整URL"""
        seen: Set[str] = set()
        unique_links: List[str] = []
        dup_count = 0
        
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
            else:
                dup_count += 1
        
        return unique_links, dup_count
    
    @classmethod
    def _extract_article_id(cls, url: str) -> str:
        """提取文章唯一标识
        
        优先使用 __biz + mid + idx 组合
        其次使用短链接ID
        最后使用URL哈希
        """
        try:
            parsed = urlparse(url)
            
            # 短链接: /s/xxxxx
            if '/s/' in parsed.path:
                path_parts = parsed.path.split('/s/')
                if len(path_parts) > 1:
                    short_id = path_parts[1].split('?')[0].split('#')[0]
                    if short_id and len(short_id) > 5:
                        return f"short:{short_id}"
            
            # 标准链接: 解析参数
            params = parse_qs(parsed.query)
            
            biz = params.get('__biz', [''])[0]
            mid = params.get('mid', params.get('appmsgid', ['']))[0]
            idx = params.get('idx', params.get('itemidx', ['1']))[0]
            sn = params.get('sn', [''])[0]
            
            if biz and mid:
                return f"biz:{biz}:mid:{mid}:idx:{idx}"
            
            if sn:
                return f"sn:{sn}"
            
        except Exception as e:
            logger.debug(f"解析URL失败: {e}")
        
        # 回退: 使用URL哈希 (MD5仅用于去重标识，非安全用途)
        return f"hash:{hashlib.md5(url.encode(), usedforsecurity=False).hexdigest()[:16]}"
    
    @classmethod
    def is_valid_wechat_link(cls, url: str) -> bool:
        """验证是否为有效的微信公众号链接"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # 必须是HTTP(S)
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # 必须是微信域名
            if parsed.netloc not in cls.ALLOWED_DOMAINS:
                return False
            
            # 路径检查
            valid_paths = ['/s', '/s/', '/mp/appmsg']
            if not any(parsed.path.startswith(p) for p in valid_paths):
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def normalize_url(cls, url: str) -> str:
        """标准化URL - 移除追踪参数，保留核心参数"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # 核心参数
            core_params = ['__biz', 'mid', 'idx', 'sn', 'chksm']
            
            # 过滤参数
            filtered = {
                k: v[0] for k, v in params.items() 
                if k in core_params and v
            }
            
            if filtered:
                new_query = urlencode(filtered)
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
            
            return url
            
        except Exception:
            return url


class ClipboardManager:
    """剪贴板管理器 - 使用 pyperclip 安全访问剪贴板"""
    
    @staticmethod
    def get_clipboard_content() -> Optional[str]:
        """获取剪贴板内容
        
        Returns:
            剪贴板文本内容，失败返回None
        """
        # 使用 pyperclip（跨平台且安全）
        try:
            import pyperclip
            content = pyperclip.paste()
            if content:
                logger.debug(f"剪贴板内容长度: {len(content)} 字符")
            return content if content else None
        except Exception as e:
            logger.debug(f"pyperclip 获取剪贴板失败: {e}")
        
        # 回退到 tkinter
        try:
            import tkinter as tk
            temp_root = tk.Tk()
            temp_root.withdraw()
            try:
                content = temp_root.clipboard_get()
                logger.debug(f"剪贴板内容长度: {len(content) if content else 0} 字符")
                return content
            except tk.TclError:
                return None
            finally:
                temp_root.destroy()
        except Exception as e:
            logger.debug(f"tkinter 获取剪贴板失败: {e}")
            return None


class BrowserDetector:
    """浏览器探测器 - 检测当前浏览器是否在浏览微信公众号页面"""
    
    @staticmethod
    def get_active_browser_url() -> Optional[str]:
        """获取当前活动浏览器窗口的URL（仅Windows）
        
        Returns:
            当前浏览器URL，失败返回None
        """
        try:
            # 使用PowerShell脚本获取活动窗口信息
            # 这个方法需要UI Automation，可能不完全可靠
            ps_script = '''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            using System.Text;
            public class Win32 {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll")]
                public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
                [DllImport("user32.dll")]
                public static extern int GetWindowTextLength(IntPtr hWnd);
            }
"@
            $hwnd = [Win32]::GetForegroundWindow()
            $len = [Win32]::GetWindowTextLength($hwnd)
            $sb = New-Object System.Text.StringBuilder($len + 1)
            [Win32]::GetWindowText($hwnd, $sb, $sb.Capacity)
            $sb.ToString()
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            window_title = result.stdout.strip()
            
            # 检查窗口标题是否包含微信公众号相关内容
            if window_title and any(kw in window_title.lower() for kw in ['微信', 'wechat', 'mp.weixin']):
                logger.debug(f"检测到微信相关窗口: {window_title}")
                return window_title
            
            return None
            
        except Exception as e:
            logger.debug(f"浏览器探测失败: {e}")
            return None
    
    @staticmethod
    def check_wechat_browser_activity() -> bool:
        """检查是否有微信公众号相关浏览器活动
        
        Returns:
            是否检测到微信公众号页面
        """
        window_title = BrowserDetector.get_active_browser_url()
        return window_title is not None


class AutoLinkDetector:
    """自动链接检测器 - 整合剪贴板和浏览器检测
    
    增强版 (2026):
    - 支持批量URL检测
    - 智能去重报告
    - 安全验证
    """
    
    @staticmethod
    def detect(smart_dedup: bool = True) -> DetectionResult:
        """执行自动检测
        
        优先检测剪贴板，其次检测浏览器活动。
        
        Args:
            smart_dedup: 是否启用智能去重
        
        Returns:
            DetectionResult 检测结果
        """
        # 1. 检测剪贴板
        clipboard_content = ClipboardManager.get_clipboard_content()
        if clipboard_content:
            links, dup_count, invalid_count = WeChatLinkDetector.extract_links(
                clipboard_content, 
                smart_dedup=smart_dedup
            )
            if links:
                logger.info(f"从剪贴板检测到 {len(links)} 个微信链接")
                
                # 构建消息
                msg_parts = [f"从剪贴板检测到 {len(links)} 个微信公众号链接"]
                if dup_count > 0:
                    msg_parts.append(f"(去除 {dup_count} 个重复)")
                if invalid_count > 0:
                    msg_parts.append(f"(过滤 {invalid_count} 个无效)")
                
                return DetectionResult(
                    links=links,
                    source="clipboard",
                    message=" ".join(msg_parts),
                    duplicates_removed=dup_count,
                    invalid_removed=invalid_count
                )
        
        # 2. 检测浏览器活动
        if BrowserDetector.check_wechat_browser_activity():
            logger.info("检测到微信公众号浏览器活动")
            return DetectionResult(
                links=[],
                source="browser",
                message="检测到您正在浏览微信公众号页面\n请复制链接后重试"
            )
        
        # 3. 无检测结果
        return DetectionResult(
            links=[],
            source="none",
            message=""
        )
    
    @staticmethod
    def detect_from_text(
        text: str,
        smart_dedup: bool = True
    ) -> DetectionResult:
        """从指定文本检测链接
        
        Args:
            text: 要检测的文本
            smart_dedup: 是否启用智能去重
            
        Returns:
            DetectionResult 检测结果
        """
        if not text:
            return DetectionResult(
                links=[],
                source="text",
                message="输入文本为空"
            )
        
        links, dup_count, invalid_count = WeChatLinkDetector.extract_links(
            text,
            smart_dedup=smart_dedup
        )
        
        if links:
            msg_parts = [f"检测到 {len(links)} 个微信公众号链接"]
            if dup_count > 0:
                msg_parts.append(f"(去除 {dup_count} 个重复)")
            if invalid_count > 0:
                msg_parts.append(f"(过滤 {invalid_count} 个无效)")
            
            return DetectionResult(
                links=links,
                source="text",
                message=" ".join(msg_parts),
                duplicates_removed=dup_count,
                invalid_removed=invalid_count
            )
        
        return DetectionResult(
            links=[],
            source="text",
            message="未检测到有效的微信公众号链接"
        )
    
    @staticmethod
    def batch_detect(texts: List[str]) -> DetectionResult:
        """批量检测多个文本
        
        Args:
            texts: 文本列表
            
        Returns:
            DetectionResult 合并后的检测结果
        """
        all_links = []
        total_dups = 0
        total_invalid = 0
        
        for text in texts:
            if text:
                links, dups, invalid = WeChatLinkDetector.extract_links(text)
                all_links.extend(links)
                total_dups += dups
                total_invalid += invalid
        
        # 最终去重
        unique_links, final_dups = WeChatLinkDetector._smart_deduplicate(all_links)
        total_dups += final_dups
        
        if unique_links:
            msg_parts = [f"批量检测到 {len(unique_links)} 个微信公众号链接"]
            if total_dups > 0:
                msg_parts.append(f"(去除 {total_dups} 个重复)")
            
            return DetectionResult(
                links=unique_links,
                source="batch",
                message=" ".join(msg_parts),
                duplicates_removed=total_dups,
                invalid_removed=total_invalid
            )
        
        return DetectionResult(
            links=[],
            source="batch",
            message="批量检测未发现有效链接"
        )
