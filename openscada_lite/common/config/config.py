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

import os
import json
import xml.etree.ElementTree as ET
from openscada_lite.common.models.entities import Animation, AnimationEntry, Rule


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Use Config.get_instance() instead of direct instantiation.")
        return super().__new__(cls)

    def __init__(self, config_path: str):
        # config_path is the directory containing system_config.json
        if os.path.isdir(config_path):
            config_file = os.path.join(config_path, "system_config.json")
        else:
            # If a file is given, use it directly
            config_file = config_path
        with open(config_file) as f:
            self._config = json.load(f)
        self._config_path = config_path  # Save the config directory path for later use

    @classmethod
    def get_instance(cls, config_path=None):
        if cls._instance is None:
            if config_path is None:
                config_path = os.environ.get("SCADA_CONFIG_PATH", "config")
            cls._instance = cls(config_path)
        return cls._instance

    def load_system_config(self):
        """Return the loaded system config dict."""
        return self._config

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
                return {dp["name"]: types.get(dp["type"]) for dp in drv.get("datapoints", [])}
        return {}

    def get_allowed_datapoint_identifiers(self):
        """Return fully qualified tag_ids: driver_name@datapoint_identifier"""
        datapoint_identifiers = []
        for driver in self.get_drivers():
            driver_name = driver["name"]
            for datapoint_identifier in driver.get("datapoints", []):
                # Check if the datapoint_identifier is already fully qualified
                # Fully qualified dps are handled by its own driver
                if "@" not in datapoint_identifier["name"]:
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

    def get_default_value(self, datapoint_identifier: str):
        """
        Returns the default value for a given datapoint_identifier, e.g. 'WaterTank@TANK'.
        """
        # Split into driver and datapoint name
        if "@" not in datapoint_identifier:
            return None
        driver_name, dp_name = datapoint_identifier.split("@", 1)
        # Find the driver
        for driver in self._config.get("drivers", []):
            if driver.get("name") == driver_name:
                # Search in datapoints
                for dp in driver.get("datapoints", []):
                    if dp.get("name") == dp_name:
                        dp_type = dp.get("type")
                        # Get default from dp_types
                        type_info = self._config.get("dp_types", {}).get(dp_type, {})
                        return type_info.get("default")
                # Search in command_datapoints if not found
                for dp in driver.get("command_datapoints", []):
                    if dp.get("name") == dp_name:
                        dp_type = dp.get("type")
                        type_info = self._config.get("dp_types", {}).get(dp_type, {})
                        return type_info.get("default")
        return None

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

    def get_module_config(self, module_name: str) -> dict:
        """
        Returns the config dict for a module by name, or an empty dict if not found.
        """
        modules = self._config.get("modules", [])
        for module in modules:
            if isinstance(module, dict) and module.get("name") == module_name:
                return module.get("config", {})
        return {}

    def get_animations(self):
        animations_dict = self._config.get("animations", {})
        return {
            name: Animation(name=name, entries=[AnimationEntry(**entry) for entry in entries])
            for name, entries in animations_dict.items()
        }

    def get_streams(self):
        """
        Returns the list of streams from the configuration.
        """
        return self._config.get("streams", [])

    def _get_svg_folder(self) -> str:
        """
        Internal: Returns the SVG folder path from config or defaults to './svg'.
        """
        config_dir = (
            os.path.dirname(self._config_path) if hasattr(self, "_config_path") else os.getcwd()
        )
        svg_folder = self._config.get("svg_folder", None)
        if svg_folder:
            return os.path.join(config_dir, svg_folder)
        return os.path.join(config_dir, "svg")

    def get_svg_files(self) -> list:
        """
        Returns SVG file names from config or scans the svg folder.
        """
        svg_files = self._config.get("svg_files", [])
        if svg_files:
            return svg_files

        svg_folder = self._get_svg_folder()
        if not os.path.exists(svg_folder):
            # folder missing — return empty list instead of crashing
            return []

        return [f for f in os.listdir(svg_folder) if f.endswith(".svg")]

    def get_animation_datapoint_map(self) -> dict:
        """
        Parses all SVG files and returns a map:
        {datapoint_identifier: [(svg_name, element_id, animation_type), ...]}
        """
        svg_folder = self._get_svg_folder()
        svg_files = self.get_svg_files()
        datapoint_map = {}
        for fname in svg_files:
            svg_path = os.path.join(svg_folder, fname)
            if not os.path.exists(svg_path):
                continue
            tree = ET.parse(svg_path)
            root = tree.getroot()
            for elem in root.iter():
                dp = elem.attrib.get("data-datapoint")
                anim = elem.attrib.get("data-animation")
                if dp and anim:
                    datapoint_map.setdefault(dp, []).append((fname, elem.attrib.get("id"), anim))
        return datapoint_map

    def get_security_config_path(self) -> str:
        """
        Returns the absolute path to security_config.json in the config folder.
        """
        config_dir = (
            os.path.dirname(self._config_path) if hasattr(self, "_config_path") else os.getcwd()
        )
        return os.path.join(config_dir, "security_config.json")

    def get_gis_icons(self) -> list:
        """
        Returns the list of GIS icon configs from system_config.json.
        """
        return self._config.get("gis_icons", [])
