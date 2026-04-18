"""Container assembly helpers.

These functions host concrete adapter-construction logic so that
``container.py`` can stay focused on lifecycle, caching, and composition-root
behavior instead of growing into a giant factory file.
"""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

if TYPE_CHECKING:
    from ...application.ports.outbound import (
        EmbedderPort,
        ExporterPort,
        ScraperPort,
        StoragePort,
        SummarizerPort,
        VectorStorePort,
    )
    from ..plugins import PluginLoader
    from .settings import AppSettings


def build_scrapers(settings: AppSettings, plugin_loader: PluginLoader) -> list[ScraperPort]:
    """Build scraper adapters."""
    from ..adapters.scrapers import (
        GenericHttpxScraper,
        ToutiaoScraper,
        WechatHttpxScraper,
        WechatPlaywrightScraper,
        ZhihuScraper,
    )

    scrapers: list[ScraperPort] = []

    httpx_scraper: ScraperPort = WechatHttpxScraper(
        timeout=settings.scraper.timeout,
        max_retries=settings.scraper.max_retries,
        proxy=settings.scraper.proxy,
        user_agent_rotation=settings.scraper.user_agent_rotation,
    )

    playwright_scraper: ScraperPort | None = None
    try:
        if WechatPlaywrightScraper.runtime_available():
            playwright_scraper = WechatPlaywrightScraper(timeout=settings.scraper.timeout)
        else:
            logger.warning(
                "Playwright抓取器不可用: 未检测到 Chromium 浏览器，可运行 "
                "`python -m playwright install chromium` 启用"
            )
    except Exception as exc:
        logger.warning(f"Playwright抓取器不可用: {exc}")

    if settings.scraper.use_playwright and playwright_scraper is not None:
        scrapers.append(playwright_scraper)
        scrapers.append(httpx_scraper)
    else:
        scrapers.append(httpx_scraper)
        if playwright_scraper is not None:
            scrapers.append(playwright_scraper)

    scrapers.append(
        ZhihuScraper(
            timeout=settings.scraper.timeout,
            user_agent_rotation=settings.scraper.user_agent_rotation,
        )
    )
    scrapers.append(
        ToutiaoScraper(
            timeout=settings.scraper.timeout,
            user_agent_rotation=settings.scraper.user_agent_rotation,
        )
    )
    scrapers.append(
        GenericHttpxScraper(
            timeout=settings.scraper.timeout,
            max_retries=settings.scraper.max_retries,
            proxy=settings.scraper.proxy,
            user_agent_rotation=settings.scraper.user_agent_rotation,
        )
    )

    try:
        plugin_scrapers = plugin_loader.load_scrapers()
        if plugin_scrapers:
            scrapers.extend(plugin_scrapers)
            logger.info(f"已加载 {len(plugin_scrapers)} 个插件抓取器")
    except Exception as exc:
        logger.warning(f"加载插件抓取器失败: {exc}")

    logger.info(f"已加载 {len(scrapers)} 个抓取器")
    return scrapers


def build_summarizers(
    settings: AppSettings,
    plugin_loader: PluginLoader,
    embedders: dict[str, EmbedderPort],
    vector_stores: dict[str, VectorStorePort],
    extra_api_keys: dict[str, str] | None = None,
) -> dict[str, SummarizerPort]:
    """Build summarizer adapters and derived variants."""
    extra_api_keys = extra_api_keys or {}
    summarizers: dict[str, SummarizerPort] = {}

    _create_base_summarizers(settings, summarizers, extra_api_keys)
    llm_names = ["openai", "anthropic", "zhipu", "deepseek", "ollama"]

    _create_mapreduce_variants(summarizers, llm_names)
    _create_rag_variants(summarizers, llm_names, embedders, vector_stores)
    _create_graphrag_variants(summarizers, llm_names)

    try:
        plugin_summarizers = plugin_loader.load_summarizers()
        for summarizer in plugin_summarizers:
            if hasattr(summarizer, "name"):
                summarizers[summarizer.name] = summarizer
                logger.debug(f"已加载插件摘要器: {summarizer.name}")
    except Exception as exc:
        logger.warning(f"加载插件摘要器失败: {exc}")

    logger.info(f"已加载 {len(summarizers)} 个摘要器")
    return summarizers


