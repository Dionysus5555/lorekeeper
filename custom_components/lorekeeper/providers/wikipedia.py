from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WikipediaProvider:
    """Wikipedia knowledge provider."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        language: str = "en",
        user_agent: str = "Lorekeeper Home Assistant Integration",
    ) -> None:
        self.session = session
        self.language = language
        self.user_agent = user_agent

    @property
    def api_base(self) -> str:
        return f"https://{self.language}.wikipedia.org"

    def _make_speech(
        self,
        title: str,
        summary: str | None,
        description: str | None = None,
    ) -> str | None:
        """Create a short Gaia-friendly speech response."""
        if not summary:
            return None

        first_sentence = summary.split(". ")[0].strip()

        if first_sentence and not first_sentence.endswith("."):
            first_sentence += "."

        if len(first_sentence) > 240:
            first_sentence = first_sentence[:237].rsplit(" ", 1)[0] + "..."

        return first_sentence

    async def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Search Wikipedia for matching page titles."""
        url = f"{self.api_base}/w/api.php"

        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "namespace": 0,
            "format": "json",
            "redirects": "resolve",
        }

        data = await self._get_json(url, params=params)

        titles = data[1] if len(data) > 1 else []
        descriptions = data[2] if len(data) > 2 else []
        urls = data[3] if len(data) > 3 else []

        results = []

        for index, title in enumerate(titles):
            results.append(
                {
                    "title": title,
                    "description": descriptions[index] if index < len(descriptions) else "",
                    "url": urls[index] if index < len(urls) else None,
                }
            )

        return {
            "found": len(results) > 0,
            "provider": "wikipedia",
            "query": query,
            "results": results,
        }

    async def summary(self, title: str) -> dict[str, Any]:
        """Get a Wikipedia page summary by exact title."""
        safe_title = quote(title.replace(" ", "_"), safe="")
        url = f"{self.api_base}/api/rest_v1/page/summary/{safe_title}"

        try:
            data = await self._get_json(url)
        except aiohttp.ClientResponseError as err:
            if err.status == 404:
                return {
                    "found": False,
                    "provider": "wikipedia",
                    "title": title,
                    "summary": None,
                    "speech": None,
                    "context": None,
                    "url": None,
                    "image": None,
                    "error": "not_found",
                }

            raise

        page_url = data.get("content_urls", {}).get("desktop", {}).get("page")

        image = None
        if data.get("thumbnail"):
            image = data["thumbnail"].get("source")
        elif data.get("originalimage"):
            image = data["originalimage"].get("source")

        page_title = data.get("title", title)
        summary_text = data.get("extract")
        description = data.get("description")
        speech = self._make_speech(page_title, summary_text, description)

        context = None
        if summary_text:
            context = f"Source: Wikipedia. {page_title}: {summary_text}"

        return {
            "found": bool(summary_text),
            "provider": "wikipedia",
            "title": page_title,
            "summary": summary_text,
            "speech": speech,
            "context": context,
            "description": description,
            "url": page_url,
            "image": image,
        }

    async def lookup(self, query: str) -> dict[str, Any]:
        """Search Wikipedia, then return the best page summary."""
        search_result = await self.search(query, limit=1)

        if not search_result["found"]:
            return {
                "found": False,
                "provider": "wikipedia",
                "query": query,
                "title": None,
                "summary": None,
                "speech": None,
                "context": None,
                "url": None,
                "image": None,
                "error": "no_results",
            }

        best_title = search_result["results"][0]["title"]
        result = await self.summary(best_title)
        result["query"] = query

        return result

    async def _get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        async with self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            response.raise_for_status()
            return await response.json()
