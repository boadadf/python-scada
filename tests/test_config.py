import os
import pytest

from openscada_lite.common.config.config import Config

@pytest.fixture
def sample_config_file():
    # Path to test_config.json in the tests directory
    return os.path.join(os.path.dirname(__file__), "test_config.json")


def test_validate_value(sample_config_file):
    config = Config.get_instance(sample_config_file)

    # Float type: valid and invalid
    assert config.validate_value("WaterTank@TANK", 50.0) is True  # within range
    assert config.validate_value("WaterTank@TANK", 0.0) is True   # min
    assert config.validate_value("WaterTank@TANK", 100.0) is True # max
    assert config.validate_value("WaterTank@TANK", -1) is False   # below min
    assert config.validate_value("WaterTank@TANK", 101) is False  # above max
    assert config.validate_value("WaterTank@TANK", "not_a_float") is False

    # Enum type: valid and invalid
    assert config.validate_value("WaterTank@PUMP", "OPENED") is True
    assert config.validate_value("WaterTank@PUMP", "CLOSED") is True
    assert config.validate_value("WaterTank@PUMP", "INVALID") is False

    # Unknown tag
    assert config.validate_value("ServerX@UNKNOWN", 42) is False

def test_get_instance_returns_singleton(sample_config_file):
    c1 = Config.get_instance(sample_config_file)
    c2 = Config.get_instance(sample_config_file)
    assert c1 is c2

def test_get_drivers(sample_config_file):
    config = Config.get_instance(sample_config_file)
    drivers = config.get_drivers()
    assert isinstance(drivers, list)
    assert drivers[0]["name"] == "WaterTank"
    assert drivers[1]["name"] == "Server2"
    assert any(dp["name"] == "TANK" for dp in drivers[0]["datapoints"])
    assert any(dp["name"] == "TEMPERATURE" for dp in drivers[1]["datapoints"])

def test_get_rules(sample_config_file):
    config = Config.get_instance(sample_config_file)
    rules = config.get_rules()
    assert isinstance(rules, list)
    assert any(r.rule_id == "close_valve_if_high" for r in rules)
    assert any(r.rule_id == "door_open_alarm" for r in rules)

def test_get_allowed_tags(sample_config_file):
    config = Config.get_instance(sample_config_file)
    tags = config.get_allowed_datapoint_identifiers()
    # Should include all tags in the config
    for tag in [
        "WaterTank@TANK",
        "WaterTank@PUMP",
        "WaterTank@DOOR",
        "Server2@VALVE",
        "Server2@PRESSURE",
        "Server2@TEMPERATURE"
    ]:
        assert tag in tags