from enum import Enum
from queue import Full
from lib.task_serializer import TaskSerializer
from lib.task import Task
import struct

class PacketType(Enum):
    RegisterAgent = 0
    RegisterAgentResponse = 1
    Task = 2
    Metrics = 3

class Packet():
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
        else:
            raise ValueError("Unknown packet type.")

class RegisterAgentPacket():
    def __init__(self, agent_id):
        self.packet_type = PacketType.RegisterAgent
        self.agent_id = agent_id

    # Packet structure :
    # | 1 byte | 5 bytes           | (6 bytes)
    # | Type   | Agent ID          |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += self.agent_id.ljust(5).encode('utf-8')
        return packet_bytes

    def deserialize(data):
        agent_id = data[1:6].decode('utf-8').strip()
        return RegisterAgentPacket(agent_id)

class AgentRegistrationStatus(Enum):
    Success = 0
    AlreadyRegistered = 1
    InvalidID = 2

class RegisterAgentPacketResponse():
    def __init__(self, agent_registration_status):
        self.packet_type = PacketType.RegisterAgentResponse
        self.agent_registration_status = agent_registration_status

    # Packet structure :
    # | 1 byte | 1 byte | (2 bytes)
    # | Type   | Status |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')
        packet_bytes += self.agent_registration_status.value.to_bytes(1, byteorder='big')
        return packet_bytes

    def deserialize(data):
        agent_registration_status = AgentRegistrationStatus(data[1])
        return RegisterAgentPacketResponse(agent_registration_status)
    
class TaskPacket:
    def __init__(self, tasks):
        self.packet_type = PacketType.Task
        self.tasks = tasks

    # Packet structure :
    # | 1 byte | 1 byte | ? bytes | 
    # | Type   | #Tasks | Task 1  | Task 2 | ... | Task N |

    def serialize(self):
        packet_bytes = b''
        packet_bytes += self.packet_type.value.to_bytes(1, byteorder='big')

        # Serialize number of tasks
        packet_bytes += len(self.tasks).to_bytes(1, byteorder='big')

        # Serialize each task
        for task in self.tasks:
            packet_bytes += TaskSerializer.serialize(task)

        return packet_bytes
    
    def deserialize(data):
        tasks = []

        # Deserialize number of tasks
        num_tasks = data[1]

        # Deserialize each task
        offset = 2
        for i in range(num_tasks):
            task, offset = TaskSerializer.deserialize(data, offset)
            tasks.append(task)

        return TaskPacket(tasks)

class MetricsPacket:
    def __init__(self, task_id, device_id, bandwidth=None, jitter=None, loss=None, latency=None, timestamp=None):
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
        packet_bytes += self.task_id.ljust(10).encode('utf-8')
        packet_bytes += self.device_id.ljust(5).encode('utf-8')

        packet_bytes += struct.pack('f', self.bandwidth if self.bandwidth is not None else float('nan'))
        packet_bytes += struct.pack('f', self.jitter if self.jitter is not None else float('nan'))
        packet_bytes += struct.pack('f', self.loss if self.loss is not None else float('nan'))
        packet_bytes += struct.pack('f', self.latency if self.latency is not None else float('nan'))
        packet_bytes += struct.pack('f', self.timestamp)

        return packet_bytes

    def deserialize(data):
        packet_type = PacketType(data[0])
        if packet_type != PacketType.Metrics:
            raise ValueError("Invalid packet type for MetricsPacket.")

        # Deserialize Task ID and Device ID
        task_id = data[1:11].decode('utf-8').strip()
        device_id = data[11:16].decode('utf-8').strip()

        # Deserialize metrics as floats (convert NaN to None)
        bandwidth = struct.unpack('f', data[16:20])[0]
        jitter = struct.unpack('f', data[20:24])[0]
        loss = struct.unpack('f', data[24:28])[0]
        latency = struct.unpack('f', data[28:32])[0]
        timestamp = struct.unpack('f', data[32:36])[0]

        # Replace NaN values with None
        bandwidth = None if bandwidth != bandwidth else bandwidth  # Check for NaN
        jitter = None if jitter != jitter else jitter
        loss = None if loss != loss else loss
        latency = None if latency != latency else latency

        return MetricsPacket(task_id, device_id, bandwidth, jitter, loss, latency, timestamp)