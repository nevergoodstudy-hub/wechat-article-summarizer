"""本地 JSON 存储（用于缓存）

实现 StoragePort：
- save / get / get_by_url / list_recent / delete / exists
- cleanup_expired / clear_all / get_stats（缓存管理）

存储位置：默认写入用户目录下的 .wechat_summarizer/cache。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from loguru import logger

from ....domain.entities import Article
from ....domain.value_objects import ArticleContent, ArticleURL
from ....shared.constants import CACHE_DIR_NAME, CONFIG_DIR_NAME
from ....shared.exceptions import StorageError


@dataclass
class CacheConfig:
    """缓存配置"""

    max_age_hours: int = 24 * 7  # 默认7天过期
    max_entries: int = 1000  # 最大缓存条目数


@dataclass
class CacheStats:
    """缓存统计信息"""

    total_entries: int
    total_size_bytes: int
    oldest_entry: datetime | None
    newest_entry: datetime | None


class LocalJsonStorage:
    """本地 JSON 存储"""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        config: CacheConfig | None = None,
    ):
        self._dir = (
            Path(cache_dir) if cache_dir else (Path.home() / CONFIG_DIR_NAME / CACHE_DIR_NAME)
        )
        self._dir.mkdir(parents=True, exist_ok=True)
        self._config = config or CacheConfig()

        self._index_path = self._dir / "index.json"
        self._index: dict[str, str] = self._load_index()

    def save(self, article: Article) -> None:
        try:
            url = str(article.url)
            data = self._article_to_dict(article)

            path = self._dir / f"{article.id}.json"
            tmp_path = self._dir / f".{article.id}.json.tmp"
            # 原子写入：先写临时文件，再用 os.replace 覆盖
            tmp_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            import os

            os.replace(tmp_path, path)

            self._index[url] = str(article.id)
            self._persist_index()
        except Exception as e:
            raise StorageError(f"保存失败: {e}") from e

    def get(self, article_id: UUID) -> Article | None:
        path = self._dir / f"{article_id}.json"
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._dict_to_article(data)
        except Exception as e:
            raise StorageError(f"读取失败: {e}") from e

    def get_by_url(self, url: str) -> Article | None:
        try:
            normalized = str(ArticleURL.from_string(url))
        except Exception:
            normalized = url

        article_id = self._index.get(normalized)
        if not article_id:
            return None

        try:
            return self.get(UUID(article_id))
        except Exception as e:
            logger.warning(f"缓存读取失败，忽略: {e}")
            return None

    def list_recent(self, limit: int = 20) -> list[Article]:
        items: list[tuple[float, Path]] = []
        for p in self._dir.glob("*.json"):
            if p.name == self._index_path.name:
                continue
            try:
                items.append((p.stat().st_mtime, p))
            except Exception:
                continue

        items.sort(key=lambda x: x[0], reverse=True)

        result: list[Article] = []
        for _, p in items[:limit]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                result.append(self._dict_to_article(data))
            except Exception:
                continue
        return result

    def delete(self, article_id: UUID) -> bool:
        path = self._dir / f"{article_id}.json"
        if not path.exists():
            return False

        try:
            path.unlink()

            # 清理 index
            to_delete = [url for url, aid in self._index.items() if aid == str(article_id)]
            for url in to_delete:
                self._index.pop(url, None)
            self._persist_index()
            return True
        except Exception as e:
            raise StorageError(f"删除失败: {e}") from e

    def exists(self, url: str) -> bool:
        try:
            normalized = str(ArticleURL.from_string(url))
        except Exception:
            normalized = url
        return normalized in self._index

    # ---------------- 缓存管理 ----------------

    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        cleaned = 0
        cutoff = datetime.now() - timedelta(hours=self._config.max_age_hours)

        for cache_file in self._dir.glob("*.json"):
            if cache_file.name == self._index_path.name:
                continue

            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    # 获取article_id用于清理index
                    article_id = cache_file.stem
                    cache_file.unlink()

                    # 清理index
                    to_delete = [
                        url for url, aid in self._index.items() if aid == article_id
                    ]
                    for url in to_delete:
                        self._index.pop(url, None)

                    cleaned += 1
            except Exception as e:
                logger.warning(f"清理缓存文件失败 {cache_file}: {e}")

        if cleaned > 0:
            self._persist_index()
            logger.info(f"已清理 {cleaned} 条过期缓存")

        return cleaned

    def clear_all(self) -> int:
        """清理所有缓存，返回清理数量"""
        cleaned = 0

        for cache_file in self._dir.glob("*.json"):
            if cache_file.name == self._index_path.name:
                continue

            try:
                cache_file.unlink()
                cleaned += 1
            except Exception as e:
                logger.warning(f"删除缓存文件失败 {cache_file}: {e}")

        # 清空index
        self._index.clear()
        self._persist_index()

        logger.info(f"已清理所有缓存 ({cleaned} 条)")
        return cleaned

    def get_stats(self) -> CacheStats:
        """获取缓存统计信息"""
        total_entries = 0
        total_size = 0
        oldest: datetime | None = None
        newest: datetime | None = None

        for cache_file in self._dir.glob("*.json"):
            if cache_file.name == self._index_path.name:
                continue

            try:
                stat = cache_file.stat()
                total_entries += 1
                total_size += stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime)

                if oldest is None or mtime < oldest:
                    oldest = mtime
                if newest is None or mtime > newest:
                    newest = mtime
            except Exception:
                continue

        return CacheStats(
            total_entries=total_entries,
            total_size_bytes=total_size,
            oldest_entry=oldest,
            newest_entry=newest,
        )

    # ---------------- internal ----------------

    def _load_index(self) -> dict[str, str]:
        if not self._index_path.exists():
            return {}
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

        if isinstance(data, dict) and all(
            isinstance(k, str) and isinstance(v, str) for k, v in data.items()
        ):
            return data

        return {}

    def _persist_index(self) -> None:
        tmp_path = self._index_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        import os

        os.replace(tmp_path, self._index_path)

    @staticmethod
    def _article_to_dict(article: Article) -> dict[str, Any]:
        publish_time = article.publish_time.isoformat() if article.publish_time else None

        content_html = article.content_html
        content_text = article.content_text
        images = list(getattr(article.content, "images", ()) or ()) if article.content else []

        return {
            "id": str(article.id),
            "url": str(article.url),
            "title": article.title,
            "author": article.author,
            "account_name": article.account_name,
            "publish_time": publish_time,
            "content": {
                "html": content_html,
                "text": content_text,
                "images": images,
            },
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        }

    @staticmethod
    def _dict_to_article(data: dict[str, Any]) -> Article:
        from uuid import UUID, uuid4

        url = ArticleURL.from_string(data.get("url", ""))
        article_id = UUID(data.get("id")) if data.get("id") else uuid4()

        publish_time = data.get("publish_time")
        publish_dt = datetime.fromisoformat(publish_time) if publish_time else None

        created_at = data.get("created_at")
        created_dt = datetime.fromisoformat(created_at) if created_at else datetime.now()

        updated_at = data.get("updated_at")
        updated_dt = datetime.fromisoformat(updated_at) if updated_at else datetime.now()

        c = data.get("content") or {}
        content = ArticleContent(
            html=c.get("html", ""),
            text=c.get("text", ""),
            images=tuple(c.get("images", []) or []),
        )

        return Article(
            id=article_id,
            url=url,
            title=data.get("title", ""),
            author=data.get("author"),
            account_name=data.get("account_name"),
            publish_time=publish_dt,
            content=content,
            created_at=created_dt,
            updated_at=updated_dt,
        )
