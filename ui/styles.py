"""
UI styles for the Overland Intelligence System.

Baja pit crew meets tactical operations display.
Earned, not neglected. Field command center aesthetic.

Inject with: st.markdown(get_css(), unsafe_allow_html=True)
"""


def get_css() -> str:
    return f"""
<style>
/* ============================================================
   FONTS
   ============================================================ */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600&display=swap');

/* ============================================================
   ROOT VARIABLES
   ============================================================ */
:root {{
    --bg:           #0A0E0A;
    --bg-panel:     #0F140F;
    --bg-raised:    #141A14;
    --accent:       #39FF14;
    --accent-dim:   #1A7A08;
    --brass:        #C8B560;
    --alert:        #D4431A;
    --text:         #D6DDD0;
    --text-dim:     #7A8A78;
    --grid:         #1E241E;
    --border:       #2A342A;
    --rust:         #5C2E10;
}}

/* ============================================================
   BASE
   ============================================================ */
.stApp {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif !important;
}}

/* Hide Streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{
    padding-top: 0 !important;
    max-width: 1200px !important;
}}

/* ============================================================
   HEADER STRIP — diamond plate texture + hazard stripe
   ============================================================ */
.ois-header {{
    background:
        repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(212,67,26,0.08) 10px,
            rgba(212,67,26,0.08) 20px
        ),
        repeating-linear-gradient(
            -45deg,
            transparent,
            transparent 6px,
            rgba(200,181,96,0.06) 6px,
            rgba(200,181,96,0.06) 8px
        ),
        linear-gradient(180deg, #1A1F1A 0%, #0F140F 100%);
    border-bottom: 3px solid var(--brass);
    padding: 18px 28px 14px 28px;
    margin-bottom: 0;
    position: relative;
}}

.ois-header::after {{
    content: '';
    display: block;
    height: 6px;
    background: repeating-linear-gradient(
        90deg,
        var(--alert) 0px,
        var(--alert) 20px,
        var(--bg) 20px,
        var(--bg) 40px
    );
    position: absolute;
    bottom: -9px;
    left: 0;
    right: 0;
    opacity: 0.7;
}}

.ois-title {{
    font-family: 'Orbitron', monospace !important;
    font-size: 1.8rem !important;
    font-weight: 900 !important;
    color: var(--accent) !important;
    letter-spacing: 0.12em !important;
    text-shadow: 0 0 18px rgba(57,255,20,0.35) !important;
    margin: 0 !important;
    line-height: 1.1 !important;
}}

.ois-subtitle {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--brass) !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    margin-top: 4px !important;
}}

.ois-tagline {{
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.65rem !important;
    color: var(--text-dim) !important;
    letter-spacing: 0.1em !important;
    margin-top: 2px !important;
}}

/* ============================================================
   SIDEBAR — corrugated steel
   ============================================================ */
[data-testid="stSidebar"] {{
    background:
        repeating-linear-gradient(
            180deg,
            #0F140F 0px,
            #0F140F 3px,
            #111711 3px,
            #111711 6px
        ) !important;
    border-right: 2px solid var(--border) !important;
}}

[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {{
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--text) !important;
    font-size: 0.9rem !important;
}}

/* Sidebar section headers */
.sidebar-section-label {{
    font-family: 'Orbitron', monospace !important;
    font-size: 0.62rem !important;
    color: var(--brass) !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 4px !important;
    margin-bottom: 8px !important;
}}

/* Rivet dots on sidebar */
.sidebar-rivet {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #5A6A5A, #1E241E);
    border: 1px solid #3A4A3A;
    margin-right: 6px;
    vertical-align: middle;
}}

/* ============================================================
   PANELS — brushed metal gauge faces
   ============================================================ */
.ois-panel {{
    background: linear-gradient(145deg, #141A14, #0F140F);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 16px 18px;
    margin-bottom: 14px;
    position: relative;
    box-shadow:
        inset 0 1px 0 rgba(200,181,96,0.08),
        0 2px 8px rgba(0,0,0,0.5);
}}

/* Hex bolt corners */
.ois-panel::before {{
    content: '⬡';
    position: absolute;
    top: 6px;
    left: 8px;
    font-size: 0.6rem;
    color: var(--border);
    opacity: 0.6;
}}

.ois-panel::after {{
    content: '⬡';
    position: absolute;
    top: 6px;
    right: 8px;
    font-size: 0.6rem;
    color: var(--border);
    opacity: 0.6;
}}

/* Panel title */
.ois-panel-title {{
    font-family: 'Orbitron', monospace !important;
    font-size: 0.68rem !important;
    color: var(--brass) !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    margin-bottom: 12px !important;
    padding-bottom: 6px !important;
    border-bottom: 1px solid var(--grid) !important;
}}

/* Rust bleed accent — left edge on active panels */
.ois-panel-active {{
    border-left: 3px solid var(--alert) !important;
    box-shadow:
        inset 0 1px 0 rgba(200,181,96,0.08),
        -2px 0 12px rgba(212,67,26,0.12),
        0 2px 8px rgba(0,0,0,0.5);
}}

/* ============================================================
   GAUGE DISPLAY
   ============================================================ */
.gauge-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 16px 0;
}}

.gauge-cell {{
    background: linear-gradient(145deg, #141A14, #0F140F);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px 8px;
    text-align: center;
    position: relative;
}}

.gauge-label {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.62rem;
    color: var(--text-dim);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 4px;
}}

.gauge-value {{
    font-family: 'Orbitron', monospace;
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1;
}}

.gauge-value.green  {{ color: var(--accent); text-shadow: 0 0 10px rgba(57,255,20,0.4); }}
.gauge-value.brass  {{ color: var(--brass);  text-shadow: 0 0 10px rgba(200,181,96,0.3); }}
.gauge-value.alert  {{ color: var(--alert);  text-shadow: 0 0 10px rgba(212,67,26,0.4); }}
.gauge-value.dim    {{ color: var(--text-dim); }}

.gauge-unit {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.58rem;
    color: var(--text-dim);
    letter-spacing: 0.1em;
    margin-top: 2px;
}}

/* ============================================================
   AGENT FEED — live status panel
   ============================================================ */
.agent-feed {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    background: #080C08;
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 12px 14px;
    position: relative;
    overflow: hidden;
}}

/* Scanline effect */
.agent-feed::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(57,255,20,0.015) 2px,
        rgba(57,255,20,0.015) 4px
    );
    pointer-events: none;
}}

.agent-row {{
    display: flex;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid #0F140F;
}}

.agent-row:last-child {{ border-bottom: none; }}

.agent-status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 10px;
    flex-shrink: 0;
}}

.dot-complete {{ background: var(--accent); box-shadow: 0 0 6px var(--accent); }}
.dot-running  {{ background: var(--brass);  box-shadow: 0 0 6px var(--brass);
                 animation: pulse 1.2s ease-in-out infinite; }}
.dot-waiting  {{ background: var(--text-dim); }}
.dot-failed   {{ background: var(--alert);  box-shadow: 0 0 6px var(--alert); }}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.3; }}
}}

.agent-name {{
    color: var(--text);
    flex: 1;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
}}

.agent-badge {{
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 2px;
    letter-spacing: 0.1em;
    font-weight: 600;
}}

.badge-complete {{ background: rgba(57,255,20,0.12);  color: var(--accent); border: 1px solid var(--accent-dim); }}
.badge-running  {{ background: rgba(200,181,96,0.12); color: var(--brass);  border: 1px solid #5A4A20; }}
.badge-waiting  {{ background: transparent;           color: var(--text-dim); border: 1px solid var(--border); }}
.badge-failed   {{ background: rgba(212,67,26,0.15);  color: var(--alert);  border: 1px solid #7A2010; }}

.agent-elapsed {{
    font-size: 0.62rem;
    color: var(--text-dim);
    margin-left: 10px;
    min-width: 48px;
    text-align: right;
}}

/* ============================================================
   STREAMLIT WIDGET OVERRIDES
   ============================================================ */

/* Text inputs */
.stTextArea textarea,
.stTextInput input {{
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif !important;
    border-radius: 3px !important;
}}

.stTextArea textarea:focus,
.stTextInput input:focus {{
    border-color: var(--accent-dim) !important;
    box-shadow: 0 0 0 1px var(--accent-dim) !important;
}}

/* Selectbox */
.stSelectbox > div > div {{
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
    background: var(--bg-raised) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 3px !important;
}}

/* Primary button — RUN ANALYSIS */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #1A4010, #0F2A08) !important;
    border: 1px solid var(--accent-dim) !important;
    color: var(--accent) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 10px 28px !important;
    border-radius: 3px !important;
    box-shadow: 0 0 14px rgba(57,255,20,0.15) !important;
    transition: all 0.15s ease !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg, #22541A, #142E0A) !important;
    box-shadow: 0 0 24px rgba(57,255,20,0.3) !important;
    border-color: var(--accent) !important;
}}

/* Secondary buttons */
.stButton > button:not([kind="primary"]) {{
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-dim) !important;
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 0.08em !important;
    border-radius: 3px !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}}

.stTabs [data-baseweb="tab"] {{
    font-family: 'Orbitron', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.15em !important;
    color: var(--text-dim) !important;
    background: transparent !important;
    border: none !important;
    padding: 8px 16px !important;
}}

.stTabs [aria-selected="true"] {{
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}}

/* Expanders */
.streamlit-expanderHeader {{
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--text) !important;
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
}}

/* Metric values */
[data-testid="stMetricValue"] {{
    font-family: 'Orbitron', monospace !important;
    color: var(--accent) !important;
}}

/* Dividers */
hr {{
    border-color: var(--border) !important;
}}

/* Scrollbars */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text-dim); }}

/* ============================================================
   SUGGESTED QUESTION PILLS
   ============================================================ */
.question-pill {{
    display: inline-block;
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 6px 12px;
    margin: 4px 4px 4px 0;
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.82rem;
    color: var(--text);
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
}}

.question-pill:hover {{
    border-color: var(--brass);
    color: var(--brass);
}}

/* ============================================================
   FINDINGS LIST
   ============================================================ */
.finding-item {{
    display: flex;
    align-items: flex-start;
    padding: 6px 0;
    border-bottom: 1px solid var(--grid);
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.9rem;
    color: var(--text);
    line-height: 1.4;
}}

.finding-item:last-child {{ border-bottom: none; }}

.finding-bullet {{
    color: var(--accent);
    margin-right: 10px;
    flex-shrink: 0;
    font-size: 0.7rem;
    margin-top: 4px;
    font-family: 'Share Tech Mono', monospace;
}}

/* ============================================================
   RECOMMENDATION CARDS
   ============================================================ */
.rec-card {{
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-left: 3px solid var(--brass);
    border-radius: 3px;
    padding: 12px 16px;
    margin-bottom: 10px;
}}

.rec-rank {{
    font-family: 'Orbitron', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.15em;
    margin-bottom: 4px;
}}

.rec-action {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
}}

.rec-rationale {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.84rem;
    color: var(--text-dim);
    line-height: 1.4;
}}

.rec-badges {{
    display: flex;
    gap: 8px;
    margin-top: 8px;
}}

.priority-high    {{ color: var(--alert);  font-size: 0.65rem; letter-spacing: 0.1em; font-family: 'Share Tech Mono', monospace; }}
.priority-medium  {{ color: var(--brass);  font-size: 0.65rem; letter-spacing: 0.1em; font-family: 'Share Tech Mono', monospace; }}
.priority-low     {{ color: var(--text-dim); font-size: 0.65rem; letter-spacing: 0.1em; font-family: 'Share Tech Mono', monospace; }}
.timeframe-badge  {{ color: var(--text-dim); font-size: 0.65rem; letter-spacing: 0.1em; font-family: 'Share Tech Mono', monospace; }}

/* ============================================================
   STATUS BAR
   ============================================================ */
.status-bar {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-dim);
    letter-spacing: 0.08em;
    padding: 6px 0;
    border-top: 1px solid var(--grid);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.status-indicator {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}

.status-dot-online  {{ width: 6px; height: 6px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 4px var(--accent); display: inline-block; }}
.status-dot-offline {{ width: 6px; height: 6px; border-radius: 50%; background: var(--text-dim); display: inline-block; }}
</style>
"""


