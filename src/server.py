import threading
import time

from lib.packets import (
    AgentRegistrationStatus,
    PacketType,
    RegisterAgentPacketResponse,
    TaskPacket
)
from lib.udp import UDPServer
from server.agents_manager import AgentManager
from server.task_json import load_tasks_json

agent_manager = AgentManager()

def server_packet_handler(message, client_address):
    if message.packet_type == PacketType.RegisterAgent:
        return handle_register_agent(message, client_address)
    return None

def handle_register_agent(message, client_address):
    agent_id = message.agent_id
    if agent_manager.register_agent(agent_id, client_address):
        # Agent registered successfully.
        print(f"Agent {agent_id} registered.")
        return RegisterAgentPacketResponse(AgentRegistrationStatus.Success)
    
    # Agent already registered.
    return RegisterAgentPacketResponse(AgentRegistrationStatus.AlreadyRegistered)

def distribute_tasks_to_agents(server, tasks):
    device_tasks = {}

    # Group tasks by device.
    for task in tasks:
        for device in task.devices:
            device_tasks.setdefault(device.device_id, []).append(task)

    # Send tasks to each agent.
    for device in device_tasks:
        agent_address = agent_manager.get_agent_by_id(device)
        if agent_address:
            task_packet = TaskPacket(device_tasks[device])
            server.send_message(task_packet, agent_address)
            print(f"Tasks sent to agent {device}")

def main():
    print("Hello, from NMS Server!")

    tasks = load_tasks_json("tasks.json")
    for task in tasks: print(task)

    server = UDPServer("0.0.0.0", 8080, server_packet_handler)
    alert_task_thread = threading.Thread(target=server.start, daemon=True)
    alert_task_thread.start()

    # TODO: Send tasks when all agents needed are connected and registered.
    time.sleep(10)

    distribute_tasks_to_agents(server, tasks)

    alert_task_thread.join()

if __name__ == "__main__":
    main()