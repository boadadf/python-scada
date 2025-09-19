import os
import pytest

from openscada_lite.common.config.config import Config

@pytest.fixture
def sample_config_file():
    # Path to test_config.json in the tests directory
    return os.path.join(os.path.dirname(__file__), "test_config.json")

def test_get_instance_returns_singleton(sample_config_file):
    c1 = Config.get_instance(sample_config_file)
    c2 = Config.get_instance(sample_config_file)
    assert c1 is c2

def test_get_drivers(sample_config_file):
    config = Config(sample_config_file)
    drivers = config.get_drivers()
    assert isinstance(drivers, list)
    assert drivers[0]["name"] == "Server1"
    assert drivers[1]["name"] == "Server2"
    assert any(dp["name"] == "TANK" for dp in drivers[0]["datapoints"])
    assert any(dp["name"] == "TEMPERATURE" for dp in drivers[1]["datapoints"])

def test_get_rules(sample_config_file):
    config = Config(sample_config_file)
    rules = config.get_rules()
    assert isinstance(rules, list)
    assert any(r.rule_id == "close_valve_if_high" for r in rules)
    assert any(r.rule_id == "door_open_alarm" for r in rules)

def test_get_allowed_tags(sample_config_file):
    config = Config(sample_config_file)
    tags = config.get_allowed_datapoint_identifiers()
    # Should include all tags in the config
    for tag in [
        "Server1@TANK",
        "Server1@PUMP",
        "Server1@DOOR",
        "Server2@VALVE",
        "Server2@PRESSURE",
        "Server2@TEMPERATURE"
    ]:
        assert tag in tags