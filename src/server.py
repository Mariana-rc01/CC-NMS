import threading

from lib.packets import (
    AgentRegistrationStatus,
    PacketType,
    RegisterAgentPacketResponse,
    TaskPacket
)
from lib.udp import UDPServer
from server.agents_manager import AgentManager
from server.task_json import load_tasks_json
from lib.logging import log

agent_manager = AgentManager()
all_agents_registered = threading.Condition()
required_agents = set()

def server_packet_handler(message, client_address):
    if message.packet_type == PacketType.RegisterAgent:
        return handle_register_agent(message, client_address)
    return None

def handle_register_agent(message, client_address):
    agent_id = message.agent_id
    if agent_manager.register_agent(agent_id, client_address):
        log(f"Agent {agent_id} registered.")

        # Check if all required agents are registered
        with all_agents_registered:
            required_agents.discard(agent_id)
            if not required_agents:  # All agents are registered
                all_agents_registered.notify_all()

        return RegisterAgentPacketResponse(AgentRegistrationStatus.Success)

    return RegisterAgentPacketResponse(AgentRegistrationStatus.AlreadyRegistered)

def distribute_tasks_to_agents(server, tasks):
    device_tasks = {}

    # Group tasks by device
    for task in tasks:
        for device in task.devices:
            device_tasks.setdefault(device.device_id, []).append(task)

    # Send tasks to each agent
    for device in device_tasks:
        agent_address = agent_manager.get_agent_by_id(device)
        if agent_address:
            task_packet = TaskPacket(device_tasks[device])
            server.send_message(task_packet, agent_address)
            log(f"Tasks sent to agent with ID {device}.")

def main():
    log("Starting up NMS server.")

    tasks = load_tasks_json("tasks.json")

    # Store device IDs to check if all required agents are registered
    for task in tasks:
        for device in task.devices:
            required_agents.add(device.device_id)

    server = UDPServer("0.0.0.0", 8080, server_packet_handler)
    alert_task_thread = threading.Thread(target=server.start, daemon=True)
    alert_task_thread.start()

    # Wait for all required agents to be registered
    with all_agents_registered:
        all_agents_registered.wait()

    # Distribute tasks to agents
    distribute_tasks_to_agents(server, tasks)

    alert_task_thread.join()

if __name__ == "__main__":
    main()
