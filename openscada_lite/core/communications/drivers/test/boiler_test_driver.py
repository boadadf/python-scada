# tank_test_driver.py
import datetime
from openscada_lite.core.communications.drivers.test.test_driver import TestDriver


class BoilerTestDriver(TestDriver):
    async def _simulate_values(self):
        now = datetime.datetime.now()

        # Get tags safely
        valve_tag = self._tags.get("VALVE")
        pressure_tag = self._tags.get("PRESSURE")
        temp_tag = self._tags.get("TEMPERATURE")
        heater_tag = self._tags.get("HEATER")

        if not (valve_tag and pressure_tag and temp_tag and heater_tag):
            print("[SIM] Missing tag(s):", {
                "VALVE": bool(valve_tag),
                "PRESSURE": bool(pressure_tag),
                "TEMPERATURE": bool(temp_tag),
                "HEATER": bool(heater_tag)
            })
            return

        valve = valve_tag.value if valve_tag.value else "CLOSED"
        heater = heater_tag.value if heater_tag.value else "CLOSED"

        try:
            pressure = float(pressure_tag.value) if pressure_tag.value not in (None, "") else 50.0
        except Exception as e:
            print(f"[SIM] Error parsing pressure value: {pressure_tag.value} ({e})")
            pressure = 50.0

        try:
            temp = float(temp_tag.value) if temp_tag.value not in (None, "") else 120.0
        except Exception as e:
            print(f"[SIM] Error parsing temperature value: {temp_tag.value} ({e})")
            temp = 120.0

        print(f"[SIM] Before: pressure={pressure}, temp={temp}, valve={valve}, heater={heater}")

        # --- simulate pressure ---
        if heater == "OPENED":
            if valve == "CLOSED":
                pressure += 2.0
            else:
                pressure += 0.5
        else:
            pressure -= 1.0

        # clamp between 0–200
        pressure = max(0.0, min(200.0, pressure))
        pressure_tag.value = pressure
        pressure_tag.timestamp = now

        # --- simulate temperature ---
        if heater == "OPENED":
            temp += 1.0
        else:
            temp -= 0.5

        # clamp between 100–150
        temp = max(100.0, min(150.0, temp))
        temp_tag.value = temp
        temp_tag.timestamp = now

        print(f"[SIM] After: pressure={pressure}, temp={temp}")
