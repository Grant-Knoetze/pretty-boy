#!/usr/bin/env python3
import signal
import socket
import threading


class Server:

    def __int__(self, config):
        """Create a socket serverSocket in the constructor method
        of the server class. This creates a socket for the incoming
        connections, then bind the socket and wait for the clients to connect."""
        # Shutdown on CTL C
        signal.signal(signal.SIGINT, self.shutdown)
        # Create a TCP socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Re-use the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to a public host, and a port
        self.serverSocket.bind((config['HOST_NAME'], config['BIND_PORT']))
        # Become a server socket
        self.serverSocket.listen(10)
        self._clients = {}
        """Accept client and process"""
        while True:
            # Establish socket connection
            (clientSocket, client_address) = self.serverSocket.accept()
            d = threading.Thread(name=self._getClientName(client_address), target=self.proxy_thread,
                                 args=(clientSocket, client_address)
                                 )
            d.setDaemon(True)
            d.start()
        # Redirecting the traffic - fetch data from source and pass it to the client
        # Extract URL from recieved request data:
        # Get the request from browser
        request = conn.recv(config['MAX_REQUEST_LEN'])
        # Parse the first line
        first_line = request.split('\n')[0]
        # Get URl
        url = first_line.split(' ')[1]

