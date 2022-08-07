import cryptography
import signal
import socket
import ssl
import sys
import threading

from cryptography import fernet
from cryptography.fernet import Fernet

HEX_FILTER = "".join([(len(repr(chr(i))) == 3) and chr(i) or "." for i in range(256)])

# This function provides us with a way to watch the communication
# going through a proxy in real time


def hexdump(src, length=16, show=True):
    if isinstance(src, bytes):
        src = src.decode()

    results = list()
    for i in range(0, len(src), length):
        word = str(src[i : i + length])

        printable = word.translate(HEX_FILTER)
        hexa = " ".join([f"{ord(c):02X}" for c in word])
        hexwidth = length * 3
        results.append(f"{i:04x}  {hexa:<{hexwidth}}  {printable}")
    if show:
        for line in results:
            print(line)
    else:
        return results


def new_func(show, results):
    if show:
        for line in results:
            print(line)
    else:
        return results


# The receive_from function allows the two ends of the proxy
# to receive data, ie: both ends of the proxy use this function
# to receive data
def recieve_from(connection):
    """We create an empty byte string (buffer)
    that will accumulate responses from the socket
    We set a default timeout of 5 connections which
    may not be sufficient so increase timeout as
    necessary.We set up a loop to read response data
    into the buffer until there is no more data
    or we timeout. Finally, we return the
    buffer byte string to the caller
    which could be either the local or remote machine"""
    buffer = b""
    connection.settimeout(5)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception as e:
        pass
    return buffer


# We may want to modify the response or request packets
# before the proxy sends them away....
# Inside these functions, you can modify the packet contents, perform
# fuzzing tasks, test for authentication issues, or do whatever else your heart
# desires. This can be useful, for example, if you find plaintext user credentials
# being sent and want to try to elevate privileges on an application by
# passing in admin instead of your own username


def request_handler(buffer, fernet=None, encMessage=None):
    """Encrypt buffer with fernet"""
    message = buffer
    key = fernet.generate_key()
    fernet = Fernet(key)
    print("original string: ", message)
    print("encrypted string: ", encMessage)
    decMessage = fernet.decrypt(encMessage).decode()
    print("decrypted string: ", decMessage)
    return buffer


def response_handler(buffer):
    """Perform packet modifications"""
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    if receive_first:
        remote_buffer = recieve_from(remote_socket)
        hexdump(remote_buffer)

    remote_buffer = response_handler(remote_buffer)
    if len(remote_buffer):
        print("[<==] Sending %d bytes to localhost." % len(remote_buffer))

    while True:
        local_buffer = recieve_from(client_socket)
        if len(local_buffer):
            line = "[==>]Received %d bytes from localhost." % len(local_buffer)
            print(line)
            hexdump(local_buffer)

            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        remote_buffer = request_handler(local_buffer)
        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")

        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


# The server loop function follows to manage the connection...


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    """We create a socket here, then bind to
    the localhost and listen. In the main loop,
    when a fresh connection request comes in,
    we hand it off to the proxy_handler in a
    new thread, which does all the sending
    and receiving on either side of the data
    stream."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print("problem on bind: %r" % e)

        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(0)

    print("[*] listening on %s:%d" % (local_host, local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # print out the local connection information
        line = "> Received incoming connection from %s:%d" % (addr[0], addr[1])
        print(line)
        # start a thread to talk to the remote host
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first),
        )
        proxy_thread.start()


def main():
    """We take in some command
    line arguments and
    start up the server loop that
    listens for connections"""
    # Shutdown on CTL C
    signal.signal(signal.SIGINT)
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end="")
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


if __name__ == "__main__":
    main()
