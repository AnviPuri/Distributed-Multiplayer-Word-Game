import json
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
    def __init__(self, server_ip, server_port, is_primary_server):
        """Initializing the Server class"""
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_primary_server = is_primary_server
        self.multicast_thread = None
        self.server_running = False  # Flag to control server running state
        self.server_socket = None  # To store the server socket for cleanup

    def set_primary_server(self, is_primary):
        """Setting this server as primary or backup"""
        self.is_primary_server = is_primary

    def start(self):
        """Starting both unicast server and multicast sending if primary"""
        # Starting the unicast server in a separate thread
        self.server_running = True
        unicast_thread = threading.Thread(target=self.start_server)
        unicast_thread.daemon = True
        unicast_thread.start()

        # Start multicast if primary server
        self.start_multicast()

    def cleanup(self):
        """Clean up the server resources"""
        print('Server shutting down...')
        if self.server_socket:
            self.server_socket.close()
        print('Server resources cleaned up.')

    def stop(self):
        """Stop the server"""
        self.running = False
        self.cleanup()

    def handle_client(self, conn, addr):
        """Handle an individual client connection"""
        print(f"Connection established with {addr}")
        try:
            while self.server_running:
                data = conn.recv(1024)
                if not data:
                    break  # Client disconnected
                print(f"Received from {addr}: {data.decode()}")
                conn.sendall(b"Hello from server")
        except Exception as e:
            print(f"Error with connection {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            conn.close()

    def start_server(self):
        """Starting the unicast server to handle client connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(5)
        print(f"Server is listening on {self.server_ip}:{self.server_port}")

        # while True:
        #     conn, addr = server_socket.accept()
        #     print(f"Connection received from {addr}")
        #     data = conn.recv(1024)
        #     print(f"Server received: {data.decode()}")
        #     conn.sendall(b"Hello from server")
        #     # connection to be closed later
        #     conn.close()
        while self.server_running:
            try:
                # self.server_socket.settimeout(1.0)  # Set timeout for accept to check running state
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                print("Socket Timeout")
                continue  # Continue to check the `server_running` flag
            except Exception as e:
                print(f"Error: {e}")
                break

    def start_multicast(self):
        """Starting multicast server if this is the primary server"""
        if self.is_primary_server:
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

        server_data = {}
        server_data["ip"] = self.server_ip
        server_data["port"] = self.server_port

        server_data_message = json.dumps(server_data)
        try:
            while True:
                # Send data to the multicast group
                print(f'Sending multicast message: {server_data_message} to {multicast_group}:{port}')
                sock.sendto(server_data_message.encode(), (multicast_group, port))
                time.sleep(1)  # Wait for 1 second between messages

        except KeyboardInterrupt:
            print('\nClosing server')
            sock.close()


if __name__ == "__main__":
    # server started by passing its ip and port and if its primary server
    server = Server('127.0.0.1', 4000, True)
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server stopped.")
        # trigger this externally?
        server.stop()
