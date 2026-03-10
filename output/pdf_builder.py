import base64
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def build_pdf(
    report_markdown: str,
    charts: dict[str, str],
    output_path: str = None,
) -> str:
    """
    Converts the Markdown report and base64 charts into a styled PDF.

    Args:
        report_markdown: Full Markdown report string from report_agent.
        charts:          Dict of chart_name -> base64 PNG string from chart_tools.
        output_path:     Optional file path to save the PDF.
                         Defaults to output/reports/report_YYYYMMDD_HHMMSS.pdf

    Returns:
        Path to the saved PDF file.

    Raises:
        RuntimeError: If WeasyPrint fails to generate the PDF.
    """
    from weasyprint import HTML, CSS

    html_body = _markdown_to_html(report_markdown)
    charts_html = _build_charts_html(charts)
    full_html = _build_full_html(html_body, charts_html)

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(__file__).resolve().parent.parent / "output" / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"report_{timestamp}.pdf")

    try:
        HTML(string=full_html).write_pdf(output_path)
    except Exception as e:
        raise RuntimeError(f"PDF generation failed: {str(e)}")

    return output_path


def _markdown_to_html(markdown: str) -> str:
    """
    Converts a subset of Markdown to HTML.
    Handles: h1-h3, bold, bullet lists, horizontal rules, paragraphs.
    Keeps the implementation dependency-free (no markdown library needed).
    """
    lines = markdown.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{_inline(stripped[2:])}</h1>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline(stripped[2:])}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            text = re.sub(r"^\d+\.\s+", "", stripped)
            html_lines.append(f"<p class='numbered'>{_inline(text)}</p>")
        elif stripped == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
        elif stripped == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _inline(text: str) -> str:
    """Converts inline Markdown (bold, italic, code) to HTML."""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def _build_charts_html(charts: dict[str, str]) -> str:
    """Embeds base64 chart images into an HTML section."""
    if not charts:
        return ""

    parts = ["<div class='charts-section'><h2>Supporting Charts</h2>"]
    chart_titles = {
        "revenue_by_year":           "Revenue by Year",
        "revenue_by_build_category": "Revenue by Build Category",
        "baja_growth_trend":         "Baja vs Other Builds — Growth Trend",
        "revenue_by_region":         "Revenue by Region",
    }

    for key, b64 in charts.items():
        if not b64:
            continue
        title = chart_titles.get(key, key.replace("_", " ").title())
        parts.append(
            f"<div class='chart'>"
            f"<h3>{title}</h3>"
            f"<img src='data:image/png;base64,{b64}' alt='{title}' />"
            f"</div>"
        )

    parts.append("</div>")
    return "\n".join(parts)


def _build_full_html(body: str, charts: str) -> str:
    """Wraps HTML body and charts in a complete styled HTML document."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: letter;
    margin: 1.2in 1in 1in 1in;
    @bottom-right {{
      content: "Page " counter(page) " of " counter(pages);
      font-size: 9pt;
      color: #888;
    }}
  }}
  body {{
    font-family: 'Georgia', serif;
    font-size: 11pt;
    color: #1a1a1a;
    line-height: 1.6;
  }}
  h1 {{
    font-size: 18pt;
    color: #1a1a1a;
    border-bottom: 2px solid #C8B560;
    padding-bottom: 6px;
    margin-top: 0;
  }}
  h2 {{
    font-size: 13pt;
    color: #2c2c2c;
    border-left: 4px solid #D4431A;
    padding-left: 10px;
    margin-top: 24px;
  }}
  h3 {{
    font-size: 11pt;
    color: #3a3a3a;
    margin-top: 14px;
  }}
  ul {{
    margin: 8px 0 12px 0;
    padding-left: 20px;
  }}
  li {{
    margin-bottom: 4px;
  }}
  p.numbered {{
    margin: 6px 0 6px 16px;
  }}
  hr {{
    border: none;
    border-top: 1px solid #ccc;
    margin: 24px 0;
  }}
  em {{
    font-style: italic;
    color: #555;
    font-size: 9pt;
  }}
  code {{
    font-family: monospace;
    background: #f4f4f4;
    padding: 1px 4px;
    border-radius: 2px;
    font-size: 10pt;
  }}
  .charts-section {{
    margin-top: 32px;
    page-break-before: always;
  }}
  .chart {{
    margin-bottom: 28px;
    page-break-inside: avoid;
  }}
  .chart img {{
    width: 100%;
    max-width: 540pt;
  }}
  .chart h3 {{
    font-size: 10pt;
    color: #555;
    margin-bottom: 6px;
  }}
</style>
</head>
<body>
{body}
{charts}
</body>
</html>"""