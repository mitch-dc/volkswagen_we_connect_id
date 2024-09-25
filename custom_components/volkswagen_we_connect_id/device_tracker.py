"""
Support for Volkswagen WeConnect Platform
"""
import logging

from weconnect import weconnect

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
    we_connect = domain_entry.we_connect
    coordinator = domain_entry.coordinator

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for index, vehicle in enumerate(coordinator.data):
        entities.append(VolkswagenIDSensor(we_connect, coordinator, index))

    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, TrackerEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    def __init__(
        self,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(we_connect, coordinator, index)

        self._coordinator = coordinator
        self._attr_name = f"{self.data.nickname} tracker"
        self._attr_unique_id = f"{self.data.vin}-tracker"

    @property
    def latitude(self) -> float:
        """Return latitude value of the device."""
        try:
            return get_object_value(
                self.data.domains["parking"]["parkingPosition"].latitude.value
            )
        except KeyError:
            return None

    @property
    def longitude(self) -> float:
        """Return longitude value of the device."""
        try:
            return get_object_value(
                self.data.domains["parking"]["parkingPosition"].longitude.value
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

    @property
    def extra_state_attributes(self):
        """Return timestamp of when the data was captured."""
        try:
            return {
                "last_captured": get_object_value(
                    self.data.domains["parking"][
                        "parkingPosition"
                    ].carCapturedTimestamp.value
                )
            }
        except KeyError:
            return None
