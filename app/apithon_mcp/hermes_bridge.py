"""Seto Hermes integration — wires SetoManus + Seto Dashboard as a Hermes sub-controller.

This module provides:
- SetoAgent: drop-in Hermes-compatible agent that wraps SetoManus
- start_seto_dashboard: launch the Seto dashboard as a background service
- seto_query: single research query via SetoManus
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Project root
OPENMANUS_ROOT = Path(os.path.expanduser("~/projects/OpenManus"))
DASHBOARD_SCRIPT = OPENMANUS_ROOT / "run_seto_dashboard.py"
DASHBOARD_PORT = 8891


# ── Agent Wrapper ──────────────────────────────────────────────────────────


class SetoAgent:
    """Hermes-compatible wrapper around SetoManus.
    
    Usage:
        from app.apithon_mcp.hermes_bridge import SetoAgent
        agent = SetoAgent()
        result = await agent.query("research quantum computing")
    """
    
    def __init__(self):
        self._agent = None
    
    @property
    def agent(self):
        if self._agent is None:
            sys.path.insert(0, str(OPENMANUS_ROOT))
            # Suppress noisy logs
            import logging
            logging.getLogger("app.logger").setLevel(logging.WARNING)
            from app.agent.seto import SetoManus
            from app.tool import ToolCollection
            self._agent = SetoManus(available_tools=ToolCollection())
        return self._agent
    
    async def query(self, prompt: str, timeout: int = 180) -> str:
        """Run a research query through SetoManus.
        
        Returns the agent's response text.
        """
        result = await self.agent.run(prompt)
        return result
    
    def check_ready(self) -> dict:
        """Quick health check without starting full agent."""
        try:
            sys.path.insert(0, str(OPENMANUS_ROOT))
            from app.apithon_mcp.bridge import check_apithon
            import app.logger
            status = check_apithon()
            ready = [k for k, v in status.items() if v]
            return {
                "ready": len(ready) >= 5,
                "apithon": status,
                "services": ready,
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}


# ── Dashboard Service ──────────────────────────────────────────────────────


_dashboard_process: Optional[subprocess.Popen] = None


def start_seto_dashboard(port: int = DASHBOARD_PORT) -> dict:
    """Launch Seto dashboard as a background process.
    
    Returns status dict with pid and url.
    """
    global _dashboard_process
    
    if _dashboard_process and _dashboard_process.poll() is None:
        return {
            "status": "already running",
            "pid": _dashboard_process.pid,
            "url": f"http://localhost:{port}",
        }
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{OPENMANUS_ROOT}:{env.get('PYTHONPATH', '')}"
    env["DASHBOARD_PORT"] = str(port)
    
    _dashboard_process = subprocess.Popen(
        [sys.executable, str(DASHBOARD_SCRIPT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(OPENMANUS_ROOT),
    )
    
    return {
        "status": "started",
        "pid": _dashboard_process.pid,
        "url": f"http://localhost:{port}",
    }


def stop_seto_dashboard():
    """Stop the dashboard background process."""
    global _dashboard_process
    if _dashboard_process and _dashboard_process.poll() is None:
        _dashboard_process.terminate()
        _dashboard_process.wait(timeout=5)
        _dashboard_process = None
        return {"status": "stopped"}
    return {"status": "not running"}


def dashboard_status() -> dict:
    """Check if dashboard is running."""
    global _dashboard_process
    if _dashboard_process and _dashboard_process.poll() is None:
        return {
            "status": "running",
            "pid": _dashboard_process.pid,
            "url": f"http://localhost:{DASHBOARD_PORT}",
        }
    return {"status": "stopped"}
