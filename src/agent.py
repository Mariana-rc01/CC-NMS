import sys
import threading
import time

from lib.packets import AgentRegistrationStatus, MetricsPacket, PacketType, RegisterAgentPacket
from lib.udp import UDPServer
from agent.metrics import MetricsResult, calculate_bandwidth, calculate_jitter, calculate_packet_loss, calculate_latency
from agent.tools import iperf
from lib.logging import log

agent_id = None

def task_runner(task, server_address, udp_server):
    global agent_id
    subtasks = list(filter(lambda device: device.device_id == agent_id, task.devices))[0].link_metrics
    result = MetricsResult()

    # Bandwidth
    if subtasks.bandwidth and subtasks.bandwidth.is_server == False:
        log(f"Calculating Bandwidth for task ({task.id}).")
        result.set_bandwidth(calculate_bandwidth(subtasks.bandwidth))

    # Jitter
    if subtasks.jitter and subtasks.jitter.is_server == False:
        log(f"Calculating Jitter for task ({task.id}).")
        result.set_jitter(calculate_jitter(subtasks.jitter))

    # Packet Loss
    if subtasks.packet_loss and subtasks.packet_loss.is_server == False:
        log(f"Calculating Packet Loss for task ({task.id}).")
        result.set_packet_loss(calculate_packet_loss(subtasks.packet_loss))

    # Latency
    if subtasks.latency:
        log(f"Calculating Latency for task ({task.id}).")
        result.set_latency(calculate_latency(subtasks.latency))

    if not result.bandwidth and not result.jitter and not result.packet_loss and not result.latency:
        # No metrics were able to be recorded
        return

    # Send the results back to the server
    packet = MetricsPacket(task.id, agent_id, result.bandwidth, result.jitter, result.packet_loss, result.latency, time.time())
    udp_server.send_message(packet, server_address)


def run_task_periodically(task, server_address, udp_server):
    def run():
        while True:
            # Run task_runner in a separate thread
            threading.Thread(target=task_runner, args=(task, server_address, udp_server), daemon=True).start()
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
        log("Starting iperf servers for TCP and UDP.")
        threading.Thread(target=iperf, args=(True, None, 0, "tcp"), daemon=True).start()
        threading.Thread(target=iperf, args=(True, None, 0, "udp"), daemon=True).start()


def agent_packet_handler(message, server_address, server):
    if message.packet_type == PacketType.RegisterAgentResponse:
        register_status = message.agent_registration_status
        if register_status == AgentRegistrationStatus.Success:
            log("Agent registered successfully.")
        elif register_status == AgentRegistrationStatus.AlreadyRegistered:
            log("An agent with this ID is already registered.", "ERROR")
            exit(1)
        elif register_status == AgentRegistrationStatus.InvalidID:
            log("The server isn't configured to accept agents with this ID.", "ERROR")
            exit(1)
    elif message.packet_type == PacketType.Task:
        # Received tasks from the server
        tasks = message.tasks

        maybe_start_iperf_servers(tasks)

        for task in tasks:
            task_thread = threading.Thread(target=run_task_periodically, args=(task, server_address, server), daemon=True)
            task_thread.start()

    return None

def main():
    global agent_id
    log("Starting up NMS agent.")

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