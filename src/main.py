from conf import *

from machine import Pin, ADC
from time import sleep
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
    wlan.config(dhcp_hostname = "component-tester")
    wlan.active(True)

    if not wlan.isconnected():
        debug('Connecting to WiFi...')
        wlan.connect(ssid, password)
        attempts = 0
        while not wlan.isconnected():
            if attempts > 3:
                debug('Failed to connect after 3 attempts. Exiting...')
                return False
            sleep(1)
            attempts += 1
    debug('Connected to WiFi:' + ssid)
    debug('IP address:' + wlan.ifconfig()[0])
    return True
    
def handle_request(conn):
    """
    Handles a client request by sending an HTTP response.

    Args:
        conn (socket): The client socket.

    Returns:
        None
    """
    template_content  = ""
    
    with open('template.html', 'r') as file:
        template_content = file.read()
        
    dynamic_data = {
        'tp1_v': str(tp1.get_v()) + " " + tp1.get_status(),
        'tp2_v': str(tp2.get_v()) + " " + tp2.get_status(),
        'tp3_v': str(tp3.get_v()) + " " + tp3.get_status(),
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
        debug("Found saved WiFi AP: {0} with password {1}", saved_ssid, saved_password)

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

    sleep(0.001)
    debug('High-side {0}: {1} v'.format(tp_y.get_name(), tp_y.get_v()))
    
    for i in range(0, 10):
        adc_tpy += tp_y.get_v()
    
    adc_tpy = adc_tpy / 10
    
    debug('Average voltage tpy: {0} v'.format(adc_tpy))
    
    # Disarming the pins
    tp_y.set_pins_floating()
    
    ## Loop II, TP-X measures now
    tp_x.set_r1_low()
    tp_y.set_r0_high()
    
    debug('Low-side {0}: {1} v'.format(tp_x.get_name(), tp_x.get_v()))
    
    for i in range(0, 10):
        adc_tpx += tp_x.get_v()
    
    adc_tpx = adc_tpx / 10
    
    debug('Average voltage tpx: {0} v'.format(adc_tpx))

    print(adc_tpy*(resistance+pin_res)/adc_tpx - pin_res)
    
    # Disarming the pins
    tp_y.set_pins_floating()

def measure_resistance():
    global tp1, tp2, tp3
    measure_resistance_function(tp1, tp2, 680)
    measure_resistance_function(tp2, tp1, 680)
    measure_resistance_function(tp1, tp2, 470000)
    measure_resistance_function(tp2, tp1, 470000)

def capacitor_discharge(tp_x, tp_y):
    # Safety check
    tp_x.set_pins_floating()
    tp_y.set_pins_floating()
    
    # Testing if the would-be capacitor has any charge left
    cap_voltage_x = tp_x.get_v()
    cap_voltage_y = tp_y.get_v()
    
    cap_threshold_voltage = 1.3

    if cap_voltage_x > cap_threshold_voltage or cap_voltage_y > cap_threshold_voltage:
        debug('Capacitor has big charge. Discharge it with a screwdriver')
        return -2

    debug('Capacitor has a small charge. Short the pins')
    # Pin shorting through the 680 Ohm resistor
    tp_x.set_r0_low()
    tp_y.set_r1_low()
    max_count_discharge = 10
    index = 0
    while tp_x.get_v() > 0.1 or tp_y.get_v() > 0.1:
        sleep(0.05)
        index+=1
        if index > max_count_discharge:
            debug('Discharge failed. Exiting...')
            return -1

    return 0

def capacitor_charge(tp_x, tp_y):
    pulse_time_ms = 10
    pulse_count = 0
    pulse_timeout = 256
    capacitor_minimum_threshold = 63.2 * 3.3 
    # Charge the pins
    tp_x.set_r0_low()
    tp_y.set_r1_high()

    while pulse_count < pulse_timeout:
        sleep(pulse_time_ms/1000)
        pulse_count += 1
        if tp_x.get_v() > capacitor_minimum_threshold or tp_y.get_v() > capacitor_minimum_threshold:
            return pulse_count
        
    debug('Capacitor charge failed. Exiting...')

    return -1

def measure_capacitance_test(tp_x, tp_y):

    # Discharge the capacitor
    rc = capacitor_discharge(tp_x, tp_y)
    
    if rc == -1:
        # treat capacitor big charge
        return
    elif rc == -2:
        # treat capacitor discharge fail
        return
    
    # Charge the pins
    rc = capacitor_charge(tp_x, tp_y)
    if rc == -1:
        # treat capacitor charge fail
        return
    
    capacitance = rc / (68 * math.log(2)) # capacitance in uF

    debug('Capacitance: {0} F'.format(capacitance))

def measure_capacitance():
    global tp1, tp2, tp3
    measure_capacitance_test(tp1, tp2)
    measure_capacitance_test(tp2, tp1)

def measure_phase():
    measure_resistance()
    measure_capacitance()

def main():
    """
    The main function of the program.

    Returns:
        None
    """
    init_pins()
    debug("###################\n$ ## Init Pass: OK ##\n$ ###################\n$")

    #init_serial()
    #debug("\n$ ###########################\n$ ## Serial Comms Pass: OK ##\n$ ###########################\n$ ")

    if wifi_enabled:
        init_wifi()
        
    measure_phase()
    
    debug("\n$ ##########################\n$ ## Measurement Pass: OK ##\n$ ##########################\n$ ")

if __name__ == "__main__":
    main()