# ============================================================
# HTML component helpers — called from app.py
# ============================================================

def render_header() -> str:
    return """
<div class="ois-header">
    <div class="ois-title">⬡ OVERLAND INTELLIGENCE SYSTEM</div>
    <div class="ois-subtitle">High Desert Expeditions &nbsp;|&nbsp; Tucson, AZ</div>
    <div class="ois-tagline">Know the terrain before you move</div>
</div>
"""


def render_agent_feed(agent_statuses: list[dict]) -> str:
    """
    Renders the live agent feed panel.

    Args:
        agent_statuses: List of dicts with keys:
            - name:    str — display name
            - status:  'complete' | 'running' | 'waiting' | 'failed'
            - elapsed: str — elapsed time string e.g. '4.2s'

    Returns:
        HTML string for st.markdown(..., unsafe_allow_html=True)
    """
    rows = []
    for agent in agent_statuses:
        status  = agent.get("status", "waiting")
        name    = agent.get("name", "Agent")
        elapsed = agent.get("elapsed", "")

        dot_class   = f"dot-{status}"
        badge_class = f"badge-{status}"
        badge_text  = status.upper()

        rows.append(f"""
<div class="agent-row">
    <div class="agent-status-dot {dot_class}"></div>
    <div class="agent-name">{name}</div>
    <div class="agent-badge {badge_class}">{badge_text}</div>
    <div class="agent-elapsed">{elapsed}</div>
</div>""")

    return f"""
<div class="agent-feed">
{''.join(rows)}
</div>"""


