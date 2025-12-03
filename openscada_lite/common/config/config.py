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
from pathlib import Path
import xml.etree.ElementTree as ET
from openscada_lite.common.models.entities import Animation, AnimationEntry, Rule
import logging

logger = logging.getLogger(__name__)


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Use Config.get_instance() instead of direct instantiation.")
        return super().__new__(cls)

    def __init__(self, config_path: str):
        logger.debug(f"Config path received: {config_path}")
        # Always treat config_path as a directory
        config_file = ""
        if os.path.isfile(config_path):
            config_file = config_path
        else:
            config_file = os.path.join(config_path, "system_config.json")
        with open(config_file) as f:
            self._config = json.load(f)
        self._config_path = os.path.dirname(
            config_file
        )  # Save the config directory path for later use

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

    def _get_default_for_datapoint(self, dp_name: str, datapoints: list) -> any:
        """Helper method to get default value from a list of datapoints."""
        for dp in datapoints:
            if dp.get("name") == dp_name:
                dp_type = dp.get("type")
                type_info = self._config.get("dp_types", {}).get(dp_type, {})
                return type_info.get("default")
        return None

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
                default = self._get_default_for_datapoint(dp_name, driver.get("datapoints", []))
                if default is not None:
                    return default
                # Search in command_datapoints if not found
                return self._get_default_for_datapoint(
                    dp_name, driver.get("command_datapoints", [])
                )
        return None

    def _find_datapoint_type(self, datapoint_identifier: str):
        """Find and return the datapoint type definition for a given identifier."""
        for driver in self.get_drivers():
            driver_name = driver["name"]
            for dp in driver.get("datapoints", []) + driver.get("command_datapoints", []):
                if f"{driver_name}@{dp['name']}" == datapoint_identifier:
                    dp_type_name = dp.get("type")
                    return self.get_types().get(dp_type_name)
        return None

    def _validate_float_value(self, value, dp_type: dict) -> bool:
        """Validate a float value against its type constraints."""
        try:
            v = float(value)
        except (ValueError, TypeError):
            return False
        if "min" in dp_type and v < dp_type["min"]:
            return False
        if "max" in dp_type and v > dp_type["max"]:
            return False
        return True

    def _validate_enum_value(self, value, dp_type: dict) -> bool:
        """Validate an enum value against allowed values."""
        return value in dp_type.get("values", [])

    def validate_value(self, datapoint_identifier: str, value) -> bool:
        """
        Validate if the value is valid for the given datapoint_identifier.
        Supports enum and float types as defined in dp_types.
        """
        dp_type = self._find_datapoint_type(datapoint_identifier)
        if not dp_type:
            return False
        if dp_type["type"] == "float":
            return self._validate_float_value(value, dp_type)
        elif dp_type["type"] == "enum":
            return self._validate_enum_value(value, dp_type)
        return True

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
        logger.debug(f"Config path for SVGs: {self._config_path}")
        config_dir = Path(self._config_path) / "svg"
        return str(config_dir)

    def get_svg_files(self) -> list:
        """
        Returns SVG file names from config or scans the svg folder.
        """
        svg_files = self._config.get("svg_files", [])
        logger.debug(f"SVG files from config: {svg_files}")
        if svg_files:
            return svg_files
        logger.debug("No svg_files in config, scanning folder.")
        svg_folder = self._get_svg_folder()
        if not os.path.exists(svg_folder):
            logger.debug(f"SVG folder does not exist: {svg_folder}")
            # folder missing — return empty list instead of crashing
            return []
        logger.debug(f"Scanning SVG folder: {svg_folder}")
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

    def get_gis_icons(self) -> list:
        """
        Returns the list of GIS icon configs from system_config.json.
        """
        return self._config.get("gis_icons", [])

    def get_security_config_path(self) -> str:
        """
        Returns the absolute path to security_config.json in the config folder.
        If SCADA_CONFIG_PATH points to a file, use its parent directory.
        """
        raw_path = os.environ.get("SCADA_CONFIG_PATH", "config")
        logger.debug(f"Getting security config path from: {raw_path}")
        if os.path.isfile(raw_path):
            logger.debug(
                f"SCADA_CONFIG_PATH is a file. Using its directory: {os.path.dirname(raw_path)}"
            )
            base_dir = os.path.dirname(raw_path)
        else:
            logger.debug(f"SCADA_CONFIG_PATH is a directory. Using it directly: {raw_path}")
            base_dir = raw_path
        logger.debug(
            f"Security config will be at: {os.path.join(base_dir, 'security_config.json')}"
        )
        self.config_path = base_dir
        logger.debug(f"Config path set to: {self.config_path}")
        return os.path.join(base_dir, "security_config.json")
