import os
import pytest

from common.config.config import Config

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
    assert "TANK1_LEVEL" in drivers[0]["datapoints"]
    assert "TEMPERATURE" in drivers[1]["datapoints"]

def test_get_rules(sample_config_file):
    config = Config(sample_config_file)
    rules = config.get_rules()
    assert isinstance(rules, list)
    assert any(r.rule_id == "close_valve_if_high" for r in rules)
    assert any(r.rule_id == "door_open_alarm" for r in rules)

def test_get_allowed_tags(sample_config_file):
    config = Config(sample_config_file)
    tags = config.get_allowed_tags()
    # Should include all tags in the config
    for tag in [
        "Server1@TANK1_LEVEL",
        "Server1@PUMP1_STATUS",
        "Server1@DOOR1_OPEN",
        "Server2@VALVE1_POS",
        "Server2@PRESSURE",
        "Server2@TEMPERATURE"
    ]:
        assert tag in tags