def build_storage() -> StoragePort | None:
    """Build the default storage adapter."""
    try:
        from ..adapters.storage import LocalJsonStorage

        return LocalJsonStorage()
    except Exception as exc:
        logger.warning(f"本地缓存存储不可用: {exc}")
        return None


def build_exporters(
    settings: AppSettings,
    plugin_loader: PluginLoader,
) -> dict[str, ExporterPort]:
    """Build exporter adapters."""
    from ..adapters.exporters import (
        HtmlExporter,
        MarkdownExporter,
        WordExporter,
        ZipExporter,
    )

    exporters: dict[str, ExporterPort] = {
        "html": HtmlExporter(output_dir=settings.export.default_output_dir),
        "markdown": MarkdownExporter(output_dir=settings.export.default_output_dir),
        "word": WordExporter(output_dir=settings.export.default_output_dir),
        "zip": ZipExporter(output_dir=settings.export.default_output_dir),
    }

    if settings.export.obsidian_vault_path:
        try:
            from ..adapters.exporters.obsidian import ObsidianExporter

            exporters["obsidian"] = ObsidianExporter(vault_path=settings.export.obsidian_vault_path)
            logger.debug("Obsidian 导出器已创建")
        except Exception as exc:
            logger.warning(f"Obsidian 导出器不可用: {exc}")

    notion_key = settings.export.notion_api_key.get_secret_value()
    if notion_key and settings.export.notion_database_id:
        try:
            from ..adapters.exporters.notion import NotionExporter

            exporters["notion"] = NotionExporter(
                api_key=notion_key,
                database_id=settings.export.notion_database_id,
            )
            logger.debug("Notion 导出器已创建")
        except Exception as exc:
            logger.warning(f"Notion 导出器不可用: {exc}")

    if settings.export.onenote_client_id:
        try:
            from ..adapters.exporters.onenote import OneNoteExporter

            exporters["onenote"] = OneNoteExporter(
                client_id=settings.export.onenote_client_id,
                tenant=settings.export.onenote_tenant,
                notebook=settings.export.onenote_notebook,
                section=settings.export.onenote_section,
            )
            logger.debug("OneNote 导出器已创建")
        except Exception as exc:
            logger.warning(f"OneNote 导出器不可用: {exc}")

    try:
        plugin_exporters = plugin_loader.load_exporters()
        for exporter in plugin_exporters:
            if hasattr(exporter, "name"):
                exporters[exporter.name] = exporter
                logger.debug(f"已加载插件导出器: {exporter.name}")
    except Exception as exc:
        logger.warning(f"加载插件导出器失败: {exc}")

    logger.info(f"已加载 {len(exporters)} 个导出器")
    return exporters


def build_embedders(settings: AppSettings) -> dict[str, EmbedderPort]:
    """Build embedding adapters."""
    from ..adapters.embedders import LocalEmbedder, OpenAIEmbedder, SimpleHashEmbedder

    embedders: dict[str, EmbedderPort] = {"simple": SimpleHashEmbedder(dimension=384)}

    openai_key = settings.openai.api_key.get_secret_value()
    if openai_key:
        try:
            embedders["openai"] = OpenAIEmbedder(
                api_key=openai_key,
                model="text-embedding-3-small",
                base_url=settings.openai.base_url,
            )
            logger.debug("OpenAI 嵌入器已创建")
        except Exception as exc:
            logger.warning(f"OpenAI 嵌入器不可用: {exc}")

    try:
        embedders["local"] = LocalEmbedder(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            local_files_only=True,
        )
        logger.debug("本地嵌入器已创建")
    except Exception as exc:
        logger.debug(f"本地嵌入器不可用（需要安装 sentence-transformers）: {exc}")

    logger.info(f"已加载 {len(embedders)} 个向量嵌入器")
    return embedders


