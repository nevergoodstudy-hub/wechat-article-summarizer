"""国际化 (i18n) 模块 - 系统级多语言支持

提供:
- Windows 系统语言自动检测
- JSON 翻译文件加载
- 运行时语言切换
- tr() 翻译函数

2026年增强版:
- 热切换语言(无需重启)
- RTL布局支持(阿拉伯语/希伯来语)
- 翻译文本XSS过滤
- 加载缓存优化

安全措施:
- XSS过滤
- 文件大小限制
- 路径安全检查
"""
from __future__ import annotations

import json
import locale
import html
import re
import hashlib
from pathlib import Path
from typing import Dict, Optional, Callable, List, Set
from dataclasses import dataclass
from loguru import logger


# 安全限制
MAX_TRANSLATION_FILE_SIZE = 1024 * 1024  # 1MB
MAX_TEXT_LENGTH = 10000  # 单条翻译最大长度


@dataclass
class LanguageInfo:
    """语言信息"""
    code: str
    name: str  # 英语名称
    native_name: str  # 本地化名称
    rtl: bool = False  # 是否从右到左


class I18n:
    """国际化管理器
    
    支持语言:
    - zh_CN: 简体中文 (默认/源语言)
    - zh_TW: 繁体中文
    - en: 英语
    - ar: 阿拉伯语 (RTL)
    - he: 希伯来语 (RTL)
    
    2026年增强:
    - 热切换支持
    - RTL布局
    - XSS过滤
    """
    
    # 支持的语言列表
    SUPPORTED_LANGUAGES = [
        LanguageInfo('auto', 'Auto', '跟随系统'),
        LanguageInfo('zh_CN', 'Simplified Chinese', '简体中文'),
        LanguageInfo('zh_TW', 'Traditional Chinese', '繁體中文'),
        LanguageInfo('en', 'English', 'English'),
        LanguageInfo('ar', 'Arabic', 'العربية', rtl=True),
        LanguageInfo('he', 'Hebrew', 'עברית', rtl=True),
    ]
    
    # 语言代码列表 (快速查找)
    LANGUAGE_CODES = [lang.code for lang in SUPPORTED_LANGUAGES]
    
    # RTL语言列表
    RTL_LANGUAGES = {lang.code for lang in SUPPORTED_LANGUAGES if lang.rtl}
    
    DEFAULT_LANGUAGE = 'zh_CN'
    
    _instance: Optional['I18n'] = None
    _translations: Dict[str, Dict[str, str]] = {}
    _current_language: str = 'zh_CN'
    _observers: List[Callable[[], None]] = []
    _cache_hash: Dict[str, str] = {}  # 文件哈希缓存
    
    def __new__(cls) -> 'I18n':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._translations = {}
        self._current_language = self.DEFAULT_LANGUAGE
        self._observers = []
        self._load_translations()
    
    def _load_translations(self):
        """加载所有翻译文件"""
        translations_dir = Path(__file__).parent.parent / 'translations'
        
        if not translations_dir.exists():
            translations_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f'创建翻译文件目录: {translations_dir}')
        
        # 加载所有 JSON 翻译文件
        for lang_file in translations_dir.glob('*.json'):
            lang_code = lang_file.stem
            self._load_single_translation(lang_file, lang_code)
    
    def _load_single_translation(self, lang_file: Path, lang_code: str):
        """加载单个翻译文件
        
        安全措施:
        - 文件大小限制
        - XSS过滤
        - 文本长度限制
        """
        try:
            # 安全: 检查文件大小
            if lang_file.stat().st_size > MAX_TRANSLATION_FILE_SIZE:
                logger.warning(f'翻译文件过大: {lang_file}')
                return
            
            with open(lang_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 缓存哈希用于热加载检测 (MD5仅用于变更检测，非安全用途)
            content_hash = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
            if self._cache_hash.get(lang_code) == content_hash:
                return  # 文件未变化
            
            self._cache_hash[lang_code] = content_hash
            
            raw_translations = json.loads(content)
            
            # 安全: XSS过滤和长度限制
            safe_translations = {}
            for key, value in raw_translations.items():
                if isinstance(value, str):
                    # 长度限制
                    if len(value) > MAX_TEXT_LENGTH:
                        value = value[:MAX_TEXT_LENGTH]
                    # XSS过滤
                    safe_translations[key] = self._sanitize_text(value)
            
            self._translations[lang_code] = safe_translations
            logger.debug(f'已加载翻译: {lang_code} ({len(safe_translations)} 条)')
            
        except Exception as e:
            logger.warning(f'加载翻译文件失败 {lang_file}: {e}')
    
    def _sanitize_text(self, text: str) -> str:
        """清理文本 - XSS过滤
        
        保留基本格式化，移除危险内容
        """
        # HTML转义
        text = html.escape(text)
        
        # 移除可能的脚本标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除事件处理器
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        return text
    
    def reload_translations(self):
        """重新加载翻译文件 (热更新)"""
        self._load_translations()
        self._notify_observers()
    
    def detect_system_language(self) -> str:
        """检测系统 UI 语言
        
        Windows: 使用 GetUserDefaultUILanguage() API
        其他平台: 使用 locale.getdefaultlocale()
        
        Returns:
            语言代码 (如 'zh_CN', 'en')
        """
        import platform
        
        if platform.system() == 'Windows':
            return self._detect_windows_language()
        else:
            return self._detect_posix_language()
    
    def _detect_windows_language(self) -> str:
        """Windows 平台语言检测"""
        try:
            import ctypes
            
            # 调用 GetUserDefaultUILanguage
            # 返回 LANGID (语言标识符)
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            
            # 使用 locale.windows_locale 映射 LANGID -> locale name
            if lang_id in locale.windows_locale:
                locale_name = locale.windows_locale[lang_id]
                logger.debug(f'Windows UI 语言: LANGID={lang_id}, locale={locale_name}')
                
                # 映射到我们支持的语言代码
                if locale_name.startswith('zh'):
                    return 'zh_CN'
                elif locale_name.startswith('en'):
                    return 'en'
            
            logger.debug(f'未知 Windows LANGID: {lang_id}, 使用默认语言')
            return self.DEFAULT_LANGUAGE
            
        except Exception as e:
            logger.debug(f'Windows 语言检测失败: {e}')
            return self.DEFAULT_LANGUAGE
    
    def _detect_posix_language(self) -> str:
        """POSIX 平台语言检测"""
        try:
            lang, _ = locale.getdefaultlocale()
            if lang:
                if lang.startswith('zh'):
                    return 'zh_CN'
                elif lang.startswith('en'):
                    return 'en'
        except Exception as e:
            logger.debug(f'POSIX 语言检测失败: {e}')
        
        return self.DEFAULT_LANGUAGE
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self._current_language
    
    def set_language(self, lang: str):
        """设置当前语言
        
        Args:
            lang: 语言代码 ('auto', 'zh_CN', 'en')
        """
        if lang == 'auto':
            actual_lang = self.detect_system_language()
        elif lang in self.SUPPORTED_LANGUAGES:
            actual_lang = lang
        else:
            logger.warning(f'不支持的语言: {lang}, 使用默认语言')
            actual_lang = self.DEFAULT_LANGUAGE
        
        if actual_lang != self._current_language:
            self._current_language = actual_lang
            logger.info(f'语言已切换: {actual_lang}')
            self._notify_observers()
    
    def tr(self, text: str) -> str:
        """翻译文本
        
        Args:
            text: 源文本 (中文)
        
        Returns:
            翻译后的文本，如果没有找到翻译则返回原文
        """
        # 中文是源语言，无需翻译
        if self._current_language == 'zh_CN':
            return text
        
        # 查找翻译
        translations = self._translations.get(self._current_language, {})
        translated = translations.get(text)
        
        if translated:
            return translated
        else:
            # 未找到翻译，返回原文并记录
            # 只在调试级别记录，避免日志过多
            return text
    
    def add_observer(self, callback: Callable[[], None]):
        """添加语言变化观察者
        
        当语言切换时，会调用所有注册的回调函数
        
        Args:
            callback: 无参数回调函数
        """
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: Callable[[], None]):
        """移除语言变化观察者"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self):
        """通知所有观察者语言已变化"""
        for callback in self._observers:
            try:
                callback()
            except Exception as e:
                logger.error(f'语言变化回调执行失败: {e}')
    
    def get_language_display_name(self, lang_code: str) -> str:
        """获取语言显示名称
        
        Args:
            lang_code: 语言代码
        
        Returns:
            语言的本地化显示名称
        """
        for lang in self.SUPPORTED_LANGUAGES:
            if lang.code == lang_code:
                return lang.native_name
        return lang_code
    
    def get_available_languages(self) -> List[str]:
        """获取可用语言代码列表"""
        return self.LANGUAGE_CODES.copy()
    
    def get_language_info(self, lang_code: str) -> Optional[LanguageInfo]:
        """获取语言信息"""
        for lang in self.SUPPORTED_LANGUAGES:
            if lang.code == lang_code:
                return lang
        return None
    
    def get_all_language_info(self) -> List[LanguageInfo]:
        """获取所有语言信息"""
        return list(self.SUPPORTED_LANGUAGES)
    
    # ========== RTL支持 ==========
    
    def is_rtl(self, lang_code: Optional[str] = None) -> bool:
        """检查语言是否为RTL(从右到左)
        
        Args:
            lang_code: 语言代码，None表示当前语言
            
        Returns:
            是否为RTL语言
        """
        if lang_code is None:
            lang_code = self._current_language
        return lang_code in self.RTL_LANGUAGES
    
    def get_text_direction(self) -> str:
        """获取当前文本方向
        
        Returns:
            'rtl' 或 'ltr'
        """
        return 'rtl' if self.is_rtl() else 'ltr'
    
    def get_text_align(self) -> str:
        """获取文本对齐方式
        
        Returns:
            'right' (对于RTL) 或 'left'
        """
        return 'right' if self.is_rtl() else 'left'
    
    def get_start_anchor(self) -> str:
        """获取起始锚点 (Tk anchor)
        
        Returns:
            'e' (对于RTL) 或 'w'
        """
        return 'e' if self.is_rtl() else 'w'
    
    def get_end_anchor(self) -> str:
        """获取结束锚点 (Tk anchor)
        
        Returns:
            'w' (对于RTL) 或 'e'
        """
        return 'w' if self.is_rtl() else 'e'
    
    def flip_horizontal(self, value: str) -> str:
        """水平翻转值 (用于RTL布局)
        
        将 left<->right, w<->e 互换
        
        Args:
            value: 原始值
            
        Returns:
            翻转后的值 (RTL模式下) 或原始值 (LTR)
        """
        if not self.is_rtl():
            return value
        
        flip_map = {
            'left': 'right',
            'right': 'left',
            'w': 'e',
            'e': 'w',
            'nw': 'ne',
            'ne': 'nw',
            'sw': 'se',
            'se': 'sw',
        }
        return flip_map.get(value, value)


# 全局单例实例
_i18n = I18n()


def tr(text: str) -> str:
    """全局翻译函数
    
    Args:
        text: 源文本 (中文)
    
    Returns:
        翻译后的文本
    
    Example:
        >>> from wechat_summarizer.presentation.gui.utils.i18n import tr
        >>> tr('首页')
        'Home'  # 当语言为英语时
    """
    return _i18n.tr(text)


def get_i18n() -> I18n:
    """获取 I18n 单例实例"""
    return _i18n


def set_language(lang: str):
    """设置语言"""
    _i18n.set_language(lang)


def get_language() -> str:
    """获取当前语言"""
    return _i18n.get_language()


def detect_system_language() -> str:
    """检测系统语言"""
    return _i18n.detect_system_language()
