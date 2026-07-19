"""
APITHON MCP Bridge — adapts APITHON protocols as OpenManus tools.

Provides Perplexity deep research, Gemini/Qwen/Claude web chat, and
browser automation as native OpenManus agent tools. This bridge
imports directly from the APITHON protocol modules (no subprocess).
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger("apithon_bridge")

# ──────────────────────────────────────────
# APITHON path setup
# ──────────────────────────────────────────
APITHON_PATH = os.environ.get(
    "APITHON_PATH",
    os.path.expanduser("~/projects/APITHON-main/APITHON-main/mcp_apithon"),
)

if APITHON_PATH and APITHON_PATH not in sys.path:
    sys.path.insert(0, APITHON_PATH)

# ──────────────────────────────────────────
# Proxy imports — lazy-loaded to avoid import errors
# ──────────────────────────────────────────
_perplexity = None
_gemini = None
_qwen = None
_claude = None
_scraper = None
_ai_router = None
_session_manager = None


def _lazy_import(module_name: str):
    """Lazy-import an APITHON protocol module."""
    global _perplexity, _gemini, _qwen, _claude, _scraper, _ai_router, _session_manager
    try:
        if module_name == "perplexity" and _perplexity is None:
            import protocols.perplexity as p
            _perplexity = p
        elif module_name == "gemini" and _gemini is None:
            import protocols.gemini as g
            _gemini = g
        elif module_name == "qwen" and _qwen is None:
            import protocols.qwen as q
            _qwen = q
        elif module_name == "claude" and _claude is None:
            import protocols.claude_web as c
            _claude = c
        elif module_name == "scraper" and _scraper is None:
            import protocols.smart_scraper as s
            _scraper = s
        elif module_name == "router" and _ai_router is None:
            from protocols.ai_router import AIOrchestrator, SUPPORTED_PROVIDERS as ROUTER_PROVIDERS
            _ai_router = (AIOrchestrator, ROUTER_PROVIDERS)
        elif module_name == "session" and _session_manager is None:
            from auth.session_manager import SessionManager
            _session_manager = SessionManager
        return True
    except ImportError as e:
        logger.warning(f"APITHON protocol '{module_name}' not available: {e}")
        return False


def check_apithon() -> Dict[str, bool]:
    """Check which APITHON protocols are available."""
    available = {}
    for name in ("perplexity", "gemini", "qwen", "claude", "scraper", "router", "session"):
        available[name] = _lazy_import(name)
    return available


# ═══════════════════════════════════════════
# Tool wrappers — return compatible dicts for OpenManus
# ═══════════════════════════════════════════

async def perplexity_search(query: str, max_results: int = 5, mode: str = "auto") -> Dict[str, Any]:
    """
    Search using Perplexity AI via APITHON protocol.
    
    Args:
        query: Search query string
        max_results: Maximum number of results (1-10)
        mode: Search mode — "auto", "concise", or "research"
    
    Returns:
        Dict with 'results' (list of result dicts) and 'source' str
    """
    try:
        # Use the real call_ai_provider from mcp_server
        sys.path.insert(0, APITHON_PATH)
        import importlib
        mcp_server = importlib.import_module("mcp_server")
        call_ai_provider = mcp_server.call_ai_provider
        
        result = await call_ai_provider(
            "perplexity",
            query,
            mode=mode,
        )
        return {
            "query": query,
            "results": [{"content": result, "source": "perplexity"}],
            "source": "perplexity",
            "raw": result,
        }
    except Exception as e:
        logger.error(f"Perplexity search failed: {e}")
        return {"error": str(e), "results": [], "source": "perplexity"}


async def ai_research(
    prompt: str,
    providers: Optional[List[str]] = None,
    delay_ms: int = 750,
) -> Dict[str, Any]:
    """
    Multi-provider research using APITHON AI Orchestrator.
    
    Chains queries across available providers (Gemini, Qwen, Claude, Perplexity).
    
    Args:
        prompt: Research query text
        providers: List of providers to use (default: all available)
        delay_ms: Delay between provider calls in ms
    
    Returns:
        Dict with 'results' key mapping provider names to responses
    """
    if not _lazy_import("router"):
        return {"error": "AI Router not available", "results": {}}
    
    try:
        # Import the live call_ai_provider and sessions from mcp_server
        sys.path.insert(0, APITHON_PATH)
        import importlib
        mcp_server = importlib.import_module("mcp_server")
        sessions = mcp_server.sessions
        call_ai_provider = mcp_server.call_ai_provider
        
        if _ai_router is None:
            return {"error": "AI Router not initialized", "results": {}}
        AIOrchestrator = _ai_router[0]
        orchestrator = AIOrchestrator(sessions=sessions, provider_caller=call_ai_provider)
        result = await orchestrator.research(
            prompt,
            providers=providers,
            delay_ms=delay_ms,
        )
        return {"results": result, "prompt": prompt}
    except Exception as e:
        logger.error(f"AI research failed: {e}")
        return {"error": str(e), "results": {}}


async def web_scrape(url: str, use_vision: bool = False) -> Dict[str, Any]:
    """
    Scrape a webpage using APITHON SmartWebScraper.
    
    Args:
        url: URL to scrape
        use_vision: Whether to capture a screenshot for vision-based parsing
    
    Returns:
        Dict with 'content', 'title', 'screenshot' (if use_vision)
    """
    if not _lazy_import("scraper"):
        return {"error": "Smart scraper not available"}
    
    try:
        scraper = _scraper.SmartWebScraper()
        result = await scraper.scrape(url, needs_vision=use_vision)
        
        output = {
            "url": url,
            "content": getattr(result, "content", str(result)),
            "title": getattr(result, "title", ""),
        }
        if use_vision and hasattr(result, "screenshot"):
            output["screenshot"] = result.screenshot
        return output
    except Exception as e:
        logger.error(f"Web scrape failed: {e}")
        return {"error": str(e), "url": url}


__all__ = [
    "check_apithon",
    "perplexity_search",
    "ai_research",
    "web_scrape",
]
