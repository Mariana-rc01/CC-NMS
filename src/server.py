import threading
import sys
from time import localtime
import time

from lib.packets import (
    ACKPacket,
    AgentRegistrationStatus,
    Packet,
    PacketType,
    RegisterAgentPacketResponse,
    TaskPacket
)
from lib.udp import UDPServer
from server.agents_manager import AgentManager
from server.database import insert_metrics, setup_database, insert_alert
from server.task_json import load_tasks_json
from lib.logging import log
from lib.tcp import AlertMessage, TCPServer

agent_manager = AgentManager()
all_agents_registered = threading.Condition()
required_agents = set()
db_path = None

def server_packet_handler(message, client_address, server):
    '''
    Handles incoming packets from the UDP server.

    If the packet is an ACK, it logs the acknowledgment. For registration packets,
    it attempts to register the agent. For metrics packets, it processes and stores metrics.

    Args:
        message (Packet): The incoming packet object.
        client_address : The address of the client sending the packet.
        server (UDPServer): The UDP server instance.

    Returns:
        RegisterAgentPacketResponse or None: A response packet for agent registration or None.
    '''
    if message.ack_number != 0:
        log(f"ACK received for sequence {message.ack_number} from {client_address}.")
        return
    ack_packet = ACKPacket(message.sequence_number, message.sequence_number)
    server.send_message(ack_packet, client_address)

    if message.packet_type == PacketType.RegisterAgent:
        return handle_register_agent(message, client_address)
    elif message.packet_type == PacketType.Metrics:
        return handle_metrics(message, client_address)
    return None

def handle_metrics(message, client_address):
    '''
    Processes metrics packets sent by agents.

    Stores the metrics data in the database.

    Args:
        message (Packet): The metrics packet containing data.
        client_address (tuple): The address of the agent sending the metrics.

    Returns:
        None.
    '''
    global db_path

    if message.device_id in agent_manager.agent_ids:
        log(f"Metrics received from agent with ID {message.device_id}.")
        
        # Store metrics in the database
        insert_metrics(db_path, message.task_id, message.device_id, message.bandwidth, message.jitter, message.loss, message.latency, time.strftime('%Y-%m-%d %H:%M:%S', localtime(message.timestamp)))
        return None
    return None

def handle_register_agent(message, client_address):
    '''
    Registers an agent with the server.

    If the agent is successfully registered, it updates the set of required agents
    and notifies any waiting threads.

    Args:
        message (Packet): The registration packet.
        client_address : The address of the registering agent.

    Returns:
        RegisterAgentPacketResponse: The response packet indicating registration success or failure.
    '''
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

def handle_agent_alert(client_socket, client_address):
    '''
    Processes an alert received from an agent.

    Logs the alert and inserts it into the database.

    Args:
        alert_message (AlertMessage): The alert message containing alert details.
        client_address (tuple): The address of the agent sending the alert.

    Returns:
        None.
    '''
    try:
        # Receives the message
        data = client_socket.recv(1024)
        if not data:
            log(f"Empty message from {client_address}.")
            return

        # Deserializes the message
        alert_message = AlertMessage.deserialize(data)

        # Calls the alert handler
        handle_alert(alert_message, client_address)

    except Exception as e:
        log(f"Error handling client {client_address}: {e}.")
    finally:
        client_socket.close()

def handle_alert(alert_message, client_address):
    '''
    Handles an alert message from an agent.

    Logs the alert and stores it in the database.

    Args:
        alert_message (AlertMessage): The alert message containing alert details.
        client_address: The address of the agent sending the alert.

    Returns:
        None.
    '''
    log(f"Received alert from {client_address}.")

    insert_alert(db_path, alert_message.task_id, alert_message.device_id, alert_message.alert_type.name, alert_message.details,  time.strftime('%Y-%m-%d %H:%M:%S', localtime(alert_message.timestamp)))


def distribute_tasks_to_agents(server, tasks):
    '''
    Distributes monitoring tasks to registered agents.

    Groups tasks by device and sends them to the respective agents.

    Args:
        server (UDPServer): The UDP server instance.
        tasks (list): A list of tasks to be distributed.

    Returns:
        None.
    '''
    device_tasks = {}

    # Group tasks by device
    for task in tasks:
        for device in task.devices:
            device_tasks.setdefault(device.device_id, []).append(task)

    # Send tasks to each agent
    for device in device_tasks:
        agent_address = agent_manager.get_agent_by_id(device)
        if agent_address:
            task_packet = TaskPacket(device_tasks[device], None, None)
            server.send_message(task_packet, agent_address)
            log(f"Tasks sent to agent with ID {device}.")
            # Received ack:
            server_packet_handler(ACKPacket(0, task_packet.sequence_number), agent_address, server)
            # here we need to be careful when the task isn't send to the agent, we need to resend it

def main():
    '''
    Main function for starting the NMS server.

    Sets up the database, loads tasks, starts the TCP and UDP servers, and
    waits for all agents to register before distributing tasks.

    Returns:
        None.
    '''

    global db_path

    log("Starting up NMS server.")

    if len(sys.argv) != 3:
        print("Usage: python " + sys.argv[0] + " <tasks-json-file> <metrics-db-file>")
        sys.exit(1)

    tasks = load_tasks_json(sys.argv[1])

    db_path = sys.argv[2]
    setup_database(db_path)

    # Store device IDs to check if all required agents are registered
    for task in tasks:
        for device in task.devices:
            required_agents.add(device.device_id)

    tcp_server = TCPServer("0.0.0.0", 9090, handle_alert)
    tcp_server_thread = threading.Thread(target=tcp_server.start, daemon=True)
    tcp_server_thread.start()

    udp_server = UDPServer("0.0.0.0", 8080, server_packet_handler)
    alert_task_thread = threading.Thread(target=udp_server.start, daemon=True)
    alert_task_thread.start()

    # Wait for all required agents to be registered
    with all_agents_registered:
        all_agents_registered.wait()

    # Distribute tasks to agents
    distribute_tasks_to_agents(udp_server, tasks)

    alert_task_thread.join()

if __name__ == "__main__":
    main()
