from abc import ABC, abstractmethod

class Driver(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def subscribe(self, datapoints: list):
        pass    

    @abstractmethod
    def register_value_listener(self, callback):
        pass    

    @abstractmethod
    def register_communication_status_listener(self, callback):
        pass

    @abstractmethod
    def register_command_feedback(self, callback):
        pass

    @abstractmethod
    def send_command(self, tag_id: str, command: any, command_id: str):
        pass

    @property
    @abstractmethod
    def server_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass