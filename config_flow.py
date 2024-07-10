import logging
import os
import json
import aiofiles
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_TV_IDS, CONF_DAYS, DOMAIN
from .sensor import async_reload_sensors

_LOGGER = logging.getLogger(__name__)

class EPGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EPG sensor."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._data: dict[str, str] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EPGOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        # Load TV station data from JSON file asynchronously
        data_file = os.path.join(os.path.dirname(__file__), "default_channels.json")
        async with aiofiles.open(data_file, "r") as f:
            tv_data = await f.read()
        tv_data = json.loads(tv_data)

        tv_ids = {tv["id"]: tv["name"] for tv in tv_data}

        if user_input is not None:
            # Validate user input
            selected_tv_ids = user_input.get(CONF_TV_IDS, [])
            days = user_input.get(CONF_DAYS, 3)

            _LOGGER.debug(f"User Input: {user_input}")

            # Create or update entry with both data and options
            self._data = {
                CONF_TV_IDS: selected_tv_ids,
                CONF_DAYS: days,
            }

            return self.async_create_entry(title="EPG Sensor", data=self._data)

        # If no user input, initialize with default or saved values
        current_entry = self._async_current_entries()
        saved_data = current_entry[0].data if current_entry else {}

        _LOGGER.debug(f"Saved Data: {saved_data}")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TV_IDS, default=saved_data.get(CONF_TV_IDS, [])): cv.multi_select(tv_ids),
                vol.Required(CONF_DAYS, default=saved_data.get(CONF_DAYS, 7)): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
            }),
            errors=errors,
        )

class EPGOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for the EPG sensor."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle options flow initialization."""
        if user_input is not None:
            # Update entry with new options
            self.hass.config_entries.async_update_entry(self.config_entry, options=user_input)
            await async_reload_sensors(self.hass, self.config_entry)
            return self.async_create_entry(title="", data=user_input)

        # Load TV station data from JSON file asynchronously
        data_file = os.path.join(os.path.dirname(__file__), "default_channels.json")
        async with aiofiles.open(data_file, "r") as f:
            tv_data = await f.read()
        tv_data = json.loads(tv_data)

        tv_ids = {tv["id"]: tv["name"] for tv in tv_data}

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_TV_IDS, default=self.config_entry.options.get(CONF_TV_IDS, [])): cv.multi_select(tv_ids),
                vol.Required(CONF_DAYS, default=self.config_entry.options.get(CONF_DAYS, 7)): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
            }),
        )
