# -*- coding: utf-8 -*-
import logging
import asyncio
from cbpi.api import *
import RPi.GPIO as GPIO
from cbpi.api.dataclasses import NotificationType


mode = GPIO.getmode()
if mode == None:
    GPIO.setmode(GPIO.BCM)
    
class Logger():
    def __init__(self,cbpi):
        self.cbpi=cbpi
        self.logger = logging.getLogger(__name__)

    def set_notification(self, notification):
        self.notification = notification

    def debug(self, message):
        self.logger.debug(f"LevelSensorPumpActor - {message}")

    def info(self, message):
        self.logger.info(f"LevelSensorPumpActor - {message}")
        if self.notification == "Yes":
            self.cbpi.notify("LevelSensorPumpActor", message, NotificationType.INFO)

    def warning(self, message):
        self.logger.warning(f"LevelSensorPumpActor - {message}")
        if self.notification == "Yes":
            self.cbpi.notify("LevelSensorPumpActor", message, NotificationType.WARNING)

    def error(self, message):
        self.logger.error(f"LevelSensorPumpActor - {message}")
        if self.notification == "Yes":
            self.cbpi.notify("LevelSensorPumpActor", message, NotificationType.ERROR)

@parameters([Property.Select(label="notification", options=["Yes", "No"], description="Will show notification when GPIO switches actor off"),
             Property.Select(label="logic", options=["Vorlaufgefaess", "Laeuterbottich"], description="Vorlaufgefaess: Pump is on when both sensors are high. Laeuterbottich: Pump is on when both sensors are low"),
             Property.Number(label="gpio_pump", description="The GPIO pin for the pump (BCM numbering)"),
             Property.Number(label="gpio_level_upper", description="The GPIO pin for the upper level sensor (BCM numbering)"),
             Property.Number(label="gpio_level_lower", description="The GPIO pin for the lower level sensor (BCM numbering)")])


class LevelSensorPumpActor(CBPiActor):

    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.logger = Logger(cbpi)
        self.logger.debug("Init called")

    
    async def on_start(self):
        '''
        This method defines initial variables for the actor instance.
        '''
        self.logger.debug("On_start method called")

        self.notification = self.props.get("notification", "Yes")
        self.logger.set_notification(self.notification)

        self.logic = self.props.get("logic", "Vorlaufgefaess")

        self.gpio_pump = int(self.props.get("gpio_pump", 8))
        self.gpio_level_upper = int(self.props.get("gpio_level_upper", 9))
        self.gpio_level_lower = int(self.props.get("gpio_level_lower", 19))

        GPIO.setup(self.gpio_pump, GPIO.OUT)
        GPIO.output(self.gpio_pump, GPIO.LOW)

        GPIO.setup(self.gpio_level_upper, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.gpio_level_lower, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.state = False
        self.logger.debug(f"Variable state: {self.state}")
    
        pass

    async def on(self, power=0):
        '''
        This asyncio coroutine defines what needs to be done to switch the actor on.
        :param power: power to be set
        '''
        self.logger.info(f"ACTOR {self.id} ON")
        self.state = True

    def get_state(self):
        '''
        This method is called e.g. by server functions to read the state of the actor
        '''
        self.logger.debug("Get_state coroutine called")
        return self.state
    
    async def off(self):
        '''
        This asyncio coroutine defines what needs to be done to switch the actor off.
        '''
        self.logger.info(f"ACTOR {self.id} OFF")
        GPIO.output(int(self.gpio_pump), GPIO.LOW)
        self.state = False

    async def run(self):
        '''
        This asyncio coroutine is continuously running, while the actor is available in the system.
        '''

        self.logger.debug("Run coroutine called")
        while self.running == True:
            if self.state == True:
                self.run_iteration()

            await asyncio.sleep(1)

    def run_iteration(self):
        level_upper=GPIO.input(int(self.gpio_level_upper))
        level_lower=GPIO.input(int(self.gpio_level_lower))
        self.logger.debug(f"Run iteration: level_upper: {level_upper} and level_lower: {level_lower}")



        if level_upper and level_lower:
            if self.logic == "Vorlaufgefaess":
                self.logger.debug("Both sensors are high, switch pump on.")
                GPIO.output(int(self.gpio_pump), GPIO.HIGH)
            elif self.logic == "Laeuterbottich":
                self.logger.debug("Both sensors are high, switch pump off.")
                GPIO.output(int(self.gpio_pump), GPIO.LOW)

        elif not level_upper and not level_lower:
            if self.logic == "Vorlaufgefaess":
                self.logger.debug("Both sensors are low, switch pump off.")
                GPIO.output(int(self.gpio_pump), GPIO.LOW)
            elif self.logic == "Laeuterbottich":
                self.logger.debug("Both sensors are low, switch pump on.")
                GPIO.output(int(self.gpio_pump), GPIO.HIGH)