import socket
import struct
import threading
import time


# The server when it starts
# in case it is primary
# -- it starts sending multicast message, listens to multicast message for backup server and is open to recieve unicast connection from client
# In case it is backup
# -- it sends multicast message and all other servers send it a unicast message establisihing a connection

def create_multicast_socket(multicast_group, port):
    """
    Creating and configuring a socket for multicast sending
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Setting the time-to-live for messages to 1 to restrict to the local network segment
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    return sock

class Server:
    def __init__(self, server_ip, server_port):
        """Initializing the Server class"""
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_primary_server = False
        self.multicast_thread = None

    def set_primary_server(self, is_primary):
        """Setting this server as primary or backup"""
        self.primary_server = is_primary

    def start(self):
        """Starting both unicast server and multicast sending if primary"""
        # Start the unicast server in a separate thread
        unicast_thread = threading.Thread(target=self.start_server)
        unicast_thread.daemon = True
        unicast_thread.start()

        # Start multicast if primary server
        self.start_multicast()

    def start_server(self):
        """Starting the unicast server to handle client connections"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server_socket.bind(('127.0.0.1', 4000))
        server_socket.bind((self.server_ip, self.server_port))
        server_socket.listen(1)
        print(f"Server is listening on {self.server_ip}:{self.server_port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"Connection received from {addr}")
            data = conn.recv(1024)
            print(f"Server received: {data.decode()}")
            conn.sendall(b"Hello from server")
            # connection to be closed later
            conn.close()

    def start_multicast(self):
        """Starting multicast server if this is the primary server"""
        if self.primary_server:
            print('Starting multicast server...')
            self.send_multicast_message()
        else:
            print('Not the primary server. Skipping multicast...')

    def send_multicast_message(self, multicast_group='224.3.29.71', port=10000, message='Default Multicast message'):
        """
        Run the multicast server

        Parameters:
            multicast_group (str): The multicast group IP address
            port (int): The port number to use for multicast
            message (str): The multicast message to be sent
        """
        sock = create_multicast_socket(multicast_group, port)
        print(f'Starting multicast server on group {multicast_group}:{port}')

        message_count = 0
        try:
            while True:
                # Create a message with an incrementing counter
                message = f'Multicast message #{message_count}'.encode()

                # Send data to the multicast group
                print(f'Sending multicast message: {message.decode()} to {multicast_group}:{port}')
                sock.sendto(message, (multicast_group, port))

                message_count += 1
                time.sleep(1)  # Wait for 1 second between messages

        except KeyboardInterrupt:
            print('\nClosing server')
            sock.close()


if __name__ == "__main__":
    server = Server('127.0.0.1', 4000)
    server.set_primary_server(True)
    server.start()

