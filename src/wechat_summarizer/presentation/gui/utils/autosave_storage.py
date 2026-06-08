"""Draft persistence for GUI autosave."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any, cast

from .autosave_constants import DRAFT_EXPIRE_DAYS, MAX_DRAFT_SIZE, MAX_DRAFTS_PER_FORM
from .autosave_encryptor import SimpleEncryptor
from .autosave_models import Draft

logger = logging.getLogger(__name__)


class DraftStorage:
    """草稿存储管理"""

    def __init__(self, storage_dir: str | None = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.path.expanduser("~"), ".wechat_summarizer", "drafts")

        self._storage_dir = storage_dir
        self._encryptor = SimpleEncryptor()
        self._ensure_dir()
        self._cleanup_expired()

    def _ensure_dir(self) -> None:
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
        except Exception as exc:
            logger.error("创建草稿目录失败: %s", exc)

    def _get_file_path(self, form_id: str) -> str:
        safe_id = hashlib.md5(form_id.encode(), usedforsecurity=False).hexdigest()
        return os.path.join(self._storage_dir, f"draft_{safe_id}.json")

    def save(self, draft: Draft) -> bool:
        """保存草稿"""
        try:
            file_path = self._get_file_path(draft.form_id)
            drafts = self._load_drafts(draft.form_id)
            draft_dict = self._draft_to_dict(draft)
            drafts.append(draft_dict)

            if len(drafts) > MAX_DRAFTS_PER_FORM:
                drafts = drafts[-MAX_DRAFTS_PER_FORM:]

            content = json.dumps(drafts, ensure_ascii=False)
            if len(content) > MAX_DRAFT_SIZE:
                logger.warning("草稿大小超限，仅保留最新版本")
                drafts = [draft_dict]

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(drafts, file, ensure_ascii=False, indent=2)

            return True
        except Exception as exc:
            logger.error("保存草稿失败: %s", exc)
            return False

    def _draft_to_dict(self, draft: Draft) -> dict[str, Any]:
        data = draft.data.copy()
        if draft.encrypted:
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self._encryptor.encrypt(value)

        return {
            "form_id": draft.form_id,
            "data": data,
            "timestamp": draft.timestamp,
            "version": draft.version,
            "encrypted": draft.encrypted,
        }

    def _load_drafts(self, form_id: str) -> list[dict[str, Any]]:
        try:
            file_path = self._get_file_path(form_id)
            if os.path.exists(file_path):
                with open(file_path, encoding="utf-8") as file:
                    payload = json.load(file)
                    if isinstance(payload, list):
                        return cast(list[dict[str, Any]], payload)
        except Exception as exc:
            logger.warning("加载草稿失败: %s", exc)
        return []

    def load_latest(self, form_id: str) -> Draft | None:
        """加载最新草稿"""
        drafts = self._load_drafts(form_id)
        if not drafts:
            return None

        return self._dict_to_draft(drafts[-1])

    def load_history(self, form_id: str) -> list[Draft]:
        """加载草稿历史"""
        return [self._dict_to_draft(draft) for draft in self._load_drafts(form_id)]

    def _dict_to_draft(self, draft_data: dict[str, Any]) -> Draft:
        data = draft_data["data"].copy()
        if draft_data.get("encrypted"):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self._encryptor.decrypt(value)

        return Draft(
            form_id=draft_data["form_id"],
            data=data,
            timestamp=draft_data["timestamp"],
            version=draft_data.get("version", 1),
            encrypted=draft_data.get("encrypted", False),
        )

    def delete(self, form_id: str) -> bool:
        """删除表单草稿"""
        try:
            file_path = self._get_file_path(form_id)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as exc:
            logger.error("删除草稿失败: %s", exc)
            return False

    def _cleanup_expired(self) -> None:
        try:
            expire_time = time.time() - (DRAFT_EXPIRE_DAYS * 24 * 3600)

            for filename in os.listdir(self._storage_dir):
                if not filename.startswith("draft_"):
                    continue

                self._cleanup_file(filename, expire_time)
        except Exception as exc:
            logger.warning("清理过期草稿失败: %s", exc)

    def _cleanup_file(self, filename: str, expire_time: float) -> None:
        file_path = os.path.join(self._storage_dir, filename)
        try:
            with open(file_path, encoding="utf-8") as file:
                drafts = json.load(file)

            valid_drafts = [draft for draft in drafts if draft.get("timestamp", 0) > expire_time]

            if not valid_drafts:
                os.remove(file_path)
            elif len(valid_drafts) < len(drafts):
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(valid_drafts, file, ensure_ascii=False)
        except Exception:
            pass


__all__ = ["DraftStorage"]
