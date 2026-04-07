import importlib

level_sensor_pump_actor = importlib.import_module("cbpi4-LevelSensorPumpActor.level_sensor_pump_actor")

def setup(cbpi):
    '''
    This method is called by the server during startup
    Here you need to register your plugins at the server
    :param cbpi: the cbpi core
    '''
    cbpi.plugin.register("Level Sensor Pump Actor", level_sensor_pump_actor.LevelSensorPumpActor)
    pass