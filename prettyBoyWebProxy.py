#!/usr/bin/env python3
import signal
import socket
import threading


class Server:

    def __int__(self, config):
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
