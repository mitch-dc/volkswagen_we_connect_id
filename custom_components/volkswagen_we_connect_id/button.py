"""Button integration."""
from weconnect import weconnect
from weconnect.elements.vehicle import Vehicle

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    DomainEntry,
    get_object_value,
    set_ac_charging_speed,
    set_climatisation,
    start_stop_charging,
)
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Add buttons for passed config_entry in HA."""
    domain_entry: DomainEntry = hass.data[DOMAIN][config_entry.entry_id]
    we_connect = domain_entry.we_connect
    vehicles = domain_entry.vehicles

    entities = []
    for vehicle in vehicles:  # weConnect.vehicles.items():
        entities.append(VolkswagenIDStartClimateButton(vehicle, we_connect))
        entities.append(VolkswagenIDStopClimateButton(vehicle, we_connect))
        entities.append(VolkswagenIDToggleACChargeSpeed(vehicle, we_connect))
        entities.append(VolkswagenIDStartChargingButton(vehicle, we_connect))
        entities.append(VolkswagenIDStopChargingButton(vehicle, we_connect))

    async_add_entities(entities)

    return True


class VolkswagenIDStartClimateButton(ButtonEntity):
    """Button for starting climate."""

    def __init__(self, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Start Climate"
        self._attr_unique_id = f"{vehicle.vin}-start_climate"
        self._attr_icon = "mdi:fan-plus"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        set_climatisation(self._vehicle.vin.value, self._we_connect, "start", 0)


class VolkswagenIDStopClimateButton(ButtonEntity):
    """Button for stopping climate."""

    def __init__(self, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Stop Climate"
        self._attr_unique_id = f"{vehicle.vin}-stop_climate"
        self._attr_icon = "mdi:fan-off"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        set_climatisation(self._vehicle.vin.value, self._we_connect, "stop", 0)


class VolkswagenIDToggleACChargeSpeed(ButtonEntity):
    """Button for toggling the charge speed."""

    def __init__(self, vehicle: Vehicle, we_connect: weconnect.WeConnect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Toggle AC Charge Speed"
        self._attr_unique_id = f"{vehicle.vin}-toggle_ac_charge_speed"
        self._attr_icon = "mdi:ev-station"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""

        current_state = get_object_value(
            self._vehicle.domains["charging"]["chargingSettings"].maxChargeCurrentAC
        )

        if current_state == "maximum":
            set_ac_charging_speed(
                self._vehicle.vin.value,
                self._we_connect,
                "reduced",
            )
        else:
            set_ac_charging_speed(
                self._vehicle.vin.value,
                self._we_connect,
                "maximum",
            )


class VolkswagenIDStartChargingButton(ButtonEntity):
    """Button for start charging."""

    def __init__(self, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Start Charging"
        self._attr_unique_id = f"{vehicle.vin}-start_charging"
        self._attr_icon = "mdi:play-circle-outline"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        start_stop_charging(self._vehicle.vin.value, self._we_connect, "start")


class VolkswagenIDStopChargingButton(ButtonEntity):
    """Button for stop charging."""

    def __init__(self, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Stop Charging"
        self._attr_unique_id = f"{vehicle.vin}-stop_charging"
        self._attr_icon = "mdi:stop-circle-outline"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        start_stop_charging(self._vehicle.vin.value, self._we_connect, "stop")
