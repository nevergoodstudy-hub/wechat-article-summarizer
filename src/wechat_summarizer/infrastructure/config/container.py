"""依赖注入容器 - 组装应用组件"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

from ...application.use_cases import (
    BatchProcessUseCase,
    ExportArticleUseCase,
    FetchArticleUseCase,
    SummarizeArticleUseCase,
)
from ...domain.services.summary_evaluator import SummaryEvaluator
from ..plugins import PluginLoader, PluginType
from .settings import AppSettings, get_settings

if TYPE_CHECKING:
    from ...application.ports.outbound import (
        EmbedderPort,
        ExporterPort,
        ScraperPort,
        StoragePort,
        SummarizerPort,
        VectorStorePort,
    )


@dataclass
class Container:
    """
    依赖注入容器

    负责创建和管理应用程序的所有依赖项。
    支持插件系统、MapReduce 摘要器、摘要质量评估等。
    """

    settings: AppSettings = field(default_factory=get_settings)

    # 线程安全锁（保护懒加载属性的初始化）
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    # 适配器缓存
    _scrapers: list[ScraperPort] | None = field(default=None, init=False)
    _summarizers: dict[str, SummarizerPort] | None = field(default=None, init=False)
    _exporters: dict[str, ExporterPort] | None = field(default=None, init=False)
    _storage: StoragePort | None = field(default=None, init=False)

    # RAG 组件缓存
    _embedders: dict[str, EmbedderPort] | None = field(default=None, init=False)
    _vector_stores: dict[str, VectorStorePort] | None = field(default=None, init=False)

    # 插件和评估器
    _plugin_loader: PluginLoader | None = field(default=None, init=False)
    _evaluator: SummaryEvaluator | None = field(default=None, init=False)

    # 用例缓存
    _fetch_use_case: FetchArticleUseCase | None = field(default=None, init=False)
    _summarize_use_case: SummarizeArticleUseCase | None = field(default=None, init=False)
    _export_use_case: ExportArticleUseCase | None = field(default=None, init=False)
    _batch_use_case: BatchProcessUseCase | None = field(default=None, init=False)

    @property
    def scrapers(self) -> list[ScraperPort]:
        """获取抓取器列表"""
        if self._scrapers is None:
            with self._lock:
                if self._scrapers is None:
                    self._scrapers = self._create_scrapers()
        return self._scrapers

    @property
    def summarizers(self) -> dict[str, SummarizerPort]:
        """获取摘要器字典"""
        if self._summarizers is None:
            with self._lock:
                if self._summarizers is None:
                    self._summarizers = self._create_summarizers()
        return self._summarizers

    @property
    def exporters(self) -> dict[str, ExporterPort]:
        """获取导出器字典"""
        if self._exporters is None:
            with self._lock:
                if self._exporters is None:
                    self._exporters = self._create_exporters()
        return self._exporters

    @property
    def storage(self) -> StoragePort | None:
        """获取存储适配器（用于缓存，可选）"""
        if self._storage is None:
            with self._lock:
                if self._storage is None:
                    self._storage = self._create_storage()
        return self._storage

    @property
    def embedders(self) -> dict[str, EmbedderPort]:
        """获取向量嵌入器字典"""
        if self._embedders is None:
            with self._lock:
                if self._embedders is None:
                    self._embedders = self._create_embedders()
        return self._embedders

    @property
    def vector_stores(self) -> dict[str, VectorStorePort]:
        """获取向量存储字典"""
        if self._vector_stores is None:
            with self._lock:
                if self._vector_stores is None:
                    self._vector_stores = self._create_vector_stores()
        return self._vector_stores

    @property
    def plugin_loader(self) -> PluginLoader:
        """获取插件加载器"""
        if self._plugin_loader is None:
            with self._lock:
                if self._plugin_loader is None:
                    self._plugin_loader = PluginLoader()
                    self._plugin_loader.discover()
        return self._plugin_loader

    @property
    def evaluator(self) -> SummaryEvaluator:
        """获取摘要质量评估器"""
        if self._evaluator is None:
            # 默认使用第一个可用的 LLM 摘要器进行评估
            llm_summarizer = None
            for name in ["openai", "anthropic", "zhipu", "ollama"]:
                if name in self.summarizers and self.summarizers[name].is_available():
                    llm_summarizer = self.summarizers[name]
                    break

            self._evaluator = SummaryEvaluator(
                summarizer=llm_summarizer,
                use_rouge=True,
                use_hallucination_detection=True,
                use_llm=llm_summarizer is not None,
            )
        return self._evaluator

    @property
    def fetch_use_case(self) -> FetchArticleUseCase:
        """获取抓取文章用例"""
        if self._fetch_use_case is None:
            with self._lock:
                if self._fetch_use_case is None:
                    self._fetch_use_case = FetchArticleUseCase(self.scrapers, storage=self.storage)
        return self._fetch_use_case

    @property
    def summarize_use_case(self) -> SummarizeArticleUseCase:
        """获取摘要用例"""
        if self._summarize_use_case is None:
            with self._lock:
                if self._summarize_use_case is None:
                    self._summarize_use_case = SummarizeArticleUseCase(self.summarizers)
        return self._summarize_use_case

    @property
    def export_use_case(self) -> ExportArticleUseCase:
        """获取导出用例"""
        if self._export_use_case is None:
            with self._lock:
                if self._export_use_case is None:
                    self._export_use_case = ExportArticleUseCase(self.exporters)
        return self._export_use_case

    @property
    def batch_use_case(self) -> BatchProcessUseCase:
        """获取批量处理用例"""
        if self._batch_use_case is None:
            with self._lock:
                if self._batch_use_case is None:
                    self._batch_use_case = BatchProcessUseCase(
                        fetch_use_case=self.fetch_use_case,
                        summarize_use_case=self.summarize_use_case,
                        export_use_case=self.export_use_case,
                    )
        return self._batch_use_case

    def _create_scrapers(self) -> list[ScraperPort]:
        """创建抓取器列表"""
        from ..adapters.scrapers import (
            GenericHttpxScraper,
            ToutiaoScraper,
            WechatHttpxScraper,
            WechatPlaywrightScraper,
            ZhihuScraper,
        )

        scrapers: list[ScraperPort] = []

        # 微信公众号抓取器
        httpx_scraper: ScraperPort = WechatHttpxScraper(
            timeout=self.settings.scraper.timeout,
            max_retries=self.settings.scraper.max_retries,
            proxy=self.settings.scraper.proxy,
            user_agent_rotation=self.settings.scraper.user_agent_rotation,
        )

        playwright_scraper: ScraperPort | None = None
        try:
            playwright_scraper = WechatPlaywrightScraper(
                timeout=self.settings.scraper.timeout,
            )
        except Exception as e:
            logger.warning(f"Playwright抓取器不可用: {e}")

        # 根据配置决定优先级：use_playwright=true 时 Playwright 优先
        if self.settings.scraper.use_playwright and playwright_scraper is not None:
            scrapers.append(playwright_scraper)
            scrapers.append(httpx_scraper)
        else:
            scrapers.append(httpx_scraper)
            if playwright_scraper is not None:
                scrapers.append(playwright_scraper)

        # 知乎抓取器
        scrapers.append(
            ZhihuScraper(
                timeout=self.settings.scraper.timeout,
                user_agent_rotation=self.settings.scraper.user_agent_rotation,
            )
        )

        # 头条抓取器
        scrapers.append(
            ToutiaoScraper(
                timeout=self.settings.scraper.timeout,
                user_agent_rotation=self.settings.scraper.user_agent_rotation,
            )
        )

        # 通用抓取器（非微信公众号链接的后备）
        scrapers.append(
            GenericHttpxScraper(
                timeout=self.settings.scraper.timeout,
                max_retries=self.settings.scraper.max_retries,
                proxy=self.settings.scraper.proxy,
                user_agent_rotation=self.settings.scraper.user_agent_rotation,
            )
        )

        # 加载第三方插件抓取器
        try:
            plugin_scrapers = self.plugin_loader.load_scrapers()
            if plugin_scrapers:
                scrapers.extend(plugin_scrapers)
                logger.info(f"已加载 {len(plugin_scrapers)} 个插件抓取器")
        except Exception as e:
            logger.warning(f"加载插件抓取器失败: {e}")

        logger.info(f"已加载 {len(scrapers)} 个抓取器")
        return scrapers

    def _create_summarizers(self, extra_api_keys: dict[str, str] | None = None) -> dict[str, SummarizerPort]:
        """创建摘要器字典
        
        Args:
            extra_api_keys: 额外的 API 密钥字典，优先级高于 settings（用于 GUI 配置的密钥）
        """
        extra_api_keys = extra_api_keys or {}
        summarizers: dict[str, SummarizerPort] = {}

        # 1) 基础摘要器（simple / textrank / LLM）
        self._create_base_summarizers(summarizers, extra_api_keys)

        # 可用 LLM 名称列表（用于派生变体）
        llm_names = ["openai", "anthropic", "zhipu", "deepseek", "ollama"]

        # 2) MapReduce 变体
        self._create_mapreduce_variants(summarizers, llm_names)

        # 3) RAG / HyDE 变体
        self._create_rag_variants(summarizers, llm_names)

        # 4) GraphRAG 变体
        self._create_graphrag_variants(summarizers, llm_names)

        # 5) 第三方插件摘要器
        try:
            plugin_summarizers = self.plugin_loader.load_summarizers()
            for s in plugin_summarizers:
                if hasattr(s, "name"):
                    summarizers[s.name] = s
                    logger.debug(f"已加载插件摘要器: {s.name}")
        except Exception as e:
            logger.warning(f"加载插件摘要器失败: {e}")

        logger.info(f"已加载 {len(summarizers)} 个摘要器")
        return summarizers

    # ---------- _create_summarizers 子方法 ----------

    def _create_base_summarizers(
        self,
        summarizers: dict[str, SummarizerPort],
        extra_api_keys: dict[str, str],
    ) -> None:
        """创建基础摘要器（简单 / TextRank / 各 LLM）"""
        from ..adapters.summarizers import (
            AnthropicSummarizer,
            DeepSeekSummarizer,
            OllamaSummarizer,
            OpenAISummarizer,
            SimpleSummarizer,
            TextRankSummarizer,
            ZhipuSummarizer,
        )

        summarizers["simple"] = SimpleSummarizer()
        summarizers["textrank"] = TextRankSummarizer()

        summarizers["ollama"] = OllamaSummarizer(
            host=self.settings.ollama.host,
            model=self.settings.ollama.model,
            timeout=self.settings.ollama.timeout,
        )

        openai_key = extra_api_keys.get("openai") or self.settings.openai.api_key.get_secret_value()
        if openai_key:
            try:
                summarizers["openai"] = OpenAISummarizer(
                    api_key=openai_key,
                    model=self.settings.openai.model,
                    base_url=self.settings.openai.base_url,
                )
            except Exception as e:
                logger.warning(f"OpenAI摘要器不可用（可能未安装 openai 依赖）: {e}")

        deepseek_key = extra_api_keys.get("deepseek") or self.settings.deepseek.api_key.get_secret_value()
        if deepseek_key:
            try:
                summarizers["deepseek"] = DeepSeekSummarizer(
                    api_key=deepseek_key,
                    model=self.settings.deepseek.model,
                )
            except Exception as e:
                logger.warning(f"DeepSeek摘要器不可用: {e}")

        anthropic_key = extra_api_keys.get("anthropic") or self.settings.anthropic.api_key.get_secret_value()
        if anthropic_key:
            try:
                summarizers["anthropic"] = AnthropicSummarizer(
                    api_key=anthropic_key,
                    model=self.settings.anthropic.model,
                )
            except Exception as e:
                logger.warning(f"Anthropic摘要器不可用（可能未安装 anthropic 依赖）: {e}")

        zhipu_key = extra_api_keys.get("zhipu") or self.settings.zhipu.api_key.get_secret_value()
        if zhipu_key:
            summarizers["zhipu"] = ZhipuSummarizer(
                api_key=zhipu_key,
                model=self.settings.zhipu.model,
            )

    def _create_mapreduce_variants(
        self,
        summarizers: dict[str, SummarizerPort],
        llm_names: list[str],
    ) -> None:
        """为可用 LLM 创建 MapReduce 变体"""
        from ..adapters.summarizers import MapReduceSummarizer

        for name in llm_names:
            if name in summarizers and summarizers[name].is_available():
                try:
                    mr_name = f"mapreduce-{name}"
                    summarizers[mr_name] = MapReduceSummarizer(
                        base_summarizer=summarizers[name],
                        chunk_size=4000,
                        overlap=200,
                        max_chunks=20,
                    )
                    logger.debug(f"MapReduce 摘要器已创建: {mr_name}")
                except Exception as e:
                    logger.warning(f"MapReduce 摘要器 {name} 创建失败: {e}")

    def _create_rag_variants(
        self,
        summarizers: dict[str, SummarizerPort],
        llm_names: list[str],
    ) -> None:
        """为可用 LLM 创建 RAG / HyDE 变体"""
        from ..adapters.summarizers import HyDEEnhancedSummarizer, RAGEnhancedSummarizer

        embedders = self.embedders
        vector_stores = self.vector_stores
        default_embedder = embedders.get("openai") or embedders.get("local") or embedders.get("simple")
        default_store = vector_stores.get("chromadb") or vector_stores.get("memory")

        if not (default_embedder and default_store):
            logger.info("RAG 组件不可用，跳过 RAG 摘要器创建")
            return

        for name in llm_names:
            if name in summarizers and summarizers[name].is_available():
                try:
                    rag_name = f"rag-{name}"
                    summarizers[rag_name] = RAGEnhancedSummarizer(
                        base_summarizer=summarizers[name],
                        embedder=default_embedder,
                        vector_store=default_store,
                        chunk_size=512,
                        chunk_overlap=50,
                        top_k=5,
                    )
                    logger.debug(f"RAG 摘要器已创建: {rag_name}")

                    if name in ["openai", "anthropic", "deepseek"]:
                        hyde_name = f"hyde-{name}"
                        summarizers[hyde_name] = HyDEEnhancedSummarizer(
                            base_summarizer=summarizers[name],
                            embedder=default_embedder,
                            vector_store=default_store,
                            chunk_size=512,
                            chunk_overlap=50,
                            top_k=5,
                        )
                        logger.debug(f"HyDE 摘要器已创建: {hyde_name}")
                except Exception as e:
                    logger.warning(f"RAG 摘要器 {name} 创建失败: {e}")

    def _create_graphrag_variants(
        self,
        summarizers: dict[str, SummarizerPort],
        llm_names: list[str],
    ) -> None:
        """为可用 LLM 创建 GraphRAG 变体"""
        from ..adapters.summarizers import GraphRAGSummarizer

        for name in llm_names:
            if name in summarizers and summarizers[name].is_available():
                try:
                    graphrag_name = f"graphrag-{name}"
                    summarizers[graphrag_name] = GraphRAGSummarizer(
                        base_summarizer=summarizers[name],
                        chunk_size=2000,
                        use_global_search=True,
                    )
                    logger.debug(f"GraphRAG 摘要器已创建: {graphrag_name}")
                except Exception as e:
                    logger.warning(f"GraphRAG 摘要器 {name} 创建失败: {e}")

    def close(self) -> None:
        """关闭容器持有的资源（httpx 客户端、向量存储等）"""
        for scraper in (self._scrapers or []):
            close_fn = getattr(scraper, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception as e:
                    logger.debug(f"关闭 scraper 失败: {e}")

        for summarizer in (self._summarizers or {}).values():
            close_fn = getattr(summarizer, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception as e:
                    logger.debug(f"关闭 summarizer 失败: {e}")

        logger.debug("容器资源已关闭")

    def reload_summarizers(self, api_keys: dict[str, str]) -> None:
        """重新加载摘要器（用于 GUI 保存 API 密钥后刷新）
        
        Args:
            api_keys: API 密钥字典 {"openai": "sk-...", "deepseek": "sk-...", ...}
        """
        self._summarizers = self._create_summarizers(extra_api_keys=api_keys)
        # 重建依赖 summarizers 的用例
        self._summarize_use_case = None
        self._batch_use_case = None
        logger.info(f"摘要器已重新加载，当前可用: {list(self._summarizers.keys())}")

    def _create_storage(self) -> StoragePort | None:
        """创建存储适配器（默认本地 JSON 缓存）。"""
        try:
            from ..adapters.storage import LocalJsonStorage

            return LocalJsonStorage()
        except Exception as e:
            logger.warning(f"本地缓存存储不可用: {e}")
            return None

    def _create_exporters(self) -> dict[str, ExporterPort]:
        """创建导出器字典"""
        from ..adapters.exporters import (
            HtmlExporter,
            MarkdownExporter,
            WordExporter,
            ZipExporter,
        )

        exporters: dict[str, ExporterPort] = {}

        # HTML导出器
        exporters["html"] = HtmlExporter(
            output_dir=self.settings.export.default_output_dir,
        )

        # Markdown导出器
        exporters["markdown"] = MarkdownExporter(
            output_dir=self.settings.export.default_output_dir,
        )

        # Word导出器
        exporters["word"] = WordExporter(
            output_dir=self.settings.export.default_output_dir,
        )

        # ZIP 批量导出器
        exporters["zip"] = ZipExporter(
            output_dir=self.settings.export.default_output_dir,
        )

        # Obsidian 导出器（需要配置 vault 路径）
        if self.settings.export.obsidian_vault_path:
            try:
                from ..adapters.exporters.obsidian import ObsidianExporter

                exporters["obsidian"] = ObsidianExporter(
                    vault_path=self.settings.export.obsidian_vault_path,
                )
                logger.debug("Obsidian 导出器已创建")
            except Exception as e:
                logger.warning(f"Obsidian 导出器不可用: {e}")

        # Notion 导出器（需要 API key + database ID）
        notion_key = self.settings.export.notion_api_key.get_secret_value()
        if notion_key and self.settings.export.notion_database_id:
            try:
                from ..adapters.exporters.notion import NotionExporter

                exporters["notion"] = NotionExporter(
                    api_key=notion_key,
                    database_id=self.settings.export.notion_database_id,
                )
                logger.debug("Notion 导出器已创建")
            except Exception as e:
                logger.warning(f"Notion 导出器不可用: {e}")

        # OneNote 导出器（需要 Azure App 配置 + 已授权）
        if self.settings.export.onenote_client_id:
            try:
                from ..adapters.exporters.onenote import OneNoteExporter

                exporters["onenote"] = OneNoteExporter(
                    client_id=self.settings.export.onenote_client_id,
                    tenant=self.settings.export.onenote_tenant,
                    notebook=self.settings.export.onenote_notebook,
                    section=self.settings.export.onenote_section,
                )
                logger.debug("OneNote 导出器已创建")
            except Exception as e:
                logger.warning(f"OneNote 导出器不可用: {e}")

        # 加载第三方插件导出器
        try:
            plugin_exporters = self.plugin_loader.load_exporters()
            for e in plugin_exporters:
                if hasattr(e, "name"):
                    exporters[e.name] = e
                    logger.debug(f"已加载插件导出器: {e.name}")
        except Exception as e:
            logger.warning(f"加载插件导出器失败: {e}")

        logger.info(f"已加载 {len(exporters)} 个导出器")
        return exporters

    def _create_embedders(self) -> dict[str, EmbedderPort]:
        """创建向量嵌入器字典"""
        from ..adapters.embedders import LocalEmbedder, OpenAIEmbedder, SimpleHashEmbedder

        embedders: dict[str, EmbedderPort] = {}

        # 简单哈希嵌入器（始终可用，用于测试）
        embedders["simple"] = SimpleHashEmbedder(dimension=384)

        # OpenAI 嵌入器
        openai_key = self.settings.openai.api_key.get_secret_value()
        if openai_key:
            try:
                embedders["openai"] = OpenAIEmbedder(
                    api_key=openai_key,
                    model="text-embedding-3-small",
                    base_url=self.settings.openai.base_url,
                )
                logger.debug("OpenAI 嵌入器已创建")
            except Exception as e:
                logger.warning(f"OpenAI 嵌入器不可用: {e}")

        # 本地嵌入器（sentence-transformers）
        try:
            embedders["local"] = LocalEmbedder(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
            )
            logger.debug("本地嵌入器已创建")
        except Exception as e:
            logger.debug(f"本地嵌入器不可用（需要安装 sentence-transformers）: {e}")

        logger.info(f"已加载 {len(embedders)} 个向量嵌入器")
        return embedders

    def _create_vector_stores(self) -> dict[str, VectorStorePort]:
        """创建向量存储字典"""
        from ..adapters.vector_stores import ChromaDBStore, MemoryVectorStore

        stores: dict[str, VectorStorePort] = {}

        # 内存向量存储（始终可用）
        stores["memory"] = MemoryVectorStore()
        logger.debug("内存向量存储已创建")

        # ChromaDB 持久化存储
        try:
            stores["chromadb"] = ChromaDBStore(
                collection_name="wechat_summarizer",
                persist_directory=".chromadb",
            )
            logger.debug("ChromaDB 向量存储已创建")
        except Exception as e:
            logger.debug(f"ChromaDB 存储不可用（需要安装 chromadb）: {e}")

        logger.info(f"已加载 {len(stores)} 个向量存储")
        return stores


# 全局容器实例
_container: Container | None = None


def get_container() -> Container:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def reset_container() -> None:
    """重置容器（用于测试）"""
    global _container
    if _container is not None:
        _container.close()
    _container = None
