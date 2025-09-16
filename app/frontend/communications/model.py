class CommunicationsModel:
    def __init__(self):
        self.driver_status = {}  # {driver_name: "connect"/"disconnect"}

    def set_status(self, driver_name, status):
        self.driver_status[driver_name] = status

    def get_all_status(self):
        return self.driver_status.copy()