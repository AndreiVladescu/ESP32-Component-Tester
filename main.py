from machine import Pin, ADC
from time import sleep

## Pin definitions
adc_tp1, adc_tp2, adc_tp3 = 39, 34, 35
tp1_pins = [32, 33, 25]
tp2_pins = [26, 27, 14]
tp3_pins = [12, 13, 15]

## Variable definitions
debug_check = True
esp32_driving_pin_resistance = 40

class TestPoint:
    def __init__(self, adc_pin, r0_pin, r1_pin, r2_pin, name):
            
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
        print('$ ' + message)


def init_pins():
    global tp1, tp2, tp3
    # Test point 1/A
    tp1 = TestPoint(adc_tp1, tp1_pins[0], tp1_pins[1], tp1_pins[2], 'TP1')
    # Test point 2/B
    tp2 = TestPoint(adc_tp2, tp2_pins[0], tp2_pins[1], tp2_pins[2], 'TP2')
    # Test point 3/C
    tp3 = TestPoint(adc_tp3, tp3_pins[0], tp3_pins[1], tp3_pins[2], 'TP3')


def measure_resistance_680(tp_x, tp_y):
    tp_x.set_r0_low()
    tp_y.set_r1_high()
    sleep(0.001)
    debug('680 Low Impedance Test')
    debug('Low-side {0}: {1}'.format(tp_x.get_name(), tp_x.get_v()))
    debug('High-side {0}: {1}'.format(tp_y.get_name(), tp_y.get_v()))
    average_current_tpx = 0
    average_current_tpy = 0
    for i in range(0, 9):
        average_current_tpx = tp_x.get_uv()
        average_current_tpy = tp_y.get_uv()
    
    average_current_tpx = average_current_tpx / 10
    average_current_tpy = average_current_tpy / 10
    
    debug('Average tpx: {0}'.format(average_current_tpx))
    debug('Average tpy: {0}'.format(average_current_tpy))
    
def measure_resistance_470k(tp_x, tp_y):
    tp_x.set_r0_low()
    tp_y.set_r2_high()
    sleep(0.001)
    debug('470k High Impedance Test')
    debug('Low-side {0}: {1}'.format(tp_x.get_name(), tp_x.get_v()))
    debug('High-side {0}: {1}'.format(tp_y.get_name(), tp_y.get_v()))

def measure_resistance():
    global tp1, tp2, tp3
    measure_resistance_680(tp1, tp2)
    return
    measure_resistance_680(tp2, tp1)
    measure_resistance_470k(tp1, tp2)
    measure_resistance_470k(tp2, tp1)
    
def measure_phase():
    measure_resistance()

def main():
    init_pins()
    debug("###################\n$ ## Init Pass: OK ##\n$ ###################\n$")

    measure_phase()
    
    debug("\n$ ##########################\n$ ## Measurement Pass: OK ##\n$ ##########################\n$ ")

if __name__ == "__main__":
    main()
