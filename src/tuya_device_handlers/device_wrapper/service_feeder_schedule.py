"""Device quirks for Tuya devices."""

import base64
from enum import IntFlag
from typing import Any, NamedTuple, TypedDict

from tuya_sharing import CustomerDevice

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
        if (entries := _RawFeederScheduleData.from_bytes(data)) is None:
            return None
        return [_RawFeederScheduleData.decode_entry(entry) for entry in entries]

    def _convert_value_to_raw_value(
        self, device: CustomerDevice, value: list[FeederSchedule]
    ) -> Any:
        """Convert display value back to a raw device value."""
        payload = _RawFeederScheduleData.to_bytes(
            [_RawFeederScheduleData.encode_entry(item) for item in value]
        )
        return base64.b64encode(payload).decode("utf-8")


def get_feeder_schedule_wrapper(
    device: CustomerDevice,
) -> DeviceWrapper[list[FeederSchedule]] | None:
    if device.product_id == "wfkzyy0evslzsmoi":
        return _DefaultFeederScheduleWrapper.find_dpcode(
            device, "meal_plan", prefer_function=True
        )
    return None


class _DaysOfWeek(IntFlag):
    """Bit 0 = Monday … bit 6 = Sunday; bit 7 unused."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 4
    THURSDAY = 8
    FRIDAY = 16
    SATURDAY = 32
    SUNDAY = 64


class _RawFeederScheduleDataEntry(NamedTuple):
    """One feeder schedule entry."""

    days: _DaysOfWeek
    """Bitmask: bit 0 Monday … bit 6 Sunday; bit 7 ignored."""
    hour: int
    """0-23."""
    minute: int
    """0-59."""
    portion: int
    enabled: int
    """0 or 1."""


class _RawFeederScheduleData:
    """Feeder schedule RAW value."""

    _ENTRY_LEN = 5

    @classmethod
    def from_bytes(cls, raw: bytes) -> list[_RawFeederScheduleDataEntry] | None:
        """Parse bytes into a list of _RawFeederScheduleDataEntry."""
        # Format: concatenated 5-byte entries (see _RawFeederScheduleDataEntry).
        if len(raw) % cls._ENTRY_LEN != 0:
            return None
        return [
            _RawFeederScheduleDataEntry(
                _DaysOfWeek(raw[i]),
                raw[i + 1],
                raw[i + 2],
                raw[i + 3],
                raw[i + 4],
            )
            for i in range(0, len(raw), cls._ENTRY_LEN)
        ]

    @classmethod
    def to_bytes(cls, entries: list[_RawFeederScheduleDataEntry]) -> bytes:
        """Serialize a list of _RawFeederScheduleDataEntry."""
        return bytes(b for entry in entries for b in entry)

    @staticmethod
    def decode_entry(entry: _RawFeederScheduleDataEntry) -> FeederSchedule:
        """Convert a raw entry to a HA FeederSchedule dict."""
        bitmask = entry.days & 0x7F
        return FeederSchedule(
            days=[
                name.lower()
                for name, member in _DaysOfWeek.__members__.items()
                if bitmask & member
            ],
            time=f"{entry.hour:02d}:{entry.minute:02d}",
            portion=entry.portion,
            enabled=bool(entry.enabled),
        )

    @staticmethod
    def encode_entry(item: FeederSchedule) -> _RawFeederScheduleDataEntry:
        """Convert a HA FeederSchedule dict to a raw entry."""
        bitmask = _DaysOfWeek(0)
        for name, member in _DaysOfWeek.__members__.items():
            if name.lower() in item["days"]:
                bitmask |= member
        hour, minute = map(int, item["time"].split(":"))
        return _RawFeederScheduleDataEntry(
            days=(bitmask),
            hour=hour,
            minute=minute,
            portion=item["portion"],
            enabled=int(item["enabled"]),
        )
