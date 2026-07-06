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

    async def search(
        self,
        query: str,
        provider: str = "wikipedia",
    ) -> dict[str, Any]:
        """Search a knowledge provider."""
        if provider != "wikipedia":
            return {
                "found": False,
                "provider": provider,
                "query": query,
                "results": [],
                "error": "unsupported_provider",
            }

        wikipedia = self._get_wikipedia_provider()
        return await wikipedia.search(query)

    async def summary(
        self,
        title: str,
        provider: str = "wikipedia",
    ) -> dict[str, Any]:
        """Get a summary from a knowledge provider."""
        if provider != "wikipedia":
            return {
                "found": False,
                "provider": provider,
                "title": title,
                "summary": None,
                "url": None,
                "image": None,
                "error": "unsupported_provider",
            }

        wikipedia = self._get_wikipedia_provider()
        return await wikipedia.summary(title)

    async def lookup(
        self,
        query: str,
        provider: str = "wikipedia",
    ) -> dict[str, Any]:
        """Look up a topic using a knowledge provider."""
        if provider != "wikipedia":
            return {
                "found": False,
                "provider": provider,
                "query": query,
                "title": None,
                "summary": None,
                "url": None,
                "image": None,
                "error": "unsupported_provider",
            }

        wikipedia = self._get_wikipedia_provider()
        return await wikipedia.lookup(query)
