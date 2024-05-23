from conf import *

from machine import Pin, ADC, Timer
from time import sleep, sleep_us, sleep_ms, ticks_ms, ticks_diff, ticks_us
import _thread
import network
import socket
import select
import ujson
import uos
import math
import _thread
import select
import sys

rx_ch = select.poll() # new select object
rx_ch.register(sys.stdin) # register the stdin file descriptor

tp1, tp2, tp3 = None, None, None

resistor_component = Resistor(0)
diode_component = Diode(0, [0, 0])
capacitor_component = Capacitor(0)
inductor_component = Inductor(0)

detected_component = 0

def save_wifi_credentials(ssid, password):
    """
    Save the provided Wi-Fi credentials to a JSON file.

    Args:
        ssid (str): The SSID of the Wi-Fi network.
        password (str): The password of the Wi-Fi network.

    Returns:
        None
    """
    wifi_credentials = {'ssid': ssid, 'password': password}
    
    wifi_credentials_json = ujson.dumps(wifi_credentials)
    
    with open('wifi_credentials.json', 'w') as file:
        file.write(wifi_credentials_json)

def read_wifi_credentials():
    """
    Reads the WiFi credentials from a JSON file and returns the SSID and password.

    Returns:
        tuple: A tuple containing the SSID and password. If the JSON file doesn't exist, returns (None, None).
    """
    if 'wifi_credentials.json' in uos.listdir():
        with open('wifi_credentials.json', 'r') as file:
            wifi_credentials_json = file.read()
        
        wifi_credentials = ujson.loads(wifi_credentials_json)
        return wifi_credentials['ssid'], wifi_credentials['password']
    else:
        return None, None
        
def connect_wifi(ssid, password):
    """
    Connects to a WiFi network using the provided SSID and password.

    Args:
        ssid (str): The SSID of the WiFi network.
        password (str): The password of the WiFi network.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    if not ssid:  # Check if the SSID is empty
        debug('SSID is empty. Exiting...')
        return False

    wlan = network.WLAN(network.STA_IF)
    #wlan.config(dhcp_hostname = "component-tester")
    wlan.active(True)

    if not wlan.isconnected():
        debug('Connecting to WiFi...')
        wlan.connect(ssid, password)
        attempts = 0
        while not wlan.isconnected():
            if attempts > 10:
                debug('Failed to connect after 10 attempts. Exiting...')
                return False
            sleep(1)
            attempts += 1
    debug('Connected to WiFi: ' + ssid)
    debug('IP address: ' + wlan.ifconfig()[0])
    return True
    
def handle_request(conn):
    """
    Handles a client request by sending an HTTP response.

    Args:
        conn (socket): The client socket.

    Returns:
        None
    """
    global resistor_component, diode_component, capacitor_component, inductor_component
    global detected_component
    template_content  = ""
    
    with open('template.html', 'r') as file:
        template_content = file.read()
    
    component_name = ''
    component_image_url = ''
    component_characteristics = ''
    
    if detected_component & 3:    
        component_name = diode_component.get_name()
        component_image_url = diode_component.get_image()
        component_characteristics = diode_component.get_data()
    elif detected_component == 1:
        component_name = resistor_component.get_name()
        component_image_url = resistor_component.get_image()
        component_characteristics = resistor_component.get_data()
    elif detected_component & 2:
        component_name = capacitor_component.get_name()
        component_image_url = capacitor_component.get_image()
        component_characteristics = capacitor_component.get_data()
    elif detected_component & 8:
        component_name = inductor_component.get_name()
        component_image_url = inductor_component.get_image()
        component_characteristics = inductor_component.get_data()
        
    detected_component = 0
    
    dynamic_data = {
        'tp1': str(tp1.get_v()),
        'tp2': str(tp2.get_v()),
        'tp3': str(tp3.get_v()),
        'component_name': component_name,
        'component_image_url': component_image_url,
        'component_characteristics': component_characteristics,
        'css_style': css_style,
    }
    
    rendered_content = template_content.format(**dynamic_data)
    
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + rendered_content
    
    conn.send(response.encode())  # Send the HTTP response
    conn.close()  # Close the connection

def init_wifi():
    """
    Initializes the Wi-Fi connection and starts the server.

    Returns:
        None
    """
    saved_ssid, saved_password = read_wifi_credentials()
    if saved_ssid and saved_password:
        debug("Found saved WiFi AP: {0} with password {1}".format(saved_ssid, saved_password))
        wifi_connected = connect_wifi(saved_ssid, saved_password)
        if wifi_connected:
            _thread.start_new_thread(start_server, ())
            debug("###################\n$ ## WiFi Pass: OK ##\n$ ###################\n$")
        
def start_server():
    """
    Starts a TCP/IP server on address '0.0.0.0' and port 80.
    Listens for incoming connections and handles client requests.

    Returns:
        None
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Set the socket option to reuse the address
    s.bind(('0.0.0.0', 80))  # Bind the socket to address and port
    s.listen(5)  # Listen for incoming connections

    debug("Server started. Waiting for connections...")

    inputs = [s]  # List of input sockets including the server socket

    while True:
        readable, _, _ = select.select(inputs, [], [])  # Select readable sockets

        for sock in readable:
            if sock is s:  # If the server socket is readable, accept new connection
                conn, addr = s.accept()  # Accept a connection
                debug("Connection from:" + str(addr))
                inputs.append(conn)  # Add the new connection to the list of inputs
            else:  # If a client socket is readable, handle the request
                request = sock.recv(1024)  # Receive data from the client
                debug("Request:" + str(request))
                handle_request(sock)
                inputs.remove(sock)  # Remove the client socket from the list of inputs
        sleep(1)  # Wait for 1 second before checking for new connections

