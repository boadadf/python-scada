# OpenSCADA Lite


OpenSCADA Lite is a modular, extensible, and modern SCADA (Supervisory Control and Data Acquisition) + GIS platform written in Python.  
Following the principle of keeping things simple, it is designed for rapid prototyping, research, and small-to-medium automation projects, with a focus on clarity, testability, and real-time feedback via WebSockets.
OpenSCADA Lite is offered free for testing purposes and licensed for commercial use. Open is referred to its capability to be extended by anyone with Python knowledge.

---

## Features

- **Backend Modular architecture**: Easily add new modules by extending the base module classes
- **Driver abstraction**: Plug in new drivers for different protocols or simulated devices.
- **Real-time updates**: Uses Flask-SocketIO for live data feeds to the frontend.
- **React front end**: Use the openscadalite.js to easily generate views for the backend modules.
- **Event bus**: Decoupled communication between modules.
- **Type-safe DTOs**: All messages use dataclasses for clarity and validation.
- **Secure**: All endpoints are secured automatically
- **Configurable**: All system structure is defined in JSON config files.
- **Testable**: Extensive unit and integration tests.

---

## Project Structure

```text
openscada_lite/
  app.py                  # Main Flask app and SocketIO server
  common/                 # Common folder of shared resources by all modules
    config/               # Configuration loader and validator
    models/               # DTOs, entities, and event types
    bus/                  # Event bus implementation
    tracking/             # Dataflow tracability utilities     
  modules/                # Modules folder
    alarm/                # In charge of alarm life cycle                
    alert/                # In charge of alerting with popups the front end
    animation/            # In charge of generating animations on SVGs
    base/                 # Base cimplementation for all modules following the MSC (Model, Service, Controller) architecture
    command/              # In charge of handling the command life cycle, including feedback
    communication/        # In charge of starting/stopping communications through drivers
      drivers/            # Driver implementations (simulated, real, etc.)
      manager/            # Manages driver instances and routing  
    datapoint/            # In charge of ensuring datapoint integrity
    rule/                 # Automatic actions based in datapoint values (alarms, alerts, commands,...)
    security/             # In charge of login and security of endpoints
    tracking/             # In charge of tracking of data flow inside of the SCADA system
  web/                    # Folder for the frontend application
    config_editor/        # System configuration editor
    login/                # Common login view
    scada/                # SCADA application views
    security_editor/      # Security configuration editor
config/                   # Folder for the configuration files
    svg/                  # Folder for the SVG files
    system_config.json    # Defines datapoint types, ranges, enums, systems, rules...
    security_config.json  # Defines the users and user groups
tests/                    # Folder for unit and integration tests  
```

---

## Getting Started

## 1. Install dependencies

```bash
pip install -r requirements.txt
```
## 2. Run the server

```bash
python -m openscada_lite.app
```

The server will start on `http://localhost:5443`.

---

## 3. Configure your system

### 3.1 Configuring Security with the Security Editor

The **Security Editor** is a react web-based application that lets you manage users, groups, and permissions for your SCADA system through a simple web interface.

#### How to Use

3.1.1. **Open the Security Editor in your browser**  
   Navigate to:
   ```
   http://localhost:5443/security_editor
   ```
   (or the URL provided by your deployment)

3.1.2. **View and Edit Users & Groups**  
   - The editor loads the current `security_config.json`.
   - You’ll see a list of users and groups.
   - Click a user or group to view or edit their permissions.

3.1.3. **Add or Remove Users/Groups**  
   - Use the “Add User” or “Add Group” buttons to create new entries.
   - Fill in usernames, passwords (hashed or plain, depending on your setup), and assign groups.

3.1.4. **Assign Permissions**  
   - For each group, select which permissions (e.g., `VIEW`, `CONTROL`, `ADMIN`) they should have.
   - Assign users to groups for role-based access.

3.1.5. **Save Changes**  
   - Click “Save” to write your changes to `config/security_config.json`.
   - The backend will reload the config and apply new permissions immediately.

3.1.6. **Test Access**  
   - Log in with a user account to verify permissions.
   - Try accessing datapoints, commands, or views to confirm restrictions.

---

#### Example Workflow

- Add a new operator user and assign them to the “operators” group.
- Give the “operators” group permission to view and control datapoints, but not to edit system configuration.
- Save and verify that the new user can log in and only see/control what you allowed.


### 3.2 Configuring Your System with the Config Editor

The **Config Editor** is a react web-based tool for managing your SCADA system’s configuration files, such as `system_config.json` and SVG layouts.  
It provides a user-friendly interface for editing datapoints, drivers, rules, and other system settings, making it easy to customize and extend your automation project.

---

#### How to Use
   
