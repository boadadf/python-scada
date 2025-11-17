# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

# tank_test_driver.py
import datetime
from openscada_lite.modules.communication.drivers.test.test_driver import TestDriver


class TankTestDriver(TestDriver):
    def _simulate_values(self):
        now = datetime.datetime.now()

        # current states
        level_tag = self._tags.get("TANK")
        pump_tag = self._tags.get("PUMP")
        door_tag = self._tags.get("DOOR")

        if not (level_tag and pump_tag and door_tag):
            print(
                "[SIM] Missing tag(s):",
                {
                    "TANK": bool(level_tag),
                    "PUMP": bool(pump_tag),
                    "DOOR": bool(door_tag),
                },
            )
            return

        try:
            level = float(level_tag.value) if level_tag.value not in (None, "") else 0.0
        except Exception as e:
            level = 0.0
        pump = pump_tag.value if pump_tag.value else "CLOSED"
        door = door_tag.value if door_tag.value else "CLOSED"

        # --- compute next level ---
        if pump == "OPENED":
            level += 1.0
        if door == "OPENED":
            level -= 2.0

        # clamp between 0 and 100
        level = max(0.0, min(100.0, level))

        level_tag.value = level
        level_tag.timestamp = now
