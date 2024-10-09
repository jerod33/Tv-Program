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

async def load_tv_data():
    """Load TV station data from JSON file asynchronously."""
    data_file = os.path.join(os.path.dirname(__file__), "default_channels.json")
    async with aiofiles.open(data_file, "r") as f:
        tv_data = await f.read()
    return json.loads(tv_data)

class EPGConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EPG sensor."""

    VERSION = 1

    def __init__(self):
        self._data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EPGOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        tv_data = await load_tv_data()
        _LOGGER.info(f"TV Data: {tv_data}")
        # Výběr všech dostupných jazykových kódů (lang_code) a žánrů
        lang_codes = list(set(tv["lang_code"] for tv in tv_data))
        genres = list(set(tv["genre"] for tv in tv_data))

        # Výchozí stav - zobrazit všechny TV stanice
        filtered_tv_data = tv_data

        # Pokud máme vstup od uživatele, aplikujeme filtrování
        if user_input is not None:
            selected_lang_code = user_input.get("lang_code")
            selected_genre = user_input.get("genre")

            # Filtrování TV stanic podle lang_code a žánru
            filtered_tv_data = [
                tv for tv in tv_data
                if (selected_lang_code is None or tv["lang_code"] == selected_lang_code)
                and (selected_genre is None or tv["genre"] == selected_genre)
            ]

            # Aktualizace seznamu TV ID pro formulář na základě filtrování
            tv_ids = {tv["id"]: tv["name"] for tv in filtered_tv_data}

            selected_tv_ids = user_input.get(CONF_TV_IDS, [])
            days = user_input.get(CONF_DAYS, 3)

            # Pokud uživatel vyplnil formulář, uložíme výsledek
            if selected_tv_ids:
                self._data = {
                    CONF_TV_IDS: selected_tv_ids,
                    CONF_DAYS: days,
                }
                return self.async_create_entry(title="EPG Sensor", data=self._data)

        # Pokud nebylo dosud vyplněno, zobrazíme formulář
        tv_ids = {tv["id"]: tv["name"] for tv in filtered_tv_data}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("lang_code"): vol.In(lang_codes),  # Výběr jazyka
                vol.Optional("genre"): vol.In(genres),          # Výběr žánru
                vol.Required(CONF_TV_IDS, default=[]): cv.multi_select(tv_ids),  # Zobrazení filtrovaných stanic
                vol.Required(CONF_DAYS, default=7): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
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
        tv_data = await load_tv_data()

        # Výběr dostupných lang_code a žánrů
        lang_codes = list(set(tv["lang_code"] for tv in tv_data))
        genres = list(set(tv["genre"] for tv in tv_data))

        # Pokud existuje uživatelský vstup (v options flow), aplikujeme filtrování
        if user_input is not None:
            selected_lang_code = user_input.get("lang_code")
            selected_genre = user_input.get("genre")

            # Filtrování stanic podle vybraného lang_code a žánru
            filtered_tv_data = [
                tv for tv in tv_data
                if (selected_lang_code is None or tv["lang_code"] == selected_lang_code)
                and (selected_genre is None or tv["genre"] == selected_genre)
            ]

            # Aktualizace seznamu TV stanic podle filtru
            tv_ids = {tv["id"]: tv["name"] for tv in filtered_tv_data}

            # Uložení uživatelských možností
            self.hass.config_entries.async_update_entry(self.config_entry, options=user_input)
            await async_reload_sensors(self.hass, self.config_entry)
            return self.async_create_entry(title="", data=user_input)

        # Načítání aktuálních hodnot z možností (options)
        selected_tv_ids = self.config_entry.options.get(CONF_TV_IDS, [])
        selected_days = self.config_entry.options.get(CONF_DAYS, 7)
        selected_lang_code = self.config_entry.options.get("lang_code")
        selected_genre = self.config_entry.options.get("genre")

        # Filtrování stanic na základě uloženého lang_code a žánru
        filtered_tv_data = [
            tv for tv in tv_data
            if (selected_lang_code is None or tv["lang_code"] == selected_lang_code)
            and (selected_genre is None or tv["genre"] == selected_genre)
        ]

        tv_ids = {tv["id"]: tv["name"] for tv in filtered_tv_data}

        # Zobrazení formuláře pro úpravu možností
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("lang_code", default=selected_lang_code): vol.In(lang_codes),  # Výběr jazyka
                vol.Optional("genre", default=selected_genre): vol.In(genres),              # Výběr žánru
                vol.Required(CONF_TV_IDS, default=selected_tv_ids): cv.multi_select(tv_ids),  # Filtrovaný seznam TV stanic
                vol.Required(CONF_DAYS, default=selected_days): vol.All(vol.Coerce(int), vol.Range(min=1, max=7)),
            }),
        )