3.2.1. **Open the Config Editor in your browser**
   ```
   http://localhost:5443/config_editor
   ```
   (or your deployed Railway/production URL)

3.2.2. **View and Edit Configuration**
   - The editor loads the current `system_config.json`.
   - You can browse and edit datapoints, drivers, enums, rules, and SVG mappings.
   - Use the UI to add, remove, or modify entries.

3.2.3. **SVG Layout Management**
   - Upload or edit SVG files for your system’s visual layout.
   - Assign datapoints and animation types to SVG elements.

3.2.4. **Save Changes**
   - Click “Save” to write your changes to `config/system_config.json` and/or SVG files.
   - The backend will reload the config and apply changes immediately.

3.2.5. **Test and Validate**
   - Use the live preview to check your configuration.
   - The editor validates your changes and highlights errors before saving.

---

### Example Workflow

- Add a new driver and define its connection info.
- Create new datapoints and assign them to the driver.
- Set up rules for automatic actions or alarms.
- Upload an SVG layout and map datapoints to visual elements.
- Save and verify that your changes are reflected in the running SCADA system.

### 3.3 SCADA Frontend

The **SCADA Frontend** is the main web interface for OpenSCADA Lite.  
It provides real-time visualization, control, and monitoring of your automation system using modern React components and SVG graphics.

---

### Features

- **Live Data Visualization:** See real-time values for all datapoints, alarms, and system status.
- **Interactive Controls:** Send commands to devices and drivers directly from the UI.
- **SVG-based Graphics:** Visualize tanks, pumps, valves, and other equipment with dynamic animations.
- **Alarm & Alert Display:** View active alarms and receive pop-up alerts for critical events.
- **User Authentication:** Secure login and role-based access to views and controls.
- **Responsive Design:** Works on desktop and tablet browsers.

---

### Main Views

- **Dashboard:**  
  Overview of system status, key metrics, and recent alarms.  
  Quick access to important controls and summary charts.

- **Process Graphics:**  
  Interactive SVG-based visualizations of your plant or process.  
  Clickable elements allow direct control (e.g., start/stop pumps, open/close valves).

- **Alarms & Alerts:**  
  List of active alarms and historical events.  
  Pop-up notifications for new or critical alarms.

- **Datapoint Table:**  
  Tabular view of all datapoints, showing live values, quality, and status.  
  Useful for diagnostics and detailed monitoring.

- **Command Panel:**  
  Interface for sending manual commands to devices or drivers.  
  Shows feedback and command status.

- **Login:**  
  Secure authentication for users.  
  Access to views and controls is based on user roles and permissions.

---

### How to Use

3.3.1. **Open the SCADA frontend in your browser**
   ```
   http://localhost:5443/scada
   ```
   (or your deployed Railway/production URL)

3.3.2. **Log in**
   - Enter your username and password.
   - Access is controlled by the security configuration.

3.3.3. **Monitor and Control**
   - View live process graphics and dashboards.
   - Click on interactive elements to send commands (e.g., start/stop pumps).
   - Watch for alarms and alerts in the notification area.

---

### Example Workflow

- Log in as an operator.
- Monitor tank levels and pump status in real time.
- Click a valve to open/close it.
- Receive an alarm pop-up if a threshold is exceeded.
- Use the dashboard to track system performance.


---

## 4 Architecture

### 4.1 Module Architecture: Model-Service-Controller (MSC)

OpenSCADA Lite uses a modular architecture based on the **MSC pattern** (Model, Service, Controller).  
This design makes it easy to add new features, maintain code, and ensure clear separation of concerns.

---

#### 4.1.1 Base MSC Classes

- **BaseModel**  
  Stores and manages the state of messages or entities (e.g., datapoints, alarms).  
  Provides methods for updating, retrieving, and listing stored objects.

- **BaseService**  
  Handles business logic, event bus communication, and message processing.  
  Receives messages from the event bus and controller, processes them, updates the model, and notifies the controller.

- **BaseController**  
  Manages frontend-backend communication via WebSocket and HTTP.  
  Publishes updates to clients, handles incoming requests, and validates data.

---

#### 4.1.2 How Modules Extend MSC

Each functional module (e.g., **datapoint**, **alarm**, **command**, **security**) extends the base MSC classes:

- **Model:**  
  Inherit from `BaseModel` and specify the type of message/entity it stores.

- **Service:**  
  Inherit from `BaseService` and implement logic for handling messages, updating the model, and interacting with other modules.

- **Controller:**  
  Inherit from `BaseController` and define endpoints, validation, and publish logic for the frontend.

**Example: Datapoint Module**

