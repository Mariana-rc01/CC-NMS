from enum import Enum
from queue import Full
from lib.task_serializer import TaskSerializer
from lib.task import Task

class PacketType(Enum):
    RegisterAgent = 0
    RegisterAgentResponse = 1
    Task = 2

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
    # | Type   | #Tasks | Task 1 | Task 2 | ... | Task N |

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
