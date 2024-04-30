from conf import *
from web_service import *

from machine import Pin, ADC
from time import sleep
import _thread
        
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
    debug('Low-side {0}: {1} v'.format(tp_x.get_name(), tp_x.get_v()))
    debug('High-side {0}: {1} v'.format(tp_y.get_name(), tp_y.get_v()))
    average_current_tpx = 0
    average_current_tpy = 0
    for i in range(0, 9):
        average_current_tpx = tp_x.get_uv()
        average_current_tpy = tp_y.get_uv()
    
    average_current_tpx = average_current_tpx / 10
    average_current_tpy = average_current_tpy / 10
        
    debug('Average tpx: {0} uv'.format(average_current_tpx))
    debug('Average tpy: {0} uv'.format(average_current_tpy))
    
    # R = U/I
    # 680 ohms for low resistance test, + 
    resistance = 3.3 / average_current_tpx - 680 - esp32_driving_pin_resistance
    print(resistance)
    
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
    measure_resistance_680(tp2, tp1)
    measure_resistance_470k(tp1, tp2)
    measure_resistance_470k(tp2, tp1)
    
def measure_phase():
    measure_resistance()

def main():
    connect_wifi('DEV', '%yE+Tr_4hru87Kx4')
    
    _thread.start_new_thread(start_server, ())
    
    debug("###################\n$ ## WiFi Pass: OK ##\n$ ###################\n$")
    
    init_pins()
    debug("###################\n$ ## Init Pass: OK ##\n$ ###################\n$")

    measure_phase()
    
    debug("\n$ ##########################\n$ ## Measurement Pass: OK ##\n$ ##########################\n$ ")

if __name__ == "__main__":
    main()
