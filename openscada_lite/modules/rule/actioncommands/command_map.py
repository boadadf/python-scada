from typing import Dict
from openscada_lite.modules.rule.actioncommands.action import Action
from openscada_lite.modules.rule.actioncommands.lower_alarm import LowerAlarmAction
from openscada_lite.modules.rule.actioncommands.raise_alarm import RaiseAlarmAction
from openscada_lite.modules.rule.actioncommands.send_command import SendCommandAction
from openscada_lite.modules.rule.actioncommands.client_alert import ClientAlertAction


ACTION_MAP: Dict[str, Action] = {
    "send_command": SendCommandAction(),
    "raise_alarm": RaiseAlarmAction(),
    "lower_alarm": LowerAlarmAction(),
    "client_alert": ClientAlertAction()
}