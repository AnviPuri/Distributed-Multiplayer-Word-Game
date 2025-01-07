import argparse
import json
import socket
import struct
import threading
import time


# Primary server -
# 1. start multicast thread for sending its own information
# 2. keep on listening multicast thread for other servers
# 3. build unicast connection with client and other servers
# Backup server -
# 1. send multicast message for 5 minutes every 30 seconds
# 2. Build unicast connection (bidirectional: with primary and backup servers - they will initiate the connection)

def create_multicast_sender_socket():
    """
    Create and configure a socket for multicast sending.
    """
    print("Creating multicast sender socket.")
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set the TTL for multicast messages
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    return sock


def create_multicast_receiver_socket(multicast_group, port):
    """
    Create and configure a socket for multicast receiving.
    """
    print("Creating multicast receiver socket.")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Bind to the multicast address and port
    sock.bind(('', port))

    # Join the multicast group
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    return sock


class Server:
    def __init__(self, server_ip, server_port, is_primary_server):
        """Initializing the Server class"""
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_primary_server = is_primary_server
        self.server_running = False
        self.server_socket = None
        self.multicast_group = '224.3.29.71'
        self.multicast_port = 10000

    def start(self):
        """Start the server with unicast and multicast behavior"""
        self.server_running = True

        # Start unicast server to handle incoming connections
        threading.Thread(target=self.start_unicast_server, daemon=True).start()

        # Start multicast behavior based on server role
        if self.is_primary_server:
            threading.Thread(target=self.send_multicast_message, daemon=True).start()
            threading.Thread(target=self.listen_multicast_messages, daemon=True).start()
        else:
            threading.Thread(target=self.send_multicast_for_backup, daemon=True).start()
            threading.Thread(target=self.listen_multicast_messages, daemon=True).start()

        # Keep the main thread alive to allow background threads to continue running
        try:
            while self.server_running:
                time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            print("Server shutting down...")
            self.stop()

    # def start_unicast_server(self):
    #     """Start the unicast server to handle incoming connections"""
    #     self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.server_socket.bind((self.server_ip, self.server_port))
    #     self.server_socket.listen(5)
    #     print(f"Server running on {self.server_ip}:{self.server_port}")
    #
    #     while self.server_running:
    #         try:
    #             conn, addr = self.server_socket.accept()
    #             threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
    #         except socket.timeout:
    #             print("Socket Timeout")
    #             continue  # Continue to check the `server_running` flag
    #         except Exception as e:
    #             print(f"Error in unicast connection: {e}")

    def start_unicast_server(self):
        """Start the unicast server to handle incoming connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.server_ip, self.server_port))
            self.server_socket.listen(5)
            print(f"Server running on {self.server_ip}:{self.server_port} for receiving messages")

            while self.server_running:
                try:
                    conn, addr = self.server_socket.accept()
                    print(f"Establishing Connection...")
                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    print(f"Error during accept or client handling: {e}")
        except Exception as e:
            print(f"Error starting unicast server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            print("Unicast server has been stopped.")

    def handle_client(self, conn, addr):
        """Handle incoming unicast connection"""
        print(f"Connection established with {addr}")
        try:
            while self.server_running:
                data = conn.recv(1024)
                if not data:
                    break  # Client disconnected
                print(f"Received from {addr}: {data.decode()}")
                conn.sendall(b"Server response")
        except Exception as e:
            print(f"Error with connection {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            conn.close()

    # def start_server(self):
    #     """Starting the unicast server to handle client connections"""
    #     self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.server_socket.bind((self.server_ip, self.server_port))
    #     self.server_socket.listen(5)
    #     print(f"Server is listening on {self.server_ip}:{self.server_port}")
    #
    #     # while True:
    #     #     conn, addr = server_socket.accept()
    #     #     print(f"Connection received from {addr}")
    #     #     data = conn.recv(1024)
    #     #     print(f"Server received: {data.decode()}")
    #     #     conn.sendall(b"Hello from server")
    #     #     # connection to be closed later
    #     #     conn.close()
    #     while self.server_running:
    #         try:
    #             # self.server_socket.settimeout(1.0)  # Set timeout for accept to check running state
    #             conn, addr = self.server_socket.accept()
    #             client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
    #             client_thread.daemon = True
    #             client_thread.start()
    #         except socket.timeout:
    #             print("Socket Timeout")
    #             continue  # Continue to check the `server_running` flag
    #         except Exception as e:
    #             print(f"Error: {e}")
    #             break

    def start_multicast(self):
        """Starting multicast server if this is the primary server"""
        if self.is_primary_server:
            print('Starting multicast server...')
            self.send_multicast_message()

    def send_multicast_message(self, multicast_group='224.3.29.71', port=10000, message='Default Multicast message'):
        """
        Primary server sends multicast messages continuously every 30 seconds

        Parameters:
            multicast_group (str): The multicast group IP address
            port (int): The port number to use for multicast
            message (str): The multicast message to be sent
        """
        sock = create_multicast_sender_socket()
        print(f'Starting multicast server on group {multicast_group}:{port}')

        server_data = {"ip": self.server_ip, "port": self.server_port, "type": "Primary"}
        server_data_message = json.dumps(server_data)
        try:
            while self.server_running:
                print(f'Sending multicast message: {server_data_message} to {multicast_group}:{port}')
                sock.sendto(server_data_message.encode(), (multicast_group, port))
                time.sleep(30)  # Wait for 30 seconds between messages
        except KeyboardInterrupt:
            print('Multicast server stopped.')
        finally:
            sock.close()

    def send_multicast_for_backup(self):
        """Backup server sends multicast messages for 5 minutes"""
        sock = create_multicast_sender_socket()
        server_data = {"ip": self.server_ip, "port": self.server_port, "type": "Backup"}
        server_data_message = json.dumps(server_data)
        start_time = time.time()

        try:
            while self.server_running and (time.time() - start_time < 300):
                try:
                    print("Sending multicast message...")
                    sock.sendto(server_data_message.encode(), (self.multicast_group, self.multicast_port))
                    print(f"Backup server sent multicast message: {server_data_message}")
                    print("Sleeping for 30 seconds...")
                    time.sleep(30)
                except Exception as e:
                    print(f"Error in multicast send loop: {e}")
                    break
        except Exception as outer_e:
            print(f"Unexpected error in send_multicast_for_backup: {outer_e}")
        finally:
            print("Stopped sending multicast messages. Closing socket.")
            sock.close()

    def listen_multicast_messages(self):
        """
        Listen to multicast messages and establish unicast connection with backup servers
        """
        sock = create_multicast_receiver_socket(self.multicast_group, self.multicast_port)
        print(f"Listening for multicast messages on {self.multicast_group}:{self.multicast_port}")

        while self.server_running:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())
                print(f"Received multicast message from {addr}: {message}")

                # Establish unicast connection to backup server
                if message.get("type") == "Backup":
                    self.connect_to_backup_server(message["ip"], message["port"])
            except Exception as e:
                print(f"Error receiving multicast: {e}")
                break
        sock.close()

    # Dual connection is to be established
    def connect_to_backup_server(self, backup_server_ip, backup_server_port):
        """
        Establish unicast connection with a backup server.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((backup_server_ip, backup_server_port))
                print(f"Connected to backup server at {backup_server_port}:{backup_server_port}")
                sock.sendall(b"Hello from server")
        except Exception as e:
            print(f"Error connecting to backup server: {e}")

    def stop(self):
        """Stop the server and cleanup resources"""
        print('Server shutting down...')
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a server (primary or backup).")
    parser.add_argument("ip", type=str, help="IP address of the server.")
    parser.add_argument("port", type=int, help="Port number of the server.")
    parser.add_argument("--primary", action="store_true", help="Set as primary server.")

    args = parser.parse_args()

    # server started by passing its own ip, port and whether its a primary server
    server = Server(args.ip, args.port, args.primary)
    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
        # trigger this externally?
        server.stop()
