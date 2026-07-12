"""Agent module — lazy imports for faster module loading."""

from app.agent.base import BaseAgent
from app.agent.toolcall import ToolCallAgent
from app.agent.react import ReActAgent

# Optional — depends on browser-use, etc.
_BROWSER_AGENT = None
_MCP_AGENT = None
_SWE_AGENT = None

def _get_browser_agent():
    global _BROWSER_AGENT
    if _BROWSER_AGENT is None:
        try:
            from app.agent.browser import BrowserAgent
            _BROWSER_AGENT = BrowserAgent
        except Exception:
            _BROWSER_AGENT = False
    return _BROWSER_AGENT if _BROWSER_AGENT else None

def _get_mcp_agent():
    global _MCP_AGENT
    if _MCP_AGENT is None:
        try:
            from app.agent.mcp import MCPAgent
            _MCP_AGENT = MCPAgent
        except Exception:
            _MCP_AGENT = False
    return _MCP_AGENT if _MCP_AGENT else None

def _get_swe_agent():
    global _SWE_AGENT
    if _SWE_AGENT is None:
        try:
            from app.agent.swe import SWEAgent
            _SWE_AGENT = SWEAgent
        except Exception:
            _SWE_AGENT = False
    return _SWE_AGENT if _SWE_AGENT else None

# Compatibility wrappers
BrowserAgent = _get_browser_agent
MCPAgent = _get_mcp_agent
SWEAgent = _get_swe_agent


__all__ = [
    "BaseAgent",
    "BrowserAgent",
    "ReActAgent",
    "SWEAgent",
    "ToolCallAgent",
    "MCPAgent",
]
