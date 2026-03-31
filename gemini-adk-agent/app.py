"""
Flask HTTP server — exposes the ADK Summarizer Agent via:
  POST /run        → JSON API endpoint (for graders / curl)
  GET  /           → Browser UI
  GET  /health     → Health check
"""

import os
from flask import Flask, request, jsonify, render_template_string
from agent import SummarizerAgent

app = Flask(__name__)

# Instantiate once at startup (not per-request → saves init time)
try:
    agent = SummarizerAgent()
    AGENT_READY = True
except Exception as e:
    agent = None
    AGENT_READY = False
    AGENT_ERROR = str(e)

# ── HTML UI (single-file, embedded) ──────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Gemini ADK Summarizer Agent</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --border: #2a2a3a;
    --accent: #7c6dff;
    --accent2: #00e5a0;
    --text: #e8e8f0;
    --muted: #6b6b80;
    --error: #ff5a5a;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { font-size: 16px; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem 1rem 4rem;
  }
  /* grid bg */
  body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(rgba(124,109,255,.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(124,109,255,.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }

  .wrap { position: relative; z-index: 1; width: 100%; max-width: 720px; }

  /* Header */
  header { text-align: center; margin-bottom: 3rem; }
  .badge {
    display: inline-flex; align-items: center; gap: .5rem;
    background: rgba(124,109,255,.12);
    border: 1px solid rgba(124,109,255,.3);
    border-radius: 999px;
    padding: .3rem 1rem;
    font-family: 'Space Mono', monospace;
    font-size: .72rem;
    color: var(--accent);
    margin-bottom: 1.2rem;
    letter-spacing: .06em;
  }
  .dot { width:6px;height:6px;border-radius:50%;background:var(--accent2);animation:pulse 1.8s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
  h1 { font-size: clamp(1.8rem, 5vw, 2.8rem); font-weight: 800; letter-spacing: -.02em; line-height: 1.1; }
  h1 span { color: var(--accent); }
  .sub { color: var(--muted); font-size: .95rem; margin-top: .6rem; font-weight: 400; }

  /* Card */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
  }
  label { display:block; font-size:.8rem; font-weight:700; letter-spacing:.08em; color:var(--muted); margin-bottom:.6rem; text-transform:uppercase; }
  textarea {
    width: 100%;
    min-height: 160px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: .85rem;
    line-height: 1.6;
    padding: 1rem;
    resize: vertical;
    transition: border-color .2s;
    outline: none;
  }
  textarea:focus { border-color: var(--accent); }
  .row { display:flex; gap:.8rem; margin-top:1rem; align-items:center; flex-wrap:wrap; }
  .counter { font-family:'Space Mono',monospace; font-size:.75rem; color:var(--muted); flex:1; }
  button {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: .75rem 2rem;
    font-family: 'Syne', sans-serif;
    font-size: .95rem;
    font-weight: 700;
    cursor: pointer;
    transition: opacity .15s, transform .1s;
    white-space: nowrap;
  }
  button:hover { opacity:.88; transform:translateY(-1px); }
  button:active { transform:translateY(0); }
  button:disabled { opacity:.4; cursor:not-allowed; transform:none; }
  .examples {
    display: flex; gap:.5rem; flex-wrap:wrap; margin-top:1rem;
  }
  .ex-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    border-radius:8px;
    padding:.35rem .9rem;
    font-size:.78rem;
    cursor:pointer;
    transition: border-color .2s, color .2s;
  }
  .ex-btn:hover { border-color:var(--accent); color:var(--accent); }

  /* Result */
  #result { display:none; }
  .tag {
    display:inline-block;
    background: rgba(0,229,160,.1);
    border: 1px solid rgba(0,229,160,.25);
    color: var(--accent2);
    border-radius:6px;
    padding:.2rem .6rem;
    font-family:'Space Mono',monospace;
    font-size:.72rem;
    margin-bottom:1rem;
    letter-spacing:.05em;
  }
  .summary-text {
    font-size:1.05rem;
    line-height:1.7;
    color:var(--text);
    margin-bottom:1.5rem;
    padding-bottom:1.5rem;
    border-bottom:1px solid var(--border);
  }
  .kp-label { font-size:.78rem; font-weight:700; letter-spacing:.08em; color:var(--muted); text-transform:uppercase; margin-bottom:.8rem; }
  .kp-list { list-style:none; display:flex; flex-direction:column; gap:.6rem; }
  .kp-list li {
    display:flex; gap:.75rem; align-items:flex-start;
    font-size:.92rem; line-height:1.5;
  }
  .kp-list li::before {
    content:'→';
    color:var(--accent);
    font-family:'Space Mono',monospace;
    flex-shrink:0;
    margin-top:.05rem;
  }

  /* JSON toggle */
  .json-toggle {
    background:transparent; border:1px solid var(--border);
    color:var(--muted); border-radius:8px; padding:.4rem .9rem;
    font-size:.78rem; cursor:pointer; margin-top:1.2rem;
    width:100%; transition:border-color .2s;
  }
  .json-toggle:hover { border-color:var(--accent); }
  #raw-json { display:none; margin-top:.8rem; }
  pre {
    background:var(--bg); border:1px solid var(--border);
    border-radius:10px; padding:1rem;
    font-family:'Space Mono',monospace; font-size:.78rem;
    color:#a0a0c0; overflow-x:auto; white-space:pre-wrap;
  }

  /* Loader */
  .loader { display:none; text-align:center; padding:2rem; }
  .spinner {
    width:36px;height:36px;border-radius:50%;
    border:3px solid var(--border);
    border-top-color:var(--accent);
    animation:spin .8s linear infinite;
    margin:0 auto .8rem;
  }
  @keyframes spin { to{ transform:rotate(360deg) } }
  .loader p { color:var(--muted); font-size:.85rem; font-family:'Space Mono',monospace; }

  /* Error */
  .err { color:var(--error); background:rgba(255,90,90,.08); border:1px solid rgba(255,90,90,.2); border-radius:10px; padding:1rem; font-size:.9rem; }

  /* API docs */
  .api-card { margin-top: 2rem; }
  .api-card h3 { font-size:.9rem; font-weight:700; letter-spacing:.06em; color:var(--muted); text-transform:uppercase; margin-bottom:1rem; }
  .endpoint { display:flex; align-items:center; gap:.8rem; flex-wrap:wrap; margin-bottom:.8rem; }
  .method { background:rgba(124,109,255,.15); color:var(--accent); border-radius:6px; padding:.2rem .7rem; font-family:'Space Mono',monospace; font-size:.78rem; font-weight:700; }
  .path { font-family:'Space Mono',monospace; font-size:.85rem; color:var(--text); }
  .desc { font-size:.83rem; color:var(--muted); }

  footer { margin-top:3rem; text-align:center; font-size:.78rem; color:var(--muted); font-family:'Space Mono',monospace; }
  footer a { color:var(--accent); text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="badge"><span class="dot"></span> ADK + Gemini 1.5 Flash · Live</div>
    <h1>Text <span>Summarizer</span> Agent</h1>
    <p class="sub">Paste any text. The ADK agent calls Gemini and returns a structured summary.</p>
  </header>

  <div class="card">
    <label for="txt">Input Text</label>
    <textarea id="txt" placeholder="Paste an article, paragraph, or any text you want summarized…"></textarea>
    <div class="row">
      <span class="counter" id="counter">0 / 2000 chars</span>
      <button id="btn" onclick="summarize()">✦ Summarize</button>
    </div>
    <div class="examples">
      <span style="font-size:.78rem;color:var(--muted);align-self:center;">Try:</span>
      <button class="ex-btn" onclick="loadExample(0)">AI Article</button>
      <button class="ex-btn" onclick="loadExample(1)">Climate Science</button>
      <button class="ex-btn" onclick="loadExample(2)">Tech News</button>
    </div>
  </div>

  <div class="loader" id="loader">
    <div class="spinner"></div>
    <p>Agent is thinking…</p>
  </div>

  <div class="card" id="result">
    <span class="tag">✓ SUMMARY READY</span>
    <div class="summary-text" id="summary-text"></div>
    <div class="kp-label">Key Points</div>
    <ul class="kp-list" id="kp-list"></ul>
    <button class="json-toggle" onclick="toggleJson()">{ } View Raw JSON</button>
    <div id="raw-json"><pre id="json-pre"></pre></div>
  </div>

  <div class="card api-card">
    <h3>HTTP API</h3>
    <div class="endpoint">
      <span class="method">POST</span>
      <span class="path">/run</span>
      <span class="desc">Submit text, get structured JSON summary</span>
    </div>
    <pre style="margin-top:.5rem;">curl -X POST /run \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Your text here…"}'</pre>
    <div class="endpoint" style="margin-top:1rem;">
      <span class="method">GET</span>
      <span class="path">/health</span>
      <span class="desc">Agent health check</span>
    </div>
  </div>

  <footer>
    Built with <a href="https://google.github.io/adk-docs/" target="_blank">Google ADK</a> + Gemini 1.5 Flash ·
    <a href="https://github.com/YOUR_USERNAME/gemini-adk-agent" target="_blank">GitHub</a>
  </footer>
</div>

<script>
const EXAMPLES = [
  `Artificial intelligence (AI) is transforming industries at an unprecedented pace. Machine learning models can now write code, generate images, compose music, and even assist in medical diagnoses. Companies like Google, OpenAI, and Anthropic are racing to build more capable systems. However, experts warn that rapid deployment without adequate safety measures poses significant risks. Governments worldwide are beginning to draft AI regulations, while researchers debate the timeline to artificial general intelligence. The economic implications are vast — studies suggest AI could automate up to 30% of current jobs by 2030, while simultaneously creating entirely new categories of work.`,

  `Climate scientists have issued a stark warning: the window to limit global warming to 1.5°C above pre-industrial levels is rapidly closing. The latest IPCC report indicates that without immediate and drastic reductions in greenhouse gas emissions, the world is on track for 2.5–3°C of warming by 2100. This would trigger widespread coral reef collapse, accelerate sea level rise threatening coastal cities, and increase the frequency of extreme weather events. Renewable energy adoption is accelerating — solar capacity doubled in three years — but fossil fuel consumption is still at record highs. Carbon capture technologies remain expensive and unproven at scale.`,

  `Apple unveiled its latest chip architecture at WWDC, promising a 40% performance improvement over the previous generation while reducing power consumption by 25%. The new silicon integrates a dedicated neural processing unit capable of running large language models locally, without cloud connectivity. This marks a significant shift in the industry as on-device AI inference becomes mainstream. Developers will gain access to new APIs that tap into the NPU directly, enabling real-time translation, advanced photo editing, and context-aware automation — all processed privately on the device. Analysts expect competitors to accelerate their own custom silicon roadmaps in response.`
];

const textarea = document.getElementById('txt');
textarea.addEventListener('input', () => {
  document.getElementById('counter').textContent = `${textarea.value.length} / 2000 chars`;
});

function loadExample(i) {
  textarea.value = EXAMPLES[i];
  textarea.dispatchEvent(new Event('input'));
}

function toggleJson() {
  const el = document.getElementById('raw-json');
  el.style.display = el.style.display === 'block' ? 'none' : 'block';
}

async function summarize() {
  const text = textarea.value.trim();
  if (!text) { alert('Please enter some text first.'); return; }

  document.getElementById('btn').disabled = true;
  document.getElementById('loader').style.display = 'block';
  document.getElementById('result').style.display = 'none';

  try {
    const res = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const json = await res.json();

    document.getElementById('loader').style.display = 'none';

    if (json.status === 'error') {
      const r = document.getElementById('result');
      r.style.display = 'block';
      r.innerHTML = `<div class="err">⚠ ${json.message || 'Agent error. Check your API key.'}</div>`;
      return;
    }

    const data = json.data || {};
    document.getElementById('summary-text').textContent = data.summary || '—';

    const kpList = document.getElementById('kp-list');
    kpList.innerHTML = '';
    (data.key_points || []).forEach(p => {
      const li = document.createElement('li');
      li.textContent = p;
      kpList.appendChild(li);
    });

    document.getElementById('json-pre').textContent = JSON.stringify(json, null, 2);
    document.getElementById('result').style.display = 'block';

  } catch(e) {
    document.getElementById('loader').style.display = 'none';
    alert('Network error: ' + e.message);
  } finally {
    document.getElementById('btn').disabled = false;
  }
}
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    if AGENT_READY:
        return jsonify({"status": "ok", "agent": "SummarizerAgent", "model": "gemini-1.5-flash"})
    return jsonify({"status": "error", "message": AGENT_ERROR}), 500


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/run", methods=["POST"])
def run_agent():
    """
    Main ADK agent endpoint.
    Body: { "text": "..." }
    Returns: { "status": "success"|"error", "data": { "summary": "...", "key_points": [...] } }
    """
    if not AGENT_READY:
        return jsonify({"status": "error", "message": "Agent not initialized. Check GEMINI_API_KEY."}), 500

    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()

    if not text:
        return jsonify({"status": "error", "message": "Field 'text' is required."}), 400

    result = agent.run(text)
    code = 200 if result.get("status") == "success" else 500
    return jsonify(result), code


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
