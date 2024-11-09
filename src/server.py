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
from server.task_manager import load_tasks_json, show_tasks

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

    for task in tasks:
        for device in task.devices:
            agent_address = agent_manager.get_agent_by_id(device.device_id)
            if agent_address:
                task_packet = TaskPacket(task)
                server.send_message(task_packet, agent_address)
                print(f"Task {task.task_id} sent to agent {device.device_id}")

def main():
    print("Hello, from NMS Server!")

    tasks = load_tasks_json("tasks.json")
    show_tasks(tasks)

    server = UDPServer("0.0.0.0", 8080, server_packet_handler)
    alert_task_thread = threading.Thread(target=server.start, daemon=True)
    alert_task_thread.start()

    time.sleep(10)

    distribute_tasks_to_agents(server,tasks)

    alert_task_thread.join()

if __name__ == "__main__":
    main()