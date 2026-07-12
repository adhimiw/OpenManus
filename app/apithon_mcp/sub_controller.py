"""
OpenManus Sub-Controller — multi-agent task routing.

Concept:
┌──────────────┐   sub_agent.run(request)   ┌─────────────────┐
│  Manus/Main  │ ──────────────────────────▶ │  Sub-Controller │
│  OpenManus   │                             │  (this module)  │
└──────────────┘                             └───┬───┬───┬───┬──┘
     ▲                                          │   │   │   │
     │                   routes to:             │   │   │   │
     │                ┌────────────┐ ◄──────────┘   │   │   │
     │                │  Seto      │                │   │   │
     │                │  (Research)│ ◄──────────────┘   │   │
     │                └────────────┘                    │   │
     │                ┌────────────┐ ◄──────────────────┘   │
     │                │  Veto      │                        │
     │                │  (Pentest) │ ◄──────────────────────┘
     │                └────────────┘
     │                ┌────────────┐
     │                │  Jarvis    │
     │                │  (General) │
     │                └────────────┘
"""

import asyncio
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from app.logger import logger

logger = logging.getLogger("sub_controller")


class AgentType(str, Enum):
    """Available sub-agent types."""
    SETO = "seto"          # AI research across providers
    VETO = "veto"          # Security auditing / pentesting
    JARVIS = "jarvis"      # General assistance
    ODYSSEUS = "odysseus"  # Framework extension
    APITHON = "apithon"    # APITHON protocol bridge (research)