```python
# Model
class DatapointModel(BaseModel[DatapointMsg]):
    pass

# Service
class DatapointService(BaseService[TagUpdateMsg, DatapointCommand, DatapointMsg]):
    def should_accept_update(self, msg: TagUpdateMsg) -> bool:
        # Custom acceptance logic
        return True

# Controller
class DatapointController(BaseController[DatapointMsg, DatapointCommand]):
    def validate_request_data(self, data: DatapointCommand):
        # Validate incoming command
        return data        
```
You can see with almost no code your datapoint service is ready!

---

### 4.1.3 Adding a New Module

1. **Create Model, Service, and Controller classes** in your module folder, inheriting from the base MSC classes.
2. **Define your DTOs** (data transfer objects) for messages, commands, and events.
3. **Register your module** in `app.py` by instantiating its controller and passing the model, service, and socketio as needed.
4. **Implement custom logic** in your service and controller as required.

---

### 4.1.4 Benefits

- **Consistency:** All modules follow the same structure.
- **Extensibility:** Easily add new modules by extending the base classes.
- **Testability:** Each part (model, service, controller) can be tested independently.
- **Separation of Concerns:** Business logic, state management, and frontend communication are clearly separated.

---
## 5 Modules 

Like we saw in the previous section, the server is composed of modules binded by the event bus. Each module has a specific purpose and is composed always of controller.py, model.py and service.py

Next we will describe the properties of the main modules

### 5.1 Communication Module

The **communication module** in OpenSCADA Lite manages all driver interactions, enabling connectivity to real or simulated devices.  
It uses a flexible driver protocol, making it easy to add support for new hardware or protocols.

---

#### 5.1.1 How Drivers Work

- Each driver implements the `DriverProtocol` interface (see `driver_protocol.py`).
- Drivers are managed by the `ConnectorManager`, which handles driver lifecycle, subscriptions, and event routing.
- Drivers publish tag updates, command feedback, and connection status via async callbacks.

---

#### 5.1.2 Adding a New Driver

5.1.2.1. **Create a Driver Class**

   - Inherit from `DriverProtocol` (see `driver_protocol.py`).
   - Implement required methods:  
     - `connect`, `disconnect`, `subscribe`, `register_value_listener`, `register_communication_status_listener`, `register_command_feedback`, `send_command`.
   - Implement the simulation or hardware logic in your driver.

   **Example:**
   ```python
   # my_new_driver.py
   from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol

   class MyNewDriver(DriverProtocol):
       async def connect(self): ...
       async def disconnect(self): ...
       def subscribe(self, datapoints): ...
       def register_value_listener(self, callback): ...
       async def register_communication_status_listener(self, callback): ...
       def register_command_feedback(self, callback): ...
       async def send_command(self, data): ...
       @property
       def server_name(self): ...
       @property
       def is_connected(self): ...
   ```

5.1.2.2. **Register Your Driver**

   - Add your driver class to the `DRIVER_REGISTRY` dictionary in the communication module.
   - Example:
     ```python
     DRIVER_REGISTRY = {
         "TankTestDriver": TankTestDriver,
         "BoilerTestDriver": BoilerTestDriver,
         "TrainTestDriver": TrainTestDriver,
         "MyNewDriver": MyNewDriver,  # <-- Add your driver here
     }
     ```

5.1.2.3. **Configure Your Driver in the System Config**

   - Add a new entry to the `"drivers"` section of your `system_config.json`:
     ```json
     {
       "name": "MyDevice",
       "driver_class": "MyNewDriver",
       "connection_info": {
         "ip": "192.168.1.100",
         "port": 502
       },
       "datapoints": [
         { "name": "TEMPERATURE", "type": "float" },
         { "name": "PRESSURE", "type": "float" }
       ]
     }
     ```

5.1.2.4. **Implement Simulation or Hardware Logic**

   - For simulated drivers, implement the `_simulate_values` method to periodically update datapoint values.
   - For real hardware, implement communication logic in `send_command`, `connect`, etc.

5.1.2.5. **Test Your Driver**

   - Start the backend and verify your driver connects, publishes updates, and responds to commands.
   - Use the SCADA frontend and Config Editor to monitor and control your new device.

---

#### 5.1.3 Example Drivers

- **TankTestDriver:** Simulates a tank with level, pump, and door.
- **BoilerTestDriver:** Simulates a boiler with valve, pressure, temperature, and heater.
- **TrainTestDriver:** Simulates a train controller (extend as needed).

See the `drivers/test/` folder for reference implementations.

---

#### 5.1.4 Tips

- Use async methods for all I/O and event publishing.
- Always register your driver in `DRIVER_REGISTRY` and the config file.
- Use the provided DTOs (`RawTagUpdateMsg`, `CommandFeedbackMsg`, `DriverConnectStatus`) for communication.
- Test with both simulated and real hardware for reliability.

