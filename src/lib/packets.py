from enum import Enum
import hashlib
from queue import Full
from lib.task_serializer import TaskSerializer
from lib.task import Task
import struct

class PacketType(Enum):
    RegisterAgent = 0
    RegisterAgentResponse = 1
    Task = 2
    Metrics = 3
    ACK = 4

class Packet():
    def __init__(self, sequence_number = None, ack_number = None):
        self.sequence_number = sequence_number
        self.ack_number = ack_number

    def calculate_checksum(data):
        return hashlib.sha256(data).hexdigest()
    
    def validate_checksum(data, checksum):
        return checksum == Packet.calculate_checksum(data)

    @staticmethod
    def deserialize(data):
        packet_type_value = data[0]
        packet_type = PacketType(packet_type_value)
           
        if packet_type == PacketType.RegisterAgent:
            return RegisterAgentPacket.deserialize(data)
        elif packet_type == PacketType.RegisterAgentResponse:
            return RegisterAgentPacketResponse.deserialize(data)
        elif packet_type == PacketType.Task:
            return TaskPacket.deserialize(data)
        elif packet_type == PacketType.Metrics:
            return MetricsPacket.deserialize(data)
        elif packet_type == PacketType.ACK:
            return ACKPacket.deserialize(data)
        else:
            raise ValueError("Unknown packet type.")

class RegisterAgentPacket():
    def __init__(self, agent_id, sequence_number = None, ack_number = None):
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.packet_type = PacketType.RegisterAgent
        self.agent_id = agent_id

    # Packet structure :
    # | 1 byte | 5 bytes           | (6 bytes)
    # | Type   | Agent ID          |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += (self.sequence_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += (self.ack_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += self.agent_id.ljust(5).encode('utf-8')
        return packet_bytes

    def deserialize(data):
        sequence_number = data[1]
        ack_number = data[2]
        agent_id = data[3:8].decode('utf-8').strip()
        return RegisterAgentPacket(agent_id, sequence_number, ack_number)

class AgentRegistrationStatus(Enum):
    Success = 0
    AlreadyRegistered = 1
    InvalidID = 2

class RegisterAgentPacketResponse():
    def __init__(self, agent_registration_status, sequence_number=None, ack_number=None):
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.packet_type = PacketType.RegisterAgentResponse
        self.agent_registration_status = agent_registration_status

    # Packet structure :
    # | 1 byte | 1 byte | (2 bytes)
    # | Type   | Status |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += (self.sequence_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += (self.ack_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += self.agent_registration_status.value.to_bytes(1, byteorder='big')
        return packet_bytes

    def deserialize(data):
        sequence_number = data[1]
        ack_number = data[2]
        agent_registration_status = AgentRegistrationStatus(data[3])
        return RegisterAgentPacketResponse(agent_registration_status, sequence_number, ack_number)
    
class TaskPacket:
    def __init__(self, tasks, sequence_number, ack_number):
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.packet_type = PacketType.Task
        self.tasks = tasks

    # Packet structure :
    # | 1 byte | 1 byte | ? bytes | 
    # | Type   | #Tasks | Task 1  | Task 2 | ... | Task N |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += self.sequence_number.to_bytes(1, byteorder='big')
        packet_bytes += (self.ack_number or 0).to_bytes(1, byteorder='big')

        # Serialize number of tasks
        packet_bytes += len(self.tasks).to_bytes(1, byteorder='big')

        # Serialize each task
        for task in self.tasks:
            packet_bytes += TaskSerializer.serialize(task)

        checksum = Packet.calculate_checksum(packet_bytes)
        packet_bytes += checksum.encode('utf-8')

        return packet_bytes
    
    def deserialize(data):
        sequence_number = data[1]
        ack_number = data[2]
        tasks = []

        # Deserialize number of tasks
        num_tasks = data[3]

        # Deserialize each task
        offset = 4
        for i in range(num_tasks):
            task, offset = TaskSerializer.deserialize(data, offset)
            tasks.append(task)

        # Validate checksum
        checksum = data[offset:].decode('utf-8')
        if not Packet.validate_checksum(data[:offset], checksum):
            raise ValueError("Invalid checksum for TaskPacket")

        return TaskPacket(tasks, sequence_number, ack_number)

class MetricsPacket:
    def __init__(self, task_id, device_id, bandwidth=None, jitter=None, loss=None, latency=None, timestamp=None, sequence_number=None, ack_number=None):
        self.sequence_number = sequence_number
        self.ack_number = ack_number
        self.packet_type = PacketType.Metrics
        self.task_id = task_id
        self.device_id = device_id
        self.bandwidth = bandwidth
        self.jitter = jitter
        self.loss = loss
        self.latency = latency
        self.timestamp = timestamp

    # Packet structure:
    # | 1 byte  | 10 bytes | 5 bytes | 4 bytes   | 4 bytes | 4 bytes | 4 bytes   | 4 bytes    | (36 bytes)
    # | Type    | Task ID  | Dev ID  | Bandwidth | Jitter  | Loss    | Latency   | Timestamp  |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += (self.sequence_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += (self.ack_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += self.task_id.ljust(10).encode('utf-8')
        packet_bytes += self.device_id.ljust(5).encode('utf-8')

        packet_bytes += struct.pack('f', self.bandwidth if self.bandwidth is not None else float('nan'))
        packet_bytes += struct.pack('f', self.jitter if self.jitter is not None else float('nan'))
        packet_bytes += struct.pack('f', self.loss if self.loss is not None else float('nan'))
        packet_bytes += struct.pack('f', self.latency if self.latency is not None else float('nan'))
        packet_bytes += struct.pack('f', self.timestamp)

        checksum = Packet.calculate_checksum(packet_bytes)
        packet_bytes += checksum.encode('utf-8')

        return packet_bytes

    def deserialize(data):
        packet_type = PacketType(data[0])
        if packet_type != PacketType.Metrics:
            raise ValueError("Invalid packet type for MetricsPacket.")
        
        sequence_number = data[1]
        ack_number = data[2]

        # Deserialize Task ID and Device ID
        task_id = data[3:13].decode('utf-8').strip()
        device_id = data[13:18].decode('utf-8').strip()

        # Deserialize metrics as floats (convert NaN to None)
        bandwidth = struct.unpack('f', data[18:22])[0]
        jitter = struct.unpack('f', data[22:26])[0]
        loss = struct.unpack('f', data[26:30])[0]
        latency = struct.unpack('f', data[30:34])[0]
        timestamp = struct.unpack('f', data[34:38])[0]

        # Replace NaN values with None
        bandwidth = None if bandwidth != bandwidth else bandwidth  # Check for NaN
        jitter = None if jitter != jitter else jitter
        loss = None if loss != loss else loss
        latency = None if latency != latency else latency

        checksum = data[38:].decode('utf-8')
        if not Packet.validate_checksum(data[:38], checksum):
            raise ValueError("Invalid checksum for MetricsPacket")

        return MetricsPacket(task_id, device_id, bandwidth, jitter, loss, latency, timestamp, sequence_number, ack_number)
    
class ACKPacket():
    def __init__(self, sequence_number, ack_number):
        self.packet_type = PacketType.ACK
        self.sequence_number = sequence_number
        self.ack_number = ack_number

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += (self.sequence_number or 0).to_bytes(1, byteorder='big')
        packet_bytes += (self.ack_number or 0).to_bytes(1, byteorder='big')
        return packet_bytes
    
    @staticmethod
    def deserialize(data):
        sequence_number = data[1]
        ack_number = data[2]
        return ACKPacket(sequence_number, ack_number)