def render_gauge_grid(
    data_health: int,
    market_signal: int,
    confidence: int,
    report_pct: int,
) -> str:
    """
    Renders the four instrument gauges as an HTML grid.
    Values are 0-100 integers.
    """
    def gauge(label, value, unit, color_class):
        return f"""
<div class="gauge-cell">
    <div class="gauge-label">{label}</div>
    <div class="gauge-value {color_class}">{value}</div>
    <div class="gauge-unit">{unit}</div>
</div>"""

    def color_for(v):
        if v >= 75: return "green"
        if v >= 40: return "brass"
        if v >  0:  return "alert"
        return "dim"

    return f"""
<div class="gauge-grid">
    {gauge("Data Health",       data_health, "/ 100",  color_for(data_health))}
    {gauge("Market Signal",     market_signal, "/ 100", color_for(market_signal))}
    {gauge("Insight Conf.",     confidence, "/ 100",   color_for(confidence))}
    {gauge("Report",            report_pct, "% DONE",  color_for(report_pct))}
</div>"""


def render_finding(text: str) -> str:
    return f"""
<div class="finding-item">
    <span class="finding-bullet">▶</span>
    <span>{text}</span>
</div>"""


def render_recommendation(rec: dict) -> str:
    rank      = rec.get("rank", "?")
    action    = rec.get("action", "")
    rationale = rec.get("rationale", "")
    priority  = rec.get("priority", "medium")
    timeframe = rec.get("timeframe", "short_term").replace("_", " ")

    return f"""
<div class="rec-card">
    <div class="rec-rank">REC #{rank:02d}</div>
    <div class="rec-action">{action}</div>
    <div class="rec-rationale">{rationale}</div>
    <div class="rec-badges">
        <span class="priority-{priority}">● {priority.upper()}</span>
        <span class="timeframe-badge">⧖ {timeframe.upper()}</span>
    </div>
</div>"""


def render_status_bar(llm_provider: str, search_provider: str, status: str) -> str:
    online = status not in ("", "starting")
    dot = "status-dot-online" if online else "status-dot-offline"
    return f"""
<div class="status-bar">
    <span class="status-indicator">
        <span class="{dot}"></span>
        {status.replace("_", " ").upper()}
    </span>
    <span>LLM: {llm_provider.upper()} &nbsp;|&nbsp; SEARCH: {search_provider.upper()}</span>
</div>"""