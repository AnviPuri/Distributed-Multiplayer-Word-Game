import argparse
import datetime
import json
import socket
import struct

import subprocess
import threading
import time
from server_details import ServerDetail
from client_details import ClientDetail
import os
import sys


from server_details import ServerDetail

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from game.game import Game

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
        self.server_id = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.is_primary_server = is_primary_server
        self.server_running = False
        self.server_socket = None

        self.multicast_group = '224.3.29.71'
        self.is_primary=self.is_primary_server
        self.multicast_port = 10000

        self.id_counter = None  # to allot id to the server
        self.is_acknowledged_by_primary_server = False

        self.connected_servers = []
        self.server_failed=False
        self.total_connected_servers = []
        self.connected_clients = []
        self.new_primary_server = []
        self.received_higher_id_response = False


        self.last_heartbeat = {}
        self.heartbeat_interval = 10
        self.heartbeat_timeout = 30
        self.heartbeat_failed_flag = False  # Global flag to indicate heartbeat failure

        if self.is_primary_server is True:
            self.server_id = 1
            self.id_counter = 1
            self.is_acknowledged_by_primary_server = True


        self.game_round = 1
        self.max_rounds= 3
        self.game_ended = False

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
        time.sleep(30)
        threading.Thread(target=self.start_game(), daemon=True).start()

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
        """
    Sends periodic heartbeat messages to all connected servers.
    Each heartbeat contains the server's ID and a timestamp.
    If a server is unresponsive, it is removed from the list of connected servers.
    Heartbeats are sent at intervals defined by `self.heartbeat_interval`.
    """
        while self.server_running:
            try:
                for server in self.connected_servers:
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
                self.heartbeat_failed_flag = True  # Set the flag to indicate failure
                break


    # def send_heartbeat_backup(self):
    #     """
    #     Sends periodic heartbeat messages to all connected servers.
    #     Each heartbeat contains the server's ID and a timestamp.
    #     If a server is unresponsive, it is removed from the list of connected servers.
    #     Heartbeats are sent at intervals defined by `self.heartbeat_interval`.
    #     """
    #     while self.server_running and self.is_primary:
    #         try:
    #             for server in self.connected_servers:
    #                 heartbeat_message = json.dumps({
    #                     "message_type": "HEARTBEAT",
    #                     "server_id": self.server_id,  # Send heartbeat from the elected leader
    #                     "timestamp": str(datetime.datetime.now())
    #                 })
                    
    #                 print(f"Sending heartbeat to Server ID={server.id} at {server.ip}:{server.port}")
    #                 with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    #                     sock.connect((server.ip, server.port))
    #                     sock.sendall(heartbeat_message.encode())
    #                     print(f"Sent heartbeat to {server.ip}:{server.port}")

    #         except ConnectionRefusedError:
    #             print(f"Error sending heartbeat to {server.id} at {server.ip}:{server.port}: Connection refused")
    #             self.heartbeat_failed_flag = False  # Reset the heartbeat failure flag
    #             break  # Exit the loop if the leader fails to send a heartbeat
    def start_unicast_server(self):
        """Start the unicast server to handle incoming connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.server_ip, self.server_port))
            self.server_socket.listen(5)
            print(f"Server listening on {self.server_ip}:{self.server_port} for receiving messages")

            while self.server_running:
                try:
                    conn, addr = self.server_socket.accept()
                    print(f"Establishing Connection...")
                    client_thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
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

    def monitor_heartbeat(self):
        """
        Monitors heartbeat messages from connected servers to detect failures.
        If a server is unresponsive, it is removed from the list, and a failure flag is set.
        If the unresponsive server is the primary, a leader election is triggered.
        Otherwise, the failure is handled for backup servers.
        """
        while self.server_running:
            now = datetime.datetime.now()
            for server in self.connected_servers:
                last_heartbeat = self.last_heartbeat.get(server.id)
                if last_heartbeat and (now - last_heartbeat).total_seconds() > self.heartbeat_timeout:
                    print(f"Server {server.id} at {server.ip}:{server.port} is unresponsive!")
                    self.connected_servers.remove(server)
                    self.heartbeat_failed_flag = True

                    # If the unresponsive server is the primary, trigger leader election
                    if server.is_primary:
                        print("Primary server failure detected. Initiating leader election...")
                        self.leader_election()
                    else:
                        print(f"Backup server {server.id} failure detected. Removing from connected servers list.")

                    # Reset the heartbeat failure flag
                    self.heartbeat_failed_flag = False

            # Check if the heartbeat_failed_flag is set (leader failure)
            if self.heartbeat_failed_flag:
                print("Leader failure detected. Initiating leader election...")
                self.leader_election()
                self.heartbeat_failed_flag = False  # Reset the flag after leader election

            time.sleep(self.heartbeat_interval)
    def total_servers(self):
        for i in self.connected_servers:
            self.total_connected_servers.append(i)

    def handle_heartbeat_failure(self, server):
        """
        Handles the actions when a heartbeat failure is detected for a server.
        If the server is primary, initiates a leader election; if backup, removes it from the list.
        Prints messages to log the server's failure and which action is taken.
        Resets the heartbeat failure flag after handling the failure.
        """
        print(f"Handling heartbeat failure for server {server.id} at {server.ip}:{server.port}.")

        if server.is_primary:
            print("Primary server failure detected. Initiating leader election...")
            self.total_servers()
            self.server_failed = True
            self.leader_election()
        else:
            print(f"Backup server {server.id} failure detected. Removing from connected servers list.")

        # Reset the heartbeat failure flag
        self.heartbeat_failed_flag = False


    def leader_election(self):
        """Run leader election using the Bully Algorithm when the primary server fails."""
        print("Starting leader election...")

        # Get current server details
        print(f"Current Server Details: ID={self.server_id}, IP={self.server_ip}, Port={self.server_port}")
        current_server = ServerDetail(self.server_ip, self.server_port, self.server_id, False)

        if self.connected_servers:
            all_servers = self.connected_servers + [current_server]

            # Find the server with the highest ID
            highest_id_server = max(all_servers, key=lambda server: server.id)

            if highest_id_server.id == self.server_id:
                # Declare self as primary
                self.declare_self_as_leader()
            

            else:
                # Send election message to the highest ID server
                self.send_election_message(highest_id_server)

                # Wait for the highest ID server to respond
                time.sleep(3)

                if not self.received_higher_id_response:
                    # No response → declare self as leader
                    self.declare_self_as_leader()
        else:
            print("No connected servers available for leader election.")
            self.declare_self_as_leader()
            

    def declare_self_as_leader(self):
        """Declare the current server as the new primary leader."""
        if not self.is_primary:  # Ensure this is called only once
            print(f"Server {self.server_id} is now the primary leader.")
            self.is_primary = True

            # Send multicast announcement to all servers
            self.send_multicast_announcement()

            # Send unicast leader announcements to all connected servers
            for server in self.connected_servers:
                self.send_leader_announcement(server)

            # Start sending heartbeats to backup servers
            threading.Thread(target=self.send_heartbeat, daemon=True).start()
            self.heartbeat_failed_flag = False


    def send_leader_announcement(self, server):
        """Notify backup servers that a new primary has been elected."""
        message = {
            "message_type": "LEADER_ANNOUNCEMENT",
            "new_leader_id": self.server_id,
            "ip": self.server_ip,
            "port": self.server_port
        }
        self.send_message(server, message)
        print(f"Sent leader announcement to server {server.id}.")

    
    def send_election_message(self, server):
        """Send election message to a higher ID server."""
        print(f"Sending election message to server {server.id}...")
        message = {"message_type": "ELECTION", "candidate_id": self.server_id}
        self.send_message(server, message)

        # Wait for a response
        time.sleep(3)  # Adjust the timeout as needed


    def send_multicast_announcement(self):
        """Send a multicast message to announce the new primary leader."""
        sock = create_multicast_sender_socket()
        announcement_message = json.dumps({
            "message_type": "PRIMARY_LEADER_ANNOUNCEMENT",
            "new_leader_id": self.server_id,
            "ip": self.server_ip,
            "port": self.server_port
        })
        try:
            print(f"Sending multicast announcement: {announcement_message}")
            sock.sendto(announcement_message.encode(), (self.multicast_group, self.multicast_port))
        except Exception as e:
            print(f"Error sending multicast announcement: {e}")
        finally:
            sock.close()


    def send_message(self, server, message):
        """Send a JSON message to another server over a socket connection."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server.ip, server.port))
                s.sendall(json.dumps(message).encode('utf-8'))
                print(f"Sent message to server {server.id}: {message}")
        except Exception as e:
            print(f"Failed to send message to server {server.id}: {e}")
    
    def handle_election_response(self, message):
        """Handle responses from higher-ID servers during election."""
        if message.get("type") == "ELECTION_RESPONSE":
            # Acknowledge the response from a higher ID server
            self.received_higher_id_response = True
            print(f"Received response from higher ID server {message['server_id']}. Waiting for their decision.")

    def handle_connection(self, conn, addr):
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
                        is_primary=False
                    )
                    self.connected_servers.append(new_server)
                    print(f"Added server: {new_server.ip}:{new_server.port}")
                    response = json.dumps({
                        "message_type": "NEW_BACKUP_ADDITION",
                        "server_id": self.server_id,
                    })
                    conn.sendall(response.encode())
                    
                elif message_type == "HEARTBEAT":
                    print(f"Heartbeat received from {addr}: {message}")
                    self.last_heartbeat[message["server_id"]] = datetime.datetime.now()

                elif message_type == "PRIMARY_CONNECTION_TO_BACKUP":
                    print(f"Primary to Backup connection received from {addr}: {data.decode()}")
                    new_server = ServerDetail(
                        ip=message["ip"],
                        port=message["port"],
                        server_id=message["server_id"],
                        is_primary=True
                    )
                    self.connected_servers.append(new_server)
                    print(f"Added server: {new_server.ip}:{new_server.port}")
                    self.server_id = message["new_server_id"]
                    self.is_acknowledged_by_primary_server = True
                    conn.sendall(b"Received server id and added primary server details.")

                elif message_type == "CLIENT_CONNECTION_TO_SERVER":
                    print(f"Client to Primary connection received from {addr}: {data.decode()}")
                    new_client = ClientDetail(
                        ip=message["client_ip"],
                        port=message["client_port"]
                    )
                    self.connected_clients.append(new_client)
                    print(f"Added client: {new_client.ip}:{new_client.port}")
                    conn.sendall(b"Received and saved client details.")
               
                
                elif message_type == "LEADER_ANNOUNCEMENT":
                    print(f"Leader announcement received from {addr}: {message}")
                    new_leader = ServerDetail(
                        ip=message["ip"],
                        port=message["port"],
                        server_id=message["new_leader_id"],
                        is_primary=True
                    )
                    # Check if the leader is already in the list
                    if not any(server.id == new_leader.id for server in self.connected_servers):
                        self.connected_servers.append(new_leader)
                        print(f"Added new primary leader: {new_leader.ip}:{new_leader.port}")
                    else:
                        print(f"Leader {new_leader.id} is already recognized.")

                    # Stop the election process if this server was running one
                    self.received_higher_id_response = True


        except Exception as e:
            print(f"Error with connection {addr}: {e}")
        finally:
            print(f"Closing connection with {addr}")
            conn.close()

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

        server_data = {"ip": self.server_ip, "port": self.server_port, "server_type": "Primary"}
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
        start_time = time.time()

        try:
            while self.server_running and (time.time() - start_time < 300):
                try:
                    is_acknowledged_by_primary_server = "N"
                    if self.server_id is not None:
                        is_acknowledged_by_primary_server = "Y"

                    server_data = {"ip": self.server_ip, "port": self.server_port, "server_type": "Backup",
                                   "is_acknowledged_by_primary_server": is_acknowledged_by_primary_server,
                                   "id": self.server_id}
                    server_data_message = json.dumps(server_data)

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
        Listen to multicast messages and establish unicast connection with backup servers.
        """
        sock = create_multicast_receiver_socket(self.multicast_group, self.multicast_port)
        print(f"Listening for multicast messages on {self.multicast_group}:{self.multicast_port}")
        while self.server_running:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())
                server_ip = message.get("ip")
                server_port = message.get("port")

                if server_ip != self.server_ip and server_port != self.server_port:
                    print(f"Received multicast message from {addr}: {message}")

                    # Handle PRIMARY_LEADER_ANNOUNCEMENT
                    if message.get("message_type") == "PRIMARY_LEADER_ANNOUNCEMENT":
                        print(f"Primary leader announcement received from {addr}: {message}")
                        new_leader = ServerDetail(
                            ip=message["ip"],
                            port=message["port"],
                            server_id=message["new_leader_id"],
                            is_primary=True
                        )
                        # Check if the leader is already in the list
                        if not any(server.id == new_leader.id for server in self.connected_servers):
                            self.connected_servers.append(new_leader)
                            print(f"Added new primary leader: {new_leader.ip}:{new_leader.port}")
                        else:
                            print(f"Leader {new_leader.id} is already recognized.")

                        # Stop the election process if this server was running one
                        self.received_higher_id_response = True

                    # Handle backup server announcements
                    elif message.get("server_type") == "Backup":
                        if self.is_primary_server and message.get(
                                "is_acknowledged_by_primary_server") == "N" and not self.is_server_in_connected_list(
                            server_ip, server_port):
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
                                is_primary=False
                            )
                            self.connected_servers.append(new_server)
                            print(f"Added to list of servers: {new_server.ip}:{new_server.port}")
                        elif not self.is_primary_server and not self.is_server_in_connected_list(server_ip, server_port):
                            # in case of a backup server only establish unicast connection when "is_acknowledged_by_primary_server" is set to Y
                            # backup servers send their details - ip, port, id and message_type and in turn receive the backup servers id which they then store
                            # Also if the server itself does not have an id it does not try to contact any other server because it is assumed it is still in the process of getting an id
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
                            self.connected_servers.append(new_server)
                            print(f"New Backup server added to list of servers.")
        except Exception as e:
            print(f"Error connecting to backup server: {e}")

    def is_server_in_connected_list(self, new_server_ip, new_server_port):
        """
        Check if a server with the given IP and port exists in the connected servers list.

        :param ip: IP address of the server to search for.
        :param port: Port number of the server to search for.
        :return: True if a server with the given IP and port exists, otherwise False.
        """
        for server in self.connected_servers:
            if server.ip == new_server_ip and server.port == new_server_port:
                return True
        return False

    def start_game(self):
        """Start the game if we have more than 1 client connected."""
        try:
            while self.server_running:
                if len(self.connected_clients) > 1:
                    print("Starting the game...")
                    game = Game()
                    game.choose_word()
                    self.enable_all_connected_clients_to_play()
                    while self.game_round <= self.max_rounds:
                        print(f"Round {self.game_round} begins.")
                        self.play_round(game)
                        self.enable_all_connected_clients_to_play()
                        if self.game_ended:
                            print("Correct Word has been guessed!")
                            print("Game Over...")
                            self.notify_end_result(game)
                            self.end_game()
                            break
                        self.game_round += 1
                    print("Game Over...")
                    self.notify_end_result(game)
                    self.end_game()
                else:
                    print("Not enough clients to start the game.")
                time.sleep(60)  # Wait for 60 seconds before checking whether game can be started.
        except KeyboardInterrupt:
            print('Multicast server stopped.')

    def play_round(self, game):
        """Each client guesses the word in FIFO order."""
        for client in self.connected_clients:
            if client.can_play_the_round:
                self.ask_client_to_guess(client, game)
                if(self.game_ended):
                    break

    def ask_client_to_guess(self, client, game):
        """
        Ask the client to guess the word and calculate the score.
        If correct, end the game.
        """
        print(f"Client {client.ip} making a guess.")
        guessed_word = self.receive_client_guess(client)
        client.set_last_played_word(guessed_word)
        result = game.get_game_result(guessed_word, client.client_score)

        if result["result_output"] == "CORRECT_GUESS":
            print("Client guessed the correct word!")
            self.game_ended = True
            client.set_has_guessed_word(True)
        else:
            print("Client guessed an incorrect word!")
            client.set_client_score(result["updated_score"])
            client.set_last_word_interpretation(result["last_word_interpretation"])
            self.notify_guess_result(client)

    def receive_client_guess(self, client):
        """
        Method to recieve a guess from the client.
        """
        try:
            client_guess_message = json.dumps({
                "message_type": "WORD_GUESS",
                "server_id": self.server_id,
                "timestamp": str(datetime.datetime.now())
            })
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((client.ip, client.port))
                sock.sendall(client_guess_message.encode())
                print(f"Requested client {client.ip}:{client.port} to guess the word.")

                # Wait for the client to send their guess
                # sock.settimeout(10)  # Setting a timeout to avoid indefinite blocking
                # the response will contain the guessed word and message id ( for now the timestamp will act as the message id)
                data = sock.recv(1024)
                print(f"Recieved {data}")

                message = json.loads(data.decode())
                server_ip = message.get("ip")
                server_port = message.get("port")

                response = json.loads(data.decode())
                guessed_word = response.get("guess")
                print(f"Received guess '{guessed_word}' from Client {client.ip}:{client.port}.")
                return guessed_word
        except ConnectionRefusedError:
            print(f"Error sending message to client at {client.ip}:{client.port}: Connection refused")

    def notify_guess_result(self, client):
        """Notify a single client of their score and guesses."""
        try:
            message = json.dumps({
                "message_type": "INCORRECT_GUESS_NOTIFICATION",
                "score": client.client_score,
                "word_interpretation": client.last_word_interpretation,
                "guessed_word": client.last_played_word
            })
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((client.ip, client.port))
                sock.sendall(message.encode())
                print(f"Client {client.ip}:{client.port} informed about their guess.")
        except ConnectionRefusedError:
            print(f"Error sending message to client at {client.ip}:{client.port}: Connection refused")

    def notify_end_result(self, game):
        """Notify all clients of the game result."""
        message = {}
        winner_details = self.get_winner()
        for client in self.connected_clients:
            if self.game_ended:
                print("Game ended by guessing the correct word")
                if client.has_guessed_word:
                    message["message_type"] = "GAME_WINNER_CORRECT_WORD"
                    message["message"] = "Congratulations! You Win by guessing the correct word!"
                else:
                    message["message_type"] = "FINAL_RESULT_CORRECT_WORD_GUESSED"
                    message["correct_word"] = game.current_word
                    message["message"] = f"Player with ip {winner_details["ip"]} and port {winner_details["port"]} has correctly guessed the word and won!"
            else:
                print("Game ended but correct word wasn't guessed.")
                if client.ip == winner_details["ip"] and client.port == winner_details["port"]:
                    message["message_type"] = "GAME_WINNER_INCORRECT_WORD"
                    message["message"] = f"Congratulations! You Win with a high score of {winner_details["winner_score"]}!"
                    message["correct_word"] = game.current_word
                else:
                    message["message_type"] = "FINAL_RESULT_CORRECT_WORD_NOT_GUESSED"
                    message["correct_word"] = game.current_word
                    message["message"] = f"Player with ip {winner_details["ip"]} and port {winner_details["port"]} has won with high score of {winner_details["winner_score"]}!"
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((client.ip, client.port))
                    sock.sendall(json.dumps(message).encode())
                    print(f"Client {client.ip}:{client.port} informed about the final result.")
            except ConnectionRefusedError:
                print(f"Error sending message to client at {client.ip}:{client.port}: Connection refused")

    def get_winner(self):
        winner_details = {}
        if self.game_ended:
            for client in self.connected_clients:
                if client.has_guessed_word:
                    # later replace ip and port with player username
                    winner_details["ip"] = client.ip
                    winner_details["port"] = client.port
                    break
        else:
            client_with_max_score = max(self.connected_clients, key=lambda client: client.client_score)
            winner_details["ip"] = client_with_max_score.ip
            winner_details["port"] = client_with_max_score.port
            winner_details["winner_score"] = client_with_max_score.client_score
        return winner_details

    def enable_all_connected_clients_to_play(self):
        for client in self.connected_clients:
            if not client.can_play_the_round:
                client.set_can_play_round(True)

    def reset_all_connected_clients_state(self):
        for client in self.connected_clients:
            if not client.can_play_the_round:
                client.set_can_play_round(True)

    def end_game(self):
        """End the game and declare the winner."""
        self.reset_game_state()
        print("Game will start again after a minute...")
        time.sleep(60)
        self.start_game()

    def reset_game_state(self):
        """Reset game variables for each game."""
        self.game_round = 1
        self.game_ended = False
        self.reset_all_connected_clients_state()
        # self.clients = deque(self.connected_clients)  # How to implement FIFO order

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
