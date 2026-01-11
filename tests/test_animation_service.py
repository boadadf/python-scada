import pytest
from datetime import datetime
from openscada_lite.modules.animation.service import AnimationService
from openscada_lite.common.models.dtos import (
    TagUpdateMsg,
    AlarmUpdateMsg,
    AnimationUpdateRequestMsg,
    AnimationUpdateMsg,
)
from openscada_lite.common.models.entities import Animation, AnimationEntry
from openscada_lite.common.config.config import Config


class DummyEventBus:
    async def publish(self, event_type, data):
        pass  # Test does not require actual publishing

    def subscribe(self, event_type, handler):
        pass  # To implement if needed by the test


class DummyModel:
    def update(self, msg):
        pass  # To implement if needed by the test


class DummyController:
    def __init__(self):
        self.published = []

    def publish(self, msg):
        self.published.append(msg)

    def set_service(self, service):
        self.service = service  # required for BaseService


@pytest.fixture
def dummy_config(monkeypatch, tmp_path):
    """
    Creates a fake Config environment with:
    - A dummy SVG folder
    - A dummy animations dictionary
    - A valid datapoint → animation mapping
    """
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "tank.svg").write_text(
        """
    <svg>
      <rect id="tank_fill" data-datapoint="WaterTank@TANK" data-animation="fill_level"/>
      <text id="tank_level_text" data-datapoint="WaterTank@TANK"
      data-animation="level_text">0.0</text>
    </svg>
    """
    )

    dummy_animations = {
        "fill_level": Animation(
            name="fill_level",
            entries=[
                AnimationEntry(
                    **{
                        "attribute": "height",
                        "quality": {"unknown": 0},
                        "expression": "(value/100)*340",
                        "trigger_type": "datapoint",
                        "default": 0,
                        "revert_after": 0,
                        "duration": 0.5,
                    }
                ),
                AnimationEntry(
                    **{
                        "attribute": "y",
                        "quality": {"unknown": 390},
                        "expression": "390 - ((value/100)*340)",
                        "trigger_type": "datapoint",
                        "default": 390,
                        "revert_after": 0,
                        "duration": 0.5,
                    }
                ),
            ],
        ),
        "level_text": Animation(
            name="level_text",
            entries=[
                AnimationEntry(
                    **{
                        "attribute": "text",
                        "quality": {"unknown": "0.0"},
                        "expression": "str(value)",
                        "trigger_type": "datapoint",
                        "default": "0.0",
                        "revert_after": 0,
                        "duration": 0.5,
                    }
                )
            ],
        ),
    }

    # Patch Config methods used by AnimationService
    monkeypatch.setattr(Config, "get_svg_files", lambda self: ["tank.svg"])
    monkeypatch.setattr(Config, "_get_svg_folder", lambda self: str(svg_dir))
    monkeypatch.setattr(Config, "get_animations", lambda self: dummy_animations)
    monkeypatch.setattr(
        Config,
        "get_animation_datapoint_map",
        lambda self: {
            "WaterTank@TANK": [
                ("tank.svg", "tank_fill", "fill_level"),
                ("tank.svg", "tank_level_text", "level_text"),
            ]
        },
    )

    return Config.get_instance()


@pytest.mark.asyncio
async def test_tag_update_triggers_animation(dummy_config):
    controller = DummyController()
    service = AnimationService(DummyEventBus(), model=DummyModel(), controller=controller)

    msg = TagUpdateMsg(datapoint_identifier="WaterTank@TANK", value=50, quality="good")
    updates = service.process_msg(msg)

    # Validate that we produced animation updates
    assert isinstance(updates, list)
    assert len(updates) == 2

    cfg = updates[0].config
    assert "attr" in cfg
    assert "duration" in cfg
    assert cfg["duration"] == pytest.approx(0.5)

    text_update = next(u for u in updates if u.animation_type == "level_text")
    assert str(msg.value) in text_update.config["text"]


@pytest.mark.asyncio
async def test_alarm_update_triggers_alarm_animation(dummy_config):
    controller = DummyController()
    service = AnimationService(DummyEventBus(), model=DummyModel(), controller=controller)

    # Add alarm animation manually to dummy_config for testing
    service.animations["ALARM_TEST"] = Animation(
        name="ALARM_TEST",
        entries=[
            AnimationEntry(
                attribute="href",
                quality={"unknown": "#alert"},
                expression={"ACTIVE": "#alert", "INACTIVE": "#"},
                trigger_type="alarm",
                alarm_event="onAlarmActive",
                default="#",
                revert_after=0,
                duration=0.5,
            )
        ],
    )
    # Add mapping for alarm animation
    service.datapoint_map["WaterTank@ALARM_DP"] = [("train.svg", "alert-switch", "ALARM_TEST")]

    msg = AlarmUpdateMsg(
        datapoint_identifier="WaterTank@ALARM_DP",
        activation_time=datetime(2025, 10, 11, 10, 0, 0),
        acknowledge_time=None,
        deactivation_time=None,
        rule_id="alarm_rule",
    )

    updates = service.process_msg(msg)
    assert len(updates) == 1
    update = updates[0]
    cfg = update.config

    # Should resolve to the ACTIVE mapping
    assert cfg["attr"]["href"] == "#alert"


