from typing import Dict
from openscada_lite.core.rule.actioncommands.action import Action
from openscada_lite.core.rule.actioncommands.lower_alarm import LowerAlarmAction
from openscada_lite.core.rule.actioncommands.raise_alarm import RaiseAlarmAction
from openscada_lite.core.rule.actioncommands.send_command import SendCommandAction


ACTION_MAP: Dict[str, Action] = {
    "send_command": SendCommandAction(),
    "raise_alarm": RaiseAlarmAction(),
    "lower_alarm": LowerAlarmAction()
}