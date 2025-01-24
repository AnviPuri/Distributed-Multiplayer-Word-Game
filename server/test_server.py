import socket

def start_server():
    # Server binds to 192.168.0.101 and port 4000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('192.168.0.101', 4000))
    server_socket.listen(5)  # Listen for up to 5 simultaneous connections
    print("Server is listening on 192.168.0.101:4000")

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Connection received from {addr}")

            # Receive data from the client
            data = conn.recv(1024)
            if not data:
                print(f"No data received from {addr}. Closing connection.")
                conn.close()
                continue
            
            print(f"Server received: {data.decode()}")

            # Send response to the client
            conn.sendall(b"Hello from server")
            conn.close()  # Close the connection
    except KeyboardInterrupt:
        print("\nShutting down the server.")
    finally:
        server_socket.close()


start_server()
