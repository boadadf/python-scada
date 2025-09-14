from .test_driver import TestDriver

# Registry of available drivers
DRIVER_REGISTRY = {
    "TestDriver": TestDriver,
    # later we’ll add "OpcUaDriver": OpcUaDriver, etc.
}