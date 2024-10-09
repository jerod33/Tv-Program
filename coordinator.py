import logging
import os
import json
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import xmltodict
import aiofiles  # Import the aiofiles library
from .const import USER_AGENT, BASE_URL, SCAN_INTERVAL, CONF_TV_IDS

_LOGGER = logging.getLogger(__name__)

class EPGDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, id_tv_list, day_offset):
        self.hass = hass
        self.id_tv_list = id_tv_list
        self.day_offset = day_offset
        super().__init__(
            hass, _LOGGER, name=f"EPG Sensor Day {day_offset + 1}", update_interval=SCAN_INTERVAL
        )

    async def _async_load_tv_data(self):
        data_file = os.path.join(os.path.dirname(__file__), "default_channels.json")
        async with aiofiles.open(data_file, "r") as f:
            tv_data = await f.read()
            return json.loads(tv_data)

    async def _async_update_data(self) -> dict:
        try:
            # Load TV station data from JSON file asynchronously
            tv_data = await self._async_load_tv_data()
            self.tv_ids_to_info = {tv["id"]: tv for tv in tv_data}

            # Updated to correctly calculate date based on day_offset
            current_date = datetime.now() + timedelta(days=self.day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            id_tv = ",".join(self.id_tv_list)
            params = {
                "datum": date_str,
                "id_tv": id_tv
            }

            url = f"{BASE_URL}?datum={params['datum']}&id_tv={params['id_tv']}"
            headers = {
                'User-Agent': USER_AGENT
            }
            _LOGGER.debug(f"Fetching data from URL: {url} with headers: {headers}")

            session = async_get_clientsession(self.hass)
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.text()

                # Transform XML data to JSON
                parsed_data = xmltodict.parse(data)
                programs = parsed_data['a']['p']

                transformed_data = []
                for program in programs:
                    title_data = program['n']
                    title = title_data.get('#text', title_data) if isinstance(title_data, dict) else title_data

                    # Get channel info based on id_tv
                    channel_info = self.tv_ids_to_info.get(program['@id_tv'], {"name": "Unknown Channel", "logo_url": ""})
                    channel_name = channel_info["name"]
                    logo_url = channel_info["logo_url"] #ToDo URL-mit to online a ne offline?Aktualne''

                    entry = {
                        "id_tv": program['@id_tv'],
                        "Start": program['@o'],
                        "Stop": program['@d'],
                        "title1": title_data.get('@u', None) if isinstance(title_data, dict) else None,
                        "Title": title,
                        "short_description": program.get('k', ''),
                        "program_genre": program.get('t', ''),
                        "channel_name": channel_name,  # Add channel name
                        "logo_url": logo_url  # Add logo URL
                    }
                    transformed_data.append(entry)

                return transformed_data

        except Exception as e:
            _LOGGER.error(f"Error fetching or transforming data: {e}")
            return []