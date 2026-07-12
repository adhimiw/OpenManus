"""Tool module — lazy imports to avoid heavy dependency chain at module load."""

from app.tool.base import BaseTool
from app.tool.tool_collection import ToolCollection
from app.tool.terminate import Terminate
from app.tool.create_chat_completion import CreateChatCompletion

# Optional — may fail without browser-use, baidusearch, etc.
_BROWSER_USE_TOOL = None
_BASH_TOOL = None
_CRAWL4AI_TOOL = None
_PLANNING_TOOL = None
_STR_REPLACE_EDITOR = None
_WEB_SEARCH = None

def _get_browser_use_tool():
    global _BROWSER_USE_TOOL
    if _BROWSER_USE_TOOL is None:
        try:
            from app.tool.browser_use_tool import BrowserUseTool
            _BROWSER_USE_TOOL = BrowserUseTool
        except Exception:
            _BROWSER_USE_TOOL = False
    return _BROWSER_USE_TOOL if _BROWSER_USE_TOOL else None

def _get_bash():
    global _BASH_TOOL
    if _BASH_TOOL is None:
        try:
            from app.tool.bash import Bash
            _BASH_TOOL = Bash
        except Exception:
            _BASH_TOOL = False
    return _BASH_TOOL if _BASH_TOOL else None

def _get_crawl4ai():
    global _CRAWL4AI_TOOL
    if _CRAWL4AI_TOOL is None:
        try:
            from app.tool.crawl4ai import Crawl4aiTool
            _CRAWL4AI_TOOL = Crawl4aiTool
        except Exception:
            _CRAWL4AI_TOOL = False
    return _CRAWL4AI_TOOL if _CRAWL4AI_TOOL else None

def _get_planning():
    global _PLANNING_TOOL
    if _PLANNING_TOOL is None:
        try:
            from app.tool.planning import PlanningTool
            _PLANNING_TOOL = PlanningTool
        except Exception:
            _PLANNING_TOOL = False
    return _PLANNING_TOOL if _PLANNING_TOOL else None

def _get_str_replace_editor():
    global _STR_REPLACE_EDITOR
    if _STR_REPLACE_EDITOR is None:
        try:
            from app.tool.str_replace_editor import StrReplaceEditor
            _STR_REPLACE_EDITOR = StrReplaceEditor
        except Exception:
            _STR_REPLACE_EDITOR = False
    return _STR_REPLACE_EDITOR if _STR_REPLACE_EDITOR else None

def _get_web_search():
    global _WEB_SEARCH
    if _WEB_SEARCH is None:
        try:
            from app.tool.web_search import WebSearch
            _WEB_SEARCH = WebSearch
        except Exception:
            _WEB_SEARCH = False
    return _WEB_SEARCH if _WEB_SEARCH else None

# Compatibility: keep direct access for code that already imports these
BrowserUseTool = _get_browser_use_tool
Bash = _get_bash
Crawl4aiTool = _get_crawl4ai
PlanningTool = _get_planning
StrReplaceEditor = _get_str_replace_editor
WebSearch = _get_web_search


__all__ = [
    "BaseTool",
    "Bash",
    "BrowserUseTool",
    "Terminate",
    "StrReplaceEditor",
    "WebSearch",
    "ToolCollection",
    "CreateChatCompletion",
    "PlanningTool",
    "Crawl4aiTool",
]
