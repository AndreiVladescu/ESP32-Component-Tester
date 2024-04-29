from machine import Pin, ADC
from time import sleep

## Pin definitions
adc_tp1, adc_tp2, adc_tp3 = 39, 34, 35
tp1_pins = [32, 33, 25]
tp2_pins = [26, 27, 14]
tp3_pins = [12, 13, 15]

## Variable definitions
debug_check = True


class TestPoint:
    def __init__(self, adc_pin, r0_pin, r1_pin, r2_pin):

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
        self.set_r2_floating()

    def set_r2_low(self):
        self.r2 = Pin(self.r2_pin, Pin.OUT)
        self.r2.off()
        self.r2_status = -1
        self.set_r1_floating()
        self.set_r2_floating()

    def set_r2_floating(self):
        self.r2_status = 0
        self.r2 = Pin(self.r2_pin, Pin.IN)


tp1, tp2, tp3 = None, None, None

## Aux functions
def debug(message):
    if debug_check:
        print(message)


def init_pins():
    global tp1, tp2, tp3
    # Test point 1/A
    tp1 = TestPoint(adc_tp1, tp1_pins[0], tp1_pins[1], tp1_pins[2])
    # Test point 2/B
    tp2 = TestPoint(adc_tp2, tp2_pins[0], tp2_pins[1], tp2_pins[2])
    # Test point 3/C
    tp3 = TestPoint(adc_tp3, tp3_pins[0], tp3_pins[1], tp3_pins[2])


def measure_resistance_680(tp_x, tp_y):
    tp_x.set_r0_low()
    tp_y.set_r1_high()
    sleep(0.001)
    print(tp_x.get_v())
    print(tp_y.get_v())

def measure_resistance_470k(tp_x, tp_y):
    tp_x.set_r0_low()
    tp_y.set_r2_high()
    sleep(0.001)
    print(tp_x.get_v())
    print(tp_y.get_v())

def measure_resistance(tp_x, tp_y):
    print("Before")
    measure_resistance_680(tp_x, tp_y)
    measure_resistance_470k(tp_x, tp_y)
    
def measure_phase():
    global tp1, tp2, tp3
    measure_resistance(tp1, tp2)
    measure_resistance(tp2, tp1)

def main():
    init_pins()
    debug("Init OK")

    measure_phase()
    

if __name__ == "__main__":
    main()
