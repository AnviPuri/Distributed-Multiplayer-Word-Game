import socket

def is_ip_in_use(ip, port=80):
    try:
        # Try to bind to the IP and port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((ip, port))
        return False  # IP is not in use if binding succeeds
    except OSError:
        return True  # IP is in use if binding fails

ip_to_check = "224.0.0.1"
port_to_check = 5004

if is_ip_in_use(ip_to_check, port_to_check):
    print(f"The IP {ip_to_check} with port {port_to_check} is in use.")
else:
    print(f"The IP {ip_to_check} with port {port_to_check} is free.")
