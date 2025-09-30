# OpenSCADA Lite

OpenSCADA Lite is a modular, extensible, and modern SCADA (Supervisory Control and Data Acquisition) platform written in Python.  
It is designed for rapid prototyping, research, and small-to-medium automation projects, with a focus on clarity, testability, and real-time feedback via WebSockets.

---

## Features

- **Modular architecture**: Easily add new modules (datapoints, commands, alarms, rules, etc.)
- **Driver abstraction**: Plug in new drivers for different protocols or simulated devices.
- **Real-time updates**: Uses Flask-SocketIO for live data feeds to the frontend.
- **Event bus**: Decoupled communication between modules.
- **Type-safe DTOs**: All messages use dataclasses for clarity and validation.
- **Configurable**: All system structure is defined in JSON config files.
- **Testable**: Extensive unit and integration tests.

---

## Project Structure

```text
openscada_lite/
  app.py                  # Main Flask app and SocketIO server
  common/
    config/               # Configuration loader and validator
    models/               # DTOs, entities, and event types
    bus/                  # Event bus implementation
  frontend/
    base/                 # Base controller/service classes
    datapoints/           # Datapoint module
    commands/             # Command module
    ...
  backend/
    communications/
      drivers/            # Driver implementations (simulated, real, etc.)
      connector_manager.py# Manages driver instances and routing
  modules/
    ...                   # Additional modules (alarms, rules, etc.)
config/
  system_config.json      # Defines datapoint types, ranges, enums, etc.
  test_config.json        # Example/test configuration
tests/
  ...                     # Unit and integration tests
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your system

Edit `config/system_config.json` to define your datapoint types, ranges, enums, and defaults.  
Edit `config/test_config.json` (or create your own) to define drivers, datapoints, and their properties.

Example `system_config.json`:
```json
{
  "dp_types": {
    "LEVEL":      { "type": "float", "min": 0, "max": 100, "default": 0.0 },
    "STATUS":     { "type": "enum", "values": ["OPENED", "CLOSED"], "default": "CLOSED" },
    "PRESSURE":   { "type": "float", "min": 0, "max": 200, "default": 50.0 },
    "TEMPERATURE":{ "type": "float", "min": 100, "max": 150, "default": 120.0 }
  }
}
```

Example driver definition in `test_config.json`:
```json
{
  "drivers": [
    {
      "name": "Server1",
      "datapoints": [
        { "name": "TANK", "type": "LEVEL" },
        { "name": "PUMP", "type": "STATUS" }
      ]
    }
  ]
}
```

### 3. Run the server

```bash
python -m openscada_lite.app
```

The server will start on `http://localhost:5000`.

---

## Adding New Modules

1. **Create a new folder in `openscada_lite/frontend/` and/or `openscada_lite/modules/`**.
2. **Inherit from the base controller/service/model classes** in `frontend/base/` or `modules/base/`.
3. **Define your DTOs** in `common/models/dtos.py` if needed.
4. **Register your module in `app.py`** by instantiating its controller and passing the model/service/socketio as needed.
5. **Add your module's events and handlers** in the frontend and backend as appropriate.

---

## Adding New Drivers

1. **Create a new driver class** in `backend/communications/drivers/`, inheriting from `DriverProtocol` or a base driver.
2. **Implement required methods**: `connect`, `disconnect`, `send_command`, `subscribe`, etc.
3. **Register the driver in your config** (`test_config.json` or `system_config.json`) under `"drivers"`.
4. **The `ConnectorManager` will automatically instantiate and manage your driver** based on the config.

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