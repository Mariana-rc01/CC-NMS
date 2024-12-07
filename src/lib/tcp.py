import socket
import threading
from enum import Enum

from lib.logging import log

class AlertType(Enum):
    '''
    Enum representing the types of alerts that can be triggered.
    '''
    HIGH_JITTER = 1
    HIGH_PACKET_LOSS = 2
    HIGH_CPU_USAGE = 3
    HIGH_RAM_USAGE = 4
    HIGH_INTERFACE_STATS = 5

class AlertMessage:
    '''
    Represents an alert message exchanged between the agent and the server.
    '''
    def __init__(self, task_id, device_id, alert_type, details, timestamp):
        '''
        Initializes an AlertMessage object.

        Args:
            task_id (str): ID of the task associated with the alert.
            device_id (str): ID of the device triggering the alert.
            alert_type (AlertType): Type of alert being triggered.
            details (str): Additional details about the alert.
            timestamp (int): Timestamp of when the alert was generated.
        '''
        self.task_id = task_id
        self.device_id = device_id
        self.alert_type = alert_type
        self.details = details
        self.timestamp = timestamp

    def serialize(self):
        '''
        Serializes the AlertMessage into bytes for network transmission.

        Returns:
            bytes: Serialized byte representation of the alert message.
        '''
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
        '''
        Deserializes bytes into an AlertMessage object.

        Args:
            data (bytes): Byte data to be deserialized.

        Returns:
            AlertMessage: The deserialized AlertMessage object.

        Raises:
            ValueError: If the alert type is invalid.
        '''
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
    '''
    A TCP client for sending alert messages to the server.
    '''
    def __init__(self, server_ip, server_port):
        '''
        Initializes the TCP client with the server's address and port.

        Args:
            server_ip (str): The server's IP address.
            server_port (int): The server's port number.
        '''
        self.server_ip = server_ip
        self.server_port = server_port

    def send_alert(self, alert_message):
        '''
        Sends an alert message to the server.

        Args:
            alert_message (AlertMessage): The alert message to send.

        Logs:
            Sends a log message indicating the status of the transmission.
        '''
        try:
            log(f"Sending alert to {self.server_ip}:{self.server_port}.")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.server_ip, self.server_port))
                s.sendall(alert_message.serialize())
                log("Alert sent.")
        except Exception as e:
            log(f"Error sending alert: {e}.")

class TCPServer:
    '''
    A multithreaded TCP server for handling alert messages from agents.
    '''
    def __init__(self, host, port, alert_handler):
        '''
        Initializes the TCP server with a host, port, and an alert handler function.

        Args:
            host (str): The host/IP address to bind the server to.
            port (int): The port to bind the server to.
            alert_handler (callable): Function to process incoming alerts.
        '''
        self.host = host
        self.port = port
        self.alert_handler = alert_handler
        self.is_running = False

    def start(self):
        '''
        Starts the TCP server to accept connections and handle incoming alerts.

        Continuously listens for connections and spawns a new thread for each client.
        '''
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
        '''
        Handles communication with a connected client.

        Receives an alert message from the client, deserializes it, and invokes the alert handler.

        Args:
            client_socket (socket): The socket connected to the client.
            client_address (tuple): The address of the connected client.

        Logs:
            Errors or issues with the connection or data processing.
        '''
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
        '''
        Stops the TCP server and closes the listening socket.
        '''
        self.is_running = False
        self.socket.close()
        log("TCP Server stopped.")
