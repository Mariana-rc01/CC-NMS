import threading

from lib.packets import (
    AgentRegistrationStatus,
    PacketType,
    RegisterAgentPacketResponse
)
from lib.udp import UDPServer
from server.agents_manager import AgentManager

agent_manager = AgentManager()

def server_packet_handler(message, client_address):
    if message.packet_type == PacketType.RegisterAgent:
        return handle_register_agent(message, client_address)
    return None

def handle_register_agent(message, client_address):
    agent_id = message.agent_id
    if agent_manager.register_agent(agent_id):
        # Agent registered successfully.
        print(f"Agent {agent_id} registered.")
        return RegisterAgentPacketResponse(AgentRegistrationStatus.Success)
    
    # Agent already registered.
    return RegisterAgentPacketResponse(AgentRegistrationStatus.AlreadyRegistered)

def main():
    print("Hello, from NMS Server!")
    server = UDPServer("0.0.0.0", 8080, server_packet_handler)
    alert_task_thread = threading.Thread(target=server.start, daemon=True)
    alert_task_thread.start()

    alert_task_thread.join()

if __name__ == "__main__":
    main()