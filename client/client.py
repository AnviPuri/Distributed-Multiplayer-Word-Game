import socket
import struct


def create_multicast_client_socket(multicast_group, port):
    """
    Create and configure a socket for multicast receiving

    This function sets up a UDP socket specifically configured for multicast:
    1. Creates the basic UDP socket
    2. Enables port reuse (so multiple clients can listen)
    3. Binds to all interfaces
    4. Joins the specified multicast group
    """
    # Create a UDP socket for multicast communication
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow multiple sockets to use the same port - this is crucial for multicast
    # where multiple clients need to listen on the same address/port combination
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
    def __init__(self):
        """Initialize the Client class"""
        self.sock = None  # Socket will be initialized when we start listening
        self.running = False  # Flag to control the listening loop

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

    def _start_command_listener(self):
        """
        Listen for user commands in the main thread
        """
        while self.running:
            command = input().strip().lower()
            if command == 'stop':
                print("Stopping client...")
                self.stop_client()
                break

    def stop_client(self):
        """
        Gracefully stop the client and clean up resources
        """
        self.running = False
        self.stop_event.set()

        if self.sock:
            print('Closing socket...')
            self.sock.close()
            self.sock = None

        # Wait for the client thread to finish
        if hasattr(self, 'client_thread') and self.client_thread.is_alive():
            self.client_thread.join()

        print('Client stopped')


if __name__ == '__main__':
    client = Client()
    client.run_client()