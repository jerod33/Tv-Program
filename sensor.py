import logging
from datetime import datetime, timezone
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback
from .const import DOMAIN, DEVICE_CLASS_TIMESTAMP, CONF_TV_IDS, CONF_DAYS, SCAN_INTERVAL
from .coordinator import EPGDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the EPG sensor platform from a config entry."""
    _LOGGER.info("Setting up the EPG sensor platform.")

    # Retrieve configuration data
    options = config_entry.options or config_entry.data

    id_tv_list = options.get(CONF_TV_IDS, [])
    days = options.get(CONF_DAYS, 3)

    # Remove old sensors
    old_sensors = hass.data.get(DOMAIN, {}).get(config_entry.entry_id, {}).get("sensors", [])
    if old_sensors:
        _LOGGER.info(f"Removing old sensors: {old_sensors}")
        entity_registry = await hass.helpers.entity_registry.async_get_registry()
        for sensor in old_sensors:
            entity_registry.async_remove(sensor)

    sensors = []
    # Adding yesterday's sensor
    yesterday_coordinator = EPGDataUpdateCoordinator(hass, id_tv_list, -1)
    await yesterday_coordinator.async_config_entry_first_refresh()
    sensors.append(EPGSensor(yesterday_coordinator, "Yesterday"))

    # Adding today's sensor and the next `days` sensors
    for day in range(days):
        coordinator = EPGDataUpdateCoordinator(hass, id_tv_list, day)
        await coordinator.async_config_entry_first_refresh()
        sensors.append(EPGSensor(coordinator, day))

    async_add_entities(sensors)

    # Save the list of sensor entity IDs
    hass.data.setdefault(DOMAIN, {}).setdefault(config_entry.entry_id, {})["sensors"] = [sensor.entity_id for sensor in sensors]

    _LOGGER.info("EPG Sensors added to Home Assistant.")

@callback
async def async_reload_sensors(hass, config_entry):
    """Reload sensors based on the updated configuration."""
    platform = next(
        (platform for platform in hass.data.get(DOMAIN, {}).values() if hasattr(platform, "async_add_entities")), 
        None
    )
    if platform is not None:
        _LOGGER.info("Reloading EPG sensors...")
        await async_setup_entry(hass, config_entry, platform.async_add_entities)
        _LOGGER.info("EPG sensors reloaded.")

class EPGSensor(CoordinatorEntity):
    """Representation of a dynamically created EPG Sensor."""

    def __init__(self, coordinator, day_offset):
        super().__init__(coordinator)
        self._attr_device_class = DEVICE_CLASS_TIMESTAMP
        self._attr_state_class = None
        self.day_offset = day_offset
        self._state = datetime.now(timezone.utc)
        self._update_interval = SCAN_INTERVAL

    async def async_update(self):
        """Fetch new state data for the sensor."""
        await self.coordinator.async_request_refresh()
        self._state = datetime.now(timezone.utc)

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.day_offset == "Yesterday":
            return "EPG Sensor Yesterday"
        return f"EPG Sensor Day {self.day_offset + 1}"

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        if self.day_offset == "Yesterday":
            return f"{DOMAIN}_sensor_yesterday"
        return f"{DOMAIN}_sensor_day_{self.day_offset + 1}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return datetime.now(timezone.utc)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "data": self.coordinator.data,
        }
