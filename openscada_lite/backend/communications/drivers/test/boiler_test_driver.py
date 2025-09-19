# tank_test_driver.py
import asyncio
import datetime
import random
from openscada_lite.backend.communications.drivers.test.test_driver import TestDriver


class BoilerTestDriver(TestDriver):
    async def _simulate_values(self):
            now = datetime.datetime.now()

            valve_tag = self._tags["VALVE"]
            pressure_tag = self._tags["PRESSURE"]
            temp_tag = self._tags["TEMPERATURE"]
            heater_tag = self._tags["HEATER"]

            valve = valve_tag.value or "CLOSED"
            heater = heater_tag.value or "OFF"

            pressure = float(pressure_tag.value or 50.0)
            temp = float(temp_tag.value or 120.0)

            # --- simulate pressure ---
            if heater == "OPEN" or heater == "ON":   # depending on enum
                if valve == "CLOSED":
                    pressure += 2.0   # heater builds pressure fast if sealed
                else:
                    pressure += 0.5   # heater builds less if valve is open
            else:
                pressure -= 1.0       # cools down, pressure drops

            # clamp between 0–200
            pressure = max(0.0, min(200.0, pressure))
            pressure_tag.value = pressure
            pressure_tag.timestamp = now

            # --- simulate temperature ---
            if heater == "OPEN" or heater == "ON":
                temp += 1.0
            else:
                temp -= 0.5

            # clamp between 100–150
            temp = max(100.0, min(150.0, temp))
            temp_tag.value = temp
            temp_tag.timestamp = now
