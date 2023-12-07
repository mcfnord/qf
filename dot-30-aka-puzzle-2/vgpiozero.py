import time
import threading
import os

class gpiozero:

    def __init__(self):
        pass

    def LED(pin, active_high=True, initial_value=False, pin_factory=None):
        pass

    class PWMLED:
        def __init__ (self, individualOutput, active_high=False):
            pass

        def off(self):
            pass

    class Button:
        def __init__ (self, pin, pull_up=True, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
            self.pin = pin
            pass
        

