import socket
import struct
import time

from server_details import ServerDetail



# Primary server -
# 1. start multicast thread for sending its own information
# 2. keep on listening multicast thread for other servers
# 3. build unicast connection with client and other servers
# Backup server -
# 1. send multicast message for 5 minutes every 30 seconds
# 2. Build unicast connection (bidirectional: with primary and backup servers - they will initiate the connection)

def create_multicast_sender_socket():
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
    def __init__(self, server_ip, server_port, is_primary_server):
        """Initializing the Server class"""
        self.server_id = None
        self.id_counter = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_primary_server = is_primary_server
        self.server_running = False
        self.server_socket = None
        self.multicast_group = '224.3.29.71'
        self.multicast_port = 10000
        self.s=[]
        global connected_servers 
        connected_servers = []

        self.connected_clients = []
        self.last_heartbeat = {}
        self.heartbeat_interval = 10  # seconds
        self.heartbeat_timeout = 30  # seconds
        self.heartbeat_failed_flag = False  # Global flag to indicate heartbeat failure
        self.is_acknowledged_by_primary_server = False
        if self.is_primary_server is True:
            self.server_id = 1
            self.id_counter = 1
            self.is_acknowledged_by_primary_server = True

    def start(self):
        """Start the server with unicast and multicast behavior"""
        self.server_running = True

        # Start unicast server to handle incoming connections
        threading.Thread(target=self.start_unicast_server, daemon=True).start()

        # Start multicast behavior based on server role
        if self.is_primary_server:
            threading.Thread(target=self.send_heartbeat, daemon=True).start()
            threading.Thread(target=self.send_multicast_message, daemon=True).start()
        else:
            threading.Thread(target=self.monitor_heartbeat, daemon=True).start()
            threading.Thread(target=self.send_multicast_for_backup, daemon=True).start()

            


        threading.Thread(target=self.listen_multicast_messages, daemon=True).start()

        # Keep the main thread alive to allow background threads to continue running
        try:
            while self.server_running:
                time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            print("Server shutting down...")
            self.stop()

    def is_server_alive(server):
        try:
            with socket.create_connection((server.ip, server.port), timeout=2):
                return True
        except:
            return False


    def send_heartbeat(self):
        global connected_servers 
        while self.server_running:
            try:
                
                servers_to_check = list(connected_servers) 
                


               
                for server in servers_to_check:
                    heartbeat_message = json.dumps({
                        "message_type": "HEARTBEAT",
                        "server_id": self.server_id,
                        "timestamp": str(datetime.datetime.now())
                    })
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((server.ip, server.port))
                        sock.sendall(heartbeat_message.encode())
                    print(f"Sent heartbeat to {server.ip}:{server.port}")
                time.sleep(self.heartbeat_interval)
            except ConnectionRefusedError:
                
                print(f"Error sending heartbeat to {server.id} at {server.ip}:{server.port}: Connection refused")
                

        


    def start_unicast_server(self):
        global connected_servers

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
                self.s.append(connected_servers)
                self.server_socket.close()
            print("Unicast server has been stopped.")
            self.s.append(connected_servers)

    def monitor_heartbeat(self):
            global connected_servers
            """
            Monitors heartbeat messages from connected servers to detect failures.
            If a server is unresponsive, it is removed from the list, and a failure flag is set.
            If the unresponsive server is the primary, a leader election is triggered.
            Otherwise, the failure is handled for backup servers.
            """
            while self.server_running:
                now = datetime.datetime.now()
                
                unresponsive_servers = []  # List to collect unresponsive servers
                for server in connected_servers:
                    # Check if the server's last heartbeat was received within the allowed timeout
                    last_heartbeat = self.last_heartbeat.get(server.id)
                    if last_heartbeat and (now - last_heartbeat).total_seconds() > self.heartbeat_timeout:
                        if server not in unresponsive_servers:  # Ensure we add it only once
                            print(f"No heartbeat received from server {server.id}. Assuming unresponsive.")
                            server.is_responding = False  # Set is_responding to False
                            unresponsive_servers.append(server)  # Add unresponsive server to the list
                            print(f"Unresponsive server detected: {server.id}")
                            self.heartbeat_failed_flag = True

                # Now remove all unresponsive servers from connected_servers
                for server in unresponsive_servers:
                    if server in self.connected_servers:  # Ensure server is still in the list before removing
                        self.connected_servers.remove(server)
                        print(f"Removed unresponsive server {server.id} from connected servers.")

                # Debug print to verify connected servers after removal
                print("Remaining connected servers:", [server.id for server in self.connected_servers])

                # After handling unresponsive servers, check if the primary server is unresponsive
                primary_server = next((server for server in self.connected_servers if server.is_primary), None)

                # Debugging to verify primary server
                if primary_server:
                    print(f"Found primary server: {primary_server.id}, is_responding: {primary_server.is_responding}")
                else:
                    print("No primary server found!")

                    if primary_server and not primary_server.is_responding:
                        print(f"Primary server {primary_server.id} is unresponsive, triggering leader election.")
                        self.leader_election(self.connected_servers)

                time.sleep(self.heartbeat_interval)

    def leader_election(self, connected_servers):
            """
            Here im not getting the the newl added servers that is back up
            """
            print("Starting leader election...")

            for i in connected_servers:
                print(f"Newly added serversssssssssss {i.port} {i.ip}")

            new_leader = next((server for server in connected_servers if server.is_primary is False), None)

            if new_leader:
                new_leader.is_primary = True  # Assign new leader
                print(f"New leader elected: Server {new_leader.id}")
            else:
                print("No suitable backup server found for leader election.")

    def handle_heartbeat_message(self, message, address):
            """
            Handle incoming heartbeat messages to update server status and last heartbeat time.
            """
            server_id = message.get("server_id")
            timestamp = message.get("timestamp")
            
            # Establish connection if not already established
            server = self.get_server_by_id(server_id)
            if not server:
                print(f"Establishing connection with server {server_id} at {address}")
                self.connected_servers.append(server)  # Add new server to connected list
                server = self.get_server_by_id(server_id)
            
            # Update the last heartbeat timestamp
            self.last_heartbeat[server_id] = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
            self.update_server_status(server_id)  # Update server's responsive status

    def update_server_status(self, server_id):
            """
            Update the responsiveness of a server based on the time of the last heartbeat.
            """
            last_heartbeat = self.last_heartbeat.get(server_id)
            now = datetime.datetime.now()
            
            if last_heartbeat:
                # Calculate the time difference since the last heartbeat
                time_difference = (now - last_heartbeat).total_seconds()
                
                # If the time difference exceeds the timeout, mark the server as unresponsive
                if time_difference > self.heartbeat_timeout:
                    print(f"No heartbeat received from server {server_id}. Marking as unresponsive.")
                    server = self.get_server_by_id(server_id)
                    if server:
                        server.is_responding = False
                    self.remove_unresponsive_server(server_id)
                else:
                    # If server is responsive, mark it as responsive
                    server = self.get_server_by_id(server_id)
                    if server:
                        server.is_responding = True
                    print(f"Server {server_id} is now responsive.")
            else:
                print(f"Heartbeat not received yet for server {server_id}.")

    def remove_unresponsive_server(self, server_id):
            """
            Removes unresponsive server from the connected servers list.
            """
            server = self.get_server_by_id(server_id)
            if server:
                self.connected_servers.remove(server)
                print(f"Removed unresponsive server {server_id} from connected servers.")
            else:
                print(f"Server {server_id} not found in connected servers.")

    def get_server_by_id(self, server_id):
            """
            Returns the server object by its ID.
            """
            return next((server for server in self.connected_servers if server.id == server_id), None)




    def handle_client(self, conn, addr):
        global connected_servers

        """Handle incoming unicast connection"""
        print(f"Connection established with {addr}")
        try:
            while self.server_running:
                data = conn.recv(1024)
                if not data:
                    break  # Client disconnected

                message = json.loads(data.decode())
                message_type = message.get("message_type")

                if message_type == "BACKUP_CONNECTION_TO_BACKUP":
                    print(f"Backup to Backup connection received from {addr}: {data.decode()}")
                    new_server = ServerDetail(
                        ip=message["ip"],
                        port=message["port"],
                        server_id=message["server_id"],
                        is_primary=False,
                        is_responding = True  

                    )
                    connected_servers.append(new_server)
                    print(f"Added server: {new_server.ip}:{new_server.port}")
                    response = json.dumps({
                        "message_type": "NEW_BACKUP_ADDITION",
                        "server_id": self.server_id,
                    })
                    conn.sendall(response.encode())
                
                # In your heartbeat handler for other servers (including the primary)
                elif message_type == "HEARTBEAT":
                    print(f"Heartbeat received from {addr}: {message}")
                    self.last_heartbeat[message["server_id"]] = datetime.datetime.now()

                    # Update the server's 'is_responding' flag based on the heartbeat
                    for server in connected_servers:
                        if server.id == message["server_id"]:
                            server.is_responding = True  # Mark the server as responding
                            print(f"Server {server.id} is now responsive.")


                    

                
                elif message_type == "PRIMARY_CONNECTION_TO_BACKUP":
                    print(f"Primary to Backup connection received from {addr}: {data.decode()}")
                    new_server = ServerDetail(
                        ip=message["ip"],
                        port=message["port"],
                        server_id=message["server_id"],
                        is_primary=True
                    )
                    connected_servers.append(new_server)
                    print(f"Added server: {new_server.ip}:{new_server.port}")
                    self.server_id = message["new_server_id"]
                    self.is_acknowledged_by_primary_server = True
                    conn.sendall(b"Received server id and added primary server details.")

                elif message_type == "CLIENT_CONNECTION_TO_SERVER":
                    print(f"Client to Primary connection received from {addr}: {data.decode()}")
                    conn.sendall(b"Server response")

        except Exception as e:
            print(f"Error with connection {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            conn.close()


    def send_multicast_message(self, multicast_group='224.3.29.71', port=10000, message='Default Multicast message'):
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

    def send_multicast_for_backup(self):
        """Backup server sends multicast messages for 5 minutes"""
        sock = create_multicast_sender_socket()
        is_acknowledged_by_primary_server = "N"
        if self.server_id is not None:
            is_acknowledged_by_primary_server = "Y"

        server_data = {"ip": self.server_ip, "port": self.server_port, "server_type": "Backup",
                       "is_acknowledged_by_primary_server": is_acknowledged_by_primary_server}
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

                # in case of a primary server - the primary server sends its own ip, port, server_id, message_type and new id of backup server
                # it also saves the server details
                # The backup server then on receiving the unicast message PRIMARY_CONNECTION_TO_BACKUP saves the details of primary server and also updates its own id
                if message.get("server_type") == "Backup":
                    if self.is_primary_server and message.get(
                                "is_acknowledged_by_primary_server") == "N":
                        new_server_id = self.id_counter + 1
                        self.id_counter += 1
                        response = json.dumps({
                            "message_type": "PRIMARY_CONNECTION_TO_BACKUP",
                            "server_id": self.server_id,
                            "ip": self.server_ip,
                            "port": self.server_port,
                            "new_server_id": new_server_id
                        })
                        self.connect_to_backup_server(message["ip"], message["port"], response)
                        new_server = ServerDetail(
                            ip=message["ip"],
                            port=message["port"],
                            server_id=new_server_id,
                            is_primary=False,
                            is_responding=True
                        )
                        connected_servers.append(new_server)
                        print(f"Added to list of servers: {new_server.ip}:{new_server.port}")
                    else:
                        # in case of a backup server only establish unicast connection when "is_acknowledged_by_primary_server" is set to Y
                        # backup servers send their details - ip, port, id and message_type and in turn receive the backup servers id which they then store
                        # Also if the server itself does not have an id it does not try to contact any other server because it is assumed it is still in the process of getting an id
                        # TO DO -- Establish unicast connection to backup server only when it is not present in the list of connected servers
                        if self.server_id is not None and message.get(
                                "is_acknowledged_by_primary_server") == "Y":
                            response = json.dumps({
                                "message_type": "BACKUP_CONNECTION_TO_BACKUP",
                                "server_id": self.server_id,
                                "ip": self.server_ip,
                                "port": self.server_port,
                            })
                            self.connect_to_backup_server(message["ip"], message["port"], response)
            except Exception as e:
                print(f"Error receiving multicast: {e}")
                break
        sock.close()

    # Dual connection is to be established
    def connect_to_backup_server(self, backup_server_ip, backup_server_port, response):
        global connected_servers

        """
        Establish unicast connection with a backup server.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((backup_server_ip, backup_server_port))
                print(f"Connected to backup server at {backup_server_port}:{backup_server_port}")
                sock.sendall(response.encode())

                # Wait for the response
                if not self.is_primary_server:
                    data = sock.recv(1024)
                    if data:
                        message = json.loads(data.decode())
                        if message.get("message_type") == "NEW_BACKUP_ADDITION":
                            print(f"Adding new bakcup server using: {message}")
                            new_server = ServerDetail(
                                ip=backup_server_ip,
                                port=backup_server_port,
                                server_id=message.get("server_id"),
                                is_primary=False
                            )
                            connected_servers.append(new_server)
                            print(f"New Backup server added to list of servers. {connected_servers.ip}:{connected_servers.port}")
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
