"""Sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from datetime import datetime

from carconnectivity import carconnectivity

from carconnectivity_connectors.volkswagen.vehicle import VolkswagenElectricVehicle

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import DomainEntry, VolkswagenIDBaseEntity, get_object_value
from .const import DOMAIN


@dataclass
class VolkswagenIdEntityDescription(SensorEntityDescription):
    """Describes Volkswagen ID sensor entity."""

    value: Callable[[VolkswagenElectricVehicle]] = lambda x, y: x


SENSORS: tuple[VolkswagenIdEntityDescription, ...] = (
    VolkswagenIdEntityDescription(
        key="carType",
        name="Car Type",
        icon="mdi:car",
        value=lambda data: data.type.value,
    ),
    VolkswagenIdEntityDescription(
        key="climatisationState",
        name="Climatisation State",
        icon="mdi:fan",
        value=lambda data: data.climatization.state.value,
    ),
    VolkswagenIdEntityDescription(
        key="remainingClimatisationTime_min",
        name="Remaining Climatisation Time",
        icon="mdi:fan-clock",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value=lambda data: (datetime.now() - data.climatization.estimated_date_reached.value).seconds / 60,
    ),
    VolkswagenIdEntityDescription(
        key="targetTemperature",
        name="Target Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data: data.climatization.settings.target_temperature.temperature_in(UnitOfTemperature.CELSIUS),
    ),
    VolkswagenIdEntityDescription(
        key="chargingState",
        name="Charging State",
        icon="mdi:ev-station",
        value=lambda data: data.charging.state.value,
    ),
    VolkswagenIdEntityDescription(
        key="remainingChargingTimeToComplete_min",
        name="Remaining Charging Time",
        icon="mdi:battery-clock",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value=lambda data: (datetime.now() - data.charging.estimated_date_reached.value).seconds / 60,
    ),
    VolkswagenIdEntityDescription(
        key="chargeMode",
        name="Charging Mode",
        icon="mdi:ev-station",
        value=lambda data: data.charging.type.value,
    ),
    VolkswagenIdEntityDescription(
        key="chargePower_kW",
        name="Charge Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        value=lambda data: data.charging.power.power_in(UnitOfPower.KILO_WATT),
    ),
    VolkswagenIdEntityDescription(
        key="chargeRate_kmph",
        name="Charge Rate",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        value=lambda data: data.charging.rate.speed_in(UnitOfSpeed.KILOMETERS_PER_HOUR),
    ),
    VolkswagenIdEntityDescription(
        key="chargingSettings",
        name="Charging Settings",
        icon="mdi:ev-station",
        value=lambda data: data.charging.settings,
    ),
    VolkswagenIdEntityDescription(
        key="chargeType",
        name="Charge Type",
        icon="mdi:ev-station",
        value=lambda data: data.charging.type.value,
    ),
    VolkswagenIdEntityDescription(
        key="maxChargeCurrentAC",
        name="Max Charge Current AC",
        icon="mdi:ev-station",
        value=lambda data: data.charging.settings.maximum_current.value,
    ),
    VolkswagenIdEntityDescription(
        key="targetSOC_pct",
        name="Target State of Charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data: data.charging.settings.target_level.value,
    ),
    VolkswagenIdEntityDescription(
        key="currentSOC_pct",
        name="State of Charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data: data.get_electric_drive().level.value,
    ),
    VolkswagenIdEntityDescription(
        name="Range",
        key="cruisingRangeElectric",
        icon="mdi:car-arrow-right",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data: data.get_electric_drive().range.range_in(UnitOfLength.KILOMETERS),
    ),
    VolkswagenIdEntityDescription(
        name="Health Inspection",
        key="inspectionDue",
        icon="mdi:wrench-clock-outline",
        native_unit_of_measurement=UnitOfTime.DAYS,
        value=lambda data: (data.maintenance.inspection_due_at.value - datetime.now()).days,
    ),
    VolkswagenIdEntityDescription(
        name="Health Inspection km",
        key="inspectionDuekm",
        icon="mdi:wrench-clock-outline",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data: data.maintenance.inspection_due_after.range_in(UnitOfLength.KILOMETERS),
    ),
    VolkswagenIdEntityDescription(
        name="Odometer",
        key="odometer",
        icon="mdi:car-cruise-control",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value=lambda data: data.odometer.range_in(UnitOfLength.KILOMETERS),
    ),
    VolkswagenIdEntityDescription(
        key="doorLockStatus",
        name="Door Lock Status",
        icon="mdi:car-door-lock",
        value=lambda data: data.doors.lock_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="bonnetLockStatus",
        name="Bonnet Lock Status",
        icon="mdi:lock-outline",
        value=lambda data: data.doors.doors["bonnet"].lock_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="trunkLockStatus",
        name="Trunk Lock Status",
        icon="mdi:lock-outline",
        value=lambda data: data.doors.doors["trunk"].lock_state.value,

    ),
    VolkswagenIdEntityDescription(
        key="rearRightLockStatus",
        name="Door Rear Right Lock Status",
        icon="mdi:car-door-lock",
        value=lambda data: data.doors.doors["rearRight"].lock_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="rearLeftLockStatus",
        name="Door Rear Left Lock Status",
        icon="mdi:car-door-lock",
        value=lambda data: data.doors.doors["rearLeft"].lock_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="frontLeftLockStatus",
        name="Door Front Left Lock Status",
        icon="mdi:car-door-lock",
        value=lambda data: data.doors.doors["frontLeft"].lock_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="frontRightLockStatus",
        name="Door Front Right Lock Status",
        icon="mdi:car-door-lock",
        value=lambda data: data.doors.doors["frontRight"].lock_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="bonnetOpenStatus",
        name="Bonnet Open Status",
        value=lambda data: data.doors.doors["bonnet"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="trunkOpenStatus",
        name="Trunk Open Status",
        value=lambda data: data.doors.doors["trunk"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="rearRightOpenStatus",
        name="Door Rear Right Open Status",
        icon="mdi:car-door",
        value=lambda data: data.doors.doors["rearRight"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="rearLeftOpenStatus",
        name="Door Rear Left Open Status",
        icon="mdi:car-door",
        value=lambda data: data.doors.doors["rearLeft"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="frontLeftOpenStatus",
        name="Door Front Left Open Status",
        icon="mdi:car-door",
        value=lambda data: data.doors.doors["frontLeft"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="frontRightOpenStatus",
        name="Door Front Right Open Status",
        icon="mdi:car-door",
        value=lambda data: data.doors.doors["frontRight"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="sunRoofStatus",
        name="Sunroof Open Status",
        value=lambda data: data.doors.doors["sunRoof"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="roofCoverStatus",
        name="Sunroof Cover Status",
        value=lambda data: data.doors.doors["roofCover"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="windowRearRightOpenStatus",
        name="Window Rear Right Open Status",
        icon="mdi:window-closed",
        value=lambda data: data.windows.windows["rearRight"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="windowRearLeftOpenStatus",
        name="Window Rear Left Open Status",
        icon="mdi:window-closed",
        value=lambda data: data.windows.windows["rearLeft"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="windowFrontLeftOpenStatus",
        name="Window Front Left Open Status",
        icon="mdi:window-closed",
        value=lambda data: data.windows.windows["frontLeft"].open_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="windowfrontRightOpenStatus",
        name="Window Front Right Open Status",
        icon="mdi:window-closed",
        value=lambda data: data.windows.windows["frontRight"].open_state.value,
    ),
    # VolkswagenIdEntityDescription(
    #     key="overallStatus",
    #     name="Overall Status",
    #     icon="mdi:car-info",
    #     value=lambda data: data["access"]["accessStatus"].overallStatus.value,
    # ),
    VolkswagenIdEntityDescription(
        key="autoUnlockPlugWhenCharged",
        name="Auto Unlock Plug When Charged",
        icon="mdi:ev-plug-type2",
        value=lambda data: data.charging.settings.auto_unlock.value,
    ),
    VolkswagenIdEntityDescription(
        key="autoUnlockPlugWhenChargedAC",
        name="Auto Unlock Plug When Charged AC",
        icon="mdi:ev-plug-type2",
        value=lambda data: data.charging.settings.auto_unlock.value,
    ),
    VolkswagenIdEntityDescription(
        key="plugConnectionState",
        name="Plug Connection State",
        icon="mdi:ev-plug-type2",
        value=lambda data: data.charging.connector.connection_state.value,
    ),
    VolkswagenIdEntityDescription(
        key="plugLockState",
        name="Plug Lock State",
        icon="mdi:ev-plug-type2",
        value=lambda data: data.charging.connector.lock_state.value,
    ),
    # VolkswagenIdEntityDescription(
    #     name="Fuel Level",
    #     key="fuelLevel",
    #     icon="mdi:fuel",
    #     native_unit_of_measurement=PERCENTAGE,
    #     value=lambda data: data["fuelStatus"]["rangeStatus"].primaryEngine.currentFuelLevel_pct.value,
    # ),
    # VolkswagenIdEntityDescription(
    #     name="Gasoline Range",
    #     key="GasolineRange",
    #     icon="mdi:car-arrow-right",
    #     device_class=SensorDeviceClass.DISTANCE,
    #     native_unit_of_measurement=UnitOfLength.KILOMETERS,
    #     value=lambda data: data["measurements"][
    #         "rangeStatus"
    #     ].gasolineRange.value,
    # ),
    # VolkswagenIdEntityDescription(
    #     name="Oil Inspection days",
    #     key="oilInspectionDue",
    #     icon="mdi:wrench-clock-outline",
    #     native_unit_of_measurement=UnitOfTime.DAYS,
    #     value=lambda data: data["vehicleHealthInspection"][
    #         "maintenanceStatus"
    #     ].oilServiceDue_days.value,
    # ),
    # VolkswagenIdEntityDescription(
    #     name="Oil Inspection km",
    #     key="oilInspectionDuekm",
    #     icon="mdi:wrench-clock-outline",
    #     device_class=SensorDeviceClass.DISTANCE,
    #     native_unit_of_measurement=UnitOfLength.KILOMETERS,
    #     value=lambda data: data["vehicleHealthInspection"][
    #         "maintenanceStatus"
    #     ].oilServiceDue_km.value,
    # ),
    VolkswagenIdEntityDescription(
        name="HV Battery Temperature Min",
        key="hvBatteryTemperatureMin",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data: data.get_electric_drive().battery.temperature_min.temperature_in(UnitOfTemperature.CELSIUS),
    ),
    VolkswagenIdEntityDescription(
        name="HV Battery Temperature Max",
        key="hvBatteryTemperatureMax",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data: data.get_electric_drive().battery.temperature_max.temperature_in(UnitOfTemperature.CELSIUS),
    ),

)

VEHICLE_SENSORS: tuple[VolkswagenIdEntityDescription, ...] = (
    VolkswagenIdEntityDescription(
        key="lastTripAverageElectricConsumption",
        name="Last Trip Average Electric consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda vehicle: vehicle.trips["shortTerm"].averageElectricConsumption.value,
    ),
    VolkswagenIdEntityDescription(
        key="lastTripAverageFuelConsumption",
        name="Last Trip Average Fuel consumption",
        native_unit_of_measurement="l/100km",
        value=lambda vehicle: vehicle.trips["shortTerm"].averageFuelConsumption.value,
    ),

)


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

    entities: list[VolkswagenIDSensor] = []

    for index, vehicle in enumerate(coordinator.data):
        for sensor in SENSORS:
            entities.append(VolkswagenIDSensor(sensor, car_connectivity, coordinator, index))
        # for sensor in VEHICLE_SENSORS:
        #     entities.append(VolkswagenIDVehicleSensor(sensor, car_connectivity, coordinator, index))

    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, SensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: VolkswagenIdEntityDescription

    def __init__(
        self,
        sensor: VolkswagenIdEntityDescription,
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(car_connectivity, coordinator, index)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"{self.data.name} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"
        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state."""

        try:
            state = get_object_value(self.entity_description.value(self.data))
        except (TypeError, KeyError, ValueError):
            return None

        return cast(StateType, state)

class VolkswagenIDVehicleSensor(VolkswagenIDBaseEntity, SensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: VolkswagenIdEntityDescription

    def __init__(
        self,
        sensor: VolkswagenIdEntityDescription,
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(car_connectivity, coordinator, index)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"{self.data.name} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"
        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state."""

        try:
            state = get_object_value(self.entity_description.value(self.data))
        except (KeyError, ValueError):
            return None

        return cast(StateType, state)
