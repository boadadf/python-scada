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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from openscada_lite.modules.datapoint.model import DatapointModel

from openscada_lite.common.models.dtos import RawTagUpdateMsg

class Utils:
    @staticmethod
    def is_valid(model: "DatapointModel", tag: RawTagUpdateMsg) -> bool:  # Use string for type hint
        # Example validation logic
        if tag.datapoint_identifier not in model._allowed_tags:
            return False
        old_tag = model._store.get(tag.datapoint_identifier)
        if old_tag and tag.timestamp is not None and old_tag.timestamp is not None:
            if tag.timestamp < old_tag.timestamp:
                return False
        return True