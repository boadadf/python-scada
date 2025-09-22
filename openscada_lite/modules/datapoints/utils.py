from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from openscada_lite.modules.datapoints.model import DatapointModel

from openscada_lite.common.models.dtos import RawTagUpdateMsg

class Util:
    @staticmethod
    def is_valid(model: "DatapointModel", tag: RawTagUpdateMsg) -> bool:  # Use string for type hint
        # Example validation logic
        if tag.datapoint_identifier not in model._allowed_tags:
            return False
        old_tag = model._store.get(tag.datapoint_identifier)
        if old_tag and tag.timestamp is not None and old_tag.timestamp is not None:
            print(f"Old timestamp: {old_tag.timestamp}, New timestamp: {tag.timestamp}")
            if tag.timestamp < old_tag.timestamp:
                return False
        return True