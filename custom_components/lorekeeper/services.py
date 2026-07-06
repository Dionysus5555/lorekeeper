from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN


LOOKUP_SCHEMA = vol.Schema(
    {
        vol.Required("query"): cv.string,
    }
)

SEARCH_SCHEMA = vol.Schema(
    {
        vol.Required("query"): cv.string,
    }
)

SUMMARY_SCHEMA = vol.Schema(
    {
        vol.Required("title"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Lorekeeper services."""

    async def lookup(call: ServiceCall) -> ServiceResponse:
        query = call.data["query"]

        return {
            "found": True,
            "provider": "test",
            "title": query,
            "summary": f"Lorekeeper is alive. You searched for: {query}",
            "url": None,
        }

    async def search(call: ServiceCall) -> ServiceResponse:
        query = call.data["query"]

        return {
            "found": True,
            "provider": "test",
            "query": query,
            "results": [
                {
                    "title": query,
                    "description": "Test search result from Lorekeeper.",
                }
            ],
        }

    async def summary(call: ServiceCall) -> ServiceResponse:
        title = call.data["title"]

        return {
            "found": True,
            "provider": "test",
            "title": title,
            "summary": f"Test summary for {title}.",
            "url": None,
        }

    hass.services.async_register(
        DOMAIN,
        "lookup",
        lookup,
        schema=LOOKUP_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        "search",
        search,
        schema=SEARCH_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        "summary",
        summary,
        schema=SUMMARY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
