"""OneNote 导出器（Microsoft Graph）

实现目标：写入指定 OneNote Notebook/Section（创建页面并写入摘要/链接）。

鉴权方式：Microsoft identity platform OAuth2 Device Code Flow（委托权限）
- 首次使用需要运行 CLI 命令获取 token，并缓存到本地文件
- 后续使用 refresh_token 自动续期

参考（Microsoft Learn）：
- Device code flow
- Create OneNote page: POST /me/onenote/sections/{id}/pages (Content-Type: application/xhtml+xml)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from ....domain.entities import Article
from ....shared.constants import CONFIG_DIR_NAME
from ....shared.exceptions import ExporterAuthError, ExporterError
from .base import BaseExporter


@dataclass(frozen=True)
class OneNoteConfig:
    client_id: str
    tenant: str
    notebook: str
    section: str
    timeout: int = 20
    graph_base_url: str = "https://graph.microsoft.com/v1.0"
    scopes: tuple[str, ...] = (
        "Notes.ReadWrite",
        "offline_access",
    )


class _TokenCache:
    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> dict[str, Any] | None:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return None

        if isinstance(data, dict):
            # 确保 key 为 str（token 缓存约定使用字符串键）
            return {str(k): v for k, v in data.items()}

        return None

    def save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def clear(self) -> None:
        try:
            if self._path.exists():
                self._path.unlink()
        except Exception:
            # best-effort
            pass


class _DeviceCodeAuth:
    def __init__(self, cfg: OneNoteConfig, token_cache: _TokenCache):
        self._cfg = cfg
        self._cache = token_cache

    def has_refresh_token(self) -> bool:
        data = self._cache.load() or {}
        return bool(data.get("refresh_token"))

    def clear_cache(self) -> None:
        self._cache.clear()

    def authenticate_device_code(self) -> str:
        """交互式设备码登录。

        返回：给 CLI 展示的提示信息。
        """
        oauth_base = f"https://login.microsoftonline.com/{self._cfg.tenant}/oauth2/v2.0"
        device_endpoint = f"{oauth_base}/devicecode"
        token_endpoint = f"{oauth_base}/token"

        scopes = " ".join(self._cfg.scopes)

        with httpx.Client(timeout=self._cfg.timeout) as client:
            resp = client.post(
                device_endpoint, data={"client_id": self._cfg.client_id, "scope": scopes}
            )
            if resp.status_code >= 400:
                raise ExporterAuthError(
                    f"OneNote 设备码请求失败 (HTTP {resp.status_code}): {resp.text}"
                )

            device = resp.json()
            message = device.get("message") or "请按提示完成登录。"
            user_code = device.get("user_code")
            verification_uri = device.get("verification_uri")
            interval = int(device.get("interval") or 5)
            expires_in = int(device.get("expires_in") or 900)
            device_code = device.get("device_code")

            if not device_code:
                raise ExporterAuthError("OneNote 设备码响应缺少 device_code")

            # 轮询 token
            deadline = time.time() + expires_in
            while time.time() < deadline:
                time.sleep(interval)
                token_resp = client.post(
                    token_endpoint,
                    data={
                        "client_id": self._cfg.client_id,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "device_code": device_code,
                    },
                )

                if token_resp.status_code == 200:
                    token = token_resp.json()
                    token["obtained_at"] = int(time.time())
                    self._cache.save(token)
                    logger.info("OneNote 已完成授权并写入本地 token 缓存")
                    return message

                # 错误处理
                err: dict[str, Any]
                try:
                    err = token_resp.json()
                except Exception:
                    raise ExporterAuthError(
                        f"OneNote token 轮询失败 (HTTP {token_resp.status_code}): {token_resp.text}"
                    )

                code = (err.get("error") or "").lower()
                desc = err.get("error_description") or ""
                if code == "authorization_pending":
                    continue
                if code == "slow_down":
                    interval += 5
                    continue
                if code in {
                    "expired_token",
                    "access_denied",
                    "authorization_declined",
                    "bad_verification_code",
                }:
                    raise ExporterAuthError(f"OneNote 授权失败: {code}: {desc}")

                raise ExporterAuthError(f"OneNote 授权异常: {code}: {desc}")

        # 超时
        msg = "OneNote 授权超时：未在有效期内完成登录"
        if user_code and verification_uri:
            msg += f"（code={user_code}, url={verification_uri}）"
        raise ExporterAuthError(msg)

    def get_access_token(self, force_refresh: bool = False) -> str:
        token = self._cache.load() or {}
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token")

        if not refresh_token:
            raise ExporterAuthError("OneNote 未授权：请先运行 `wechat-summarizer onenote-auth`")

        if not force_refresh and access_token and not self._is_expired(token):
            return str(access_token)

        # refresh
        oauth_base = f"https://login.microsoftonline.com/{self._cfg.tenant}/oauth2/v2.0"
        token_endpoint = f"{oauth_base}/token"
        scopes = " ".join(self._cfg.scopes)

        with httpx.Client(timeout=self._cfg.timeout) as client:
            resp = client.post(
                token_endpoint,
                data={
                    "client_id": self._cfg.client_id,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "scope": scopes,
                },
            )

        if resp.status_code >= 400:
            # refresh_token 可能已失效，提示重新授权
            try:
                err = resp.json()
            except Exception:
                err = {"error": "", "error_description": resp.text}
            code = (err.get("error") or "").lower()
            desc = err.get("error_description") or resp.text
            raise ExporterAuthError(
                f"OneNote token 刷新失败: {code}: {desc}；请重新运行 `wechat-summarizer onenote-auth`"
            )

        new_token = resp.json()
        new_token["obtained_at"] = int(time.time())
        if "refresh_token" not in new_token:
            new_token["refresh_token"] = refresh_token
        self._cache.save(new_token)
        return str(new_token.get("access_token") or "")

    @staticmethod
    def _is_expired(token: dict[str, Any], skew_seconds: int = 60) -> bool:
        try:
            obtained_at = int(token.get("obtained_at") or 0)
            expires_in = int(token.get("expires_in") or 0)
        except Exception:
            return True

        if obtained_at <= 0 or expires_in <= 0:
            return True

        return time.time() >= (obtained_at + expires_in - skew_seconds)


class OneNoteExporter(BaseExporter):
    """OneNote 导出器（Graph API）"""

    def __init__(
        self,
        client_id: str = "",
        tenant: str = "common",
        notebook: str = "",
        section: str = "",
        token_cache_path: str | None = None,
        timeout: int = 20,
    ):
        cache_path = (
            Path(token_cache_path)
            if token_cache_path
            else (Path.home() / CONFIG_DIR_NAME / "onenote_token.json")
        )
        self._cfg = OneNoteConfig(
            client_id=client_id.strip(),
            tenant=(tenant.strip() or "common"),
            notebook=notebook.strip(),
            section=section.strip(),
            timeout=timeout,
        )
        self._token_cache = _TokenCache(cache_path)
        self._auth = _DeviceCodeAuth(self._cfg, self._token_cache)

    @property
    def name(self) -> str:
        return "onenote"

    @property
    def target(self) -> str:
        return "onenote"

    def is_available(self) -> bool:
        # 只有在配置齐全且已授权（存在 refresh_token）时才算“可用”
        return bool(
            self._cfg.client_id
            and self._cfg.notebook
            and self._cfg.section
            and self._auth.has_refresh_token()
        )

    # ---- CLI helpers ----
    def authenticate(self) -> str:
        """执行设备码授权并保存 token。"""
        if not self._cfg.client_id:
            raise ExporterError("OneNote 未配置 export.onenote_client_id")
        return self._auth.authenticate_device_code()

    def logout(self) -> None:
        """清除本地 token 缓存。"""
        self._auth.clear_cache()

    # ---- ExporterPort ----
    def export(self, article: Article, path: str | None = None, **options) -> str:
        if not (self._cfg.client_id and self._cfg.notebook and self._cfg.section):
            raise ExporterError(
                "OneNote 未配置（需要 export.onenote_client_id / export.onenote_notebook / export.onenote_section）"
            )

        include_content = bool(options.get("include_content", False))
        max_content_chars = int(options.get("max_content_chars", 8000))

        # 1) Resolve section id (find/create)
        section_id = self._ensure_section_id()

        # 2) Create page
        html = self._build_page_html(
            article, include_content=include_content, max_content_chars=max_content_chars
        )
        resp = self._graph_request(
            "POST",
            f"{self._cfg.graph_base_url}/me/onenote/sections/{section_id}/pages",
            headers={
                "Content-Type": "application/xhtml+xml",
                "Accept": "application/json",
            },
            content=html.encode("utf-8"),
        )

        if resp.status_code in (401, 403):
            raise ExporterAuthError(
                f"OneNote 鉴权失败 (HTTP {resp.status_code})；请运行 `wechat-summarizer onenote-auth` 重新授权"
            )
        if resp.status_code >= 400:
            raise ExporterError(f"OneNote 创建页面失败 (HTTP {resp.status_code}): {resp.text}")

        try:
            data = resp.json()
        except Exception:
            data = {}

        web_url = ((data.get("links") or {}).get("oneNoteWebUrl") or {}).get("href")
        if web_url:
            logger.info(f"OneNote 导出成功: {web_url}")
            return str(web_url)

        # fallback
        page_id = data.get("id") or ""
        logger.info(f"OneNote 导出成功: {page_id}")
        return str(page_id)

    # ---------------- internal helpers ----------------

    def _graph_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        token = self._auth.get_access_token()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(timeout=self._cfg.timeout) as client:
                resp = client.request(method, url, headers=headers, **kwargs)
        except ExporterAuthError:
            raise
        except Exception as e:
            raise ExporterError(f"OneNote Graph 请求失败: {e}") from e

        # 如果 access_token 失效，尝试强制刷新一次再重试
        if resp.status_code == 401:
            try:
                token = self._auth.get_access_token(force_refresh=True)
            except ExporterAuthError:
                return resp
            headers["Authorization"] = f"Bearer {token}"
            try:
                with httpx.Client(timeout=self._cfg.timeout) as client:
                    return client.request(method, url, headers=headers, **kwargs)
            except Exception:
                return resp

        return resp

    def _graph_list(self, url: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url: str | None = url

        while next_url:
            resp = self._graph_request("GET", next_url, headers={"Accept": "application/json"})
            if resp.status_code in (401, 403):
                raise ExporterAuthError(
                    f"OneNote 鉴权失败 (HTTP {resp.status_code})；请运行 `wechat-summarizer onenote-auth` 重新授权"
                )
            if resp.status_code >= 400:
                raise ExporterError(
                    f"OneNote Graph 列表请求失败 (HTTP {resp.status_code}): {resp.text}"
                )

            data = resp.json() if resp.content else {}
            items.extend(data.get("value") or [])
            next_url = data.get("@odata.nextLink")

        return items

    def _ensure_section_id(self) -> str:
        notebook_id = self._find_notebook_id(self._cfg.notebook)
        section = self._find_section(notebook_id, self._cfg.section)
        if section is not None:
            return str(section.get("id"))

        # create section
        resp = self._graph_request(
            "POST",
            f"{self._cfg.graph_base_url}/me/onenote/notebooks/{notebook_id}/sections",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"displayName": self._cfg.section},
        )

        if resp.status_code in (401, 403):
            raise ExporterAuthError(
                f"OneNote 鉴权失败 (HTTP {resp.status_code})；请运行 `wechat-summarizer onenote-auth` 重新授权"
            )
        if resp.status_code >= 400:
            raise ExporterError(f"OneNote 创建 Section 失败 (HTTP {resp.status_code}): {resp.text}")

        data = resp.json() if resp.content else {}
        section_id = data.get("id")
        if not section_id:
            raise ExporterError("OneNote 创建 Section 成功但响应缺少 id")
        return str(section_id)

    def _find_notebook_id(self, notebook_name: str) -> str:
        notebooks = self._graph_list(
            f"{self._cfg.graph_base_url}/me/onenote/notebooks?$select=id,displayName"
        )

        want = notebook_name.strip().lower()
        for nb in notebooks:
            if (nb.get("displayName") or "").strip().lower() == want:
                nb_id = nb.get("id")
                if nb_id:
                    return str(nb_id)

        available = ", ".join(
            sorted(
                {(n.get("displayName") or "").strip() for n in notebooks if n.get("displayName")}
            )
        )
        raise ExporterError(
            f"未找到 OneNote Notebook: {notebook_name}. 可用 notebooks: {available}"
        )

    def _find_section(self, notebook_id: str, section_name: str) -> dict[str, Any] | None:
        sections = self._graph_list(
            f"{self._cfg.graph_base_url}/me/onenote/notebooks/{notebook_id}/sections?$select=id,displayName"
        )

        want = section_name.strip().lower()
        for sec in sections:
            if (sec.get("displayName") or "").strip().lower() == want:
                return sec
        return None

    @staticmethod
    def _build_page_html(article: Article, include_content: bool, max_content_chars: int) -> str:
        title = escape(article.title or "Untitled")
        url = escape(str(article.url))

        account = escape(article.account_name or "未知")
        author = escape(article.author or "")
        publish_time = escape(article.publish_time_str)
        created = escape(datetime.utcnow().isoformat())

        # Summary
        summary_html = ""
        if article.summary:
            summary_text = escape(article.summary.content or "")
            summary_text = summary_text.replace("\n", "<br/>")

            key_points_html = ""
            if article.summary.key_points:
                key_points_html = (
                    "<ul>"
                    + "".join(f"<li>{escape(p)}</li>" for p in article.summary.key_points)
                    + "</ul>"
                )

            tags_html = ""
            if article.summary.tags:
                tags_html = (
                    "<p><b>标签:</b> " + ", ".join(escape(t) for t in article.summary.tags) + "</p>"
                )

            summary_html = (
                "<h2>摘要</h2>"
                f"<p>{summary_text}</p>"
                + ("<h3>关键要点</h3>" + key_points_html if key_points_html else "")
                + tags_html
            )

        content_html = ""
        if include_content:
            text = (article.content_text or "")[: max(0, max_content_chars)]
            text = escape(text)
            content_html = "<hr/><h2>正文（节选）</h2>" + f"<pre>{text}</pre>"

        # OneNote expects XHTML-ish full document
        return (
            "<!DOCTYPE html>"
            "<html>"
            "<head>"
            f"<title>{title}</title>"
            f'<meta name="created" content="{created}" />'
            "</head>"
            "<body>"
            f"<h1>{title}</h1>"
            f"<p><b>公众号:</b> {account}</p>"
            + (f"<p><b>作者:</b> {author}</p>" if author else "")
            + f"<p><b>发布时间:</b> {publish_time}</p>"
            + f'<p><b>原文链接:</b> <a href="{url}">{url}</a></p>'
            + "<hr/>"
            + summary_html
            + content_html
            + "</body>"
            "</html>"
        )