---

### 5.2 Rule Module

The **Rule Module** in OpenSCADA Lite enables automatic actions and logic based on datapoint values, alarms, and system events.  
It allows you to define rules for triggering commands, alarms, alerts, or other actions—including direct action commands—when specific conditions are met.

---

#### 5.2.1 Features

- **Flexible Rule Engine:** Define rules using expressions based on datapoint values.
- **Automatic Actions:** Trigger commands, alarms, alerts, or other actions when rule conditions are satisfied.
- **Action Commands:** Rules can directly send commands to devices or drivers, automating control logic.
- **Modular Actions:** Each action is implemented as a class and registered in the `ACTION_MAP`, making it easy to add new types of rule actions.
- **Datapoint Monitoring:** Rules can react to any datapoint update in the system.
- **Extensible:** Add new rule types or actions as needed.

---

#### 5.2.2 How Rules Work

- Rules are defined in the `system_config.json` file under the `"rules"` section.
- Each rule specifies:
  - **Conditions:** Expressions evaluated against current datapoint values.
  - **Actions:** What to do when the condition is met (e.g., send a command, raise an alarm, trigger an alert).
- The rule engine monitors all relevant datapoints and evaluates rule conditions in real time.

---

#### 5.2.3 Modular Action Commands

A unique feature of the Rule Module is its **modular action system**.  
Each action (such as sending a command, raising an alarm, or alerting a client) is implemented as a class derived from the abstract `Action` base class.  
Actions are registered in the `ACTION_MAP` dictionary, allowing the rule engine to dynamically execute them by name.

**Example: `ACTION_MAP` registration**

```python
ACTION_MAP = {
    "send_command": SendCommandAction(),
    "raise_alarm": RaiseAlarmAction(),
    "lower_alarm": LowerAlarmAction(),
    "client_alert": ClientAlertAction()
}
```

**Adding a new action:**  
To add a new type of rule action, simply create a new class inheriting from `Action`, implement the `get_event_data` method, and register it in `ACTION_MAP`.

---

#### 5.2.4 Example Rule Definition (with Action Commands)

```json
{
  "rules": [
    {
      "name": "HighTankLevelAlarm",
      "on_condition": "WaterTank@TANK > 80",
      "on_actions": ["raise_alarm('Tank level high!')"],
      "off_actions": ["lower_alarm()"]
    },
    {
      "name": "AutoPumpStart",
      "on_condition": "WaterTank@TANK > 60 and WaterTank@PUMP == 'CLOSED'",
      "on_actions": ["send_command('WaterTank@PUMP', 'OPEN')"]
    },
    {
      "name": "ShowClientAlert",
      "on_condition": "AuxServer@VALVE == 'CLOSED' and AuxServer@PRESSURE > 100",
      "on_actions": ["client_alert('Pressure high!', 'warning', 'AuxServer@VALVE', 'TOGGLE', 10)"]
    }
  ]
}
```

- The `"send_command"` action will send a command to the specified target datapoint with the given value when the condition is met.
- The `"raise_alarm"` and `"lower_alarm"` actions manage alarm lifecycle.
- The `"client_alert"` action sends a notification to the frontend, optionally with a command button.

---

#### 5.2.5 How to Add or Edit Rules

1. **Open `system_config.json`**  
   Locate the `"rules"` section.

2. **Define a new rule**  
   - Set a unique `name`.
   - Write an `on_condition` expression using datapoint identifiers.
   - Specify the `on_actions` and/or `off_actions` as a list of action strings.

3. **Save and reload**  
   - Save your changes.
   - The backend will reload the config and apply new rules automatically.

---

#### 5.2.6 Extending the Rule Module

- Add new action types by creating a new class in `modules/rule/actioncommands/`, inheriting from `Action`, and registering it in `ACTION_MAP`.
- Rules can be made more complex by combining multiple conditions or chaining actions.

---

#### 5.2.7 Tips

- Use clear, descriptive rule names.
- Test rule conditions and action commands to avoid unintended triggers.
- Use the Config Editor for a user-friendly way to manage rules.

---
### 5.3 Animation Module

The **Animation Module** enables dynamic, real-time updates of SVG elements in the SCADA web interface. It supports animations triggered by datapoint changes, alarm events, and communication status, providing rich and informative visual feedback.

---

#### 5.3.1 How It Works

- **SVG Mapping:**  
  SVG elements are annotated with attributes such as `data-datapoint`, `data-animation`, and optionally `command-datapoint` for interactive controls.

- **Animation Configuration:**  
  Animation types and behaviors are defined in `animation_config.json`, mapping triggers to attribute changes, text updates, and durations.

