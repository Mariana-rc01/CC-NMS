import socket
import threading

from lib.packets import Packet
from lib.logging import log

class UDPServer:
    def __init__(self, host, port, handler):
        self.host = host
        self.port = port
        self.handler = handler
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.is_running = False

    def start(self):
        self.is_running = True
        hostname, port = self.socket.getsockname()
        log(f"UDP server started on {hostname}:{port}.")

        while self.is_running:
            try:
                message, client_address = self.socket.recvfrom(1024)

                # Start a new thread for handling the received packet
                threading.Thread(
                    target=self.handle_packet,
                    args=(message, client_address),
                    daemon=True
                ).start()
            except KeyboardInterrupt:
                log("Server interrupted manually. Stopping.", "INFO")
                self.stop()
            except Exception as e:
                log(f"{e}", "ERROR")

    def handle_packet(self, message, client_address):
        try:
            # Deserialize the received packet
            received_packet = Packet.deserialize(message)
            
            # Call the handler to process the packet
            response = self.handler(received_packet, client_address)
            
            # If a response is provided, serialize and send it back to the client
            if response:
                serialized_response = response.serialize()
                self.socket.sendto(serialized_response, client_address)
        except Exception as e:
            log(f"Error handling packet from {client_address}: {e}", "ERROR")

    def stop(self):
        self.is_running = False
        self.socket.close()
        log("UDP Server stopped.", "INFO")

    def send_message(self, message, client_address):
        serialized_message = message.serialize()
        self.socket.sendto(serialized_message, client_address)
