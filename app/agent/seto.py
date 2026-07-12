"""
Enhanced Manus agent with APITHON MCP bridge and Sub-Controller.
Extends the base Manus with Seto research capabilities.
"""

from typing import Dict, List, Optional

from pydantic import Field

from app.agent.manus import Manus
from app.apithon_mcp.sub_controller import AgentType, SubController, get_sub_controller
from app.logger import logger
from app.tool import ToolCollection


class SetoManus(Manus):
    """
    OpenManus agent enhanced with APITHON research tools and Sub-Controller.
    
    SetoManus = Manus + APITHON Bridge + Sub-Controller + Seto Dashboard
    
    Adds:
    - perplexity_search: Deep Perplexity AI search tool (lazy-loaded)
    - multi_ai_search: Cross-provider AI research tool (lazy-loaded)
    - web_scrape_apithon: APITHON SmartScraper tool (lazy-loaded)
    - sub_controller: Delegates Seto research tasks
    """
    
    name: str = "SetoManus"
    description: str = (
        "Enhanced agent with APITHON MCP research (Perplexity, Gemini, Qwen, Claude) "
        "and Sub-Controller for Seto research agent tasks."
    )
    
    # Sub-Controller for task routing
    sub_controller: SubController = Field(default_factory=get_sub_controller)
    
    # Override tools — populate lazily in __init__
    available_tools: ToolCollection = Field(default_factory=lambda: ToolCollection())
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._add_apithon_tools()
    
    def _add_apithon_tools(self):
        """Add APITHON tools to the available tools collection, 
        loading them lazily to avoid heavy dependencies (browser-use, etc.)."""
        try:
            # Only import base tools that don't trigger browser-use
            from app.tool.python_execute import PythonExecute
            from app.tool.str_replace_editor import StrReplaceEditor
            from app.tool.ask_human import AskHuman
            from app.tool import Terminate
            
            base_tools = [
                PythonExecute(),
                StrReplaceEditor(),
                AskHuman(),
                Terminate(),
            ]
            
            # Try browser tool — may fail without browser-use installed
            try:
                from app.tool.browser_use_tool import BrowserUseTool
                base_tools.append(BrowserUseTool())
            except Exception as e:
                logger.warning(f"Browser tool unavailable: {e}")
            
            # Conditionally add APITHON tools (lazy — construct is cheap now)
            apithon_tools = []
            try:
                from app.apithon_mcp.tools import PerplexitySearch
                apithon_tools.append(PerplexitySearch())
            except Exception as e:
                logger.warning(f"PerplexitySearch: {e}")
            
            try:
                from app.apithon_mcp.tools import MultiAISearch
                apithon_tools.append(MultiAISearch())
            except Exception as e:
                logger.warning(f"MultiAISearch: {e}")
            
            try:
                from app.apithon_mcp.tools import WebScrape
                apithon_tools.append(WebScrape())
            except Exception as e:
                logger.warning(f"WebScrape: {e}")
            
            self.available_tools = ToolCollection(*base_tools, *apithon_tools)
            logger.info(
                f"SetoManus: {len(base_tools)} base tools + {len(apithon_tools)} APITHON tools"
            )
        except Exception as e:
            logger.error(f"Failed to add APITHON tools: {e}")
    
    async def run(self, request: Optional[str] = None) -> str:
        """Run with sub-controller routing for Seto research tasks."""
        if request:
            # Route research-type requests directly to Seto sub-agent
            seto_prefixes = [
                "research", "search", "find", "investigate",
                "what is", "who is", "how does", "tell me about",
            ]
            
            request_lower = request.lower().strip()
            is_research = any(request_lower.startswith(p) for p in seto_prefixes)
            
            if is_research:
                logger.info(f"SetoManus: routing research → Seto: {request[:80]}...")
                result = await self.sub_controller.dispatch(
                    AgentType.SETO,
                    request,
                    timeout=180,
                )
                if result.status == "completed":
                    return f"Seto research complete.\n{result.output[:3000]}"
                elif result.status == "skipped":
                    logger.info("Seto unavailable, falling back to normal execution")
                else:
                    logger.warning(f"Seto: {result.status}, falling back: {result.error}")
        
        return await super().run(request)


class ResearchSetoManus(Manus):
    """Alias for SetoManus — used by Seto dashboard."""
    pass
