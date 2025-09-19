from enum import Enum, unique

"""
Defines all event types used in the EventBus.
"""
@unique
class EventType(Enum):
    RAW_TAG_UPDATE = "raw_tag_update"
    TAG_UPDATE = "tag_update"
    SEND_COMMAND = "send_command"
    COMMAND_FEEDBACK = "command_feedback"
    RAISE_ALARM = "raise_alarm"
    LOWER_ALARM = "lower_alarm"
    ACK_ALARM = "ack_alarm"
    ALARM_UPDATE = "alarm_update"
    DRIVER_CONNECT = "driver_connect"
    DRIVER_CONNECT_STATUS = "driver_connect_status"