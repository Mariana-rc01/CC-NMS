import sys
import threading
import time

from lib.packets import AgentRegistrationStatus, PacketType, RegisterAgentPacket
from lib.udp import UDPServer
from agent.metrics import MetricsResult, calculate_bandwidth, calculate_jitter, calculate_packet_loss, calculate_latency
from agent.tools import iperf

agent_id = None

def task_runner(task):
    global agent_id
    subtasks = list(filter(lambda device: device.device_id == agent_id, task.devices))[0].link_metrics
    result = MetricsResult()

    # Bandwidth
    if subtasks.bandwidth and subtasks.bandwidth.is_server == False:
        print("Calculating Bandwidth")
        result.set_bandwidth(calculate_bandwidth(subtasks.bandwidth))

    # Jitter
    if subtasks.jitter and subtasks.jitter.is_server == False:
        print("Calculating Jitter")
        result.set_jitter(calculate_jitter(subtasks.jitter))

    # Packet Loss
    if subtasks.packet_loss and subtasks.packet_loss.is_server == False:
        print("Calculating Packet Loss")
        result.set_packet_loss(calculate_packet_loss(subtasks.packet_loss))

    # Latency
    if subtasks.latency:
        print("Calculating Latency")
        result.set_latency(calculate_latency(subtasks.latency))

    print(result.__dict__)
    return result

def run_task_periodically(task):
    def run():
        while True:
            # Run task_runner in a separate thread
            threading.Thread(target=task_runner, args=(task,), daemon=True).start()
            time.sleep(task.frequency)

    # Start the periodic timer in a separate daemon thread
    threading.Thread(target=run, daemon=True).start()

def maybe_start_iperf_servers(tasks):
    # If this agent serves as an iperf server (TCP and UDP), start the server here, and leave it running while the agent is active.
    has_server = False
    
    for task in tasks:
        for device in task.devices:
            if device.device_id == agent_id:
                possible_metrics = [device.link_metrics.bandwidth, device.link_metrics.jitter, device.link_metrics.packet_loss]
                for metric in possible_metrics:
                    if metric and metric.tool == "iperf" and metric.is_server:
                        has_server = True
                        break

    if has_server:
        print("Starting iperf servers")
        threading.Thread(target=iperf, args=(True, None, 0, "tcp"), daemon=True).start()
        threading.Thread(target=iperf, args=(True, None, 0, "udp"), daemon=True).start()


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
        # Received tasks from the server
        tasks = message.tasks

        maybe_start_iperf_servers(tasks)

        for task in tasks:
            task_thread = threading.Thread(target=run_task_periodically, args=(task,), daemon=True)
            task_thread.start()

    return None

def main():
    global agent_id
    print("Hello, from NMS Agent!")

    if len(sys.argv) != 3:
        print("Usage: python " + sys.argv[0] + " <server_ip> <agent_id>")
        sys.exit(1)

    server_ip = sys.argv[1]
    agent_id = sys.argv[2]
    
    udp_server = UDPServer("0.0.0.0", 0, agent_packet_handler)
    net_task_thread = threading.Thread(target=udp_server.start, daemon=True)
    net_task_thread.start()

    udp_server.send_message(RegisterAgentPacket(agent_id), (server_ip, 8080))

    net_task_thread.join()

if __name__ == "__main__":
    main()