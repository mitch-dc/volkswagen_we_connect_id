"""
Support for Volkswagen WeConnect Platform
"""
import logging

from carconnectivity import carconnectivity

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from . import DomainEntry, VolkswagenIDBaseEntity, get_object_value
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add sensors for passed config_entry in HA."""

    domain_entry: DomainEntry = hass.data[DOMAIN][config_entry.entry_id]
    car_connectivity = domain_entry.car_connectivity
    coordinator = domain_entry.coordinator

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for index, vehicle in enumerate(coordinator.data):
        entities.append(VolkswagenIDSensor(car_connectivity, coordinator, index))

    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, TrackerEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    def __init__(
        self,
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(car_connectivity, coordinator, index)

        self._coordinator = coordinator
        self._attr_name = f"{self.data.name} tracker"
        self._attr_unique_id = f"{self.data.vin}-tracker"

    @property
    def latitude(self) -> float:
        """Return latitude value of the device."""
        try:
            return get_object_value(
                self.data.position.latitude.value
            )
        except KeyError:
            return None

    @property
    def longitude(self) -> float:
        """Return longitude value of the device."""
        try:
            return get_object_value(
                self.data.position.longitude.value
            )
        except KeyError:
            return None

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:car"