- **Handlers:**  
  Specialized handlers process different types of backend messages:
  - `TagHandler`: Handles datapoint value changes.
  - `AlarmHandler`: Handles alarm lifecycle events.
  - `ConnectionHandler`: Handles driver communication status.

- **Live Updates:**  
  When a relevant event occurs, the backend uses the appropriate handler to process the message and generate an `AnimationUpdateMsg`.  
  This message contains the animation configuration (attributes, text, duration) and is sent to subscribed clients.

---

#### 5.3.2 Client Notification and GSAP Rendering

- The backend listens for `TagUpdateMsg` (and other relevant messages) on the internal bus.
- When an update arrives:
  1. The backend uses `animation_config.json` to compute the GSAP config (attributes, text, duration).
  2. It sends an `AnimationUpdateMsg` to subscribed clients.
- The HTML page loads the selected SVG and subscribes to `AnimationUpdateMsg`.
- **GSAP** applies animations to target elements:

```js
gsap.to(elem, {
  duration: msg.config.duration,
  attr: msg.config.attr,   // optional
  text: msg.config.text    // optional, requires TextPlugin
});
```

- Command-capable elements (`command-datapoint`) can send control messages back to the server when clicked.

---

#### 5.3.3 Configuring Animations

**Define SVG Elements:**  
Each interactive or animated element must include `data-datapoint` and `data-animation`.

```xml
<circle id="pump"
        cx="70" cy="200" r="20"
        fill="gray"
        data-datapoint="WaterTank@PUMP"
        data-animation="toggle_start_stop"
        command-datapoint="WaterTank@PUMP_CMD"
        command-value="TOGGLE" />
```

**Define Animation Types:**  
Animation behaviors are defined in **`animation_config.json`**.

Supported types:
- **height_y** → animates height and y attributes (e.g., tank level)
- **fill_color** → animates fill color based on numeric values (e.g., temperature)
- **fill_toggle** → changes color based on enum/string/boolean values (e.g., STARTED/STOPPED)
- **text** → animates text content

**Example toggle mapping:**
```json
"toggle_start_stop": {
  "type": "fill_toggle",
  "map": {
    "STARTED": "green",
    "STOPPED": "gray"
  },
  "duration": 0.3
}
```

---

#### 5.3.4 Adding a New Animation

1. **Update `animation_config.json`:**
```json
"valve_toggle": {
  "type": "fill_toggle",
  "map": {
    "OPENED": "green",
    "CLOSED": "red"
  },
  "duration": 0.3
}
```

2. **Update SVG:**
```xml
<rect id="valve"
      x="180" y="360" width="40" height="20"
      fill="gray"
      data-datapoint="AuxServer@VALVE"
      data-animation="valve_toggle"
      data-command="AuxServer@VALVE_CMD" />
```

**No frontend code changes required** — the `AnimationService` handles mapping and emits `AnimationUpdateMsg`.  
The GSAP client automatically renders the animation.

---

#### 5.3.5 Handler Architecture and Extensibility

Handlers are responsible for processing messages and updating SVG elements:

- **TagHandler:**  
  Triggers on datapoint updates. Applies attribute or text changes based on value and quality.
- **AlarmHandler:**  
  Triggers on alarm events. Determines alarm state (`ACTIVE`, `ACK`, `INACTIVE`, `FINISHED`) and updates mapped SVG elements.
- **ConnectionHandler:**  
  Triggers on driver connection status. Updates SVG elements to reflect communication health.

Each handler uses the shared animation configuration and can schedule automatic reverts using the `revertAfter` property.

**To add a new handler:**

1. **Create a Handler Class:**  
   Inherit from a base handler or follow the pattern in `handlers/`. Implement `can_handle(msg)` and `handle(msg, service)` methods.

   ```python
   class CustomHandler:
       def can_handle(self, msg) -> bool:
           return isinstance(msg, CustomMsgType)

       def handle(self, msg, service):
           # Process message and return list of AnimationUpdateMsg
           ...
   ```

2. **Register the Handler:**  
   Add your handler to the `handlers` list in `AnimationService`.

   ```python
   self.handlers = [
       TagHandler(),
       AlarmHandler(),
       ConnectionHandler(),
       CustomHandler(),  # <-- Add your new handler here
   ]
   ```

3. **Update Animation Config:**  
   Define new animation types or triggers in `animation_config.json` as needed.

---

#### 5.3.6 Summary

- SVG elements declare datapoints and animation types.
- Handlers process backend events and broadcast `AnimationUpdateMsg` to clients.
- Frontend applies animations using GSAP.
- Architecture is scalable, flexible, and easily extensible for new event types and handlers.


---

### 5.4 Alarm Module

