# tank_test_driver.py
import datetime
from openscada_lite.core.communications.drivers.test.test_driver import TestDriver

class TankTestDriver(TestDriver):
    async def _simulate_values(self):
        now = datetime.datetime.now()

        # current states
        level_tag = self._tags.get("TANK")
        pump_tag = self._tags.get("PUMP")
        door_tag = self._tags.get("DOOR")

        if not (level_tag and pump_tag and door_tag):
            print("[SIM] Missing tag(s):", {
                "TANK": bool(level_tag),
                "PUMP": bool(pump_tag),
                "DOOR": bool(door_tag)
            })
            return

        try:
            level = float(level_tag.value) if level_tag.value not in (None, "") else 0.0
        except Exception as e:
            print(f"[SIM] Error parsing level value: {level_tag.value} ({e})")
            level = 0.0
        pump = pump_tag.value if pump_tag.value else "CLOSED"
        door = door_tag.value if door_tag.value else "CLOSED"

        print(f"[SIM] Before: level={level}, pump={pump}, door={door}")

        # --- compute next level ---
        if pump == "OPENED":
            level += 1.0
        if door == "OPENED":
            level -= 2.0

        # clamp between 0 and 100
        level = max(0.0, min(100.0, level))
        print(f"[SIM] After: level={level}")

        level_tag.value = level
        level_tag.timestamp = now