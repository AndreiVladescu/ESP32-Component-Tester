from conf import *

from machine import Pin, ADC
from time import sleep
import _thread
import network
import socket
import select

tp1, tp2, tp3 = None, None, None

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)  # Create a station interface
    wlan.active(True)  # Activate the station interface
    if not wlan.isconnected():  # Check if already connected
        debug('Connecting to WiFi...')
        wlan.connect(ssid, password)  # Connect to the WiFi network
        while not wlan.isconnected():  # Wait for connection
            pass
    debug('Connected to WiFi:' + ssid)
    debug('IP address:' + wlan.ifconfig()[0])  # Print the IP address
    
def handle_request(conn):
    template_content  = ""
    
    with open('template.html', 'r') as file:
        template_content = file.read()
        
    dynamic_data = {
        'tp1_v': tp1.get_v() + " " + tp1.get_status(),
        'tp2_v': tp2.get_v() + " " + tp2.get_status(),
        'tp3_v': tp3.get_v() + " " + tp3.get_status(),
    }
    
    rendered_content = template_content.format(**dynamic_data)
    
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + rendered_content
    
    conn.send(response)  # Send the HTTP response
    conn.close()  # Close the connection
    
def start_server():
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
    init_pins()
    debug("###################\n$ ## Init Pass: OK ##\n$ ###################\n$")

    connect_wifi('DEV', '%yE+Tr_4hru87Kx4')
    
    _thread.start_new_thread(start_server, ())
    
    debug("###################\n$ ## WiFi Pass: OK ##\n$ ###################\n$")
    
    measure_phase()
    
    debug("\n$ ##########################\n$ ## Measurement Pass: OK ##\n$ ##########################\n$ ")

if __name__ == "__main__":
    main()

