"""
Report generation service.
Renders Jinja2 HTML templates and converts to PDF via WeasyPrint.
"""
import asyncio
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "frontend" / "templates" / "reports"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

# Custom filters
def _timestamp_to_str(ts) -> str:
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"

_jinja_env.filters["timestamp_to_str"] = _timestamp_to_str


def _render_html(template_name: str, context: dict) -> str:
    context.setdefault("generated_at", datetime.now().strftime("%d/%m/%Y %H:%M"))
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(**context)


def _html_to_pdf(html: str) -> bytes:
    return HTML(string=html).write_pdf()


async def generate_pdf(template_name: str, context: dict) -> bytes:
    """Render template and convert to PDF in a thread pool (WeasyPrint is sync)."""
    html = _render_html(template_name, context)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _html_to_pdf, html)
