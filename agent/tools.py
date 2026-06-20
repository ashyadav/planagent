from __future__ import annotations

import os

import httpx
from langchain_community.utilities import SearxSearchWrapper
from langchain_core.tools import tool


def _get_searx() -> SearxSearchWrapper:
    return SearxSearchWrapper(searx_host=os.environ["SEARXNG_URL"])


@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    return _get_searx().run(query)


@tool
def http_fetch(url: str) -> str:
    """Fetch the content of a URL and return it as text. Use for APIs that return JSON."""
    response = httpx.get(url, timeout=10, follow_redirects=True)
    response.raise_for_status()
    return response.text[:8000]  # ponytail: cap at 8k; raise if large payloads needed


tools = [web_search, http_fetch]
