from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM

def send_rcon(host: str, port: int, password: str, command: str, timeout: float = 6, no_response: bool = False) -> bytes | None:
    socket = Socket(AF_INET, SOCK_DGRAM)
    socket.connect((host, port))
    socket.settimeout(timeout)

    socket.send(b'\xff\xff\xff\xff' + f'rcon "{password}" {command}'.encode())
    if no_response:
        socket.close()
        return

    try:
        data, _ = socket.recvfrom(1024)
    except TimeoutError:
        return

    socket.close()
    return data

def is_alive(host: str, port: int, timeout: float = 6) -> bool:
    socket = Socket(AF_INET, SOCK_DGRAM)
    socket.connect((host, port))
    socket.settimeout(timeout)

    socket.send(b'\xff\xff\xff\xffgetstatus')

    try:
        _data, _ = socket.recvfrom(1024)
    except (TimeoutError, ConnectionResetError):
        return False

    return True