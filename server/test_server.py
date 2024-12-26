import socket

def start_server():
    # Server binds to 127.0.0.1 and port 5000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 4000))
    server_socket.listen(1)
    print("Server is listening on 127.0.0.1:4000")

    conn, addr = server_socket.accept()
    print(f"Connection received from {addr}")
    data = conn.recv(1024)
    print(f"Server received: {data.decode()}")
    conn.sendall(b"Hello from server")
    conn.close()
    server_socket.close()


start_server()
