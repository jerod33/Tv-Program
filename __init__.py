import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_DAYS, CONF_TV_IDS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EPG sensor from a config entry."""
    # Load saved configuration if it exists
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    # Retrieve configuration data
    days = entry.options.get(CONF_DAYS, 7)  # Use options instead of data
    tv_ids = entry.options.get(CONF_TV_IDS, [])  # Use options instead of data

    _LOGGER.info(f"Setting up EPG sensor with {days} days and TV IDs: {tv_ids}")

    # Setup sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    #await hass.config_entries.async_forward_entry_setup(entry, "sensor")

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.info("EPG sensor unloaded")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True
