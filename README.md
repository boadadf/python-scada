# OpenSCADA Lite


OpenSCADA Lite is a modular, extensible, and modern SCADA (Supervisory Control and Data Acquisition) platform written in Python.  
Following the principle of keeping things simple, it is designed for rapid prototyping, research, and small-to-medium automation projects, with a focus on clarity, testability, and real-time feedback via WebSockets.

---

## Features

- **Modular architecture**: Easily add new modules (datapoints, commands, alarms, rules, etc.) by extending the base module classes
- **Driver abstraction**: Plug in new drivers for different protocols or simulated devices.
- **Real-time updates**: Uses Flask-SocketIO for live data feeds to the frontend.
- **React front end**: Basic react frontend provided as template, even for configuration.
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

The server will start on `http://localhost:5000`.

---

## 3. Configure your system

### 3.1 Configuring Security with the Security Editor

The **Security Editor** is a react web-based application that lets you manage users, groups, and permissions for your SCADA system through a simple web interface.

#### How to Use

3.1.1. **Open the Security Editor in your browser**  
   Navigate to:
   ```
   http://localhost:5000/security_editor
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
   http://localhost:5000/config_editor
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
   http://localhost:5000/scada
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
### 5.1 Communication Module

The **communication module** in OpenSCADA Lite manages all driver interactions, enabling connectivity to real or simulated devices.  
It uses a flexible driver protocol, making it easy to add support for new hardware or protocols.

---

## How Drivers Work

- Each driver implements the `DriverProtocol` interface (see `driver_protocol.py`).
- Drivers are managed by the `ConnectorManager`, which handles driver lifecycle, subscriptions, and event routing.
- Drivers publish tag updates, command feedback, and connection status via async callbacks.

---

## Adding a New Driver

1. **Create a Driver Class**

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

2. **Register Your Driver**

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

3. **Configure Your Driver in the System Config**

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

4. **Implement Simulation or Hardware Logic**

   - For simulated drivers, implement the `_simulate_values` method to periodically update datapoint values.
   - For real hardware, implement communication logic in `send_command`, `connect`, etc.

5. **Test Your Driver**

   - Start the backend and verify your driver connects, publishes updates, and responds to commands.
   - Use the SCADA frontend and Config Editor to monitor and control your new device.

---

## Example Drivers

- **TankTestDriver:** Simulates a tank with level, pump, and door.
- **BoilerTestDriver:** Simulates a boiler with valve, pressure, temperature, and heater.
- **TrainTestDriver:** Simulates a train controller (extend as needed).

See the `drivers/test/` folder for reference implementations.

---

## Tips

- Use async methods for all I/O and event publishing.
- Always register your driver in `DRIVER_REGISTRY` and the config file.
- Use the provided DTOs (`RawTagUpdateMsg`, `CommandFeedbackMsg`, `DriverConnectStatus`) for communication.
- Test with both simulated and real hardware for reliability.

---
---

# Animation System

The **Animation module** enables the SCADA web interface to dynamically update SVG elements based on live datapoints from the backend.  
This allows real-time visualizations such as **tank levels, boiler temperatures, pumps, valves, doors, and interactive controls**.

---

## How It Works

### 1. SVG Parsing
The `AnimationService` loads SVG files from a predefined folder (e.g., `/svg`) and scans for elements with `data-datapoint` and `data-animation` attributes.

**Example:**
```xml
<rect id="tank_fill"
      x="100" y="390" width="200" height="0"
      fill="blue"
      data-datapoint="Server1@TANK"
      data-animation="fill_level" />
```

---

### 2. Animation Configuration
Each `data-animation` refers to a type defined in **`animation_config.json`**.  
This JSON maps animation types to GSAP behavior.

**Example:**
```json
{
  "fill_level": {
    "type": "height_y",
    "maxHeight": 340,
    "baseY": 390,
    "duration": 0.5
  },
  "toggle_start_stop": {
    "type": "fill_toggle",
    "map": {
      "STARTED": "green",
      "STOPPED": "gray"
    },
    "duration": 0.3
  },
  "level_text": {
    "type": "text",
    "duration": 0.2
  }
}
```

---

### 3. Live Updates
- The backend listens for `TagUpdateMsg` on the internal bus.  
- When a tag update arrives, it:
  1. Uses `animation_config.json` to compute the GSAP config (attributes, text, duration).  
  2. Sends an `AnimationUpdateMsg` to subscribed clients.  

---

### 4. Frontend Rendering
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

## Configuring Animations

### Define SVG Elements
Each interactive or animated element must include `data-datapoint` and `data-animation`.

**Example:**
```xml
<circle id="pump"
        cx="70" cy="200" r="20"
        fill="gray"
        data-datapoint="Server1@PUMP"
        data-animation="toggle_start_stop"
        command-datapoint="Server1@PUMP_CMD"
        command-value="TOGGLE" />
```

---

### Define Animation Types
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

## Adding a New Animation

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
      data-datapoint="Server2@VALVE"
      data-animation="valve_toggle"
      data-command="Server2@VALVE_CMD" />
```

**No frontend code changes required** — the `AnimationService` handles mapping and emits `AnimationUpdateMsg`.  
The GSAP client automatically renders the animation.

---

## Summary
- **SVG elements** declare datapoints and animation types.  
- **animation_config.json** defines how values map to GSAP animations.  
- **Backend** listens for datapoint updates and broadcasts animation updates.  
- **Frontend** applies animations seamlessly with GSAP.  

This architecture ensures **scalable, flexible, and easily extensible** animations for SCADA systems.

---

## Troubleshooting & Tips
If after pasting this README you still see HTML rendering from section 2 onward, try the following:

1. **Check for missing/incorrect code fences**: Ensure every opening triple backtick (```) has a corresponding closing triple backtick and that they are on their own lines with no extra characters.
2. **Look for stray HTML outside code blocks**: If any `<tag>` appears outside a fenced block, the Markdown renderer may treat it as HTML and render it. Move such tags inside a fenced block or escape them.
3. **Use raw/plain-text view**: Some editors have a rich-text/WYSIWYG mode that can convert pasted Markdown into HTML. Switch to the raw editor or "Edit file" view.
4. **Try an HTML-safe variant**: If the editor still misbehaves, replace angle brackets in XML samples with entities (`&lt;` and `&gt;`) so they cannot be interpreted as HTML.
5. **Preview vs commit**: Use the repository’s Preview feature (or open the raw file) to verify source Markdown.

If you want, I can also add a version where every XML example uses `&lt;`/`&gt;` (HTML-safe) to guarantee literal display in any environment—tell me and I’ll add it.



## Testing

Run all tests with:

```bash
pytest
```

You can run specific tests or integration suites as needed.

---

## Contributing

- Fork the repo and submit pull requests.
- Please add or update tests for any new features or bugfixes.
- For questions or suggestions, open an issue.

---

## Roadmap

See the `TODO` file for upcoming features and ideas, including:
- Alarm and rule modules
- SVG/Canvas animations
- Feedback reasons and tracking IDs
- Logging service
- Raw-to-non-raw conversion
- Railway deployment

---

## License

MIT License

---

**OpenSCADA Lite** — Fast, flexible, and open SCADA for everyone!