def rx_serial_thread():
    global rx_ch
    
    while True:
        if rx_ch.poll(0): #is data available? .poll(0) returns an empty list if no data is available
            res = ""
            while rx_ch.poll(1):
                res+=(sys.stdin.read(1))
            print("got:",res)
        sleep(1)

def tx_serial_thread():
    while True:
        # TODO serial comms
        sleep(1)

def init_serial():
    _thread.start_new_thread(rx_serial_thread, ())
    _thread.start_new_thread(tx_serial_thread, ())

def init_pins():
    """
    Initializes the test points (tp1, tp2, tp3) with their respective ADC channels and pin configurations.
    """
    global tp1, tp2, tp3
    # Test point 1/A
    tp1 = TestPoint(adc_tp1, tp1_pins[0], tp1_pins[1], tp1_pins[2], 'TP1')
    # Test point 2/B
    tp2 = TestPoint(adc_tp2, tp2_pins[0], tp2_pins[1], tp2_pins[2], 'TP2')
    # Test point 3/C
    tp3 = TestPoint(adc_tp3, tp3_pins[0], tp3_pins[1], tp3_pins[2], 'TP3')

def measure_resistance_function(tp_x, tp_y, resistance):
    adc_tpx = 0
    adc_tpy = 0

     ## Loop I, TP-Y measures now
    tp_x.set_r0_low()
    
    if resistance == 680:
        debug('680 Low Impedance Test')
        tp_y.set_r1_high()
    else:
        debug('470k Low Impedance Test')
        tp_y.set_r2_high()

    sleep(0.005)
    debug('High-side {0}: {1} v'.format(tp_y.get_name(), tp_y.get_v()))
    
    for i in range(0, 10):
        adc_tpy += tp_y.get_v()
        #sleep(0.005)
    
    adc_tpy = adc_tpy / 10
    
    debug('Average voltage tpy: {0} v'.format(adc_tpy))
    
    # Disarming the pins
    tp_y.set_pins_floating()
    tp_x.set_pins_floating()
    ## Loop II, TP-X measures now
    if resistance == 680:
        debug('680 Low Impedance Test')
        tp_x.set_r1_low()
    else:
        debug('470k High Impedance Test')
        tp_x.set_r2_low()
        
    tp_y.set_r0_high()
    sleep(0.005)
    
    debug('Low-side {0}: {1} v'.format(tp_x.get_name(), tp_x.get_v()))
    
    for i in range(0, 10):
        adc_tpx += tp_x.get_v()
        #sleep(0.005)
    
    adc_tpx = adc_tpx / 10
    
    debug('Average voltage tpx: {0} v'.format(adc_tpx))
    
    temp_resistance = 0
    
    if resistance == 680:
        temp_resistance = adc_tpy*(resistance+pin_res)/adc_tpx - pin_res
    else:
        temp_resistance = adc_tpy * resistance / adc_tpx
        
    
    # Disarming the pins
    tp_y.set_pins_floating()
    tp_x.set_pins_floating()
    
    return temp_resistance

def measure_resistance():
    global detected_component
    global tp1, tp2, tp3
    global resistor_component

    temp_resistance1 = measure_resistance_function(tp1, tp2, 680)
    #print(temp_resistance1)
    
    temp_resistance2 = measure_resistance_function(tp2, tp1, 680)
    #print(temp_resistance2)
    
    temp_resistance3 = measure_resistance_function(tp1, tp2, 470000)
    #print(temp_resistance3)
    
    temp_resistance4 = measure_resistance_function(tp2, tp1, 470000)
    #print(temp_resistance4)
    
    avg_resistance1 = (temp_resistance1 + temp_resistance2) / 2
    avg_resistance2 = (temp_resistance3 + temp_resistance4) / 2
    
    if avg_resistance1 < 10000:
        resistor_component = Resistor(avg_resistance1)
        print(avg_resistance1)
    else:
        resistor_component = Resistor(avg_resistance2)
        print(avg_resistance2)
    
    detected_component += 1

