from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..const import (
    CONF_LANGUAGE,
    CONF_USER_AGENT,
    DEFAULT_LANGUAGE,
    DEFAULT_USER_AGENT,
    DOMAIN,
)
from .wikipedia import WikipediaProvider


class ProviderManager:
    """Manage Lorekeeper knowledge providers."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    def _get_config(self) -> dict[str, Any]:
        """Get the first Lorekeeper config entry data."""
        entries = self.hass.data.get(DOMAIN, {})

        if not entries:
            return {}

        return next(iter(entries.values()))

    def _get_wikipedia_provider(self) -> WikipediaProvider:
        """Create a Wikipedia provider."""
        config = self._get_config()

        language = config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        user_agent = config.get(CONF_USER_AGENT, DEFAULT_USER_AGENT)

        session = async_get_clientsession(self.hass)

        return WikipediaProvider(
            session=session,
            language=language,
            user_agent=user_agent,
        )

    def _select_provider(self, query: str) -> str:
        """Select the best provider for a query.

        This is deliberately simple for now. As providers are added,
        this becomes Lorekeeper's routing brain.
        """
        text = query.lower().strip()

        # Future provider hooks.
        if any(term in text for term in ("home assistant", "hass", "ha docs")):
            return "home_assistant_docs"

        if any(term in text for term in ("chord", "chords", "lyrics", "song sheet")):
            return "chords"

        if any(term in text for term in ("recipe", "recipes", "cook", "cooking")):
            return "recipes"

        # Default fallback.
        return "wikipedia"

    def _unsupported_lookup_response(
        self,
        provider: str,
        query: str,
    ) -> dict[str, Any]:
        """Return a standard unsupported-provider lookup response."""
        return {
            "found": False,
            "provider": provider,
            "query": query,
            "title": None,
            "summary": None,
            "speech": None,
            "context": None,
            "url": None,
            "image": None,
            "error": "unsupported_provider",
        }

    def _unsupported_search_response(
        self,
        provider: str,
        query: str,
    ) -> dict[str, Any]:
        """Return a standard unsupported-provider search response."""
        return {
            "found": False,
            "provider": provider,
            "query": query,
            "results": [],
            "error": "unsupported_provider",
        }

    def _unsupported_summary_response(
        self,
        provider: str,
        title: str,
    ) -> dict[str, Any]:
        """Return a standard unsupported-provider summary response."""
        return {
            "found": False,
            "provider": provider,
            "title": title,
            "summary": None,
            "speech": None,
            "context": None,
            "url": None,
            "image": None,
            "error": "unsupported_provider",
        }

    async def search(
        self,
        query: str,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Search a knowledge provider."""
        selected_provider = provider or self._select_provider(query)

        if selected_provider == "wikipedia":
            wikipedia = self._get_wikipedia_provider()
            return await wikipedia.search(query)

        return self._unsupported_search_response(selected_provider, query)

    async def summary(
        self,
        title: str,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Get a summary from a knowledge provider."""
        selected_provider = provider or self._select_provider(title)

        if selected_provider == "wikipedia":
            wikipedia = self._get_wikipedia_provider()
            return await wikipedia.summary(title)

        return self._unsupported_summary_response(selected_provider, title)

    async def lookup(
        self,
        query: str,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Look up a topic using the best available knowledge provider."""
        selected_provider = provider or self._select_provider(query)

        if selected_provider == "wikipedia":
            wikipedia = self._get_wikipedia_provider()
            return await wikipedia.lookup(query)

        return self._unsupported_lookup_response(selected_provider, query)
