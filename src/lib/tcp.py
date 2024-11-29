import socket
import threading
from enum import Enum

from lib.logging import log

class AlertType(Enum):
    HIGH_JITTER = 1
    HIGH_PACKET_LOSS = 2
    HIGH_CPU_USAGE = 3
    HIGH_RAM_USAGE = 4
    HIGH_INTERFACE_STATS = 5

class AlertMessage:
    def __init__(self, task_id, device_id, alert_type, details, timestamp):
        self.task_id = task_id
        self.device_id = device_id
        self.alert_type = alert_type
        self.details = details
        self.timestamp = timestamp

    def serialize(self):
        message = b''

        # Task ID
        task_id_bytes = self.task_id.encode('utf-8')
        message += len(task_id_bytes).to_bytes(1, byteorder='big')
        message += task_id_bytes

        # Device ID
        device_id_bytes = self.device_id.encode('utf-8')
        message += len(device_id_bytes).to_bytes(1, byteorder='big')
        message += device_id_bytes

        # Alert type
        message += self.alert_type.value.to_bytes(1, byteorder='big')

        # Timestamp
        message += int(self.timestamp).to_bytes(8, byteorder='big')

        # Details
        details_bytes = self.details.encode('utf-8')
        message += len(details_bytes).to_bytes(4, byteorder='big')
        message += details_bytes

        return message

    def deserialize(data):
        index = 0

        # Task ID
        task_id_length = int.from_bytes(data[index:index+1], byteorder='big')
        index += 1
        task_id = data[index:index+task_id_length].decode('utf-8')
        index += task_id_length

        # Device ID
        device_id_length = int.from_bytes(data[index:index+1], byteorder='big')
        index += 1
        device_id = data[index:index+device_id_length].decode('utf-8')
        index += device_id_length

        # Alert type
        alert_type_value = int.from_bytes(data[index:index+1], byteorder='big')
        try:
            alert_type = AlertType(alert_type_value)
        except ValueError:
            raise ValueError(f"Invalid AlertType value: {alert_type_value}")
        index += 1

        # Timestamp
        timestamp = int.from_bytes(data[index:index+8], byteorder='big')
        index += 8

        # Details
        details_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        details = data[index:index+details_len].decode('utf-8')

        return AlertMessage(task_id, device_id, alert_type, details, timestamp)

class TCPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

    def send_alert(self, alert_message):
        try:
            log(f"Sending alert to {self.server_ip}:{self.server_port}.")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.server_ip, self.server_port))
                s.sendall(alert_message.serialize())
                log("Alert sent.")
        except Exception as e:
            log(f"Error sending alert: {e}.")

class TCPServer:
    def __init__(self, host, port, alert_handler):
        self.host = host
        self.port = port
        self.alert_handler = alert_handler
        self.is_running = False

    def start(self):
        self.is_running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

        log(f"TCP Server started on {self.host}:{self.port}.")

        while True:
            try:
                client_socket, client_address = self.socket.accept()
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                ).start()
            except Exception as e:
                log(f"Error accepting connection: {e}.")

    def handle_client(self, client_socket, client_address):
        try:
            data = client_socket.recv(1024)
            if not data:
                log(f"Empty message from {client_address}.")
                return

            alert_message = AlertMessage.deserialize(data)
            self.alert_handler(alert_message, client_address)

        except Exception as e:
            log(f"Error handling client {client_address}: {e}.")
        finally:
            client_socket.close()

    def stop(self):
        self.is_running = False
        self.socket.close()
        log("TCP Server stopped.")
