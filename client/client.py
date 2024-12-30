import socket
import struct
import threading

# Listens to multicast message
# establishes unicast connection with primary server

def create_multicast_client_socket(multicast_group, port):
    """
    Creating and configuring a socket for multicast receiving

    This function sets up a UDP socket specifically for multicast:
    """
    # Create a UDP socket for multicast communication
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow multiple sockets to use the same port - this is crucial for multicast
    # where multiple clients need to listen on the same address/port combination
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f'mg:{multicast_group},port:{port}')
    # Bind to all interfaces on the specified port
    sock.bind(('', port))

    # Convert the multicast group IP to network format (binary)
    group = socket.inet_aton(multicast_group)
    # Create the multicast request structure: group address + interface (all interfaces)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    # Join the multicast group
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    return sock

class Client:
    def __init__(self, multicast_group='224.3.29.71', multicast_port=10000, server_ip='127.0.0.1', server_port=4000):
        """Initialize the Client class with multicast and unicast settings."""
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = False
        self.multicast_thread = None
        self.sock = None  # Socket will be initialized when we start listening
        self.running = False  # Flag to control the listening loop

    def start(self):
        """Start the multicast listener and connect to the primary server."""

        # Start the unicast client in a separate thread
        unicast_thread = threading.Thread(target=self.start_unicast_client)
        unicast_thread.daemon = True
        unicast_thread.start()

        # Start multicast if primary server
        self.running = True
        self.run_client()


    def run_client(self, multicast_group='224.3.29.71', port=10000):
        """
        Run the multicast client and listen for messages

        Parameters:
            multicast_group (str): The multicast group IP address to join
            port (int): The port number to listen on
        """
        # Initialize and store the socket as an instance variable
        self.sock = create_multicast_client_socket(multicast_group, port)
        self.running = True

        print(f'Starting multicast client listening on group {multicast_group}:{port}')
        print('Press Ctrl+C to stop listening')

        try:
            while self.running:
                try:
                    # Set a timeout so we can check the running flag periodically
                    self.sock.settimeout(1.0)
                    # Buffer size of 1024 bytes should be sufficient for most messages
                    data, address = self.sock.recvfrom(1024)
                    print(f'Received message from {address}: {data.decode()}')
                except socket.timeout:
                    # No message received within timeout period - this is normal
                    continue
                except socket.error as e:
                    print(f'Network error occurred: {e}')
                    self.running = False

        except KeyboardInterrupt:
            print('\nReceived stop signal')
        finally:
            self.stop_client()

    def stop_client(self):
        """
        Gracefully stop the client and clean up resources
        """
        self.running = False
        # self.stop_event.set()

        if self.sock:
            print('Closing socket...')
            self.sock.close()
            self.sock = None

        # Wait for the client thread to finish
        if hasattr(self, 'client_thread') and self.client_thread.is_alive():
            self.client_thread.join()

        print('Client stopped')



    def start_unicast_client(self):
        """Establish a unicast connection to the server."""
        try:
            print(f"Connecting to server {self.server_ip}:{self.server_port}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                # client_socket.bind((self.server_ip, self.server_port))  # Use a different IP and port for the client
                client_socket.connect((self.server_ip, self.server_port))
                client_socket.sendall(b"Hello from client")
                response = client_socket.recv(1024)
                print(f"Unicast response from server: {response.decode()}")
        except socket.error as e:
            print(f"Unicast connection error: {e}")

    def stop(self):
        """Stop the client."""
        print("Stopping client...")
        self.running = False
        # if self.multicast_impl:
        #     self.multicast_impl.stop_recieving()
        if self.multicast_thread and self.multicast_thread.is_alive():
            self.multicast_thread.join()
        print("Client stopped.")


if __name__ == '__main__':
    client = Client('224.3.29.71', 10000, '127.0.0.1', 4000)
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()