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

    def update(self, msg: T) -> bool:
        """
        Store or update a message.
        """
        accept_update = self.should_accept_update(msg)            
        if accept_update:
            self._store[self.get_id(msg)] = msg
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

    @abstractmethod
    def get_id(self, msg: T) -> str:
        """
        Extract the unique ID from a message.
        Must be implemented by subclasses.
        """
        pass

    def should_accept_update(self, msg: T) -> bool:
        """
        Determine if an incoming message should be accepted.
        Can be overridden by subclasses for custom logic.
        By default, all messages are accepted.
        """
        return True