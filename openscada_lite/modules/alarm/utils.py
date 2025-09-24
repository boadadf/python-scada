from openscada_lite.modules.alarm.model import AlarmModel


class Utils:
    @staticmethod
    def get_latest_alarm(model: AlarmModel, datapoint_identifier: str):
        alarms = [
            alarm for alarm in model._store.values()
            if alarm.datapoint_identifier == datapoint_identifier
        ]
        if not alarms:
            return None
        return max(alarms, key=lambda a: a.activation_time)