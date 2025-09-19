# tank_test_driver.py
import asyncio
import datetime
import random
from openscada_lite.backend.communications.drivers.test.test_driver import TestDriver

class TankTestDriver(TestDriver):
    async def _simulate_values(self):
            now = datetime.datetime.now()

            # current states
            level_tag = self._tags["TANK"]
            pump_tag = self._tags["PUMP"]
            door_tag = self._tags["DOOR"]

            level = float(level_tag.value or 0.0)
            pump = pump_tag.value or "CLOSED"
            door = door_tag.value or "CLOSED"

            # --- compute next level ---
            if pump == "OPEN": 
                level += 1.0
            if door == "OPEN":
                level -= 2.0

            # clamp between 0 and 100
            level = max(0.0, min(100.0, level))
            level_tag.value = level
            level_tag.timestamp = now