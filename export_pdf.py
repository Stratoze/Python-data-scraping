"""Export report.md / report_vi.md to PDF (report.pdf / report_vi.pdf).

Markdown -> HTML with markdown-it-py (CommonMark + tables) and Pygments code
highlighting, then HTML -> PDF with a headless Chrome / Edge already on the
machine. Run after `python main.py` so the PDFs match the latest reports:

    python export_pdf.py
"""
from __future__ import annotations

import html
import shutil
import subprocess
from pathlib import Path

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parent
REPORTS = {"report.md": ("report.pdf", "en"), "report_vi.md": ("report_vi.pdf", "vi"),
           "report_summary.md": ("report_summary.pdf", "en"),
           "report_summary_vi.md": ("report_summary_vi.pdf", "vi")}
BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 19pt; border-bottom: 2px solid #1f4e79; padding-bottom: 4px; color: #1f4e79; }
h2 { font-size: 15pt; color: #1f4e79; border-bottom: 1px solid #c8d3e0; padding-bottom: 2px;
     margin-top: 22px; break-after: avoid; }
h3 { font-size: 12.5pt; color: #2e5c8a; margin-top: 16px; break-after: avoid; }
h4 { font-size: 11pt; color: #2e5c8a; break-after: avoid; }
blockquote { margin: 8px 0; padding: 6px 12px; background: #f2f6fa; border-left: 4px solid #1f4e79; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9pt; }
th, td { border: 1px solid #b8c4d2; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #e3ebf4; }
tr { break-inside: avoid; }
img { max-width: 100%; display: block; margin: 10px auto; break-inside: avoid; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.8pt; background: #f3f3f3; padding: 0 2px; }
pre { font-family: Consolas, "Courier New", monospace; font-size: 7.8pt; line-height: 1.3; background: #f7f7f7;
      border: 1px solid #ddd; border-radius: 3px; padding: 6px 8px; white-space: pre-wrap; word-break: break-word; }
pre code { background: none; padding: 0; font-size: inherit; }
p { margin: 6px 0; }
"""


def _highlight(code: str, lang: str, _attrs) -> str:
    """Return a complete <pre> block so markdown-it does not wrap it a second time."""
    try:
        lexer = get_lexer_by_name(lang or "text")
    except ClassNotFound:
        return f"<pre><code>{html.escape(code)}</code></pre>"
    spans = highlight(code, lexer, HtmlFormatter(nowrap=True, noclasses=True, style="friendly"))
    return f"<pre><code>{spans}</code></pre>"


def md_to_html(md_text: str, lang: str, title: str) -> str:
    md = MarkdownIt("commonmark", {"highlight": _highlight, "html": False}).enable("table")
    body = md.render(md_text)
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}</body></html>")


def find_browser() -> Path:
    for b in BROWSERS:
        if b.exists():
            return b
    for name in ("chrome", "msedge", "chromium"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise RuntimeError("Chrome or Edge not found; install one to export PDF")


def html_to_pdf(html_path: Path, pdf_path: Path, browser: Path) -> None:
    subprocess.run([str(browser), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf-no-header", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                   check=True, capture_output=True, timeout=180)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"PDF was not written: {pdf_path}")


def main() -> None:
    browser = find_browser()
    for md_name, (pdf_name, lang) in REPORTS.items():
        md_path, pdf_path = ROOT / md_name, ROOT / pdf_name
        text = md_path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        # HTML lives next to the .md so relative `images/...` paths resolve.
        html_path = ROOT / f".{md_path.stem}.print.html"
        html_path.write_text(md_to_html(text, lang, title), encoding="utf-8")
        try:
            html_to_pdf(html_path, pdf_path, browser)
        finally:
            html_path.unlink(missing_ok=True)
        print(f"Wrote {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
