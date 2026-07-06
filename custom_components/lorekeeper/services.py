from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .providers.manager import ProviderManager

_LOGGER = logging.getLogger(__name__)


LOOKUP_SCHEMA = vol.Schema(
    {
        vol.Required("query"): cv.string,
        vol.Optional("provider"): cv.string,
    }
)

SEARCH_SCHEMA = vol.Schema(
    {
        vol.Required("query"): cv.string,
        vol.Optional("provider"): cv.string,
    }
)

SUMMARY_SCHEMA = vol.Schema(
    {
        vol.Required("title"): cv.string,
        vol.Optional("provider"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register Lorekeeper services."""

    manager = ProviderManager(hass)

    async def lookup(call: ServiceCall) -> ServiceResponse:
        """Lookup a topic."""
        query = call.data["query"]
        provider = call.data.get("provider")

        try:
            return await manager.lookup(
                query=query,
                provider=provider,
            )
        except Exception as err:
            _LOGGER.exception("Lorekeeper lookup failed")

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
                "error": str(err),
            }

    async def search(call: ServiceCall) -> ServiceResponse:
        """Search Lorekeeper."""
        query = call.data["query"]
        provider = call.data.get("provider")

        try:
            return await manager.search(
                query=query,
                provider=provider,
            )
        except Exception as err:
            _LOGGER.exception("Lorekeeper search failed")

            return {
                "found": False,
                "provider": provider,
                "query": query,
                "results": [],
                "error": str(err),
            }

    async def summary(call: ServiceCall) -> ServiceResponse:
        """Return a summary."""
        title = call.data["title"]
        provider = call.data.get("provider")

        try:
            return await manager.summary(
                title=title,
                provider=provider,
            )
        except Exception as err:
            _LOGGER.exception("Lorekeeper summary failed")

            return {
                "found": False,
                "provider": provider,
                "title": title,
                "summary": None,
                "speech": None,
                "context": None,
                "url": None,
                "image": None,
                "error": str(err),
            }

    if not hass.services.has_service(DOMAIN, "lookup"):
        hass.services.async_register(
            DOMAIN,
            "lookup",
            lookup,
            schema=LOOKUP_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, "search"):
        hass.services.async_register(
            DOMAIN,
            "search",
            search,
            schema=SEARCH_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    if not hass.services.has_service(DOMAIN, "summary"):
        hass.services.async_register(
            DOMAIN,
            "summary",
            summary,
            schema=SUMMARY_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )
