import socket
import threading

from lib.packets import ACKPacket, Packet, PacketType
from lib.logging import log


class UDPServer:
    def __init__(self, host, port, handler, retransmission_timeout=2, max_retries=3):
        self.host = host
        self.port = port
        self.handler = handler
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.is_running = False
        self.sequence_numbers = {} # Map client_address -> sequence_number
        self.sent_packets = {} # Map sequence_number -> (packet, client_address)
        self.lock = threading.Lock()
        self.retransmission_timeout = retransmission_timeout
        self.max_retries = max_retries

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

            if received_packet.ack_number != 0:
                return self.process_ack(received_packet, client_address)
            
            # Call the handler to process the packet
            response = self.handler(received_packet, client_address, self)
            
            # If a response is provided, serialize and send it back to the client
            if response:
                response.ack_number = received_packet.sequence_number
                self.send_message(response, client_address)
        except ValueError as e:
            log(f"Packet checksum mismatch: {e}", "ERROR")
            self.send_message(ACKPacket(received_packet.sequence_number, None), client_address)
        except Exception as e:
            log(f"Error handling packet from {client_address}: {e}", "ERROR")

    def stop(self):
        self.is_running = False
        self.socket.close()
        log("UDP Server stopped.", "INFO")

    def process_ack(self, ack_packet, client_address):
        with self.lock:
            if ack_packet.ack_number in self.sent_packets:
                del self.sent_packets[ack_packet.ack_number]  # Confirms delivery
                log(f"ACK received for sequence {ack_packet.ack_number} from {client_address}")
                return  # ACK processed
        return

    def send_message(self, message, client_address):
        if message.sequence_number is None:
            message.sequence_number = self.get_next_sequence_number(client_address)

        serialized_message = message.serialize()
        #event = threading.Event()
        self.socket.sendto(serialized_message, client_address)

        with self.lock:
            self.sent_packets[message.sequence_number] = (message, client_address)

        
    def get_next_sequence_number(self, client_address):
        self.sequence_numbers[client_address] = self.sequence_numbers.get(client_address, 0) + 1
        return self.sequence_numbers[client_address]
