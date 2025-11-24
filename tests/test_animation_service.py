import pytest
from datetime import datetime
from openscada_lite.modules.animation.service import AnimationService
from openscada_lite.common.models.dtos import TagUpdateMsg, AlarmUpdateMsg
from openscada_lite.common.models.entities import Animation, AnimationEntry
from openscada_lite.common.config.config import Config


class DummyEventBus:
    async def publish(self, event_type, data):
        pass # Test does not require actual publishing

    def subscribe(self, event_type, handler):
        pass # To implement if needed by the test


class DummyModel:
    def update(self, msg):
        pass # To implement if needed by the test


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
