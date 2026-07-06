from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_LANGUAGE,
    CONF_USER_AGENT,
    DEFAULT_LANGUAGE,
    DEFAULT_USER_AGENT,
    DOMAIN,
)


class LorekeeperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lorekeeper."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id("lorekeeper")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Lorekeeper",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): str,
                vol.Optional(CONF_USER_AGENT, default=DEFAULT_USER_AGENT): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
