import socket
import struct
from typing import Optional

PACKET_TYPE_RESPONSE = 0
PACKET_TYPE_COMMAND = 2
PACKET_TYPE_LOGIN = 3

def _send_packet(sock: socket.socket, request_id: int, packet_type: int, body: str) -> None:
    data = body.encode('utf-8')
    length = 4 + 4 + len(data) + 2
    packet = struct.pack('<iii', length - 4, request_id, packet_type) + data + b'\x00\x00'
    sock.sendall(packet)

def _read_packet(sock: socket.socket) -> Optional[tuple]:
    header = sock.recv(4)
    if not header or len(header) < 4:
        return None
    (length,) = struct.unpack('<i', header)
    payload = b''
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            break
        payload += chunk
    if len(payload) < 8:
        return None
    request_id, packet_type = struct.unpack('<ii', payload[:8])
    body = payload[8:-2].decode('utf-8', errors='ignore')
    return request_id, packet_type, body

def send_rcon_command(host: str, port: int, password: str, command: str, timeout: float = 3.0) -> Optional[str]:
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            request_id = 1
            _send_packet(sock, request_id, PACKET_TYPE_LOGIN, password)
            resp = _read_packet(sock)
            if not resp or resp[0] == -1:
                return None
            _send_packet(sock, request_id, PACKET_TYPE_COMMAND, command)
            resp = _read_packet(sock)
            if not resp:
                return None
            return resp[2]
    except Exception:
        return None
