import copy
from typing import TypeVar, Generic, Dict, Optional
from abc import ABC

from openscada_lite.common.models.dtos import DTO

T = TypeVar('T', bound=DTO)

class BaseModel(ABC, Generic[T]):
    """
    Abstract base model for storing messages of type T.
    """

    def __init__(self):
        self._store: Dict[str, T] = {}

    def update(self, msg: T):
        """
        Store or update a message.
        """
        print(f"BaseModel.update: Storing message {msg}")
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