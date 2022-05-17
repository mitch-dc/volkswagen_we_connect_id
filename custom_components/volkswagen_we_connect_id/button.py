"""Button integration."""
from weconnect import weconnect
from weconnect.elements.vehicle import Vehicle

from homeassistant.components.button import ButtonEntity

from . import get_object_value, set_ac_charging_speed, set_climatisation
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add buttons for passed config_entry in HA."""
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    vehicles = hass.data[DOMAIN][config_entry.entry_id + "_vehicles"]

    entities = []
    for vehicle in vehicles:  # weConnect.vehicles.items():
        entities.append(VolkswagenIDStartClimateButton(vehicle, we_connect))
        entities.append(VolkswagenIDToggleACChargeSpeed(vehicle, we_connect))

    async_add_entities(entities)

    return True


class VolkswagenIDStartClimateButton(ButtonEntity):
    """Button for starting climate."""

    def __init__(self, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Start Climate"
        self._attr_unique_id = f"{vehicle.vin}-start_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        set_climatisation(self._vehicle.vin.value, self._we_connect, "start", 0)


class VolkswagenIDToggleACChargeSpeed(ButtonEntity):
    """Button for toggling the charge speed."""

    def __init__(self, vehicle: Vehicle, we_connect: weconnect.WeConnect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"{vehicle.nickname} Toggle AC Charge Speed"
        self._attr_unique_id = f"{vehicle.vin}-toggle_ac_charge_speed"
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
