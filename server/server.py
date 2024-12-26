import socket
import struct
import time


def create_multicast_socket(multicast_group, port):
    """
    Create and configure a socket for multicast sending
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set the time-to-live for messages to 1 to restrict to the local network segment
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    return sock


class Server:
    def __init__(self):
        """Initialize the Server class"""
        pass  # We can add initialization code here if needed later

    def run_server(self, multicast_group='224.3.29.71', port=10000):
        """
        Run the multicast server

        Parameters:
            multicast_group (str): The multicast group IP address
            port (int): The port number to use for multicast
        """
        sock = create_multicast_socket(multicast_group, port)

        print(f'Starting multicast server on group {multicast_group}:{port}')

        message_count = 0
        try:
            while True:
                # Create a message with an incrementing counter
                message = f'Multicast message #{message_count}'.encode()

                # Send data to the multicast group
                print(f'Sending: {message.decode()}')
                sock.sendto(message, (multicast_group, port))

                message_count += 1
                time.sleep(1)  # Wait for 1 second between messages

        except KeyboardInterrupt:
            print('\nClosing server')
            sock.close()


# Example usage for server:
if __name__ == '__main__':
    server = Server()
    server.run_server()