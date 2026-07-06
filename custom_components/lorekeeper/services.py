from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_LANGUAGE,
    CONF_USER_AGENT,
    DEFAULT_LANGUAGE,
    DEFAULT_USER_AGENT,
    DOMAIN,
)
from .providers.wikipedia import WikipediaProvider

_LOGGER = logging.getLogger(__name__)


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


def _get_config(hass: HomeAssistant) -> dict:
    """Get the first Lorekeeper config entry data."""
    entries = hass.data.get(DOMAIN, {})

    if not entries:
        return {}

    return next(iter(entries.values()))


def _get_provider(hass: HomeAssistant) -> WikipediaProvider:
    """Create the Wikipedia provider."""
    config = _get_config(hass)

    language = config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    user_agent = config.get(CONF_USER_AGENT, DEFAULT_USER_AGENT)

    session = async_get_clientsession(hass)

    return WikipediaProvider(
        session=session,
        language=language,
        user_agent=user_agent,
    )


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Lorekeeper services."""

    async def lookup(call: ServiceCall) -> ServiceResponse:
        query = call.data["query"]
        provider = _get_provider(hass)

        try:
            return await provider.lookup(query)
        except Exception as err:
            _LOGGER.exception("Lorekeeper lookup failed")

            return {
                "found": False,
                "provider": "wikipedia",
                "query": query,
                "title": None,
                "summary": None,
                "url": None,
                "image": None,
                "error": str(err),
            }

    async def search(call: ServiceCall) -> ServiceResponse:
        query = call.data["query"]
        provider = _get_provider(hass)

        try:
            return await provider.search(query)
        except Exception as err:
            _LOGGER.exception("Lorekeeper search failed")

            return {
                "found": False,
                "provider": "wikipedia",
                "query": query,
                "results": [],
                "error": str(err),
            }

    async def summary(call: ServiceCall) -> ServiceResponse:
        title = call.data["title"]
        provider = _get_provider(hass)

        try:
            return await provider.summary(title)
        except Exception as err:
            _LOGGER.exception("Lorekeeper summary failed")

            return {
                "found": False,
                "provider": "wikipedia",
                "title": title,
                "summary": None,
                "url": None,
                "image": None,
                "error": str(err),
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
