"""
APITHON stdio-based MCP Server for OpenManus.

This is the MCP server that OpenManus connects to via stdio,
providing Perplexity search, Gemini/Qwen/Claude chat, and
web scraping tools.

Usage:
  python -m app.apithon.apithon_server
  
  # Or from run_mcp.py:
  python run_mcp.py --connection stdio
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.WARNING)

# APITHON path
APITHON_PATH = os.environ.get(
    "APITHON_PATH",
    os.path.expanduser("~/projects/APITHON-main/APITHON-main/mcp_apithon"),
)

if APITHON_PATH and os.path.isdir(APITHON_PATH) and APITHON_PATH not in sys.path:
    sys.path.insert(0, APITHON_PATH)

from app.logger import logger
from app.apithon_mcp.bridge import check_apithon, perplexity_search, web_scrape

# Try to load all APITHON protocols
HAS_APITHON = check_apithon()


async def handle_call(tool_name: str, args: Dict) -> Dict:
    """Execute an APITHON MCP tool."""
    logger.info(f"apithon_server: {tool_name} called with {args}")
    
    if tool_name == "apithon_status":
        return {"output": json.dumps(HAS_APITHON, indent=2)}
    
    if tool_name == "perplexity_search":
        result = await perplexity_search(
            query=args.get("query", ""),
            max_results=args.get("max_results", 5),
        )
        return {"output": result.get("raw", str(result))}
    
    if tool_name == "web_scrape":
        result = await web_scrape(
            url=args.get("url", ""),
            use_vision=args.get("use_vision", False),
        )
        return {"output": result.get("content", str(result))}
    
    return {"error": f"Unknown tool: {tool_name}"}


async def listen_stdio():
    """
    Simple stdio-based MCP transport.
    Reads JSON lines on stdin, writes JSON responses on stdout.
    """
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    loop = asyncio.get_event_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    
    writer = sys.stdout
    
    # Send initialization message
    init_msg = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "openmanus-apithon", "version": "1.0.0"},
        },
        "tools": [
            {
                "name": "apithon_status",
                "description": "Check available APITHON protocols",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "perplexity_search",
                "description": "Deep web research using Perplexity AI",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "description": "max 10"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "web_scrape",
                "description": "Scrape a webpage with APITHON",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to scrape"},
                        "use_vision": {"type": "boolean", "default": False},
                    },
                    "required": ["url"],
                },
            },
        ],
    }
    writer.write((json.dumps(init_msg) + "\n").encode())
    writer.flush()
    
    if not HAS_APITHON.get("perplexity"):
        logger.warning("APITHON perplexity protocol not available")

    logger.info("apithon_server: listening for requests")
    
    while True:
        try:
            line = await reader.readline()
        except (ConnectionError, EOFError):
            break
        
        if not line:
            break
        
        try:
            req = json.loads(line.decode())
            req_id = req.get("id", 0)
            method = req.get("method", "call_tool")
            params = req.get("params", {})
            
            if method == "list_tools":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "tools": init_msg["tools"],
                }
            elif method == "call_tool":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                result = await handle_call(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result,
                }
            elif method == "initialize":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            
            writer.write((json.dumps(response) + "\n").encode())
            writer.flush()
            
        except json.JSONDecodeError:
            logger.warning(f"apithon_server: invalid JSON received")
            continue
        except Exception as e:
            logger.error(f"apithon_server: handler error: {e}")
            continue


def main():
    logger.info("APITHON MCP Server starting (stdio)...")
    logger.info(f"Detected protocols: {HAS_APITHON}")
    try:
        asyncio.run(listen_stdio())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
