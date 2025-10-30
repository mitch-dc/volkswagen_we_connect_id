"""Button integration."""
from carconnectivity import carconnectivity
from carconnectivity_connectors.volkswagen.vehicle import VolkswagenElectricVehicle

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    DomainEntry,
    get_object_value,
    set_ac_charging_speed,
    start_stop_climatisation,
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
    car_connectivity = domain_entry.car_connectivity
    vehicles = domain_entry.vehicles

    entities = []
    for vehicle in vehicles:
        entities.append(VolkswagenIDStartClimateButton(vehicle, car_connectivity))
        entities.append(VolkswagenIDStopClimateButton(vehicle, car_connectivity))
        entities.append(VolkswagenIDToggleACChargeSpeed(vehicle, car_connectivity))
        entities.append(VolkswagenIDStartChargingButton(vehicle, car_connectivity))
        entities.append(VolkswagenIDStopChargingButton(vehicle, car_connectivity))

    async_add_entities(entities)

    return True


class VolkswagenIDStartClimateButton(ButtonEntity):
    """Button for starting climate."""

    def __init__(self, vehicle: VolkswagenElectricVehicle, car_connectivity: carconnectivity.CarConnectivity) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.name} Start Climate"
        self._attr_unique_id = f"{vehicle.vin}-start_climate"
        self._attr_icon = "mdi:fan-plus"
        self._car_connectivity = car_connectivity
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        start_stop_climatisation(self._vehicle.vin.value, self._car_connectivity, "start")


class VolkswagenIDStopClimateButton(ButtonEntity):
    """Button for stopping climate."""

    def __init__(self, vehicle: VolkswagenElectricVehicle, car_connectivity: carconnectivity.CarConnectivity) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.name} Stop Climate"
        self._attr_unique_id = f"{vehicle.vin}-stop_climate"
        self._attr_icon = "mdi:fan-off"
        self._car_connectivity = car_connectivity
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        start_stop_climatisation(self._vehicle.vin.value, self._car_connectivity, "stop")


class VolkswagenIDToggleACChargeSpeed(ButtonEntity):
    """Button for toggling the charge speed."""

    def __init__(self, vehicle: VolkswagenElectricVehicle, car_connectivity: carconnectivity.CarConnectivity) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.name} Toggle AC Charge Speed"
        self._attr_unique_id = f"{vehicle.vin}-toggle_ac_charge_speed"
        self._attr_icon = "mdi:ev-station"
        self._car_connectivity = car_connectivity
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""

        current_state = get_object_value(
            self._vehicle.charging.settings.maximum_current.value
        )

        if current_state == "maximum":
            set_ac_charging_speed(
                self._vehicle.vin.value,
                self._car_connectivity,
                "reduced",
            )
        else:
            set_ac_charging_speed(
                self._vehicle.vin.value,
                self._car_connectivity,
                "maximum",
            )


class VolkswagenIDStartChargingButton(ButtonEntity):
    """Button for start charging."""

    def __init__(self, vehicle: VolkswagenElectricVehicle, car_connectivity: carconnectivity.CarConnectivity) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.name} Start Charging"
        self._attr_unique_id = f"{vehicle.vin}-start_charging"
        self._attr_icon = "mdi:play-circle-outline"
        self._car_connectivity = car_connectivity
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        start_stop_charging(self._vehicle.vin.value, self._car_connectivity, "start")


class VolkswagenIDStopChargingButton(ButtonEntity):
    """Button for stop charging."""

    def __init__(self, vehicle: VolkswagenElectricVehicle, car_connectivity: carconnectivity.CarConnectivity) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.name} Stop Charging"
        self._attr_unique_id = f"{vehicle.vin}-stop_charging"
        self._attr_icon = "mdi:stop-circle-outline"
        self._car_connectivity = car_connectivity
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        start_stop_charging(self._vehicle.vin.value, self._car_connectivity, "stop")
