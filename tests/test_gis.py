import pytest
from unittest.mock import MagicMock, patch
from openscada_lite.modules.gis.service import GisService
from openscada_lite.common.models.dtos import GisUpdateMsg, TagUpdateMsg, AlarmUpdateMsg


@pytest.fixture(scope="function")
@patch("openscada_lite.modules.gis.service.Config")
def gis_service(mock_config):
    """Fixture for the GIS service."""
    # Mock the configuration to return test data
    mock_config.get_instance.return_value.get_gis_icons.return_value = [
        {
            "id": "icon1",
            "latitude": 0.0,
            "longitude": 0.0,
            "icon": "icon1.png",
            "datapoint": "dp1",
        },
        {
            "id": "icon2",
            "latitude": 1.0,
            "longitude": 1.0,
            "icon": "icon2.png",
            "rule_id": "rule1",
            "alarm": {"ACTIVE": "active_icon.png", "INACTIVE": "inactive_icon.png"},
        },
    ]

    event_bus = MagicMock()
    model = MagicMock()
    controller = MagicMock()

    # Configure the model.get method to return a valid GisUpdateMsg
    def mock_get(icon_id):
        if icon_id == "icon1":
            return GisUpdateMsg(
                track_id="test-track-id-1",
                id="icon1",
                latitude=0.0,
                longitude=0.0,
                icon="icon1.png",
                extra={"datapoint-value": None},
            )
        elif icon_id == "icon2":
            return GisUpdateMsg(
                track_id="test-track-id-2",
                id="icon2",
                latitude=1.0,
                longitude=1.0,
                icon="icon2.png",
                extra={"datapoint-value": None},
            )
        return None

    model.get.side_effect = mock_get

    return GisService(event_bus, model, controller)


def test_process_tag_update_match(gis_service):
    """Test _process_tag_update when the datapoint matches."""
    tag_msg = TagUpdateMsg(
        datapoint_identifier="dp1",
        value=1,
        quality="good",
        timestamp="2025-11-23T12:00:00Z",
    )
    gis_update = gis_service._process_tag_update(tag_msg, gis_service.gis_icons_config[0])
    assert gis_update is not None
    assert isinstance(gis_update, GisUpdateMsg)
    assert gis_update.id == "icon1"
    assert gis_update.icon == "icon1.png"


def test_process_tag_update_no_match(gis_service):
    """Test _process_tag_update when the datapoint does not match."""
    tag_msg = TagUpdateMsg(
        datapoint_identifier="nonexistent_dp",
        value=1,
        quality="good",
        timestamp="2025-11-23T12:00:00Z",
    )
    gis_update = gis_service._process_tag_update(tag_msg, gis_service.gis_icons_config[0])
    assert gis_update is None


def test_process_tag_update_with_states(gis_service):
    """Test _process_tag_update when states are defined."""
    gis_service.gis_icons_config[0]["states"] = {"1": "state_icon.png"}
    tag_msg = TagUpdateMsg(
        datapoint_identifier="dp1",
        value=1,
        quality="good",
        timestamp="2025-11-23T12:00:00Z",
    )
    gis_update = gis_service._process_tag_update(tag_msg, gis_service.gis_icons_config[0])
    assert gis_update is not None
    assert gis_update.icon == "state_icon.png"


def test_process_alarm_update_match(gis_service):
    """Test _process_alarm_update when the rule_id matches."""
    alarm_msg = AlarmUpdateMsg(
        datapoint_identifier="dp1",
        rule_id="rule1",
        activation_time="2025-11-23T12:00:00Z",
        acknowledge_time=None,
        deactivation_time=None,
    )

    gis_update = gis_service._process_alarm_update(alarm_msg, gis_service.gis_icons_config[1])
    assert gis_update is not None
    assert isinstance(gis_update, GisUpdateMsg)
    assert gis_update.id == "icon2"
    # Expect the icon to be updated to "active_icon.png" based on the alarm state
    assert gis_update.icon == "active_icon.png"


def test_process_alarm_update_no_match(gis_service):
    """Test _process_alarm_update when the rule_id does not match."""
    alarm_msg = AlarmUpdateMsg(
        datapoint_identifier="dp1",
        rule_id="nonexistent_rule",
        activation_time="2025-11-23T12:00:00Z",
        acknowledge_time=None,
        deactivation_time=None,
    )
    gis_update = gis_service._process_alarm_update(alarm_msg, gis_service.gis_icons_config[1])
    assert gis_update is None


def test_should_accept_update_tag(gis_service):
    """Test should_accept_update for TagUpdateMsg."""
    tag_msg = TagUpdateMsg(
        datapoint_identifier="dp1",
        value=1,
        quality="good",
        timestamp="2025-11-23T12:00:00Z",
    )
    assert gis_service.should_accept_update(tag_msg) is True


def test_should_accept_update_alarm(gis_service):
    """Test should_accept_update for AlarmUpdateMsg."""
    alarm_msg = AlarmUpdateMsg(
        datapoint_identifier="dp1",
        rule_id="rule1",
        activation_time="2025-11-23T12:00:00Z",
        acknowledge_time=None,
        deactivation_time=None,
    )
    assert gis_service.should_accept_update(alarm_msg) is True


def test_should_accept_update_no_match(gis_service):
    """Test should_accept_update when no match is found."""
    tag_msg = TagUpdateMsg(
        datapoint_identifier="nonexistent_dp",
        value=1,
        quality="good",
        timestamp="2025-11-23T12:00:00Z",
    )
    assert gis_service.should_accept_update(tag_msg) is False
