"""
Seto Research Dashboard — FastAPI web UI for the OpenManus sub-controller.

Provides a browser-based dashboard to:
1. Launch Seto research tasks across Perplexity/Gemini/Qwen/Claude
2. View task history and results
3. Monitor sub-controller activity
4. Check APITHON protocol availability
"""

import json
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.apithon_mcp.bridge import check_apithon

logger = logging.getLogger("seto_dashboard")

# Will be set during app startup
sub_controller = None
perplexity_search_func = None

app = FastAPI(title="Seto Research Dashboard", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str
    providers: Optional[List[str]] = None
    timeout: int = 120


class TaskResponse(BaseModel):
    task_id: str
    status: str
    output: str
    error: Optional[str] = None


# ── API Routes ─────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)


@app.get("/api/status")
async def api_status():
    apithon_status = check_apithon()
    history = []
    if sub_controller:
        for item in sub_controller.get_history(20):
            history.append(item.to_dict())
    return {
        "apithon": apithon_status,
        "available_providers": [k for k, v in apithon_status.items() if v],
        "task_history": history,
        "sub_controller_loaded": sub_controller is not None,
        "version": app.version,
    }


@app.post("/api/research", response_class=HTMLResponse)
async def run_research(req: ResearchRequest):
    if not sub_controller:
        raise HTTPException(status_code=500, detail="Sub-controller not initialized")
    
    from app.apithon_mcp.sub_controller import AgentType
    
    result = await sub_controller.dispatch(
        agent=AgentType.SETO,
        request=req.query,
        context={"providers": req.providers} if req.providers else {},
        timeout=req.timeout,
    )
    
    lines = [
        "<div class='result-card'>",
        f"<h3>Result [{result.status}]</h3>",
        f"<p><strong>Query:</strong> {req.query}</p>",
        f"<p><strong>Status:</strong> <span class='badge badge-{result.status}'>{result.status}</span></p>",
    ]
    if result.output:
        lines.append(f"<pre class='output'>{_escape(result.output[:3000])}</pre>")
    if result.error:
        lines.append(f"<pre class='error-text'>{_escape(result.error)}</pre>")
    lines.append(f"<p class='meta'>Agent: {result.agent.value}</p>")
    if result.metadata:
        lines.append(f"<p class='meta'>Metadata: {json.dumps(result.metadata)}</p>")
    lines.append("</div>")
    
    return HTMLResponse("\n".join(lines))


@app.get("/api/history", response_class=HTMLResponse)
async def history_page():
    if not sub_controller:
        return HTMLResponse("<p>Sub-controller not initialized</p>")
    
    items = sub_controller.get_history(20)
    cards = []
    for item in reversed(items):
        cards.append(
            f"""<div class='history-card'>
                <span class='badge badge-{item.status}'>[{item.agent.value}] {item.status}</span>
                <code>{_escape(item.output[:150])}</code>
                <small>{item.error or ''}</small>
            </div>"""
        )
    return HTMLResponse("\n".join(cards) if cards else "<p>No history</p>")


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── HTML Template ──────────────────────────────────

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Seto Dashboard — OpenManus</title>
<style>
  :root {
    --bg: #0d1117;
    --card: #161b22;
    --border: #30363d;
    --fg: #c9d1d9;
    --accent: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --yellow: #d29922;
    --font: ui-monospace,SFMono-Regular,Consolas,monospace;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--fg); font: 14px var(--font); padding: 20px; }
  h1 { font-size: 24px; margin-bottom: 20px; }
  h1 span { color: var(--accent); }
  .grid { display: grid; gap: 20px; }
  .row { display: flex; gap: 20px; flex-wrap: wrap; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .card h2 { font-size: 16px; margin-bottom: 12px; color: var(--accent); }
  .card.wide { flex: 1; min-width: 300px; }
  label { display: block; margin-bottom: 4px; font-size: 12px; color: #8b949e; }
  textarea, input, select {
    width: 100%; background: #0d1117; border: 1px solid var(--border); color: var(--fg);
    padding: 8px 12px; border-radius: 4px; font: 14px var(--font); margin-bottom: 8px;
  }
  textarea { min-height: 80px; resize: vertical; }
  button {
    background: var(--accent); color: #fff; border: 0; border-radius: 4px;
    padding: 8px 16px; cursor: pointer; font: 14px var(--font);
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.5; cursor: wait; }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 600;
  }
  .badge-completed { background: #132e1a; color: var(--green); }
  .badge-failed { background: #2e1313; color: var(--red); }
  .badge-timeout { background: #2e2613; color: var(--yellow); }
  .badge-skipped { background: #1b1b1b; color: #666; }
  pre.output { background: #0d1117; padding: 8px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-size: 12px; max-height: 300px; overflow-y: auto; margin-top: 8px; }
  .error-text { color: var(--red); }
  .meta { color: #8b949e; font-size: 11px; margin-top: 4px; }
  #task-busy .loading { text-align: center; padding: 40px; }
  .spinner { animation: spin 1s linear infinite; display: inline-block; }
  @keyframes spin { to { rotate: 360deg; } }
  #history-list { max-height: 400px; overflow-y: auto; }
  .history-card { padding: 8px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
</style>
</head>
<body>
<h1>🜁 <span>Seto</span> Research Dashboard <small style="font-size:14px;color:#666">v1 · OpenManus</small></h1>

<div class="grid">
  <div class="row">
    <div class="card wide">
      <h2>Status</h2>
      <div id="status-view">Loading...</div>
    </div>
    <div class="card wide">
      <h2>Research</h2>
      <form id="research-form">
        <textarea id="query" placeholder="Research query..."></textarea>
        <label>Providers (comma-separated, empty=all available)</label>
        <input id="providers" placeholder="gemini, perplexity, qwen" value="perplexity">
        <label>Timeout (sec)</label>
        <input id="timeout" type="number" value="120" style="max-width:100px">
        <button type="submit">🔬 Research</button>
      </form>
    </div>
  </div>

  <div class="row">
    <div class="card wide" id="task-busy" style="display:none">
      <div class="loading"><span class="spinner">⟳</span> Researching...</div>
    </div>
    <div class="card wide" id="result-view" style="display:none">
      <h2>Result</h2>
      <div id="result-content"></div>
    </div>
  </div>

  <div class="card">
    <h2>Recent Tasks</h2>
    <div id="history-list">Loading...</div>
  </div>
</div>

<script>
async function loadStatus() {
  const r = await fetch('/api/status');
  const data = await r.json();
  const apithon = data.apithon || {};
  const avail = data.available_providers || [];
  document.getElementById('status-view').innerHTML = [
    '<div style="display:flex;gap:12px;flex-wrap:wrap">',
    avail.map(p => `<span class="badge badge-completed">${p} ✓</span>`).join('') || '<span style="color:#666">none loaded</span>',
    '</div>',
    '<p class="meta">APITHON protocols: ' + Object.entries(apithon).map(([k,v]) => k+':'+(v?'✓':'✗')).join(' | ') + '</p>',
    '<p class="meta">Tasks: ' + data.task_history.length + '</p>',
  ].join('');
}
async function loadHistory() {
  const r = await fetch('/api/history');
  document.getElementById('history-list').innerHTML = await r.text();
}

document.getElementById('research-form').onsubmit = async e => {
  e.preventDefault();
  const busy = document.getElementById('task-busy');
  const result = document.getElementById('result-view');
  const content = document.getElementById('result-content');
  busy.style.display = '';
  result.style.display = 'none';
  try {
    const r = await fetch('/api/research', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        query: document.getElementById('query').value,
        providers: document.getElementById('providers').value.split(',').map(s=>s.trim()).filter(Boolean),
        timeout: parseInt(document.getElementById('timeout').value) || 120,
      }),
    });
    content.innerHTML = await r.text();
    result.style.display = '';
    loadHistory();
    loadStatus();
  } catch(e) {
    content.innerHTML = '<div class="error-text">Error: ' + e.message + '</div>';
    result.style.display = '';
  } finally {
    busy.style.display = 'none';
  }
};

loadStatus();
loadHistory();
setInterval(loadHistory, 15000);
</script>
</body>
</html>"""


def run_dashboard(host: str = "127.0.0.1", port: int = 8891):
    """Run the Seto dashboard server."""
    import uvicorn
    logger.info(f"Starting Seto Dashboard on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Bootstrap sub-controller
    from app.apithon_mcp.sub_controller import get_sub_controller
    sub_controller = get_sub_controller()
    run_dashboard()