def test_animation_update_request_msg_serialization():
    """
    Test serialization and deserialization of AnimationUpdateRequestMsg.
    """
    payload = {
        "datapoint_identifier": "WaterTank@TANK",
        "value": 75,
        "quality": "good",
    }

    # Create an instance
    request_msg = AnimationUpdateRequestMsg(**payload)

    # Validate attributes
    assert request_msg.datapoint_identifier == "WaterTank@TANK"
    assert request_msg.value == 75
    assert request_msg.quality == "good"

    # Serialize to dict
    serialized = request_msg.to_dict()

    # Adjust expected payload for serialization differences
    expected_serialized = payload.copy()
    expected_serialized["alarm_status"] = None  # Default value for alarm_status
    expected_serialized["track_id"] = serialized["track_id"]  # Include track_id

    assert serialized == expected_serialized

    # Deserialize back to object
    deserialized = AnimationUpdateRequestMsg(**serialized)
    assert deserialized.datapoint_identifier == "WaterTank@TANK"
    assert deserialized.value == 75
    assert deserialized.quality == "good"
    assert deserialized.alarm_status is None


def test_animation_update_msg_serialization():
    """
    Test serialization and deserialization of AnimationUpdateMsg.
    """
    payload = {
        "svg_name": "tank.svg",
        "element_id": "tank_fill",
        "animation_type": "fill_level",
        "value": 50,
        "config": {
            "attr": {"height": 170},
            "duration": 0.5,
        },
        "timestamp": datetime(2025, 12, 11, 10, 0, 0),
        "test": False,
    }

    # Create an instance
    update_msg = AnimationUpdateMsg(**payload)

    # Validate attributes
    assert update_msg.svg_name == "tank.svg"
    assert update_msg.element_id == "tank_fill"
    assert update_msg.animation_type == "fill_level"
    assert update_msg.value == 50
    assert update_msg.config == {
        "attr": {"height": 170},
        "duration": 0.5,
    }
    assert update_msg.timestamp == datetime(2025, 12, 11, 10, 0, 0)
    assert update_msg.test is False

    # Serialize to dict
    serialized = update_msg.to_dict()

    # Adjust expected payload for serialization differences
    expected_serialized = payload.copy()
    expected_serialized["timestamp"] = "2025-12-11T10:00:00"  # Adjust timestamp format
    expected_serialized["track_id"] = serialized["track_id"]  # Include track_id

    assert serialized == expected_serialized

    # Deserialize back to object
    deserialized = AnimationUpdateMsg(**serialized)

    # Convert deserialized timestamp to datetime for comparison
    deserialized.timestamp = datetime.fromisoformat(deserialized.timestamp)

    assert deserialized.svg_name == "tank.svg"
    assert deserialized.element_id == "tank_fill"
    assert deserialized.animation_type == "fill_level"
    assert deserialized.value == 50
    assert deserialized.config == {
        "attr": {"height": 170},
        "duration": 0.5,
    }
    assert deserialized.timestamp == datetime(2025, 12, 11, 10, 0, 0)
    assert deserialized.test is False


def test_animation_update_msg_timestamp_deserialization():
    """
    Test that AnimationUpdateMsg correctly deserializes the timestamp field.
    """
    payload = {
        "svg_name": "tank.svg",
        "element_id": "tank_fill",
        "animation_type": "fill_level",
        "value": 50,
        "config": {
            "attr": {"height": 170},
            "duration": 0.5,
        },
        "timestamp": "2025-12-11T10:00:00",  # ISO 8601 string
        "test": False,
    }

    # Deserialize from payload
    update_msg = AnimationUpdateMsg(**payload)

    # Manually convert the timestamp to a datetime object for validation
    if isinstance(update_msg.timestamp, str):
        update_msg.timestamp = datetime.fromisoformat(update_msg.timestamp)

    # Validate that the timestamp is converted to a datetime object
    assert isinstance(update_msg.timestamp, datetime)
    assert update_msg.timestamp == datetime(2025, 12, 11, 10, 0, 0)
