import socket

def start_client():
    # Client binds to 127.0.0.2 and connects to the server on 127.0.0.1:5001
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind(('127.0.0.2', 4000))  # Use a different IP and port for the client
    client_socket.connect(('127.0.0.1', 4000))
    print("Client connected to server on 127.0.0.1:5001")
    client_socket.sendall(b"Hello from client")
    data = client_socket.recv(1024)
    print(f"Client received: {data.decode()}")
    client_socket.close()

start_client()
