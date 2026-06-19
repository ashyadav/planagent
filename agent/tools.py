from __future__ import annotations

import os

from langchain_community.utilities import SearxSearchWrapper
from langchain_core.tools import tool


def _get_searx() -> SearxSearchWrapper:
    return SearxSearchWrapper(searx_host=os.environ["SEARXNG_URL"])


@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    return _get_searx().run(query)


tools = [web_search]
