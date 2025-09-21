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

```
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