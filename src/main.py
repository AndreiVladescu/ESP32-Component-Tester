from conf import *

from machine import Pin, ADC
from time import sleep
import _thread
import network
import socket
import select
import ujson
import uos
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


def measure_resistance_680(tp_x, tp_y):
    """
    Measures the resistance using the 680 Ohm test configuration.

    Args:
        tp_x (TestPoint): The test point connected to the low side of the resistor.
        tp_y (TestPoint): The test point connected to the high side of the resistor.

    Returns:
        None
    """
    tp_x.set_r0_low()
    tp_y.set_r1_high()
    sleep(0.001)
    debug('680 Low Impedance Test')
    debug('Low-side {0}: {1} v'.format(tp_x.get_name(), tp_x.get_v()))
    debug('High-side {0}: {1} v'.format(tp_y.get_name(), tp_y.get_v()))
    adc_tpx = 0
    adc_tpy = 0
    
    for i in range(0, 10):
        adc_tpx += tp_x.get_v()
        adc_tpy += tp_y.get_v()
    
    adc_tpx = adc_tpx / 10
    adc_tpy = adc_tpy / 10
    # Sanity check:
    # 1.95 / 0.075 * 40 - 40 = 1k
    #adc_tpx = 0.075
    #adc_tpy = 1.95
    debug('Average voltage tpx: {0} v'.format(adc_tpx))
    debug('Average voltage tpy: {0} v'.format(adc_tpy))
    
    resistance = adc_tpy/adc_tpx * esp32_driving_pin_resistance - esp32_driving_pin_resistance
    print(resistance)
    
def measure_resistance_470k(tp_x, tp_y):
    """
    Measures the resistance using the 470k Ohm test configuration.

    Args:
        tp_x (TestPoint): The test point connected to the low side of the resistor.
        tp_y (TestPoint): The test point connected to the high side of the resistor.

    Returns:
        None
    """
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

def capacitor_discharge(tp_x, tp_y):
    # Safety pin check they are floating
    tp_x.set_r0_floating()
    tp_y.set_r0_floating()
    tp_x.set_r1_floating()
    tp_y.set_r1_floating()
    tp_x.set_r2_floating()
    tp_y.set_r2_floating()

    # Testing if the would-be capacitor has any charge left
    cap_voltage_x = tp_x.get_v()
    cap_voltage_y = tp_y.get_v()
    
    cap_threshold_voltage = 1.3

    if cap_voltage_x > cap_threshold_voltage or cap_voltage_y > cap_threshold_voltage:
        debug('Capacitor has big charge. Discharge it with a screwdriver')
        return

    debug('Capacitor has a small charge. Short the pins')
    # Pin shorting through the 680 Ohm resistor
    tp_x.set_r0_low()
    tp_y.set_r1_low()
    sleep(0.05)

def measure_capacitance_test(tp_x, tp_y):
    capacitor_discharge(tp_x, tp_y)
    
    # Charge the pins for some time
    tp_x.set_r0_low()
    tp_y.set_r1_high()
    sleep(0.01)  # Adjust the charging time as needed
    
    # Measure the voltage after charging
    voltage_x = tp_x.get_v()
    voltage_y = tp_y.get_v()
    
    # Check if the voltage has changed significantly
    voltage_threshold = 0.1  # Adjust the threshold as needed
    if abs(voltage_x - voltage_y) > voltage_threshold:
        debug('Capacitor detected!')
        
        # Calculate the capacitance using the voltage and charging time
        capacitance = 0 # ?????
        
        debug('Capacitance: {0} F'.format(capacitance))
    else:
        debug('No capacitor detected.')


def measure_capacitance():
    global tp1, tp2, tp3
    measure_capacitance_test(tp1, tp2)
    measure_capacitance_test(tp2, tp1)

def measure_phase():
    """
    Measures the resistance.

    Returns:
        None
    """
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

    init_serial()
    debug("\n$ ###########################\n$ ## Serial Comms Pass: OK ##\n$ ###########################\n$ ")

    if wifi_enabled:
        init_wifi()
        
    measure_phase()
    
    debug("\n$ ##########################\n$ ## Measurement Pass: OK ##\n$ ##########################\n$ ")

if __name__ == "__main__":
    main()





