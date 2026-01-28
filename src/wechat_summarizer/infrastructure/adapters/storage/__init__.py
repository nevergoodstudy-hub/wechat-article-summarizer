"""存储适配器

用于文章的本地持久化/缓存。
"""

from .local_json import LocalJsonStorage

__all__ = ["LocalJsonStorage"]
