import socket
import threading
import queue
from lib.packets import ACKPacket, Packet, PacketType, FlowControlPacket
from lib.logging import log


class UDPServer:
    def __init__(self, host, port, handler, retransmission_timeout=2, max_retries=3, flow_control=20):
        '''
        Initializes the UDP server with the specified parameters.

        Args:
            host (str): Hostname or IP address to bind the server to.
            port (int): Port number to bind the server to.
            handler (callable): A handler function to process incoming packets.
            retransmission_timeout (int, optional): Timeout for retransmission of unacknowledged packets. Defaults to 2 seconds.
            max_retries (int, optional): Maximum number of retransmissions for unacknowledged packets. Defaults to 3.
            flow_control (int, optional): Maximum size of the client queue before applying flow control. Defaults to 20.
        '''
        self.host = host
        self.port = port
        self.handler = handler
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.is_running = False
        self.global_sequence_number = 0  # Global sequence number
        self.sent_packets = {}  # Map sequence_number -> (packet, client_address, event)
        self.client_queues = {}  # Map client_address -> {queue, expected_sequence_number, flow_state}
        self.lock = threading.Lock()
        self.retransmission_timeout = retransmission_timeout
        self.max_retries = max_retries
        self.flow_control = flow_control
        self.flow_condition = threading.Condition()

    def start(self):
        '''
        Starts the UDP server to listen for incoming packets.

        Continuously listens for incoming packets and spawns threads to handle them.
        '''
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
        '''
        Handles incoming packets from clients.

        Processes the packet, verifies checksums, and adds it to the appropriate client queue.

        Args:
            message (bytes): The raw packet data received from the client.
            client_address (tuple): The address of the client sending the packet.
        '''
        try:
            # Deserialize the received packet
            received_packet = Packet.deserialize(message)

            if received_packet.ack_number != 0:
                self.process_ack(received_packet)
                return

            # Add the packet to the clients queue
            self.add_to_client_queue(received_packet, client_address)

            # Process all client queues
            self.process_all_client_queues()
        except ValueError as e:
            log(f"Packet checksum mismatch: {e}", "ERROR")
            self.send_message(ACKPacket(received_packet.sequence_number, None), client_address)
        except Exception as e:
            log(f"Error handling packet from {client_address}: {e}", "ERROR")

    def stop(self):
        '''
        Stops the UDP server and releases the socket.
        '''
        self.is_running = False
        self.socket.close()
        log("UDP Server stopped.", "INFO")

    def process_ack(self, ack_packet):
        '''
        Processes an acknowledgment (ACK) packet.

        Updates the sent packets dictionary to mark the packet as acknowledged and signals waiting threads.

        Args:
            ack_packet (ACKPacket): The acknowledgment packet.
        '''
        # Handle the reception of an ACK packet.
        with self.lock:
            if ack_packet.ack_number in self.sent_packets:
                _, _, ack_event = self.sent_packets.pop(ack_packet.ack_number)
                log(f"ACK received for sequence {ack_packet.ack_number}")
                ack_event.set()  # Signal the waiting thread

        with self.flow_condition:
            self.flow_condition.notify_all()

    def send_message(self, message, client_address):
        '''
        Sends a message to the specified client with retransmission logic.

        Retransmits the message up to `max_retries` times if an acknowledgment is not received.

        Args:
            message (Packet): The packet to be sent.
            client_address (tuple): The address of the client to send the packet to.

        Returns:
            bool: True if the message was acknowledged, False otherwise.
        '''
        with self.lock:
            client_data = self.client_queues.get(client_address)
            if client_data and not client_data["can_send"]:
                log(f"Waiting for flow control to allow sending to {client_address}.")
                # Wait for the flow condition to be notified
                with self.flow_condition:
                    self.flow_condition.wait_for(lambda: client_data["can_send"])

        # Send a message with retransmission logic.
        if message.packet_type == PacketType.ACK:
            # No need for retransmission
            serialized_message = message.serialize()
            self.socket.sendto(serialized_message, client_address)
            return True

        with self.lock:
            # Assign a global sequence number
            self.global_sequence_number += 1
            message.sequence_number = self.global_sequence_number

        serialized_message = message.serialize()
         # Create an Event to wait for the ACK
        ack_event = threading.Event()
        with self.lock:
            self.sent_packets[message.sequence_number] = (message, client_address, ack_event)
        retries = 0
        while retries < self.max_retries:
            # Send the message
            self.socket.sendto(serialized_message, client_address)
            log(f"Sent message to {client_address} with sequence {message.sequence_number}, packet_type: {message.packet_type}. Attempt {retries + 1}")
            # Wait for the ACK
            if ack_event.wait(self.retransmission_timeout):
                log(f"ACK received for sequence {message.sequence_number}, stopping retransmission.")
                with self.lock:
                    self.sent_packets.pop(message.sequence_number, None)  # Clean up
                with self.flow_condition:
                    self.flow_condition.notify_all()
                return True  # ACK received, message delivered
            # Timeout, increment retry count
            retries += 1
            log(f"No ACK received for sequence {message.sequence_number}, retrying... ({retries}/{self.max_retries})")
        # Retries exhausted, clean up
        log(f"Failed to deliver message with sequence {message.sequence_number} after {self.max_retries} attempts.")
        with self.lock:
            self.sent_packets.pop(message.sequence_number, None)
        with self.flow_condition:
            self.flow_condition.notify_all()
        return False

    def add_to_client_queue(self, packet, client_address):
        '''
        Adds a received packet to the client's queue.

        Implements flow control by pausing/resuming sending based on the queue size.

        Args:
            packet (Packet): The received packet to be added to the queue.
            client_address (tuple): The address of the client sending the packet.
        '''
        with self.lock:
            if client_address not in self.client_queues:
                self.client_queues[client_address] = {
                    "queue": queue.PriorityQueue(),
                    "packets": {},
                    "expected_sequence_number": 1,
                    "can_send": True  # Initially, the server allows sending
                }
                log(f"Created queue for client {client_address}")

            client_data = self.client_queues[client_address]
            queue_size = client_data["queue"].qsize()

            # Enforce flow control
            if queue_size >= self.flow_control and client_data["can_send"]:
                log(f"Flow control triggered for {client_address}. Sending FlowControlPacket(can_send=False).")
                with self.lock:
                    self.global_sequence_number += 1
                self.send_message(FlowControlPacket(self.global_sequence_number,can_send=False), client_address)
                client_data["can_send"] = False

            elif queue_size < self.flow_control and not client_data["can_send"]:
                # If queue size is below flow control and can_send is False, resume sending
                log(f"Resuming flow for {client_address}. Sending FlowControlPacket(can_send=True).")
                client_data["can_send"] = True
                self.send_message(FlowControlPacket(self.global_sequence_number, can_send=True), client_address)

            log(f"Adding packet {packet.sequence_number} to queue for {client_address}")
            client_data["queue"].put(packet.sequence_number)
            client_data["packets"][packet.sequence_number] = packet

    def process_all_client_queues(self):
        '''
        Processes all client queues to handle packets in the correct order.

        Ensures packets are delivered to the handler function in sequence.
        '''
        with self.lock:
            for client_address, client_data in self.client_queues.items():
                self.process_client_queue(client_address, client_data)

    def process_client_queue(self, client_address, client_data):
        '''
        Processes the packet queue for a specific client.

        Delivers packets to the handler function and manages flow control based on the queue size.

        Args:
            client_address (tuple): The address of the client whose queue is being processed.
            client_data (dict): Data structure containing the client's queue and metadata.
        '''
        while not client_data["queue"].empty():
            seq_num = client_data["queue"].queue[0]
            log(f"Processing packet {seq_num} for client {client_address}")

            client_data["queue"].get()
            packet = client_data["packets"].pop(seq_num)

            threading.Thread(
                target=self.handler,
                args=(packet, client_address, self),
                daemon=True
            ).start()
            client_data["expected_sequence_number"] += 1

        # If the queue size is below the flow control limit and flow was paused, resume flow
        if client_data["queue"].qsize() < self.flow_control and not client_data["can_send"]:
            log(f"Resuming flow for {client_address}. Sending FlowControlPacket(can_send=True).")
            with self.lock:
                self.global_sequence_number += 1
            self.send_message(FlowControlPacket(self.global_sequence_number, can_send=True), client_address)
            client_data["can_send"] = True
