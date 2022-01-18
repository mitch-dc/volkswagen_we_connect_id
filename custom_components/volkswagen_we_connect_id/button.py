"""TOLO Sauna Button controls."""

from weconnect import weconnect
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.vehicle import Vehicle

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VolkswagenIDBaseEntity, set_climatisation
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add buttons for passed config_entry in HA."""
    weConnect = hass.data[DOMAIN][config_entry.entry_id]
    vehicles = hass.data[DOMAIN][config_entry.entry_id + "_vehicles"]

    entities = []
    for vin, vehicle in vehicles.items():  # weConnect.vehicles.items():
        entities.append(VolkswagenIDStartClimateButton(vehicle, weConnect))

    async_add_entities(entities)

    return True


class VolkswagenIDStartClimateButton(ButtonEntity):
    """Button for starting climate"""

    def __init__(self, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"Volkswagen ID {vehicle.nickname} Start Climate"
        self._attr_unique_id = f"{vehicle.vin}-start_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        set_climatisation(self._vehicle.vin.value, self._we_connect, "start", 0)
