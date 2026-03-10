"""
Phase 11 validation — ui/styles.py
Run with: pytest tests/test_styles.py -v
"""
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# -----------------------------------------------------------------------
# get_css
# -----------------------------------------------------------------------

def test_get_css_returns_string():
    from ui.styles import get_css
    assert isinstance(get_css(), str)

def test_get_css_contains_style_tag():
    from ui.styles import get_css
    css = get_css()
    assert "<style>" in css
    assert "</style>" in css

def test_get_css_contains_font_import():
    from ui.styles import get_css
    assert "Orbitron" in get_css()

def test_get_css_contains_palette_vars():
    from ui.styles import get_css
    css = get_css()
    for var in ("--bg", "--accent", "--brass", "--alert", "--text"):
        assert var in css, f"Missing CSS variable: {var}"

def test_get_css_contains_key_components():
    from ui.styles import get_css
    css = get_css()
    for selector in ("ois-header", "gauge-grid", "agent-feed", "rec-card", "sidebar"):
        assert selector in css, f"Missing component: {selector}"


# -----------------------------------------------------------------------
# render_header
# -----------------------------------------------------------------------

def test_render_header_returns_string():
    from ui.styles import render_header
    assert isinstance(render_header(), str)

def test_render_header_contains_title():
    from ui.styles import render_header
    html = render_header()
    assert "OVERLAND INTELLIGENCE" in html

def test_render_header_contains_tagline():
    from ui.styles import render_header
    assert "Know the terrain" in render_header()


# -----------------------------------------------------------------------
# render_agent_feed
# -----------------------------------------------------------------------

def test_render_agent_feed_returns_string():
    from ui.styles import render_agent_feed
    result = render_agent_feed([])
    assert isinstance(result, str)

def test_render_agent_feed_renders_all_statuses():
    from ui.styles import render_agent_feed
    agents = [
        {"name": "Data Analyst",  "status": "complete", "elapsed": "2.1s"},
        {"name": "Research",      "status": "running",  "elapsed": "4.8s"},
        {"name": "Insights",      "status": "waiting",  "elapsed": ""},
        {"name": "Report Writer", "status": "failed",   "elapsed": ""},
    ]
    html = render_agent_feed(agents)
    assert "dot-complete" in html
    assert "dot-running"  in html
    assert "dot-waiting"  in html
    assert "dot-failed"   in html

def test_render_agent_feed_shows_agent_names():
    from ui.styles import render_agent_feed
    agents = [{"name": "Data Analyst", "status": "complete", "elapsed": "1s"}]
    assert "Data Analyst" in render_agent_feed(agents)

def test_render_agent_feed_shows_elapsed():
    from ui.styles import render_agent_feed
    agents = [{"name": "X", "status": "running", "elapsed": "9.9s"}]
    assert "9.9s" in render_agent_feed(agents)


# -----------------------------------------------------------------------
# render_gauge_grid
# -----------------------------------------------------------------------

def test_render_gauge_grid_returns_string():
    from ui.styles import render_gauge_grid
    assert isinstance(render_gauge_grid(90, 75, 80, 100), str)

def test_render_gauge_grid_contains_values():
    from ui.styles import render_gauge_grid
    html = render_gauge_grid(88, 72, 65, 50)
    assert "88" in html
    assert "72" in html
    assert "65" in html
    assert "50" in html

def test_render_gauge_grid_high_values_get_green():
    from ui.styles import render_gauge_grid
    html = render_gauge_grid(90, 90, 90, 90)
    assert "green" in html

def test_render_gauge_grid_low_values_get_alert():
    from ui.styles import render_gauge_grid
    html = render_gauge_grid(20, 20, 20, 20)
    assert "alert" in html

def test_render_gauge_grid_zero_values_get_dim():
    from ui.styles import render_gauge_grid
    html = render_gauge_grid(0, 0, 0, 0)
    assert "dim" in html


# -----------------------------------------------------------------------
# render_finding
# -----------------------------------------------------------------------

def test_render_finding_returns_string():
    from ui.styles import render_finding
    assert isinstance(render_finding("Baja grew 64% YoY"), str)

def test_render_finding_contains_text():
    from ui.styles import render_finding
    assert "Baja grew 64% YoY" in render_finding("Baja grew 64% YoY")

def test_render_finding_contains_bullet():
    from ui.styles import render_finding
    assert "finding-bullet" in render_finding("test")


# -----------------------------------------------------------------------
# render_recommendation
# -----------------------------------------------------------------------

def test_render_recommendation_returns_string():
    from ui.styles import render_recommendation
    rec = {"rank": 1, "action": "Launch Baja line", "rationale": "64% growth",
           "priority": "high", "timeframe": "short_term"}
    assert isinstance(render_recommendation(rec), str)

def test_render_recommendation_contains_action():
    from ui.styles import render_recommendation
    rec = {"rank": 1, "action": "Launch Baja line", "rationale": "Strong signal",
           "priority": "high", "timeframe": "short_term"}
    assert "Launch Baja line" in render_recommendation(rec)

def test_render_recommendation_shows_priority():
    from ui.styles import render_recommendation
    rec = {"rank": 2, "action": "Expand SW", "rationale": "Top region",
           "priority": "medium", "timeframe": "long_term"}
    html = render_recommendation(rec)
    assert "MEDIUM" in html

def test_render_recommendation_formats_timeframe():
    from ui.styles import render_recommendation
    rec = {"rank": 1, "action": "X", "rationale": "Y",
           "priority": "high", "timeframe": "short_term"}
    assert "short term" in render_recommendation(rec).lower()


# -----------------------------------------------------------------------
# render_status_bar
# -----------------------------------------------------------------------

def test_render_status_bar_returns_string():
    from ui.styles import render_status_bar
    assert isinstance(render_status_bar("groq", "tavily", "insights_complete"), str)

def test_render_status_bar_shows_providers():
    from ui.styles import render_status_bar
    html = render_status_bar("groq", "duckduckgo", "complete")
    assert "GROQ" in html
    assert "DUCKDUCKGO" in html

def test_render_status_bar_online_dot_when_active():
    from ui.styles import render_status_bar
    html = render_status_bar("groq", "tavily", "insights_complete")
    assert "status-dot-online" in html

def test_render_status_bar_offline_dot_when_idle():
    from ui.styles import render_status_bar
    html = render_status_bar("groq", "tavily", "")
    assert "status-dot-offline" in html