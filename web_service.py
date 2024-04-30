from conf import *

import network
import socket
import select

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
    # Generate dynamic content based on some condition or data
    dynamic_content = "<h1>Dynamic Content</h1>"
    # You can add more dynamic content generation logic here
    
    # HTTP response
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + dynamic_content
    
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