def capacitor_discharge(tp_x, tp_y):
    # Safety check
    tp_x.set_r0_low()
    tp_y.set_r1_low()
    
    # Testing if the would-be capacitor has any charge left
    cap_voltage_x = tp_x.get_v()
    cap_voltage_y = tp_y.get_v()

    cap_threshold_voltage = 3.2
    if cap_voltage_x > cap_threshold_voltage or cap_voltage_y > cap_threshold_voltage:
        debug('Capacitor has big charge. Discharge it with a screwdriver')
        return -2

    # debug('Capacitor has a small charge. Short the pins')
    # Pin shorting through the 680 Ohm resistor
    
    max_count_discharge = 64
    discharge_index = 0

    while tp_x.get_v() > 0.16 or tp_y.get_v() > 0.16:
        sleep(0.2)
        
        debug('Discharging status: TP X: {0}, TP Y: {1}'.format(tp_x.get_v(), tp_y.get_v()))
        discharge_index+=1
        
        if discharge_index > max_count_discharge:
            debug('Discharge failed. Exiting...')
            return -1

    return 0

def capacitor_charge(tp_x, tp_y):
    pulse_time_ms = 1
    pulse_count = 0
    pulse_timeout = 4096
    capacitor_target_voltage = 2.0856 #0.86 * 3.3 #2.0856 # 0.632 * 3.3 
    # Charge the pins
    
    start = ticks_ms() # get millisecond counter
    
    tp_x.set_r0_low()
    tp_y.set_r1_high()
    
    # Capacitor missing
    if tp_y.get_v() > capacitor_target_voltage:
        tp_x.set_pins_floating()
        tp_y.set_pins_floating()
        debug('No capacitor detected')
        return -2
    
    diode_double_check = False
    
    while pulse_count < pulse_timeout:
        
        #sleep_ms(pulse_time_ms)
        #print(tp_x.get_v(), tp_y.get_v())
        tp_y_v = tp_y.get_v()
        pulse_count += 1
        
        debug('Charging status: TP X: {0}, TP Y: {1}'.format(tp_x.get_v(), tp_y.get_v()))
        
        if pulse_count >= 16 and (tp_y_v >= 1.9 and tp_y_v <= 1.92):
            if not diode_double_check:
                diode_double_check = True
            else:
                tp_x.set_pins_floating()
                tp_y.set_pins_floating()
                delta = ticks_diff(ticks_ms(), start)
                return delta
        
        if tp_y_v > capacitor_target_voltage:
            tp_x.set_pins_floating()
            tp_y.set_pins_floating()
            delta = ticks_diff(ticks_ms(), start)
            return delta
        
    debug('Capacitor charge failed. Exiting...')
    
    tp_x.set_pins_floating()
    tp_y.set_pins_floating()
    
    return -1

def measure_capacitance_test(tp_x, tp_y):
    global capacitor_component
    global detected_component
    
    # Discharge the capacitor
    rc = capacitor_discharge(tp_x, tp_y)
    
    if rc == -1:
        # treat capacitor big charge
        return
    elif rc == -2:
        # treat capacitor discharge fail
        return
    
    # Charge the capacitor
    rc = capacitor_charge(tp_x, tp_y)
    if rc == -1:
        # treat capacitor charge fail
        return
    elif rc == -2:
        # treat capacitor not detected
        return
    
    detected_component += 2

    capacitance = rc / 680 * 1000 # capacitance in uF
    capacitor_component = Capacitor(capacitance)
    debug('Capacitance: {0} uF'.format(capacitance))

def measure_capacitance():
    global tp1, tp2, tp3
    measure_capacitance_test(tp1, tp2)
    measure_capacitance_test(tp2, tp1)

def inductor_discharge(tp_x, tp_y):
    # Safety check
    tp_x.set_r0_low()
    tp_y.set_r1_low()
    
    # Pin shorting through the 680 Ohm resistor
    
    max_count_discharge = 4
    discharge_index = 0

    while tp_x.get_v() > 0.16 or tp_y.get_v() > 0.16:
        sleep(0.2)
        
        debug('Discharging status: TP X: {0}, TP Y: {1}'.format(tp_x.get_v(), tp_y.get_v()))
        discharge_index+=1
        
        if discharge_index > max_count_discharge:
            debug('Discharge failed. Exiting...')
            return -1

    return 0

