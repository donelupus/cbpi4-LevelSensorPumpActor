import pytest
import importlib
import types
from unittest.mock import MagicMock, Mock, AsyncMock
import logging
import sys
import asyncio
import os


logger = logging.getLogger(__name__)

@pytest.fixture
def mock_sleep(monkeypatch):
    original_sleep = asyncio.sleep
    mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", mock)
    mock.original_sleep = original_sleep
    yield mock

@pytest.fixture
def level_sensor_pump():
    # Fake GPIO module
    fake_gpio = types.ModuleType("RPi.GPIO")
    fake_gpio.OUT = "OUT"
    fake_gpio.IN = "IN"
    fake_gpio.LOW = "LOW"
    fake_gpio.HIGH = "HIGH"
    fake_gpio.BCM = "BCM"
    fake_gpio.PUD_DOWN = 21
    fake_gpio.getmode = MagicMock(return_value=None)
    fake_gpio.setmode = MagicMock()
    fake_gpio.setup = MagicMock()
    fake_gpio.output = MagicMock()
    fake_gpio.input = MagicMock()

    rpi_pkg = types.ModuleType("RPi")
    rpi_pkg.__path__ = [""]
    rpi_pkg.GPIO = fake_gpio

    # Mock cbpi modules required by the actor import
    cbpi_mod = types.ModuleType("cbpi")
    cbpi_api_mod = types.ModuleType("cbpi.api")
    cbpi_dataclasses_mod = types.ModuleType("cbpi.api.dataclasses")

    class MockCBPiActorBase:
        def __init__(self, cbpi, id, props):
            self.cbpi = cbpi
            self.id = id
            self.props = props
            self.running = False

    cbpi_api_mod.CBPiActor = MockCBPiActorBase
    cbpi_api_mod.parameters = lambda *args, **kwargs: lambda cls: cls
    cbpi_api_mod.Property = types.SimpleNamespace(
        Number=lambda *args, **kwargs: None,
        Select=lambda *args, **kwargs: None,
        Actor=lambda *args, **kwargs: None
    )
    cbpi_dataclasses_mod.NotificationType = types.SimpleNamespace(
        INFO="INFO",
        WARNING="WARNING",
        ERROR="ERROR"
    )

    sys.modules["RPi"] = rpi_pkg
    sys.modules["RPi.GPIO"] = fake_gpio
    sys.modules["cbpi"] = cbpi_mod
    sys.modules["cbpi.api"] = cbpi_api_mod
    sys.modules["cbpi.api.dataclasses"] = cbpi_dataclasses_mod

    # Python must be able to locate the package directory to import the actor module, so we add the parent directory of the package to sys.path
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    # Ensure the SUT is reloaded fresh each time
    if "cbpi4-LevelSensorPumpActor.level_sensor_pump_actor" in sys.modules:
        del sys.modules["cbpi4-LevelSensorPumpActor.level_sensor_pump_actor"]

    LevelSensorPumpActor = importlib.import_module("cbpi4-LevelSensorPumpActor.level_sensor_pump_actor")

    mock_cbpi = Mock()
    mock_cbpi.actor = Mock()
    mock_cbpi.actor.actor_update = AsyncMock(return_value="ok")

    props = {
        "notification": "No",
        "gpio_pump": 8,
        "gpio_level_upper": 12,
        "gpio_level_lower": 16
    }

    level_sensor_pump_actor = LevelSensorPumpActor.LevelSensorPumpActor(mock_cbpi, "ID", props)

    yield level_sensor_pump_actor, fake_gpio

@pytest.mark.asyncio
async def test_actor_initialization(level_sensor_pump):
    """Test that the LevelSensorPumpActor initializes correctly."""
    print("Testing LevelSensorPumpActor initialization...")

    ####  Arrange  ####
    actor, fake_gpio = level_sensor_pump

    ######  Act  ######
    try:
        await actor.on_start()

    ##### Assert  #####
    except Exception as e:
        assert False, f"Initialization raised an exception: {e}"

@pytest.mark.asyncio
async def test_run_iteration_switches_pump_on_and_off(level_sensor_pump):
    """Test the run_iteration method switches the pump output correctly."""

    ####  Arrange  ####
    actor, fake_gpio = level_sensor_pump
    await actor.on_start()

    ######  Act when empty ######

    # Both sensors low should switch the pump off.
    fake_gpio.input.side_effect = [0, 0]
    actor.run_iteration()

    ##### Assert  #####
    fake_gpio.output.assert_called_with(int(actor.gpio_pump), fake_gpio.LOW)

    ######  Act when filling ######

    # Upper level sensor low, lower level sensor high should not change the pump state.
    fake_gpio.input.side_effect = [0, 1]
    actor.run_iteration()

    ##### Assert  #####
    fake_gpio.output.assert_called_with(int(actor.gpio_pump), fake_gpio.LOW)

    ######  Act when full ######

    # Both sensors high should switch the pump on.
    fake_gpio.input.side_effect = [1, 1]
    actor.run_iteration()

    ##### Assert  #####
    fake_gpio.output.assert_called_with(int(actor.gpio_pump), fake_gpio.HIGH)

    ######  Act when emptying ######

    # Upper level sensor low, lower level sensor high should not change the pump state.
    fake_gpio.input.side_effect = [0, 1]
    actor.run_iteration()

    ##### Assert  #####
    fake_gpio.output.assert_called_with(int(actor.gpio_pump), fake_gpio.HIGH)
