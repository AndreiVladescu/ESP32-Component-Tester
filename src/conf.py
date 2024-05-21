from machine import Pin, ADC
from time import sleep

## Pin definitions
adc_tp1, adc_tp2, adc_tp3 = 39, 34, 35
tp1_pins = [32, 33, 25]
tp2_pins = [26, 27, 14]
tp3_pins = [12, 13, 15]

## Variable definitions
debug_check = True
wifi_enabled = True

pin_res = 40

debug_trace_index = 0

css_style = """
  <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
        }

        .container {
            width: 80%;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }

        h1 {
            color: #333;
            text-align: center;
        }

        p {
            color: #666;
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 10px;
        }

        .component-info {
            text-align: center;
            margin-bottom: 20px;
        }

        .component-info img {
            width: 200px;
            height: auto;
            margin-bottom: 10px;
        }

        .test-points {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }

        .test-point {
            background-color: #e0e0e0;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }

        .characteristics {
            margin-bottom: 20px;
        }

        .characteristics h2 {
            text-align: center;
            color: #333;
        }

        .characteristics p {
            text-align: center;
        }
    </style>
"""
## Aux functions
def debug(message):
    global debug_trace_index
    if debug_check:
        print('$ ' + str(debug_trace_index) + ": " + message)
        debug_trace_index += 1

## Classes
class TestPoint:
    def __init__(self, adc_pin, r0_pin, r1_pin, r2_pin, name):
        """
        Initialize the Test Point (Pin) object.

        Args:
            adc_pin (int): The ADC pin number.
            r0_pin (int): The pin number for the shunted pin.
            r1_pin (int): The pin number for the 680 ohm resistor.
            r2_pin (int): The pin number for the 470k ohm resistor.
            name (str): The name of the Test Point (Pin).

        Returns:
            None
        """
        self.name = name

        self.adc_pin = adc_pin
        self.r0_pin = r0_pin
        self.r1_pin = r1_pin
        self.r2_pin = r2_pin

        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)

        self.r0 = Pin(r0_pin, Pin.IN)
        self.r1 = Pin(r1_pin, Pin.IN)
        self.r2 = Pin(r2_pin, Pin.IN)
        self.r0_status = 0
        self.r1_status = 0
        self.r2_status = 0

    def get_uv(self):
        return self.adc.read_uv()

    def get_v(self):
        return self.get_uv() / 10**6

    def get_status(self):
        return 'R0: {0}, R1: {1}, R2: {2}'.format(self.r0_status, self.r1_status, self.r2_status)
    
    def get_name(self):
        return self.name
    
    def set_r0_high(self):
        self.r0 = Pin(self.r0_pin, Pin.OUT)
        self.r0.on()
        self.r0_status = 1
        self.set_r1_floating()
        self.set_r2_floating()

    def set_r0_low(self):
        self.r0 = Pin(self.r0_pin, Pin.OUT)
        self.r0.off()
        self.r0_status = -1
        self.set_r1_floating()
        self.set_r2_floating()

    def set_r0_floating(self):
        self.r0_status = 0
        self.r0 = Pin(self.r0_pin, Pin.IN)

    def set_r1_high(self):
        self.r1 = Pin(self.r1_pin, Pin.OUT)
        self.r1.on()
        self.r1_status = 1
        self.set_r0_floating()
        self.set_r2_floating()

    def set_r1_low(self):
        self.r1 = Pin(self.r1_pin, Pin.OUT)
        self.r1.off()
        self.r1_status = -1
        self.set_r0_floating()
        self.set_r2_floating()

    def set_r1_floating(self):
        self.r1_status = 0
        self.r1 = Pin(self.r1_pin, Pin.IN)

    def set_r2_high(self):
        self.r2 = Pin(self.r2_pin, Pin.OUT)
        self.r2.on()
        self.r2_status = 1
        self.set_r1_floating()
        self.set_r0_floating()

    def set_r2_low(self):
        self.r2 = Pin(self.r2_pin, Pin.OUT)
        self.r2.off()
        self.r2_status = -1
        self.set_r1_floating()
        self.set_r0_floating()

    def set_r2_floating(self):
        self.r2_status = 0
        self.r2 = Pin(self.r2_pin, Pin.IN)

    def set_pins_floating(self):
        self.set_r0_floating()
        self.set_r1_floating()
        self.set_r2_floating()

# Class to handle the detected components
class Component:
    def __init__(self, name, image, data):
        self.name = name
        self.image = image
        self.data = data
    
    def get_name(self):
        return self.name
    
    def get_image(self):
        return self.image
    
    def get_data(self):
        return self.data
    