"""Tests for the nfq1essvr99qsvvd cover position quirk.

This device (Canisteo Smart Zebra Shades) reports percent_state in HA
convention (0=closed, 100=open). Without the quirk the default
DPCodeInvertedPercentageWrapper incorrectly inverts position values.

See https://github.com/home-assistant/core/issues/159800.
"""

from unittest.mock import patch

from tests import create_device
from tests.integration_helpers.cover import get_cover_default_definitions
from tuya_device_handlers import TUYA_QUIRKS_REGISTRY
from tuya_device_handlers.registry import QuirksRegistry
from tuya_device_handlers.type_information import IntegerTypeInformation


def test_quirk_corrects_position(
    filled_quirks_registry: QuirksRegistry,
) -> None:
    """With quirk, percent_state=95 reads as 95 (not inverted to 5)."""
    device = create_device("cl_nfq1essvr99qsvvd.json")

    with patch.dict(TUYA_QUIRKS_REGISTRY._quirks, clear=True):
        definitions = get_cover_default_definitions(device)
    wrapper = definitions["control"].current_position_wrapper
    assert wrapper is not None
    assert wrapper.read_device_status(device) == 5

    filled_quirks_registry.initialise_device_quirk(device)

    definitions = get_cover_default_definitions(device)
    wrapper = definitions["control"].current_position_wrapper
    assert wrapper is not None
    assert wrapper.read_device_status(device) == 95


def test_quirk_keeps_control_write_native(
    filled_quirks_registry: QuirksRegistry,
) -> None:
    """Quirk overrides percent_control to the plain (non-inverted) class.

    Only the percent_state read is pre-inverted; the percent_control write
    path keeps the device's native convention, so the default wrapper still
    sends the inverted raw value (position 70 -> raw 30) before and after the
    quirk is applied.
    """
    device = create_device("cl_nfq1essvr99qsvvd.json")

    with patch.dict(TUYA_QUIRKS_REGISTRY._quirks, clear=True):
        definitions = get_cover_default_definitions(device)
    wrapper = definitions["control"].set_position_wrapper
    assert wrapper is not None
    assert wrapper.get_update_commands(device, 70) == [
        {"code": "percent_control", "value": 30}
    ]

    filled_quirks_registry.initialise_device_quirk(device)

    definitions = get_cover_default_definitions(device)
    wrapper = definitions["control"].set_position_wrapper
    assert wrapper is not None
    assert wrapper.get_update_commands(device, 70) == [
        {"code": "percent_control", "value": 30}
    ]


def test_quirk_read_handles_missing_value(
    filled_quirks_registry: QuirksRegistry,
) -> None:
    """Read returns None (not inverted) when the device reports no value."""
    device = create_device("cl_nfq1essvr99qsvvd.json")
    filled_quirks_registry.initialise_device_quirk(device)
    del device.status["percent_state"]

    type_information = IntegerTypeInformation.find_dpcode(
        device, "percent_state"
    )
    assert type_information is not None
    assert type_information.read_device_value(device) is None