The **Alarm Module** manages the lifecycle of alarms within the SCADA system, including raising, acknowledging, and lowering alarms. It ensures that alarm states are tracked, validated, and broadcast to other modules and the frontend.

---

#### 5.4.1 Components

- **AlarmModel:**  
  Stores and updates alarm messages. Automatically removes finished alarms (deactivated and acknowledged) from the store.

- **AlarmController:**  
  Handles incoming requests to acknowledge alarms. Validates requests to ensure the alarm exists, is not finished, and has not already been acknowledged.

- **AlarmService:**  
  Processes messages to raise or lower alarms, updates the model, and publishes alarm updates to the event bus. Handles controller messages for acknowledgments and ensures proper state transitions.

- **Utils:**  
  Provides helper functions, such as retrieving the latest alarm for a given rule.

---

#### 5.4.2 Alarm Lifecycle

- **Raise Alarm:**  
  Creates a new alarm or resets deactivation and acknowledgment times for an existing alarm.

- **Acknowledge Alarm:**  
  Marks the alarm as acknowledged if it is active and not already acknowledged.

- **Lower Alarm:**  
  Sets the deactivation time for the alarm.

- **Finish Alarm:**  
  An alarm is considered finished when both deactivation and acknowledgment times are set. Finished alarms are removed from the store.

---

#### 5.4.3 Extending the Alarm Module

To add new alarm behaviors or integrate with other modules:

1. **Extend the Model:**  
   Add new fields or methods to `AlarmModel` as needed.

2. **Customize the Controller:**  
   Override validation or request handling logic in `AlarmController`.

3. **Enhance the Service:**  
   Implement new message types or processing logic in `AlarmService`.  
   Use the event bus to broadcast custom alarm events.

4. **Add Utilities:**  
   Place reusable logic in `Utils` for easier maintenance.

---

#### 5.4.4 Summary

- Centralized alarm management with clear lifecycle handling.
- Validation and state transitions are enforced by the controller and service.
- Extensible architecture for custom alarm logic and integrations.
- Alarm updates are published to the event bus for system-wide visibility.

---

### 5.5 Command Module

The **Command Module** manages the sending and feedback of control commands within the SCADA system. It provides a secure and structured way for clients to issue commands to devices and receive execution feedback.

---

#### 5.5.1 Components

- **CommandModel:**  
  Maintains the set of allowed commands and stores feedback for each command. Initializes feedback entries for all permitted command identifiers.

- **CommandController:**  
  Handles incoming command requests from clients. Validates request data and forwards commands to the backend for execution.

- **CommandService:**  
  Processes command messages, updates the model with feedback, and publishes command feedback to the event bus. Accepts all feedback updates from command executors by default.

---

#### 5.5.2 Command Workflow

- **Send Command:**  
  Clients send a `SendCommandMsg` specifying the target datapoint and desired value.

- **Validate and Forward:**  
  The controller validates the request and forwards it to the backend.

- **Execute and Feedback:**  
  The backend executes the command and generates a `CommandFeedbackMsg` containing the result and any feedback.

- **Notify Clients:**  
  The service updates the model and notifies subscribed clients with the feedback message.

---

#### 5.5.3 Extending the Command Module

To add new command types or customize command handling:

1. **Extend the Model:**  
   Add new fields or logic to `CommandModel` for custom feedback or command tracking.

2. **Customize the Controller:**  
   Override `validate_request_data` in `CommandController` to enforce additional validation rules.

3. **Enhance the Service:**  
   Implement custom acceptance logic in `should_accept_update` or add new processing steps in `CommandService`.

---

#### 5.5.4 Summary

- Centralized command management and feedback.
- Secure validation and execution workflow.
- Extensible architecture for custom command logic and integrations.
- Feedback is published to the event bus for system-wide visibility.


---

### 5.6 Datapoint Module

The **Datapoint Module** manages the acquisition, validation, and distribution of real-time process values (tags) within the SCADA system. It ensures that only valid and up-to-date datapoint updates are accepted and broadcast to other modules and clients.

---

#### 5.6.1 Components

- **DatapointModel:**  
  Stores the current state of all allowed datapoints as `TagUpdateMsg` objects. Initializes all tags with default values and tracks updates.

- **DatapointController:**  
  Handles incoming requests to update datapoints. Validates request data for required fields and correct format before passing to the model.

- **DatapointService:**  
  Processes raw tag update messages, validates them using `Utils.is_valid`, and publishes accepted updates to the event bus. Converts raw messages to structured `TagUpdateMsg` objects.

- **Utils:**  
  Provides helper functions for validation, such as checking allowed tags and timestamp ordering to prevent outdated updates.

---

#### 5.6.2 Datapoint Workflow

- **Receive Update:**  
  The backend receives a `RawTagUpdateMsg` from a driver or client.

