import argparse
import json
import socket
import struct
import sys
import threading


def create_multicast_client_socket(multicast_group, port):
    """
    Creating and configuring a socket for multicast receiving

    This function sets up a UDP socket specifically for multicast:
    """
    # Create a UDP socket for multicast communication
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow multiple sockets to use the same port - this is crucial for multicast
    # where multiple clients need to listen on the same address/port combination
    if sys.platform == "win32":  # Windows
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    elif sys.platform == "darwin":  # macOS
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Only for macOS
    else:
        raise RuntimeError("Unsupported platform")

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
    def __init__(self, multicast_group='224.3.29.71', multicast_port=10000, client_ip='127.0.0.2', client_port=5001):
        """Initialize the Client class with multicast and unicast settings."""
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port

        self.sock = None  # Socket will be initialized when we start listening
        self.client_running = False

        self.server_port = None
        self.server_ip = None

        self.client_ip = client_ip
        self.client_port = client_port

    def set_primary_server_details(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

    def start(self):
        """Start the multicast listener, unicast server, and connect to the primary server."""
        self.client_running = True
        threading.Thread(target=self.start_unicast_client, daemon=True).start()

        self.receive_server_details()

        if self.server_ip and self.server_port:
            self.connect_to_server()
        else:
            print("Failed to retrieve server details. Cannot proceed with unicast connection.")

        try:
            while self.client_running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            print("Client interrupted by user.")
            self.stop()

    def start_unicast_client(self):
        """Start the unicast client to handle incoming connections."""

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.client_ip, self.client_port))
            self.sock.listen(10)
            print(f"Unicast client listening on {self.client_ip}:{self.client_port}")

            while self.client_running:
                try:
                    conn, addr = self.sock.accept()
                    connection_thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
                    connection_thread.daemon = True
                    connection_thread.start()
                except Exception as e:
                    print(f"Error during accept or connection handling: {e}")
        except Exception as e:
            print(f"Error starting unicast client: {e}")
        finally:
            if self.sock:
                self.sock.close()
            print("Unicast client has been stopped.")

    def handle_connection(self, conn, addr):
        """Handle incoming unicast connection with client."""
        try:
            while self.client_running:
                data = conn.recv(1024)
                if not data:
                    break  # Connection disconnected

                message = json.loads(data.decode())
                message_type = message.get("message_type")

                if message_type == "WORD_GUESS":
                    print(f"Client asked to guess word by primary server.")
                    timestamp = message["timestamp"]
                    while True:
                        guessed_word = input("Please guess a 5-letter word: ").strip()
                        if len(guessed_word) == 5 and guessed_word.isalpha():
                            break
                        print("Invalid input. Please enter exactly 5 letters.")
                    # send back the guessed word and message id (for now we consider the timestamp as the message id)
                    response = json.dumps({
                        "message_type": "WORD_GUESS_RESPONSE",
                        "guess": guessed_word,
                        "message_id": timestamp
                    })
                    conn.sendall(response.encode())
                elif message_type == "GAME_WINNER_CORRECT_WORD":
                    display_message = message["message"]
                    print(display_message)
                elif message_type == "FINAL_RESULT_CORRECT_WORD_GUESSED" or message_type == "GAME_WINNER_INCORRECT_WORD" or message_type == "FINAL_RESULT_CORRECT_WORD_NOT_GUESSED":
                    display_message = message["message"]
                    correct_word = message["correct_word"]
                    print(display_message)
                    print(f"The correct word was {correct_word}")
                elif message_type == "INCORRECT_GUESS_NOTIFICATION":
                    score = message["score"]
                    word_interpretation = message["word_interpretation"]
                    guessed_word = message["guessed_word"]
                    print(f"You guess was incorrect!")
                    print(f"The interpretation for your guessed word : {guessed_word} is {word_interpretation}!")
                    print(f"Your current score in the game is {score}")
                elif message_type == "SERVER_FAILED":
                    score = message["score"]
                    if score > 0:
                        print(f"Congrats! You had a score of {score} in the previous game.")
                    print(
                        "But looks like there is some problem. Please wait for another game to resume...")
                    self.server_port = None
                    self.server_ip = None
                    self.receive_server_details()
                    if self.server_ip and self.server_port:
                        self.connect_to_server()
        except Exception as e:
            print(f"Error with connection {addr}: {e}")
        finally:
            conn.close()

    def receive_server_details(self):
        """Run the multicast client and continuously listen for server details."""
        sock = create_multicast_client_socket(self.multicast_group, self.multicast_port)

        while not self.server_ip or not self.server_port:
            try:
                # Continuously receive multicast messages until valid server details are obtained
                data, address = sock.recvfrom(1024)
                message = data.decode()

                try:
                    server_data = json.loads(message)
                    server_ip = server_data.get("ip")
                    server_port = server_data.get("port")
                    server_type = server_data.get("server_type")

                    if server_type == "Primary" and server_ip and server_port:
                        self.set_primary_server_details(server_ip, server_port)
                        print(f"Primary server details set {server_ip}: {server_port}")
                    else:
                        print("Invalid server data received. Missing IP or port.")
                except json.JSONDecodeError:
                    print(f"Received invalid JSON message from {address}: {message}")
            except Exception as e:
                print(f"Error receiving multicast message: {e}")
                break

        sock.close()

    def connect_to_server(self):
        """Establish a unicast connection to the server."""
        try:
            print(f"Connecting to server {self.server_ip}:{self.server_port}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((self.server_ip, self.server_port))

                client_details = json.dumps({"client_ip": self.client_ip, "client_port": self.client_port,
                                             "message_type": "CLIENT_CONNECTION_TO_SERVER"})
                client_socket.sendall(client_details.encode())
                response = client_socket.recv(1024)
                print(f"Unicast response from server: {response.decode()}")
        except socket.error as e:
            print(f"Unicast connection error: {e}")

    def stop(self):
        """Stop the client."""
        print("Stopping client...")

        self.client_running = False
        if self.sock:
            self.sock.close()
            self.sock = None

        # Wait for the client thread to finish
        if hasattr(self, 'client_thread') and self.client_thread.is_alive():
            self.client_thread.join()
        print("Client stopped.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start a client.")
    parser.add_argument("ip", type=str, help="IP address of the client.")
    parser.add_argument("port", type=int, help="Port number of the client.")

    arguments = parser.parse_args()
    client = Client('224.3.29.71', 10000, arguments.ip, arguments.port)
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()
