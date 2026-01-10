import asyncio
import json
import pytest

from types import SimpleNamespace

from openscada_lite.common.models.dtos import SendCommandMsg, DriverConnectStatus, CommandFeedbackMsg
import openscada_lite.modules.communication.drivers.mqtt_tasmota_driver as mtd
from openscada_lite.modules.communication.drivers.mqtt_tasmota_driver import MQTTTasmotaRelayDriver


class FakeMQTTMessage:
    def __init__(self, topic: str, payload: bytes):
        self.topic = topic
        self.payload = payload


class FakeClient:
    def __init__(self, client_id=None):
        self.client_id = client_id
        self.subscriptions = []
        self.published = []
        # Callbacks assigned by driver
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None

    def username_pw_set(self, username, password=None):
        pass

    def connect(self, host, port=1883, keepalive=60):
        # No real network
        return 0

    def loop_start(self):
        pass

    def loop_stop(self):
        pass

    def disconnect(self):
        pass

    def subscribe(self, topic):
        self.subscriptions.append(topic)

    def publish(self, topic, payload, qos=1):
        self.published.append((topic, payload, qos))


@pytest.mark.asyncio
async def test_mqtt_connect_emits_status_and_subscribes(monkeypatch):
    # Patch the mqtt.Client used inside the driver module
    # Patch the internal mqtt symbol to a namespace exposing Client
    monkeypatch.setattr(mtd, "mqtt", SimpleNamespace(Client=FakeClient))

    driver = MQTTTasmotaRelayDriver("XmasServer")
    driver.initialize(
        {
            "host": "localhost",
            "port": 1883,
            "client_id": "client-1",
            "device_topic": "xmas",
            "relay_mapping": {"RELAY_1": "POWER1", "RELAY_2": "POWER2"},
            "subscriptions": [
                {"topic": "stat/{device}/POWER+", "type": "status"},
                {"topic": "stat/{device}/RESULT", "type": "feedback"},
            ],
            "publish": {"command": "cmnd/{device}/{power}"},
        }
    )

    # Capture emitted status
    status_events = []
    ev = asyncio.Event()

    async def status_cb(msg: DriverConnectStatus):
        status_events.append(msg)
        ev.set()

    driver.register_communication_status_listener(status_cb)
    await driver.connect()

    # Simulate on_connect (rc=0) with the driver's client
    driver._on_connect(driver._client, None, None, 0)

    await asyncio.wait_for(ev.wait(), timeout=1.0)

    assert status_events and status_events[0].status == "online"
    subs = driver._client.subscriptions
    assert f"stat/xmas/POWER1" in subs
    assert f"stat/xmas/POWER2" in subs
    assert f"stat/xmas/RESULT" in subs


@pytest.mark.asyncio
async def test_mqtt_toggle_publishes_opposite_and_feedback(monkeypatch):
    monkeypatch.setattr(mtd, "mqtt", SimpleNamespace(Client=FakeClient))

    driver = MQTTTasmotaRelayDriver("XmasServer")
    driver.initialize(
        {
            "host": "localhost",
            "port": 1883,
            "client_id": "client-2",
            "device_topic": "xmas",
            "relay_mapping": {"RELAY_1": "POWER1"},
            "subscriptions": [
                {"topic": "stat/{device}/POWER+", "type": "status"},
                {"topic": "stat/{device}/RESULT", "type": "feedback"},
            ],
            "publish": {"command": "cmnd/{device}/{power}"},
            "command_timeout": 2,
        }
    )

    # Async feedback capture
    feedback_events = []
    fb_ev = asyncio.Event()

    async def feedback_cb(msg: CommandFeedbackMsg):
        feedback_events.append(msg)
        fb_ev.set()

    driver.register_command_feedback(feedback_cb)

    # Value listener not strictly needed here
    async def value_cb(_):
        return None

    driver.register_value_listener(value_cb)
    await driver.connect()

    # Seed current status to ON via POWER1 message
    msg_on = FakeMQTTMessage("stat/xmas/POWER1", b"ON")
    driver._on_message(driver._client, None, msg_on)

    # Send TOGGLE command; should publish OFF
    await driver.send_command(SendCommandMsg("cmd-1", "XmasServer@RELAY_1_CMD", "TOGGLE"))
    topic, payload, qos = driver._client.published[-1]
    assert topic == "cmnd/xmas/POWER1"
    assert payload == "OFF"
    assert qos == 1

    # Simulate RESULT to generate OK feedback
    msg_result = FakeMQTTMessage("stat/xmas/RESULT", json.dumps({"POWER1": "OFF"}).encode())
    driver._on_message(driver._client, None, msg_result)

    await asyncio.wait_for(fb_ev.wait(), timeout=1.0)

    assert feedback_events, "Expected feedback event after RESULT"
    fb = feedback_events[0]
    assert fb.command_id == "cmd-1"
    assert fb.datapoint_identifier == "XmasServer@RELAY_1_CMD"
    assert fb.feedback == "OK"
    assert fb.value == "OFF"


@pytest.mark.asyncio
async def test_mqtt_toggle_unknown_state_sends_toggle(monkeypatch):
    monkeypatch.setattr(mtd, "mqtt", SimpleNamespace(Client=FakeClient))

    driver = MQTTTasmotaRelayDriver("XmasServer")
    driver.initialize(
        {
            "host": "localhost",
            "port": 1883,
            "client_id": "client-3",
            "device_topic": "xmas",
            "relay_mapping": {"RELAY_2": "POWER2"},
            "subscriptions": [],
            "publish": {"command": "cmnd/{device}/{power}"},
        }
    )

    await driver.connect()

    # Without prior status, toggle should send 'ON' (default)
    await driver.send_command(SendCommandMsg("cmd-2", "XmasServer@RELAY_2_CMD", "TOGGLE"))
    topic, payload, qos = driver._client.published[-1]
    assert topic == "cmnd/xmas/POWER2"
    assert payload == "ON"
    assert qos == 1