def build_vector_stores() -> dict[str, VectorStorePort]:
    """Build vector-store adapters."""
    from ..adapters.vector_stores.memory_store import MemoryVectorStore

    stores: dict[str, VectorStorePort] = {"memory": MemoryVectorStore()}
    logger.debug("内存向量存储已创建")

    py_major, py_minor = (int(value) for value in platform.python_version_tuple()[:2])
    if (py_major, py_minor) >= (3, 14):
        logger.debug("Python 3.14+ 暂不启用 ChromaDB（上游兼容性限制）")
    else:
        try:
            from ..adapters.vector_stores.chromadb_store import ChromaDBStore

            stores["chromadb"] = ChromaDBStore(
                collection_name="wechat_summarizer",
                persist_directory=".chromadb",
            )
            logger.debug("ChromaDB 向量存储已创建")
        except Exception as exc:
            logger.debug(f"ChromaDB 存储不可用（需要安装并兼容 chromadb）: {exc}")

    logger.info(f"已加载 {len(stores)} 个向量存储")
    return stores


def _create_base_summarizers(
    settings: AppSettings,
    summarizers: dict[str, SummarizerPort],
    extra_api_keys: dict[str, str],
) -> None:
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
        host=settings.ollama.host,
        model=settings.ollama.model,
        timeout=settings.ollama.timeout,
    )

    openai_key = extra_api_keys.get("openai") or settings.openai.api_key.get_secret_value()
    if openai_key:
        try:
            summarizers["openai"] = OpenAISummarizer(
                api_key=openai_key,
                model=settings.openai.model,
                base_url=settings.openai.base_url,
            )
        except Exception as exc:
            logger.warning(f"OpenAI摘要器不可用（可能未安装 openai 依赖）: {exc}")

    deepseek_key = extra_api_keys.get("deepseek") or settings.deepseek.api_key.get_secret_value()
    if deepseek_key:
        try:
            summarizers["deepseek"] = DeepSeekSummarizer(
                api_key=deepseek_key,
                model=settings.deepseek.model,
            )
        except Exception as exc:
            logger.warning(f"DeepSeek摘要器不可用: {exc}")

    anthropic_key = extra_api_keys.get("anthropic") or settings.anthropic.api_key.get_secret_value()
    if anthropic_key:
        try:
            summarizers["anthropic"] = AnthropicSummarizer(
                api_key=anthropic_key,
                model=settings.anthropic.model,
            )
        except Exception as exc:
            logger.warning(f"Anthropic摘要器不可用（可能未安装 anthropic 依赖）: {exc}")

    zhipu_key = extra_api_keys.get("zhipu") or settings.zhipu.api_key.get_secret_value()
    if zhipu_key:
        summarizers["zhipu"] = ZhipuSummarizer(api_key=zhipu_key, model=settings.zhipu.model)


def _create_mapreduce_variants(
    summarizers: dict[str, SummarizerPort],
    llm_names: list[str],
) -> None:
    from ..adapters.summarizers import MapReduceSummarizer

    for name in llm_names:
        if name in summarizers and summarizers[name].is_available():
            try:
                mr_name = f"mapreduce-{name}"
                summarizers[mr_name] = MapReduceSummarizer(
                    base_summarizer=cast(Any, summarizers[name]),
                    chunk_size=4000,
                    overlap=200,
                    max_chunks=20,
                )
                logger.debug(f"MapReduce 摘要器已创建: {mr_name}")
            except Exception as exc:
                logger.warning(f"MapReduce 摘要器 {name} 创建失败: {exc}")


def _create_rag_variants(
    summarizers: dict[str, SummarizerPort],
    llm_names: list[str],
    embedders: dict[str, EmbedderPort],
    vector_stores: dict[str, VectorStorePort],
) -> None:
    from ..adapters.summarizers import HyDEEnhancedSummarizer, RAGEnhancedSummarizer

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
                    base_summarizer=cast(Any, summarizers[name]),
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
                        base_summarizer=cast(Any, summarizers[name]),
                        embedder=default_embedder,
                        vector_store=default_store,
                        chunk_size=512,
                        chunk_overlap=50,
                        top_k=5,
                    )
                    logger.debug(f"HyDE 摘要器已创建: {hyde_name}")
            except Exception as exc:
                logger.warning(f"RAG 摘要器 {name} 创建失败: {exc}")


def _create_graphrag_variants(
    summarizers: dict[str, SummarizerPort],
    llm_names: list[str],
) -> None:
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
            except Exception as exc:
                logger.warning(f"GraphRAG 摘要器 {name} 创建失败: {exc}")
