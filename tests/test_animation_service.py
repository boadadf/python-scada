import pytest
from openscada_lite.modules.animation.service import AnimationService
from openscada_lite.common.models.dtos import TagUpdateMsg, AnimationUpdateMsg
from openscada_lite.common.config.config import Config

class DummyEventBus:
    async def publish(self, event_type, data):
        pass
    def subscribe(self, event_type, handler):
        pass  # No-op for testing

@pytest.fixture
def dummy_config(monkeypatch, tmp_path):
    # Create a dummy svg folder and file
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "tank.svg").write_text("""
    <svg>
      <rect id="tank_fill" data-datapoint="Server1@TANK" data-animation="fill_level"/>
      <text id="tank_level_text" data-datapoint="Server1@TANK" data-animation="level_text">0.0</text>
    </svg>
    """)
    # Patch Config to use this folder and provide animation config
    monkeypatch.setattr(Config, "get_svg_files", lambda self: ["tank.svg"])
    monkeypatch.setattr(Config, "_get_svg_folder", lambda self: str(svg_dir))
    monkeypatch.setattr(Config, "get_animation_config", lambda self: {
        "fill_level": {
            "type": "height_y",
            "maxHeight": 340,
            "baseY": 390,
            "duration": 0.5
        },
        "level_text": {
            "type": "text",
            "duration": 0.2
        }
    })
    monkeypatch.setattr(Config, "get_datapoint_map", lambda self: {
        "Server1@TANK": [
            ("tank.svg", "tank_fill", "fill_level"),
            ("tank.svg", "tank_level_text", "level_text")
        ]
    })
    return Config.get_instance()

def test_process_msg_generates_animation_updates(dummy_config):
    class DummyEventBus:
        async def publish(self, event_type, data):
            pass
        def subscribe(self, event_type, handler):
            pass  # No-op for testing

    service = AnimationService(DummyEventBus(), model=None, controller=None)
    msg = TagUpdateMsg(datapoint_identifier="Server1@TANK", value=42)
    updates = service.process_msg(msg)
    assert isinstance(updates, list)
    assert len(updates) == 2
    svg_names = {u.svg_name for u in updates}
    assert "tank.svg" in svg_names
    anim_types = {u.animation_type for u in updates}
    assert "fill_level" in anim_types
    assert "level_text" in anim_types
    text_update = next(u for u in updates if u.animation_type == "level_text")
    assert str(msg.value) in str(text_update.config.get("text", ""))
