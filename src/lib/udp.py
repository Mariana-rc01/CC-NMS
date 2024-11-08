import socket

from lib.packets import Packet

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
        print(f"UDP server started on {hostname}:{port}.")

        while self.is_running:
            try:
                message, client_address = self.socket.recvfrom(1024)

                received_packet = Packet.deserialize(message)
                
                response = self.handler(received_packet, client_address)
                
                # If a response is provided by the handler, send it back to the client (serialize it first)
                if response:
                    serialized_response = response.serialize()
                    self.socket.sendto(serialized_response, client_address)
            except KeyboardInterrupt:
                print("Server interrupted manually. Stopping.")
                self.stop()
            except Exception as e:
                print(f"Error: {e}")

    def stop(self):
        self.is_running = False
        self.socket.close()
        print("UDP Server stopped.")

    def send_message(self, message, client_address):
        serialized_message = message.serialize()
        self.socket.sendto(serialized_message, client_address)