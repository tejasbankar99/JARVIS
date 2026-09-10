"""
research.py — JARVIS Research & Knowledge Module
=================================================
Handles all web-based intelligence gathering:
  - DuckDuckGo web search with result summarization
  - Webpage reading and AI summarization
  - PDF and text file reading and summarization
"""

import re
import requests
from pathlib import Path
from urllib.parse import urlencode, quote_plus


# ── Web Search ────────────────────────────────────────────────────────────────

def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo's HTML interface and return a summarized answer.

    Args:
        query:       Search query string
        max_results: Maximum number of results to include in summary

    Returns:
        Formatted string with search results + AI summary
    """
    try:
        # DuckDuckGo HTML scraping (no API key needed)
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36")
        }
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse results
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result in soup.select(".result__body")[:max_results]:
            title_tag = result.select_one(".result__title")
            snippet_tag = result.select_one(".result__snippet")
            url_tag = result.select_one(".result__url")

            title = title_tag.get_text(strip=True) if title_tag else "No title"
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
            link = url_tag.get_text(strip=True) if url_tag else ""

            if snippet:
                results.append(f"**{title}**\n{snippet}\n({link})")

        if not results:
            return f"No results found for '{query}', sir."

        raw_results = "\n\n".join(results)

        # Use Claude to summarize
        from brain import ask_with_context
        summary = ask_with_context(
            f"Summarize these search results for the query: '{query}'. "
            f"Give a clear, direct answer based on the information. Be concise.",
            raw_results
        )
        return f"🔍 **Search: {query}**\n\n{summary}"

    except Exception as e:
        return f"Web search encountered an issue: {e}"


# ── Webpage Reader ─────────────────────────────────────────────────────────────

def read_and_summarize_url(url: str, instruction: str = None) -> str:
    """
    Fetch and summarize the content of a webpage.

    Args:
        url:         The webpage URL to read
        instruction: Optional specific question or instruction for the summary

    Returns:
        AI-generated summary of the page content
    """
    try:
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "iframe", "aside", "form", "button"]):
            tag.decompose()

        # Extract main text
        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text[:10000]  # Limit to 10k chars for Claude

        if not text.strip():
            return "The page appears to have no readable content, sir."

        from brain import ask_with_context
        prompt = instruction or "Summarize this webpage content clearly and concisely."
        summary = ask_with_context(prompt, f"URL: {url}\n\nContent:\n{text}")
        return f"📄 **Summary of {url}**\n\n{summary}"

    except requests.exceptions.ConnectionError:
        return f"I couldn't connect to {url}, sir. Please check your internet connection."
    except requests.exceptions.Timeout:
        return f"The request to {url} timed out, sir."
    except Exception as e:
        return f"Error reading {url}: {e}"


# ── PDF / Text File Reader ─────────────────────────────────────────────────────

def read_and_summarize_file(filepath: str, instruction: str = None) -> str:
    """
    Read and summarize a PDF or text file.

    Args:
        filepath:    Path to the file (PDF, TXT, MD, PY, etc.)
        instruction: Optional specific question about the file content

    Returns:
        AI-generated summary or answer
    """
    path = Path(filepath)

    if not path.exists():
        return f"I can't find the file at '{filepath}', sir. Please check the path."

    extension = path.suffix.lower()

    # ── PDF ──────────────────────────────────────────────────────────────────
    if extension == ".pdf":
        text = _read_pdf(path)
    # ── Text-based files ─────────────────────────────────────────────────────
    elif extension in {".txt", ".md", ".py", ".js", ".ts", ".json",
                       ".html", ".css", ".csv", ".log", ".yaml", ".yml"}:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"Could not read '{filepath}': {e}"
    else:
        return (f"I don't know how to read '{extension}' files, sir. "
                f"Supported: PDF, TXT, MD, PY, JS, JSON, HTML, CSV.")

    if not text.strip():
        return "The file appears to be empty, sir."

    # Truncate for Claude's context window
    text = text[:12000]

    from brain import ask_with_context
    prompt = instruction or f"Summarize the content of the file '{path.name}' clearly."
    summary = ask_with_context(prompt, f"File: {path.name}\n\nContent:\n{text}")
    return f"📂 **{path.name}**\n\n{summary}"


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF file using PyPDF2 or pdfplumber."""
    # Try pdfplumber first (better text extraction)
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages[:30]:  # Max 30 pages
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
        return "\n\n".join(text_parts)
    except ImportError:
        pass

    # Fallback to PyPDF2
    try:
        import PyPDF2
        text_parts = []
        with open(str(path), "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:30]:
                text_parts.append(page.extract_text() or "")
        return "\n\n".join(text_parts)
    except ImportError:
        return "[PDF reading requires pdfplumber or PyPDF2. Run: pip install pdfplumber]"
    except Exception as e:
        return f"[PDF read error: {e}]"


# ── Quick Fact Lookup ─────────────────────────────────────────────────────────

def quick_search(query: str) -> str:
    """
    Attempt DuckDuckGo instant answers API for quick facts.

    Args:
        query: Search query

    Returns:
        Instant answer or falls back to full web search
    """
    try:
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"
        resp = requests.get(url, timeout=8)
        data = resp.json()

        answer = data.get("Answer") or data.get("AbstractText") or ""
        if answer:
            return f"💡 {answer}"

        # No instant answer — fall back to full search
        return search_web(query)

    except Exception:
        return search_web(query)
