"""微信公众平台认证管理器

处理微信公众平台的扫码登录、凭据管理和Token刷新。
基于 wechat-article-exporter 项目的认证流程实现。
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from loguru import logger

from ....application.ports.outbound.auth_port import (
    AuthCredentials,
    AuthPort,
    CredentialStoragePort,
    QRCodeData,
)
from ....infrastructure.config.settings import get_settings
from ..http_client_pool import ClientConfig, get_http_pool


# 微信公众平台相关URL
MP_BASE_URL = "https://mp.weixin.qq.com"
MP_LOGIN_URL = f"{MP_BASE_URL}/cgi-bin/bizlogin"
MP_QRCODE_URL = f"{MP_BASE_URL}/cgi-bin/loginqrcode"
MP_CHECK_URL = f"{MP_BASE_URL}/cgi-bin/loginauth"

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": f"{MP_BASE_URL}/",
    "Origin": MP_BASE_URL,
}


class WechatAuthManager:
    """
    微信公众平台认证管理器
    
    实现微信公众平台的扫码登录流程：
    1. 获取登录二维码
    2. 轮询扫码状态
    3. 获取登录凭据（Token和Cookies）
    4. 管理凭据的持久化和刷新
    
    使用方法:
        auth = WechatAuthManager(storage)
        
        # 检查是否已登录
        if auth.is_authenticated:
            credentials = auth.credentials
        else:
            # 获取二维码
            qr = await auth.get_qrcode()
            print(f"请扫描二维码: {qr.qrcode_url}")
            
            # 轮询状态
            while True:
                status, creds = await auth.poll_scan_status(qr.uuid)
                if status == 2:  # 登录成功
                    break
    """

    def __init__(
        self,
        storage: CredentialStoragePort | None = None,
        auto_load: bool = True,
    ) -> None:
        """初始化认证管理器
        
        Args:
            storage: 凭据存储适配器（可选）
            auto_load: 是否自动加载已保存的凭据
        """
        self._storage = storage
        self._credentials: AuthCredentials | None = None
        self._client: httpx.AsyncClient | None = None
        self._settings = get_settings()
        
        # 自动加载凭据
        if auto_load and storage:
            self._credentials = storage.load()
            if self._credentials:
                logger.debug("已加载保存的登录凭据")

    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        if self._credentials is None:
            return False
        if self._credentials.is_expired:
            logger.debug("凭据已过期")
            return False
        return True

    @property
    def credentials(self) -> AuthCredentials | None:
        """获取当前凭据"""
        return self._credentials

    @property
    def token(self) -> str | None:
        """获取Token"""
        return self._credentials.token if self._credentials else None

    @property
    def cookies(self) -> dict[str, str]:
        """获取Cookies"""
        return self._credentials.cookies if self._credentials else {}

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            pool = get_http_pool()
            pool.configure(
                "mp.weixin.qq.com",
                ClientConfig(
                    timeout_read=30.0,
                    headers=DEFAULT_HEADERS.copy(),
                ),
            )
            self._client = await pool.get_client("mp.weixin.qq.com")
        return self._client

    async def get_qrcode(self) -> QRCodeData:
        """获取登录二维码
        
        Returns:
            二维码数据
            
        Raises:
            Exception: 获取二维码失败
        """
        client = await self._get_client()
        
        # 先访问登录页面获取初始cookies
        login_page_url = f"{MP_LOGIN_URL}?action=startlogin"
        resp = await client.get(login_page_url)
        
        # 获取二维码
        qrcode_url = f"{MP_QRCODE_URL}?action=getqrcode&param=4300"
        resp = await client.get(qrcode_url, follow_redirects=True)
        
        if resp.status_code != 200:
            raise Exception(f"获取二维码失败: HTTP {resp.status_code}")

        # 解析响应，提取uuid
        # 二维码页面会重定向，从URL或响应中提取uuid
        uuid = self._extract_uuid(resp)
        
        # 构造二维码图片URL
        qr_image_url = f"https://mp.weixin.qq.com/cgi-bin/loginqrcode?action=getqrcode&param=4300&rd={int(time.time())}"
        
        logger.info("已获取登录二维码")
        
        return QRCodeData(
            qrcode_url=qr_image_url,
            uuid=uuid,
            expires_in=300,
        )

    def _extract_uuid(self, response: httpx.Response) -> str:
        """从响应中提取uuid"""
        # 尝试从URL参数提取
        parsed = urlparse(str(response.url))
        params = parse_qs(parsed.query)
        if "uuid" in params:
            return params["uuid"][0]
        
        # 尝试从cookie提取
        for cookie in response.cookies.jar:
            if cookie.name == "uuid":
                return cookie.value
        
        # 尝试从响应内容提取
        try:
            text = response.text
            match = re.search(r'uuid["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]+)', text)
            if match:
                return match.group(1)
        except Exception:
            pass
        
        # 生成一个基于时间戳的临时uuid
        return f"tmp_{int(time.time() * 1000)}"

    async def poll_scan_status(
        self,
        uuid: str,
    ) -> tuple[int, AuthCredentials | None]:
        """轮询扫码状态
        
        Args:
            uuid: 二维码唯一标识
            
        Returns:
            (状态码, 凭据) 元组
            状态码：0-等待扫码, 1-已扫码待确认, 2-登录成功, -1-已过期/失败
        """
        client = await self._get_client()
        
        try:
            check_url = f"{MP_CHECK_URL}?action=ask&token=&lang=zh_CN&f=json&ajax=1"
            resp = await client.get(check_url)
            
            if resp.status_code != 200:
                logger.warning(f"检查扫码状态失败: HTTP {resp.status_code}")
                return -1, None
            
            data = resp.json()
            status = data.get("status", -1)
            
            # 状态映射
            # 微信返回的状态码可能因版本不同而有差异
            if status == 0:
                return 0, None  # 等待扫码
            elif status == 4:
                return 1, None  # 已扫码待确认
            elif status == 1:
                # 登录成功，获取凭据
                credentials = await self._complete_login(data)
                return 2, credentials
            else:
                return -1, None  # 其他状态视为失败
                
        except Exception as e:
            logger.error(f"轮询扫码状态失败: {e}")
            return -1, None

    async def _complete_login(self, login_data: dict) -> AuthCredentials:
        """完成登录流程，获取完整凭据
        
        Args:
            login_data: 登录响应数据
            
        Returns:
            认证凭据
        """
        client = await self._get_client()
        
        # 从登录数据中提取redirect_url
        redirect_url = login_data.get("redirect_url", "")
        
        if redirect_url:
            # 访问重定向URL获取token
            if not redirect_url.startswith("http"):
                redirect_url = MP_BASE_URL + redirect_url
            
            resp = await client.get(redirect_url, follow_redirects=True)
            
            # 从最终URL中提取token
            final_url = str(resp.url)
            token = self._extract_token(final_url)
        else:
            token = ""
        
        # 收集所有cookies
        cookies = {}
        for cookie in client.cookies.jar:
            cookies[cookie.name] = cookie.value
        
        # 获取用户信息（公众号信息）
        user_info = await self._get_user_info(token) if token else None
        
        credentials = AuthCredentials(
            token=token,
            cookies=cookies,
            user_info=user_info,
        )
        
        # 保存凭据
        self._credentials = credentials
        if self._storage:
            self._storage.save(credentials)
            logger.info("登录凭据已保存")
        
        return credentials

    def _extract_token(self, url: str) -> str:
        """从URL中提取token"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "token" in params:
            return params["token"][0]
        
        # 尝试从路径中提取
        match = re.search(r'token[=:](\d+)', url)
        if match:
            return match.group(1)
        
        return ""

    async def _get_user_info(self, token: str) -> dict | None:
        """获取用户（公众号）信息"""
        if not token:
            return None
        
        client = await self._get_client()
        
        try:
            # 访问主页获取公众号基本信息
            home_url = f"{MP_BASE_URL}/cgi-bin/home?t=home/index&lang=zh_CN&token={token}"
            resp = await client.get(home_url)
            
            if resp.status_code == 200:
                # 从页面中提取公众号信息
                text = resp.text
                
                # 提取公众号名称
                name_match = re.search(r'nickname["\']?\s*[:=]\s*["\']([^"\']+)', text)
                nickname = name_match.group(1) if name_match else ""
                
                return {
                    "nickname": nickname,
                    "token": token,
                }
        except Exception as e:
            logger.warning(f"获取用户信息失败: {e}")
        
        return None

    async def validate_credentials(
        self,
        credentials: AuthCredentials | None = None,
    ) -> bool:
        """验证凭据是否有效
        
        Args:
            credentials: 待验证的凭据（默认使用当前凭据）
            
        Returns:
            凭据是否有效
        """
        creds = credentials or self._credentials
        if not creds:
            return False
        
        if creds.is_expired:
            return False
        
        client = await self._get_client()
        
        try:
            # 设置cookies
            for name, value in creds.cookies.items():
                client.cookies.set(name, value)
            
            # 尝试访问一个需要登录的接口
            test_url = (
                f"{MP_BASE_URL}/cgi-bin/searchbiz"
                f"?action=search_biz&begin=0&count=1&query=test&token={creds.token}"
            )
            resp = await client.get(test_url)
            
            if resp.status_code == 200:
                data = resp.json()
                # 检查是否返回错误码
                if data.get("base_resp", {}).get("ret") == 0:
                    return True
                # 某些错误码表示未登录
                if data.get("base_resp", {}).get("ret") in [200040, 200003]:
                    return False
            
            return resp.status_code == 200
            
        except Exception as e:
            logger.warning(f"验证凭据失败: {e}")
            return False

    async def refresh_credentials(self) -> AuthCredentials | None:
        """刷新凭据
        
        微信公众平台的token通常需要重新登录才能刷新。
        此方法尝试使用现有cookies刷新token。
        
        Returns:
            新凭据，如果刷新失败则返回None
        """
        if not self._credentials:
            return None
        
        # 微信公众平台不支持token刷新，需要重新登录
        logger.warning("凭据已过期，需要重新扫码登录")
        return None

    async def logout(self) -> bool:
        """登出
        
        Returns:
            是否成功登出
        """
        if not self._credentials:
            return True
        
        try:
            client = await self._get_client()
            
            # 调用登出接口
            logout_url = f"{MP_LOGIN_URL}?action=logout&token={self._credentials.token}"
            await client.get(logout_url)
            
        except Exception as e:
            logger.warning(f"调用登出接口失败: {e}")
        
        # 清除本地凭据
        self._credentials = None
        if self._storage:
            self._storage.delete()
        
        logger.info("已登出")
        return True

    async def close(self) -> None:
        """关闭连接"""
        if self._client:
            # 连接池会管理客户端的关闭
            self._client = None


