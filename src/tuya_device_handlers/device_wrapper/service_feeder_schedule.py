"""Device quirks for Tuya devices."""

import base64
from typing import Any, TypedDict

from tuya_sharing import CustomerDevice

from tuya_device_handlers.raw_data_model import (
    FeederScheduleData as _RawFeederScheduleData,
    FeederScheduleDataEntry as _RawFeederScheduleDataEntry,
)

from .base import DeviceWrapper
from .common import DPCodeRawWrapper


class FeederSchedule(TypedDict):
    """Public class for Home Assistant representation of a feeder schedule entry."""

    days: list[str]
    """Days (monday-sunday)."""
    time: str
    """In 24h format hh:mm."""
    portion: int
    """Portion size."""
    enabled: bool
    """True or False."""


class _DefaultFeederScheduleWrapper(DPCodeRawWrapper[list[FeederSchedule]]):
    """Wrapper for a schedule received in a base64 DPCode."""

    def read_device_status(
        self, device: CustomerDevice
    ) -> list[FeederSchedule] | None:
        """Decode the meal plan data."""
        if (data := self._read_dpcode_value(device)) is None:
            return None
        return _RawFeederScheduleConverter.from_bytes(data)

    def _convert_value_to_raw_value(
        self, device: CustomerDevice, value: list[FeederSchedule]
    ) -> Any:
        """Convert display value back to a raw device value."""
        payload = _RawFeederScheduleConverter.to_bytes(value)
        return base64.b64encode(payload).decode("utf-8")


def get_feeder_schedule_wrapper(
    device: CustomerDevice,
) -> DeviceWrapper[list[FeederSchedule]] | None:
    if device.product_id == "wfkzyy0evslzsmoi":
        return _DefaultFeederScheduleWrapper.find_dpcode(
            device, "meal_plan", prefer_function=True
        )
    return None


_DAYS_OF_WEEK: list[str] = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class _RawFeederScheduleConverter:
    """Convert between raw feeder schedule data and HA FeederSchedule dicts."""

    @staticmethod
    def _decode_entry(
        entry: _RawFeederScheduleDataEntry,
    ) -> FeederSchedule:
        """Convert a raw entry to a HA FeederSchedule dict."""
        bitmask = entry.days & 0x7F
        return FeederSchedule(
            # Bit 0 = Monday … bit 6 = Sunday; bit 7 unused.
            days=[
                name
                for i, name in enumerate(_DAYS_OF_WEEK)
                if bitmask & (1 << i)
            ],
            time=f"{entry.hour:02d}:{entry.minute:02d}",
            portion=entry.portion,
            enabled=bool(entry.enabled),
        )

    @staticmethod
    def _encode_entry(
        item: FeederSchedule,
    ) -> _RawFeederScheduleDataEntry:
        """Convert a HA FeederSchedule dict to a raw entry."""
        # Bit 0 = Monday … bit 6 = Sunday; bit 7 unused.
        bitmask = 0
        for i, name in enumerate(_DAYS_OF_WEEK):
            if name in item["days"]:
                bitmask |= 1 << i
        hour, minute = map(int, item["time"].split(":"))
        return _RawFeederScheduleDataEntry(
            days=bitmask,
            hour=hour,
            minute=minute,
            portion=item["portion"],
            enabled=int(item["enabled"]),
        )

    @classmethod
    def from_bytes(cls, raw: bytes) -> list[FeederSchedule] | None:
        """Parse raw bytes into a list of HA FeederSchedule dicts."""
        if (entries := _RawFeederScheduleData.from_bytes(raw)) is None:
            return None
        return [cls._decode_entry(entry) for entry in entries]

    @classmethod
    def to_bytes(cls, items: list[FeederSchedule]) -> bytes:
        """Serialize a list of HA FeederSchedule dicts to raw bytes."""
        return _RawFeederScheduleData.to_bytes(
            [cls._encode_entry(item) for item in items]
        )
