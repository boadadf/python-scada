import json
from common.models.entities import Rule

class Config:
    _instance = None

    def __init__(self, config_file: str):
        with open(config_file) as f:
            self._config = json.load(f)

    @classmethod
    def get_instance(cls, config_file="config/system_config.json"):
        if cls._instance is None:
            cls._instance = Config(config_file)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    def get_drivers(self):
        return self._config.get("drivers", [])

    def get_rules(self):
        rules = self._config.get("rules", [])
        return [Rule(**r) for r in rules]
    
    def get_allowed_tags(self):
        """Return fully qualified tag_ids: driver_name@tag_id"""
        tags = []
        for driver in self.get_drivers():
            driver_name = driver["name"]
            for tag_id in driver.get("datapoints", []):
                tags.append(f"{driver_name}@{tag_id}")
        return tags