- **Validate:**  
  The controller checks for required fields and correct format.  
  The service uses `Utils.is_valid` to ensure the tag is allowed and the timestamp is not older than the current value.

- **Process and Broadcast:**  
  Valid updates are converted to `TagUpdateMsg` and published to the event bus for system-wide visibility.

---

#### 5.6.3 Extending the Datapoint Module

To add new datapoint behaviors or customize validation:

1. **Extend the Model:**  
   Add new fields or logic to `DatapointModel` for custom tracking or initialization.

2. **Customize the Controller:**  
   Override `validate_request_data` in `DatapointController` to enforce additional validation rules.

3. **Enhance the Service:**  
   Implement custom acceptance logic in `should_accept_update` or add new processing steps in `DatapointService`.

4. **Add Utilities:**  
   Place reusable validation or processing logic in `Utils` for easier maintenance.

---

#### 5.6.4 Summary

- Centralized management and validation of process values.
- Ensures only valid and up-to-date datapoint updates are accepted.
- Extensible architecture for custom datapoint logic and integrations.
- Updates are published to the event bus for system-wide visibility.


---

### 5.7 Security Module

The **Security Module** provides authentication and authorization for the SCADA system. It manages user credentials, group permissions, and access control for API endpoints using JWT-based authentication.

---

#### 5.7.1 Components

- **SecurityModel:**  
  Stores users and groups loaded from the configuration file. Maintains an in-memory copy and provides access to endpoint and permission data.

- **SecurityController:**  
  Exposes REST API endpoints for login, configuration management, and endpoint listing. Handles JWT token issuance and validation.

- **SecurityService:**  
  Implements user authentication, password hashing, and permission checks. Issues JWT tokens for authenticated users and verifies access rights for endpoints.

- **Utils:**  
  Provides helper functions for password hashing and JWT creation/verification.

---

#### 5.7.2 Workflow

- **Login:**  
  Clients send credentials to `/security/login`. If valid, a JWT token is returned for session authentication.

- **Authorization:**  
  Protected endpoints require a valid JWT token. The controller verifies the token and checks user permissions before granting access.

- **Configuration Management:**  
  Security configuration (users, groups, permissions) can be retrieved and updated via the `/security-editor/api/config` endpoints.

---

#### 5.7.3 Architectural Note

Unlike other modules, the Security Module does **not** listen to the internal event bus or publish messages.  
It operates independently, providing synchronous REST API endpoints for authentication and authorization.  
This design ensures that security logic is isolated and does not follow the base event-driven pattern used by datapoint, alarm, and command modules.

---

#### 5.7.4 Summary

- Centralized authentication and authorization using JWT.
- REST API endpoints for login and configuration management.
- No event bus integration; operates independently from the base module pattern.
- Extensible for custom authentication logic and permission models.

---
### 5.8 Tracking Module

The **Tracking Module** provides automatic tracking of data flow events throughout the SCADA system. It records the status and movement of DTOs (data transfer objects) for auditing, debugging, and monitoring purposes.

---

#### 5.8.1 Components

- **TrackingModel:**  
  Stores the most recent data flow events (up to a configurable limit) using an ordered dictionary for efficient rotation.

- **TrackingController:**  
  Exposes a read-only API for retrieving tracking events. Does not accept incoming requests for updates.

- **TrackingService:**  
  Accepts all incoming tracking events and updates the model. Publishes events to the event bus for system-wide visibility.

- **TrackingPublisher:**  
  Handles publishing of tracking events. Uses a background worker thread to enqueue and process events, publishing to the event bus and optionally writing to a log file.

---

#### 5.8.2 Workflow

- **Event Generation:**  
  Tracking events are generated whenever a decorated function is called or a DTO is processed.  
  Events include metadata such as source, status, timestamp, and payload.

- **Event Publishing:**  
  The publisher enqueues events for background processing.  
  Events are published to the event bus and optionally logged to a file.

- **Event Retrieval:**  
  Clients can query the tracking API to retrieve recent data flow events for auditing or debugging.

---

#### 5.8.3 Automatic Tracking with Decorators

To automatically generate tracking information, use the provided decorators in `common/tracking/decorators.py`.  
These decorators can be applied to methods to publish tracking events based on arguments or return values.

**Examples:**

- **Async function, DTO as first argument:**
  ```python
  from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async
  from openscada_lite.common.tracking.tracking_types import DataFlowStatus

  @publish_data_flow_from_arg_async(DataFlowStatus.RECEIVED)
  async def process_dto(self, dto):
      ...
  ```

