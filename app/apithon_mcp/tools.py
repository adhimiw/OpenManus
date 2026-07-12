"""OpenManus BaseTool wrappers for APITHON MCP capabilities.

Uses lazy imports to avoid heavy dependencies (browser-use, etc.)
at module load time.
"""

from typing import Any, Dict, Optional

from app.logger import logger


def _get_bridge():
    """Lazy-import the APITHON bridge."""
    from .bridge import ai_research, check_apithon, perplexity_search, web_scrape
    return ai_research, check_apithon, perplexity_search, web_scrape


def _get_base():
    """Lazy-import OpenManus tool base classes."""
    from app.tool.base import BaseTool, ToolResult
    return BaseTool, ToolResult


class PerplexitySearch:
    """Deep research tool powered by Perplexity AI via APITHON."""

    name: str = "perplexity_search"
    
    def __init__(self):
        pass
    
    @property 
    def description(self) -> str:
        return "Perform deep web research using Perplexity AI. Use for complex questions requiring synthesis across multiple sources."
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The research query or question to investigate",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results to return (1-10)",
                    "default": 5,
                },
                "mode": {
                    "type": "string",
                    "description": "Search mode: auto, concise, or research",
                    "enum": ["auto", "concise", "research"],
                    "default": "auto",
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, max_results: int = 5, mode: str = "auto", **kwargs):
        _, check, psearch, _ = _get_bridge()
        _, ToolResult = _get_base()
        
        status = check()
        if not status.get("perplexity"):
            return ToolResult(
                error=f"APITHON Perplexity protocol not available. "
                f"Available: {[k for k, v in status.items() if v] or 'none'}",
            )

        logger.info(f"PerplexitySearch: query='{query}' mode={mode}")
        result = await psearch(query, max_results, mode)

        if "error" in result:
            return ToolResult(error=result["error"])

        output_lines = [f"# Perplexity Search: {query}\n"]
        for i, r in enumerate(result.get("results", []), 1):
            content = r.get("content", "")
            if content:
                output_lines.append(f"\n### Result {i}\n{content}\n")

        return ToolResult(output="\n".join(output_lines))


class MultiAISearch:
    """Multi-provider AI research across Gemini, Qwen, Claude, and Perplexity."""

    name: str = "multi_ai_search"
    
    def __init__(self):
        pass
    
    @property
    def description(self) -> str:
        return "Multi-provider AI research across Gemini, Perplexity, Qwen, Claude. Use for questions needing multiple AI perspectives."
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The research query",
                },
                "providers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Providers to query (gemini, perplexity, qwen, claude_web)",
                    "default": None,
                },
                "delay_ms": {
                    "type": "integer",
                    "description": "Delay between provider calls in milliseconds",
                    "default": 3000,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, providers: Optional[list] = None, delay_ms: int = 3000, **kwargs):
        airesearch, check, _, _ = _get_bridge()
        _, ToolResult = _get_base()
        
        status = check()
        if not status.get("router"):
            return ToolResult(
                error="APITHON AI Router not available. "
                f"Available: {[k for k, v in status.items() if v] or 'none'}",
            )

        logger.info(f"MultiAISearch: query='{query}' providers={providers}")
        result = await airesearch(query, providers, delay_ms)

        if "error" in result:
            return ToolResult(error=result["error"])

        lines = [f"# Multi-AI Research: {query}\n"]
        for provider, response in result.get("results", {}).items():
            status_icon = response.get("status", "?")
            content = response.get("response", response.get("error", "no content"))
            if isinstance(content, str) and len(content) > 500:
                content = content[:500] + "…"
            lines.append(f"\n## {provider} [{status_icon}]\n{content}\n")

        return ToolResult(output="\n".join(lines))


class WebScrape:
    """Scrape a webpage with optional vision-based parsing."""

    name: str = "web_scrape_apithon"
    
    def __init__(self):
        pass
    
    @property
    def description(self) -> str:
        return "Scrape a webpage using APITHON's SmartScraper with optional vision-based screenshot parsing."
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to scrape",
                },
                "use_vision": {
                    "type": "boolean",
                    "description": "Enable screenshot-based vision parsing",
                    "default": False,
                },
            },
            "required": ["url"],
        }

    async def execute(self, url: str, use_vision: bool = False, **kwargs):
        _, check, _, wscrape = _get_bridge()
        _, ToolResult = _get_base()
        
        status = check()
        if not status.get("scraper"):
            return ToolResult(
                error=f"APITHON SmartScraper not available. "
                f"Available: {[k for k, v in status.items() if v] or 'none'}",
            )

        logger.info(f"WebScrape: url='{url}' vision={use_vision}")
        result = await wscrape(url, use_vision)

        if "error" in result:
            return ToolResult(error=result["error"])

        content = result.get("content", "no content extracted")
        if len(content) > 8000:
            content = content[:8000] + "… [truncated]"

        lines = [
            f"# Scraped: {result.get('url', url)}",
            f"**Title:** {result.get('title', 'N/A')}\n",
            content,
        ]
        return ToolResult(output="\n".join(lines))
