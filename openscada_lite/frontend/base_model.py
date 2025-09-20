import copy
from typing import TypeVar, Generic, Dict, Optional
from abc import ABC, abstractmethod

T = TypeVar('T')

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
        self._store[self.get_id(msg)] = msg

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

    @abstractmethod
    def get_id(self, msg: T) -> str:
        """
        Extract the unique ID from a message.
        Must be implemented by subclasses.
        """
        pass