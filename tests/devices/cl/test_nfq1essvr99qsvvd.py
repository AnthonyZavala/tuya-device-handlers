"""Tests for the nfq1essvr99qsvvd cover position quirk.

This device (Canisteo Smart Zebra Shades) reports percent_state in HA
convention (0=closed, 100=open). Without the quirk the default
DPCodeInvertedPercentageWrapper incorrectly inverts position values.

See https://github.com/home-assistant/core/issues/159800.
"""

from unittest.mock import patch

import pytest

from tests import create_device
from tests.integration_helpers.cover import get_cover_default_definitions
from tuya_device_handlers import TUYA_QUIRKS_REGISTRY
from tuya_device_handlers.device_wrapper.common import (
    DPCodeTypeInformationWrapper,
)
from tuya_device_handlers.registry import QuirksRegistry
from tuya_device_handlers.type_information import (
    PrepareSetValueError,
    TypeInformation,
)


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


def test_quirk_current_position_invalid(
    filled_quirks_registry: QuirksRegistry,
) -> None:
    """Write delegates non-numeric values to the parent for validation."""
    device = create_device("cl_nfq1essvr99qsvvd.json")
    filled_quirks_registry.initialise_device_quirk(device)

    definitions = get_cover_default_definitions(device)
    wrapper = definitions["control"].current_position_wrapper
    assert wrapper is not None
    assert isinstance(wrapper, DPCodeTypeInformationWrapper)
    assert wrapper.type_information is not None
    assert isinstance(wrapper.type_information, TypeInformation)
    # Valid numeric value is prepared correctly
    assert wrapper.type_information.prepare_set_value(device, 70) == 30
    # Invalid non-numeric value raises an error
    with pytest.raises(PrepareSetValueError):
        wrapper.type_information.prepare_set_value(device, "stop")
    # Invalid status returns None
    del device.status["percent_state"]
    assert wrapper.type_information.read_device_value(device) is None