class TaskResult:
    """Result from a sub-agent task execution."""

    def __init__(
        self,
        agent: AgentType,
        status: str,
        output: str = "",
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        self.agent = agent
        self.status = status  # "completed", "failed", "timeout", "skipped"
        self.output = output
        self.error = error
        self.metadata = metadata or {}

    def __str__(self) -> str:
        return f"[{self.agent.value}] {self.status}: {self.output[:200]}"

    def to_dict(self) -> Dict:
        return {
            "agent": self.agent.value,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


class SubController:
    """
    Routes task requests to the appropriate sub-agent.
    
    Maintains task history and provides a unified interface
    for delegating to Seto, Veto, Jarvis, etc.
    """
    
    def __init__(self):
        self.task_history: List[TaskResult] = []
        self._task_lock = asyncio.Lock()
        self._max_history = 50
    
    async def dispatch(
        self,
        agent: AgentType,
        request: str,
        context: Optional[Dict] = None,
        timeout: int = 120,
    ) -> TaskResult:
        """
        Dispatch a task to the specified sub-agent.
        
        Args:
            agent: Which sub-agent to route to
            request: The task description/prompt
            context: Optional context dict (e.g. workspace paths, credentials)
            timeout: Max seconds for task execution
        
        Returns:
            TaskResult with status and output
        """
        async with self._task_lock:
            logger.info(f"SubController: dispatching to {agent.value}: {request[:100]}...")
            
            try:
                result = await asyncio.wait_for(
                    self._execute(agent, request, context or {}),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                result = TaskResult(
                    agent=agent,
                    status="timeout",
                    error=f"Task timed out after {timeout}s",
                )
            except Exception as e:
                logger.exception(f"SubController error with {agent.value}")
                result = TaskResult(
                    agent=agent,
                    status="failed",
                    error=str(e),
                )
            
            self.task_history.append(result)
            # Trim history
            if len(self.task_history) > self._max_history:
                self.task_history = self.task_history[-self._max_history:]
            
            return result
    
    async def _execute(
        self,
        agent: AgentType,
        request: str,
        context: Dict,
    ) -> TaskResult:
        """Route to the correct execution handler."""
        handlers = {
            AgentType.SETO: self._run_seto,
            AgentType.VETO: self._run_veto,
            AgentType.JARVIS: self._run_jarvis,
            AgentType.ODYSSEUS: self._run_odysseus,
            AgentType.APITHON: self._run_apithon_bridge,
        }
        
        handler = handlers.get(agent)
        if not handler:
            return TaskResult(agent=agent, status="failed", error=f"Unknown agent: {agent}")
        
        return await handler(request, context)
    
    async def _run_seto(self, request: str, context: Dict) -> TaskResult:
        """
        Seto Research Agent — multi-provider AI research.
        
        Uses APITHON bridge internally to research across Perplexity,
        Gemini, Qwen, and Claude. Think of Seto as a persistent
        research assistant that Summarises, Evaluates, Transforms, and
        Organises information.
        """
        try:
            from .bridge import ai_research, check_apithon, perplexity_search
            
            status = check_apithon()
            if status.get("router"):
                # Multi-provider research
                providers = {
                    "gemini": status.get("gemini", False),
                    "perplexity": status.get("perplexity", False),
                    "qwen": status.get("structure", False),
                    "claude_web": status.get("claude", False),
                }
                available = [p for p, ok in providers.items() if ok]
                
                logger.info(f"Seto: multi-provider research via {available}")
                result = await ai_research(request, providers=available or None)
                
                if "error" in result:
                    # Fall back to Perplexity alone
                    result = await perplexity_search(request)
                
                output = result.get("raw", json.dumps(result.get("results", {}), indent=2))
                return TaskResult(
                    agent=AgentType.SETO,
                    status="completed",
                    output=str(output)[:5000],
                    metadata={"providers": available},
                )
            elif status.get("perplexity"):
                result = await perplexity_search(request)
                output = result.get("raw", json.dumps(result.get("results", []), indent=2))
                return TaskResult(
                    agent=AgentType.SETO,
                    status="completed",
                    output=str(output)[:5000],
                )
            else:
                return TaskResult(
                    agent=AgentType.SETO,
                    status="skipped",
                    output="Seto research unavailable: no APITHON providers loaded",
                )
        except Exception as e:
            logger.exception("Seto research failed")
            return TaskResult(agent=AgentType.SETO, status="failed", error=str(e))
    
    async def _run_veto(self, _request: str, _context: Dict) -> TaskResult:
        """
        Veto Security Agent.
        
        Placeholder — Veto would run security scans, port audits,
        dependency vulnerability checks.
        """
        return TaskResult(
            agent=AgentType.VETO,
            status="skipped",
            output="Veto agent not yet implemented. OpenManus sandbox mode enables security isolation.",
        )
    
    async def _run_jarvis(self, _request: str, _context: Dict) -> TaskResult:
        """
        Jarvis General Agent.
        
        Placeholder — Jarvis would handle general helper tasks,
        file operations, and routine automation.
        """
        return TaskResult(
            agent=AgentType.JARVIS,
            status="skipped",
            output="Jarvis agent not yet implemented. Main Manus agent handles general tasks.",
        )
    
    async def _run_odysseus(self, _request: str, _context: Dict) -> TaskResult:
        """Odysseus Extension Agent — placeholder."""
        return TaskResult(
            agent=AgentType.ODYSSEUS,
            status="skipped",
            output="Odysseus agent not yet implemented. Extends framework capabilities.",
        )
    
    async def _run_apithon_bridge(self, request: str, context: Dict) -> TaskResult:
        """APITHON Protocol Bridge."""
        from .bridge import check_apithon
        
        status = check_apithon()
        return TaskResult(
            agent=AgentType.APITHON,
            status="completed" if any(status.values()) else "failed",
            output=json.dumps(status, indent=2),
            metadata={"available": [k for k, v in status.items() if v]},
        )
    
    def get_history(self, last_n: int = 10) -> List[TaskResult]:
        """Get recent task execution history."""
        return self.task_history[-last_n:] if self.task_history else []


# Singleton
_instance: Optional[SubController] = None


def get_sub_controller() -> SubController:
    global _instance
    if _instance is None:
        _instance = SubController()
    return _instance
