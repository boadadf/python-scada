"""
Rule Engine module for evaluating and executing SCADA rules.

This module defines the RuleEngine class, which manages rule evaluation and action execution
based on tag updates. It supports rules with on/off conditions and actions, and maintains
the lifecycle state for each rule.
"""

import re
from asteval import Interpreter
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async
from openscada_lite.core.rule.actioncommands.action import Action
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.config.config import Config
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.core.rule.actioncommands.command_map import ACTION_MAP

class RuleEngine:
    """
    RuleEngine evaluates rules on tag updates and executes actions accordingly.

    - If a rule has both on_condition and off_condition, it follows an on/off lifecycle (actions are only triggered on state transitions).
    - If a rule has no off_condition, its on_actions are executed every time the on_condition is true (no latching).
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Use RuleManager.get_instance() instead of direct instantiation.")
        cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(self, event_bus: EventBus = None):
        """
        Initialize the RuleEngine.

        Args:
            event_bus (EventBus): The event bus for subscribing to tag updates.
        """
        self.event_bus = event_bus if event_bus is not None else EventBus.get_instance()
        self.asteval = Interpreter()
        self.rules = []
        self.datapoint_state = {}
        self.tag_to_rules = {}  # tag_id -> [rules]
        self.rule_states = {}   # rule_id -> bool (True=active, False=inactive)
        self.load_rules()
        self.build_tag_to_rules_index()
        self.subscribe_to_eventbus()    

    def _safe_key(self, tag_id):
        """Convert tag_id to a safe variable name for asteval."""
        return tag_id.replace("@", "__", 1)

    def load_rules(self):
        """
        Load rules from the configuration and build the tag-to-rules index.
        """
        config = Config.get_instance()
        self.rules = config.get_rules() or []

    def build_tag_to_rules_index(self):
        """
        Build mapping from tags (like Train@var) to rules that depend on them.
        This ensures both on/off conditions are considered.
        """
        self.tag_to_rules.clear()
        tag_pattern = re.compile(r"[A-Za-z0-9_]+@[A-Za-z0-9_]+")

        for rule in self.rules:
            conditions = [rule.on_condition]
            if getattr(rule, "off_condition", None):
                conditions.append(rule.off_condition)

            for condition in conditions:
                for tag in tag_pattern.findall(condition or ""):
                    self.tag_to_rules.setdefault(tag, []).append(rule)

        print(f"[RuleEngine] Tag-to-rule index built:")
        for tag, rules in self.tag_to_rules.items():
            print(f"  {tag} → {[r.rule_id for r in rules]}")

    def subscribe_to_eventbus(self):
        """
        Subscribe the rule engine to tag update events on the event bus.
        """
        self.event_bus.subscribe(EventType.TAG_UPDATE, self.on_tag_update)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def on_tag_update(self, msg: TagUpdateMsg):
        """
        Callback for tag update events. Evaluates rules impacted by the tag and executes actions.

        - If a rule has no off_condition, its on_actions are always executed when on_condition is true.
        - If a rule has an off_condition, on_actions are only executed on transition from inactive to active, and off_actions on transition from active to inactive.

        Args:
            data (dict): The tag update event data, must include 'tag_id' and 'value'.
        """
        print(f"[RuleEngine] Received tag update: {msg.datapoint_identifier} = {msg.value}")
        tag_id = msg.datapoint_identifier
        value = msg.value
        self.datapoint_state[tag_id] = value

        safe_key = self._safe_key(tag_id)
        self.asteval.symtable[safe_key] = value

        impacted_rules = self.tag_to_rules.get(tag_id, [])
        for rule in impacted_rules:
            print(f"[RuleEngine] Evaluating rule: {rule.rule_id}")
            rule_id = rule.rule_id
            on_active = self.rule_states.get(rule_id, False)
            try:
                print("Evaluating:", rule.on_condition.replace("@", "__"))
                print("Symtable value for {}: {}", safe_key , self.asteval.symtable.get(safe_key))
                on_result = self.asteval(rule.on_condition.replace("@", "__"))
                if self.asteval.error:
                    print("asteval errors:", self.asteval.error)
                off_cond = getattr(rule, "off_condition", None)
                has_off = bool(off_cond and off_cond.strip())
                off_result = False
                if has_off:
                    off_result = self.asteval(rule.off_condition.replace("@", "__"))
            except Exception as e:
                print(f"[RuleEngine] Error evaluating rule {rule_id}: {e}")
                continue
            print(f"[RuleEngine] Rule {rule_id} evaluation results: on_condition={on_result}, off_condition={off_result if has_off else 'N/A'}, on_active={on_active}")
            if has_off:
                print(f"[RuleEngine] Rule {rule_id} has off_condition.")
                # ON transition: only if not already active
                if not on_active and on_result:
                    self.rule_states[rule_id] = True
                    for action in getattr(rule, "on_actions", []):
                        await self.execute_action(action, tag_id, msg.track_id, active=True, rule_id=rule_id)
                # OFF transition: only if currently active
                elif on_active and off_result:
                    self.rule_states[rule_id] = False
                    for action in getattr(rule, "off_actions", []):
                        await self.execute_action(action, tag_id, msg.track_id, active=False, rule_id=rule_id)
            else:
                print(f"[RuleEngine] Rule {rule_id} has no off_condition.")
                # Only trigger on rising edge (transition from false to true)
                prev_active = self.rule_states.get(rule_id, False)
                if not prev_active and on_result:
                    print(f"[RuleEngine] Rule {rule_id} on_condition transitioned to true; executing on_actions.")
                    self.rule_states[rule_id] = True
                    for action in getattr(rule, "on_actions", []):
                        await self.execute_action(action, tag_id, msg.track_id, active=True, rule_id=rule_id)
                elif prev_active and not on_result:
                    # Reset state so next true will trigger again
                    self.rule_states[rule_id] = False
                    # If raise_alarm is in on_actions, trigger lower_alarm automatically
                    print(f"[RuleEngine] ======== Rule {rule_id} on_condition transitioned to false. {getattr(rule, "on_actions", [])}")
                    if any("raise_alarm" in action for action in getattr(rule, "on_actions", [])):
                        print(f"[RuleEngine] Rule {rule_id} on_condition transitioned to false; executing lower_alarm.")
                        await self.execute_action("lower_alarm()", tag_id, msg.track_id, active=False, rule_id=rule_id)

    def parse_action(self, action_str):
        """
        Parse an action string into its name and parameters.

        Args:
            action_str (str): The action string, e.g., "raise_alarm('msg')".

        Returns:
            tuple: (action_name, params)
        """
        match = re.match(r"(\w+)\((.*)\)", action_str)
        if not match:
            raise ValueError(f"Invalid action string: {action_str}")
        action_name, params_str = match.groups()
        params = eval(f"({params_str},)") if params_str else ()
        return action_name, params

    async def execute_action(self, action_str, identifier, track_id, active=True, rule_id=None):
        print(f"[RuleEngine] Executing action: {action_str} for {identifier} (active={active})")
        """
        Execute an action by looking up its handler and calling it.

        Args:
            action_str (str): The action string to execute.
            identifier (str): The tag that triggered the rule.
            active (bool): Whether this is an 'on' or 'off' action.
            track_id (str): The track ID associated with the action.
        """
        action_name, params = self.parse_action(action_str)
        handler: Action = ACTION_MAP.get(action_name)
        if handler:
            # Pass self (engine), identifier, params tuple
            await handler(identifier, params, track_id=track_id, rule_id=rule_id)
        else:
            raise ValueError(f"Unknown action: {action_name}")
