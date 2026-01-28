"""文本处理工具"""

import re
from collections.abc import Iterator


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def clean_whitespace(text: str) -> str:
    """清理多余空白"""
    # 合并多个空白字符为单个空格
    text = re.sub(r"[ \t]+", " ", text)
    # 合并多个换行为最多两个
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 4000,
    overlap: int = 200,
) -> Iterator[str]:
    """
    分块文本 (用于长文本处理)

    Args:
        text: 原始文本
        chunk_size: 每块大小（字符数）
        overlap: 块之间的重叠字符数

    Yields:
        文本块
    """
    if len(text) <= chunk_size:
        yield text
        return

    start = 0
    while start < len(text):
        end = start + chunk_size

        # 尝试在段落边界切分
        if end < len(text):
            # 向后查找换行符
            newline_pos = text.rfind("\n", start + chunk_size // 2, end)
            if newline_pos > start:
                end = newline_pos + 1

        yield text[start:end]
        start = end - overlap

        # 避免无限循环
        if start >= len(text):
            break


def extract_numbers(text: str) -> list[float]:
    """从文本中提取数字"""
    pattern = r"[-+]?\d*\.?\d+"
    return [float(x) for x in re.findall(pattern, text)]


def count_words(text: str) -> int:
    """统计字数（中英文混合）"""
    # 中文字符数
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    # 英文单词数
    english = len(re.findall(r"[a-zA-Z]+", text))
    return chinese + english


def remove_html_tags(html: str) -> str:
    """移除HTML标签"""
    clean = re.compile(r"<.*?>")
    return re.sub(clean, "", html)


def normalize_url(url: str) -> str:
    """标准化URL"""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # 移除末尾斜杠
    return url.rstrip("/")
