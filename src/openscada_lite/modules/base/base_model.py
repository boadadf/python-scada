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

import copy
from typing import TypeVar, Generic, Dict, Optional
from abc import ABC

from openscada_lite.common.models.dtos import DTO

T = TypeVar("T", bound=DTO)


class BaseModel(ABC, Generic[T]):
    """
    Abstract base model for storing messages of type T.
    """

    def __init__(self):
        self._store: Dict[str, T] = {}

    def reset(self):
        self._store: Dict[str, T] = {}

    def update(self, msg: T):
        """
        Store or update a message.
        """
        self._store[msg.get_id()] = msg

    def get(self, msg_id: str) -> Optional[T]:
        """
        Retrieve a message by its ID.
        """
        return self._store.get(msg_id)

    def get_all(self) -> Dict[str, T]:
        """
        Retrieve all messages.
        """
        return copy.deepcopy(self._store)
