import os
import json
from openscada_lite.common.models.entities import Rule

class Config:
    _instance = None

    def __init__(self, config_file: str):
        with open(config_file) as f:
            self._config = json.load(f)

    @classmethod
    def get_instance(cls, config_file=None):
        if cls._instance is None:
            if config_file is None:
                config_file = os.environ.get("SCADA_CONFIG_FILE", "config/system_config.json")
            cls._instance = cls(config_file)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    def get_drivers(self):
        return self._config.get("drivers", [])

    def get_types(self):
        return self._config.get("dp_types", [])

    def get_rules(self):
        rules = self._config.get("rules", [])
        return [Rule(**r) for r in rules]
    
    def get_datapoint_types_for_driver(self, driver_name: str, types: dict) -> dict:
        """
        Returns a dict {tag_name: dp_type_dict} for the given driver.
        """
        for drv in self.get_drivers():
            if drv["name"] == driver_name:
                return {
                    dp["name"]: types.get(dp["type"])
                    for dp in drv.get("datapoints", [])
                }
        return {}
    
    def get_allowed_datapoint_identifiers(self):
        """Return fully qualified tag_ids: driver_name@datapoint_identifier"""
        datapoint_identifiers = []
        for driver in self.get_drivers():
            driver_name = driver["name"]
            for datapoint_identifier in driver.get("datapoints", []):
                datapoint_identifiers.append(f"{driver_name}@{datapoint_identifier['name']}")
        return datapoint_identifiers

    def get_allowed_command_identifiers(self):
        """Return fully qualified tag_ids: driver_name@datapoint_identifier"""
        datapoint_identifiers = []
        for driver in self.get_drivers():
            driver_name = driver["name"]
            for datapoint_identifier in driver.get("command_datapoints", []):
                datapoint_identifiers.append(f"{driver_name}@{datapoint_identifier['name']}")
        return datapoint_identifiers

    def validate_value(self, datapoint_identifier: str, value) -> bool:
        """
        Validate if the value is valid for the given datapoint_identifier.
        Supports enum and float types as defined in dp_types.
        """
        # Find the driver and datapoint type
        for driver in self.get_drivers():
            driver_name = driver["name"]
            for dp in driver.get("datapoints", []) + driver.get("command_datapoints", []):
                if f"{driver_name}@{dp['name']}" == datapoint_identifier:
                    dp_type_name = dp.get("type")
                    dp_types = self.get_types()
                    dp_type = dp_types.get(dp_type_name)
                    if not dp_type:
                        return False
                    # Float type validation
                    if dp_type["type"] == "float":
                        try:
                            v = float(value)
                        except (ValueError, TypeError):
                            return False
                        if "min" in dp_type and v < dp_type["min"]:
                            return False
                        if "max" in dp_type and v > dp_type["max"]:
                            return False
                        return True
                    # Enum type validation
                    elif dp_type["type"] == "enum":
                        return value in dp_type.get("values", [])
                    # Add more type checks as needed
                    return True
        # If not found, invalid
        return False
