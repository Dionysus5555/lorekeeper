from __future__ import annotations

import re
from html import unescape
from typing import Any

import aiohttp


class HomeAssistantDocsProvider:
    """Home Assistant documentation provider."""

    BASE_URL = "https://www.home-assistant.io"

    DOC_ROUTES = {
        "template sensor": "/integrations/template/",
        "template sensors": "/integrations/template/",
        "template": "/docs/configuration/templating/",
        "templating": "/docs/configuration/templating/",
        "automation": "/docs/automation/",
        "automations": "/docs/automation/",
        "script": "/docs/scripts/",
        "scripts": "/docs/scripts/",
        "scene": "/docs/scene/",
        "scenes": "/docs/scene/",
        "helper": "/docs/configuration/",
        "helpers": "/docs/configuration/",
        "rest sensor": "/integrations/rest/",
        "rest command": "/integrations/rest_command/",
        "mqtt": "/integrations/mqtt/",
        "sensor": "/integrations/sensor/",
        "binary sensor": "/integrations/binary_sensor/",
        "conversation": "/integrations/conversation/",
        "assist": "/voice_control/",
    }

    def __init__(
        self,
        session: aiohttp.ClientSession,
        user_agent: str = "Lorekeeper Home Assistant Integration",
    ) -> None:
        self.session = session
        self.user_agent = user_agent

    async def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Search known Home Assistant documentation routes."""
        text = query.lower()
        results = []

        for keyword, path in self.DOC_ROUTES.items():
            if keyword in text:
                results.append(
                    {
                        "title": self._title_from_path(path),
                        "description": f"Home Assistant documentation for {keyword}.",
                        "url": f"{self.BASE_URL}{path}",
                    }
                )

        if not results:
            results.append(
                {
                    "title": "Home Assistant Documentation",
                    "description": "General Home Assistant documentation.",
                    "url": f"{self.BASE_URL}/docs/",
                }
            )

        return {
            "found": bool(results),
            "provider": "home_assistant_docs",
            "query": query,
            "results": results[:limit],
        }

    async def lookup(self, query: str) -> dict[str, Any]:
        """Look up a Home Assistant documentation page."""
        route = self._select_route(query)

        if route is None:
            return {
                "found": False,
                "provider": "home_assistant_docs",
                "query": query,
                "title": None,
                "summary": None,
                "speech": None,
                "context": None,
                "url": None,
                "image": None,
                "error": "no_matching_doc_route",
            }

        return await self.summary(route, query=query)

    async def summary(
        self,
        title: str,
        query: str | None = None,
    ) -> dict[str, Any]:
        """Return a summary for a known Home Assistant docs route."""
        route = title if title.startswith("/") else self._select_route(title)

        if route is None:
            return {
                "found": False,
                "provider": "home_assistant_docs",
                "query": query,
                "title": title,
                "summary": None,
                "speech": None,
                "context": None,
                "url": None,
                "image": None,
                "error": "no_matching_doc_route",
            }

        url = f"{self.BASE_URL}{route}"
        html = await self._get_text(url)

        page_title = self._extract_title(html) or self._title_from_path(route)
        summary = self._extract_summary(html)

        if not summary:
            return {
                "found": False,
                "provider": "home_assistant_docs",
                "query": query,
                "title": page_title,
                "summary": None,
                "speech": None,
                "context": None,
                "url": url,
                "image": None,
                "error": "no_summary_found",
            }

        speech = self._make_speech(page_title, summary)
        context = f"Source: Home Assistant documentation. {page_title}: {summary}"

        return {
            "found": True,
            "provider": "home_assistant_docs",
            "query": query,
            "title": page_title,
            "summary": summary,
            "speech": speech,
            "context": context,
            "url": url,
            "image": None,
        }

    def _select_route(self, query: str) -> str | None:
        """Select a docs route from the query."""
        text = query.lower().strip()

        for keyword, route in self.DOC_ROUTES.items():
            if keyword in text:
                return route

        return "/docs/"

    def _extract_title(self, html: str) -> str | None:
        """Extract page title."""
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        title = self._clean_html(match.group(1))
        return title.replace(" - Home Assistant", "").strip()

    def _extract_summary(self, html: str) -> str | None:
        """Extract a simple docs summary from page HTML."""
        meta = re.search(
            r'<meta\s+name="description"\s+content="(.*?)"',
            html,
            re.IGNORECASE | re.DOTALL,
        )

        if meta:
            return self._clean_html(meta.group(1))

        paragraphs = re.findall(
            r"<p>(.*?)</p>",
            html,
            re.IGNORECASE | re.DOTALL,
        )

        cleaned = []

        for paragraph in paragraphs:
            text = self._clean_html(paragraph)

            if len(text) > 60:
                cleaned.append(text)

            if len(cleaned) >= 2:
                break

        if not cleaned:
            return None

        return " ".join(cleaned)

    def _make_speech(self, title: str, summary: str) -> str:
        """Create a short Gaia-friendly response."""
        first_sentence = summary.split(". ")[0].strip()

        if first_sentence and not first_sentence.endswith("."):
            first_sentence += "."

        if len(first_sentence) > 260:
            first_sentence = first_sentence[:257].rsplit(" ", 1)[0] + "..."

        return first_sentence

    def _clean_html(self, value: str) -> str:
        """Clean basic HTML into readable text."""
        value = re.sub(r"<script.*?</script>", "", value, flags=re.DOTALL | re.IGNORECASE)
        value = re.sub(r"<style.*?</style>", "", value, flags=re.DOTALL | re.IGNORECASE)
        value = re.sub(r"<.*?>", "", value)
        value = unescape(value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _title_from_path(self, path: str) -> str:
        """Create a title from a docs path."""
        cleaned = path.strip("/").split("/")[-1]
        return cleaned.replace("-", " ").replace("_", " ").title()

    async def _get_text(self, url: str) -> str:
        """Fetch text from a URL."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html",
        }

        async with self.session.get(
            url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            response.raise_for_status()
            return await response.text()
