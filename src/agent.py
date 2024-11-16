import sys
import threading

from lib.packets import AgentRegistrationStatus, PacketType, RegisterAgentPacket
from lib.udp import UDPServer

def task_runner(task):
    print(f"Running task {task.task_id}...")
    # TODO: Implement task runner


def agent_packet_handler(message, server_address):
    if message.packet_type == PacketType.RegisterAgentResponse:
        register_status = message.agent_registration_status
        if register_status == AgentRegistrationStatus.Success:
            print("Agent registered successfully.")
        elif register_status == AgentRegistrationStatus.AlreadyRegistered:
            print("An agent with this ID is already registered.")
            exit(1)
        elif register_status == AgentRegistrationStatus.InvalidID:
            print("The server isn't configured to accept agents with this ID.")
            exit(1)
    elif message.packet_type == PacketType.Task:
        tasks = message.tasks
        for task in tasks:
            task_thread = threading.Thread(target=task_runner, args=(task,), daemon=True)
            task_thread.start()
            task_thread.join()

    return None

def main():
    print("Hello, from NMS Agent!")

    if len(sys.argv) != 3:
        print("Usage: python " + sys.argv[0] + " <server_ip> <agent_id>")
        sys.exit(1)

    server_ip = sys.argv[1]
    agent_id = sys.argv[2]
    
    udp_server = UDPServer("0.0.0.0", 0, agent_packet_handler)
    alert_task_thread = threading.Thread(target=udp_server.start, daemon=True)
    alert_task_thread.start()

    udp_server.send_message(RegisterAgentPacket(agent_id), (server_ip, 8080))

    alert_task_thread.join()

if __name__ == "__main__":
    main()