class FileCredentialStorage:
    """
    文件凭据存储
    
    将凭据以JSON格式保存到文件。
    """

    def __init__(self, filepath: str | Path | None = None) -> None:
        """初始化
        
        Args:
            filepath: 文件路径（默认使用配置中的路径）
        """
        if filepath:
            self._filepath = Path(filepath)
        else:
            settings = get_settings()
            self._filepath = Path.home() / ".wechat_summarizer" / settings.batch.credentials_file

    def save(self, credentials: AuthCredentials) -> None:
        """保存凭据"""
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = credentials.to_dict()
        self._filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug(f"凭据已保存到 {self._filepath}")

    def load(self) -> AuthCredentials | None:
        """加载凭据"""
        if not self._filepath.exists():
            return None
        
        try:
            data = json.loads(self._filepath.read_text(encoding="utf-8"))
            credentials = AuthCredentials.from_dict(data)
            
            # 检查是否过期
            if credentials.is_expired:
                logger.debug("保存的凭据已过期")
                self.delete()
                return None
            
            return credentials
            
        except Exception as e:
            logger.warning(f"加载凭据失败: {e}")
            return None

    def delete(self) -> None:
        """删除凭据"""
        if self._filepath.exists():
            self._filepath.unlink()
            logger.debug(f"已删除凭据文件 {self._filepath}")

    def exists(self) -> bool:
        """检查凭据是否存在"""
        return self._filepath.exists()