- **Sync function, DTO as return value:**
  ```python
  from openscada_lite.common.tracking.decorators import publish_data_flow_from_return_sync
  from openscada_lite.common.tracking.tracking_types import DataFlowStatus

  @publish_data_flow_from_return_sync(DataFlowStatus.SUCCESS)
  def handle_result(self, ...):
      ...
  ```

- **Decorator options:**  
  - `publish_data_flow_from_arg_async` / `publish_data_flow_from_arg_sync`
  - `publish_data_flow_from_return_async` / `publish_data_flow_from_return_sync`
  - Specify `status` and optionally `source` for each event.

These decorators ensure that tracking events are published automatically whenever the decorated function is called, reducing manual tracking code and improving consistency.

---

#### 5.8.4 Summary

- Centralized tracking of data flow events for auditing and debugging.
- Automatic event generation using decorators for async and sync functions.
- Efficient background publishing and optional file logging.
- Read-only API for retrieving recent tracking events.


## 6 Creating Views with openscadalite.js

All SCADA frontend views leverage a **common live feed library**, `useLiveFeed`, which unifies real-time updates and command handling.  
This makes adding new views for any backend MSC module **fast, consistent, and minimal code**.

#### What `openscadalite` Provides

- **Automatic WebSocket connection** to receive live updates from the backend.
- **Reactive state management**: `items` always reflect the latest data.
- **Unified command/REST interface**: `postJson()` sends commands or updates to the backend with proper headers.
- **Flexible keying**: Define a unique key per item for state mapping.
- **Security**: passes the necessary credentials to the backend

#### Using `useLiveFeed`


    const [items, setItems, postJson] = useLiveFeed(
     endpoint,       // backend MSC module name
     updateMsgType,  // WebSocket message type
     getKey,         // function returning unique key for each item
     postType?       // optional: REST message type for sending updates/commands
    );

    items: object containing live data from the backend

    setItems: optionally update items locally

    postJson(payload): send a command or data update to the backend

Example: Alarms View

    import React from "react";
    import { useLiveFeed } from "../livefeed/useLiveFeed";

    function alarmKey(a) { return a.alarm_occurrence_id; }

    export default function AlarmsView() {
      const [alarms] = useLiveFeed("alarm", "alarmupdatemsg", alarmKey);

      return (
        <div>
          <h2>Active Alarms</h2>
          <ul>
            {Object.values(alarms).map(a => (
              <li key={alarmKey(a)}>
                {a.rule_id} — {a.datapoint_identifier}
              </li>
            ))}
          </ul>
        </div>
      );
    }

    Automatically subscribes to "alarm_alarmupdatemsg" and updates in real time.

### Sending Commands. 

Some backend modules allow commands or control messages. Add a postType:

    const [commands, , postJson] = useLiveFeed(
      "command",
      "commandfeedbackmsg",
      cmd => cmd.datapoint_identifier,
      "sendcommandmsg"
    );

    async function sendCommand(datapoint, value) {
      await postJson({ datapoint_identifier: datapoint, value });
    }

This sends a POST request to:

    /command_send_sendcommandmsg

with all headers handled automatically.
Template for a New View

    import React from "react";
    import { useLiveFeed } from "../livefeed/useLiveFeed";

    function myKey(item) { return item.id; }

    export default function MyNewView() {
      const [data, setData, postJson] = useLiveFeed(
        "myendpoint",
        "myupdatemsg",
        myKey,
        "mycommandmsg"
      );

      return (
        <div>
          <h2>My Endpoint Data</h2>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      );
    }

Every view in the SCADA frontend alarms, datapoints, commands, GIS markers, communications, tracking, and animations—uses the same useLiveFeed hook.

Live Feed Data Flow

         ┌────────────────────────┐
         │   Backend MSC Module   │
         │                        │
         │  ┌───────────────┐     │
         │  │ WebSocket feed│─────┼─────────────┐
         │  └───────────────┘     │             │
         │                        │             │
         │  ┌───────────────┐     │             ▼
         │  │ REST endpoint │─────► useLiveFeed
         │  └───────────────┘     │             │
         └────────────────────────┘             │
                                                ▼
                                       ┌─────────────────┐
                                       │ React Component │
                                       │  state (items) │
                                       └─────────────────┘
                                                  │
                         User actions (button click / input)
                                                  │
                                                  ▼
                                       ┌─────────────────┐
                                       │ postJson() REST │
                                       │  sends command  │
                                       └─────────────────┘
                                                  │
                                                  ▼
                                       Backend MSC handles command

    🔹 New views can be added by defining endpoint, updateMsgType, getKey, and optionally postType. The live feed library handles WebSocket and REST automatically.

---

---

## Testing

Run all tests with:

```bash
pytest -v tests/
```

You can run specific tests or integration suites as needed.


## Copyright
All rights reserved to DFB Services LTD.