def measure_inductance_test(tp_x, tp_y):
    global inductor_component
    global detected_component
    
    debug('Inductor test')
    # Discharge the inductor
    rc = inductor_discharge(tp_x, tp_y)
    
    if rc == -1:
        # treat inductor big charge
        return -1
    
    # Charge the inductor

    time_us = 1
    sleep(0.05)

    tp_x.set_r1_low()
    voltage = tp_x.get_v()
    # debug("Initial voltage: {0}".format(voltage))


    tp_y.set_r0_high()
    sleep_us(time_us)
    tp_y.set_r0_low()
    
    voltage = tp_x.get_v()


    diff = time_us * 10**(-6)
    #voltage = 2.05
    inductance = - diff * 680 / math.log(1-voltage/3.3) * 1000 # inductance in mH
    # debug("Uref: {0}, t: {1}, Inductance: {2}".format(voltage, diff, inductance))
    detected_component += 8

    inductor_component = Inductor(inductance)
    debug('Inductance: {0} mH'.format(inductance))

def measure_inductance():
    global tp1, tp2, tp3
    measure_inductance_test(tp1, tp2)

def test_diode(tp_x, tp_y):
    diode_detected = False
    forward_voltage = -1
    flow_direction = (tp_x.get_name(), tp_y.get_name())
    
    tp_x.set_pins_floating()
    tp_y.set_pins_floating()
    
    # Testing which is cathode and anode part 1
    tp_x.set_r1_low()
    tp_y.set_r0_high()
    
    y_x_current_flow = False
    y_x_forward_voltage = 0
    
    if tp_x.get_v() > 0.15:
        y_x_current_flow = True
        y_x_forward_voltage = tp_y.get_v() - tp_x.get_v() #3.3 or tp_y.get_v for accuracy
        flow_direction = (tp_y.get_name(), tp_x.get_name()) # current flows from y to x
    
    # Testing which is cathode and anode part 1
    tp_y.set_r0_floating()
    tp_y.set_r1_low()
    tp_x.set_r0_high()
    
    x_y_current_flow = False
    x_y_forward_voltage = 0
    
    if tp_y.get_v() > 0.15:
        x_y_current_flow = True
        x_y_forward_voltage = tp_x.get_v() - tp_y.get_v() #3.3 or tp_x.get_v for accuracy
        flow_direction = (tp_x.get_name(), tp_y.get_name()) # current flows from x to y
         
    diode_detected = x_y_current_flow != y_x_current_flow
    
    if diode_detected:
        forward_voltage = max(x_y_forward_voltage, y_x_forward_voltage)
    
    tp_x.set_pins_floating()
    tp_y.set_pins_floating()
    
    return diode_detected, forward_voltage, flow_direction
    
def measure_semiconductors():
    global tp1, tp2, tp3
    global diode_component
    
    diode_detected = False
    forward_voltage = -1
    flow_direction = ('none', 'none')
    
    diode_detected, forward_voltage, flow_direction = test_diode(tp1, tp2)
    
    if diode_detected:
        debug('Diode detected with Vf: {0}, cathode at {1} and anode at {2}'.format(forward_voltage, flow_direction[1], flow_direction[0]))
        diode_component = Diode(forward_voltage, flow_direction)
    else:
        debug('Diode not detected between {0} and {1}'.format(flow_direction[1], flow_direction[0]))
    
    '''
    diode_detected, forward_voltage, flow_direction = test_diode(tp1, tp3)
    
    if diode_detected:
        debug('Diode detected with Vf: {0}, cathode at {1} and anode at {2}'.format(forward_voltage, flow_direction[1], flow_direction[0]))
    else:
        debug('Diode not detected at {0} and {1}'.format(flow_direction[1], flow_direction[0]))
        
    diode_detected, forward_voltage, flow_direction = test_diode(tp2, tp3)
        
    if diode_detected:
        debug('Diode detected with Vf: {0}, cathode at {1} and anode at {2}'.format(forward_voltage, flow_direction[1], flow_direction[0]))
    else:
        debug('Diode not detected at {0} and {1}'.format(flow_direction[1], flow_direction[0]))
    '''
def measure_phase():
    
    measure_inductance()
    #measure_capacitance()
    #measure_semiconductors()
    #measure_resistance()
    
    
def main():
    global wifi_enabled
    
    init_pins()
    debug("###################\n$ ## Init Pass: OK ##\n$ ###################\n$")
    
    #init_serial()
    #debug("\n$ ###########################\n$ ## Serial Comms Pass: OK ##\n$ ###########################\n$ ")
    
    if wifi_enabled:
        init_wifi()
    
    measure_phase()
    
    debug("\n$ ##########################\n$ ## Measurement Pass: OK ##\n$ ##########################\n$ ")
    
    debug("\n$ #####################\n$ ## Loop Status: OK ##\n$ #####################\n$ ")
if __name__ == "__main__":
    main()






