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

    def update(self, msg: T) -> bool:
        """
        Store or update a message.
        """
        accept_update = self.should_accept_update(msg)            
        if accept_update:
            self._store[msg.get_id()] = msg
        return accept_update

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

    def should_accept_update(self, msg: T) -> bool:
        """
        Determine if an incoming message should be accepted.
        Can be overridden by subclasses for custom logic.
        By default, all messages are accepted.
        """
        return True