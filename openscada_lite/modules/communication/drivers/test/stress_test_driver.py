import asyncio
import datetime
from openscada_lite.modules.communication.drivers.test.test_driver import TestDriver

class StressTestDriver(TestDriver):
    """
    A stress/performance test driver that toggles 250 BOOL datapoints sequentially.
    Each datapoint is toggled TRUE/FALSE with a configurable delay.
    """

    def __init__(self, server_name="StressTest", toggle_delay=0.02):
        super().__init__(server_name)
        self._toggle_delay = toggle_delay

    def initialize(self, config: dict):
        # Allow setting toggle_delay from config
        if "toggle_delay" in config:
            self._toggle_delay = float(config["toggle_delay"])

    async def _simulate_values(self):
        """
        Sequentially toggle all datapoints TRUE/FALSE with a delay.
        """
        now = datetime.datetime.now()
        for tag in self._tags.values():
            tag.value = "TRUE" if tag.value == "FALSE" else "FALSE"
            tag.timestamp = now
            await self._publish_value(tag)
            await asyncio.sleep(self._toggle_delay)