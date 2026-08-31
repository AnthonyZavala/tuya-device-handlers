"""Tests for light definition."""

from tests import create_device
from tuya_device_handlers.definition.light import (
    FallbackColorDataMode,
    get_default_definition,
)
from tuya_device_handlers.device_wrapper.common import (
    DPCodeBooleanWrapper,
    DPCodeEnumWrapper,
)
from tuya_device_handlers.device_wrapper.light import (
    BrightnessWrapper,
    ColorDataJsonWrapper,
    ColorDataStringWrapper,
    ColorTempWrapper,
)


def test_get_default_definition() -> None:
    """Test get_default_definition."""
    device = create_device("dj_mki13ie507rlry4r.json")
    assert (
        definition := get_default_definition(
            device,
            switch_dpcode="switch_led",
            brightness_dpcode=("bright_value_v2", "bright_value"),
            brightness_max_dpcode=None,
            brightness_min_dpcode=None,
            color_data_dpcode=("colour_data_v2", "colour_data"),
            color_mode_dpcode="work_mode",
            color_temp_dpcode=("temp_value_v2", "temp_value"),
            fallback_color_data_mode=FallbackColorDataMode.V1,
        )
    )
    assert isinstance(definition.brightness_wrapper, BrightnessWrapper)
    assert isinstance(definition.color_data_wrapper, ColorDataJsonWrapper)
    assert isinstance(definition.color_mode_wrapper, DPCodeEnumWrapper)
    assert not definition.color_temp_wrapper
    assert isinstance(definition.switch_wrapper, DPCodeBooleanWrapper)


def test_get_default_definition_fails() -> None:
    """Test get_default_definition."""
    device = create_device("cs_zibqa9dutqyaxym2.json")
    assert not get_default_definition(
        device,
        switch_dpcode="bad",
        brightness_dpcode=None,
        brightness_max_dpcode=None,
        brightness_min_dpcode=None,
        color_data_dpcode=None,
        color_mode_dpcode=None,
        color_temp_dpcode=None,
        fallback_color_data_mode=FallbackColorDataMode.V1,
    )


def test_missing_colour_data_hsv() -> None:
    """Test missing_colour_data_hsv."""
    device = create_device("jsq_op2lzjcj7fdfhid8.json")
    assert (
        definition := get_default_definition(
            device,
            switch_dpcode="switch_led",
            brightness_dpcode="bright_value",
            brightness_max_dpcode=None,
            brightness_min_dpcode=None,
            color_data_dpcode="colour_data_hsv",
            color_mode_dpcode=None,
            color_temp_dpcode=None,
            fallback_color_data_mode=FallbackColorDataMode.V1,
        )
    )
    assert definition.brightness_wrapper is None
    assert isinstance(definition.color_data_wrapper, ColorDataJsonWrapper)
    assert definition.color_mode_wrapper is None
    assert definition.color_temp_wrapper is None
    assert isinstance(definition.switch_wrapper, DPCodeBooleanWrapper)


def test_get_default_definition_hex_string_colour_data() -> None:
    """Test hex-encoded String colour_data yields a ColorDataStringWrapper."""
    device = create_device("hcdd_expmpw4xxd0kkifb.json")
    assert (
        definition := get_default_definition(
            device,
            switch_dpcode="switch_led",
            brightness_dpcode=("bright_value_v2", "bright_value"),
            brightness_max_dpcode=None,
            brightness_min_dpcode=None,
            color_data_dpcode=("colour_data_v2", "colour_data"),
            color_mode_dpcode="work_mode",
            color_temp_dpcode=("temp_value_v2", "temp_value"),
            fallback_color_data_mode=FallbackColorDataMode.V1,
        )
    )
    assert isinstance(definition.brightness_wrapper, BrightnessWrapper)
    assert isinstance(definition.color_data_wrapper, ColorDataStringWrapper)
    assert isinstance(definition.color_mode_wrapper, DPCodeEnumWrapper)
    assert isinstance(definition.color_temp_wrapper, ColorTempWrapper)
    assert isinstance(definition.switch_wrapper, DPCodeBooleanWrapper)

    # A brightness max above 255 selects the V2 remap ranges, so the hex
    # value 007803e803e8 decodes to hue 120, saturation 100%, value 255.
    assert definition.color_data_wrapper.read_device_status(device) == (
        119.33147632311977,
        100.0,
        255.0,
    )


def test_get_default_definition_without_colour_data() -> None:
    """Test a device without any colour_data has no color_data_wrapper."""
    device = create_device("dj_mki13ie507rlry4r.json")
    assert (
        definition := get_default_definition(
            device,
            switch_dpcode="switch_led",
            brightness_dpcode=("bright_value_v2", "bright_value"),
            brightness_max_dpcode=None,
            brightness_min_dpcode=None,
            color_data_dpcode="does_not_exist",
            color_mode_dpcode=None,
            color_temp_dpcode=None,
            fallback_color_data_mode=FallbackColorDataMode.V1,
        )
    )
    assert definition.color_data_wrapper is None
