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
from .github import GitHubProvider
from .home_assistant_docs import HomeAssistantDocsProvider
from .wikipedia import WikipediaProvider


class ProviderManager:
    """Manage Lorekeeper knowledge providers."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.providers = self._create_providers()

    def _get_config(self) -> dict[str, Any]:
        """Get the first Lorekeeper config entry data."""
        entries = self.hass.data.get(DOMAIN, {})

        if not entries:
            return {}

        return next(iter(entries.values()))

    def _create_providers(self) -> dict[str, Any]:
        """Create available providers."""
        config = self._get_config()

        language = config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        user_agent = config.get(CONF_USER_AGENT, DEFAULT_USER_AGENT)
        session = async_get_clientsession(self.hass)

        return {
            "wikipedia": WikipediaProvider(
                session=session,
                language=language,
                user_agent=user_agent,
            ),
            "home_assistant_docs": HomeAssistantDocsProvider(
                session=session,
                user_agent=user_agent,
            ),
            "github": GitHubProvider(
                session=session,
                user_agent=user_agent,
            ),
        }

    def _select_provider(self, query: str) -> str:
        """Select the best provider for a query."""
        text = query.lower().strip()

        if any(term in text for term in ("home assistant", "hass", "ha docs")):
            return "home_assistant_docs"

        if any(term in text for term in ("github", "repo", "repository", "release notes", "issues", "pull request", "readme")):
            return "github"

        if any(term in text for term in ("chord", "chords", "lyrics", "song sheet")):
            return "chords"

        if any(term in text for term in ("recipe", "recipes", "cook", "cooking")):
            return "recipes"

        return "wikipedia"

    def _get_provider(self, provider: str) -> Any | None:
        """Get a provider by name."""
        return self.providers.get(provider)

    def _unsupported_lookup_response(
        self,
        provider: str,
        query: str,
    ) -> dict[str, Any]:
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
        selected = self._get_provider(selected_provider)

        if selected is None:
            return self._unsupported_search_response(selected_provider, query)

        return await selected.search(query)

    async def summary(
        self,
        title: str,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Get a summary from a knowledge provider."""
        selected_provider = provider or self._select_provider(title)
        selected = self._get_provider(selected_provider)

        if selected is None:
            return self._unsupported_summary_response(selected_provider, title)

        return await selected.summary(title)

    async def lookup(
        self,
        query: str,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Look up a topic using the best available provider."""
        selected_provider = provider or self._select_provider(query)
        selected = self._get_provider(selected_provider)

        if selected is None:
            return self._unsupported_lookup_response(selected_provider, query)

        return await selected.lookup(query)
