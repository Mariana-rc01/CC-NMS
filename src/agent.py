import sys
import threading
import time

from lib.packets import ACKPacket, AgentRegistrationStatus, MetricsPacket, Packet, PacketType, RegisterAgentPacket
from lib.udp import UDPServer
from agent.metrics import MetricsResult, calculate_bandwidth, calculate_jitter, calculate_packet_loss, calculate_latency
from agent.conditions import ConditionsResult, calculate_cpu_usage, calculate_ram_usage, calculate_interface_stats
from agent.tools import iperf
from lib.logging import log
from lib.tcp import TCPClient, AlertMessage, AlertType

agent_id = None

def task_runner(task, server_address, udp_server, tcp_client):
    '''
    Executes a specific task assigned to the agent.

    This function calculates various metrics (bandwidth, jitter, packet loss, latency) 
    and conditions (CPU usage, RAM usage, interface stats) as per the task's configuration. 
    The results are sent back to the server via UDP, and alerts are sent via TCP if 
    thresholds are exceeded.

    Args:
        task: The task object containing metrics and conditions to calculate.
        server_address: The server's address to send the metrics.
        udp_server (UDPServer): The UDP server instance used for communication.
        tcp_client (TCPClient): The TCP client instance used for sending alerts.

    Returns:
        None.
    '''
    global agent_id
    subtasks = list(filter(lambda device: device.device_id == agent_id, task.devices))[0].link_metrics
    result = MetricsResult()
    resultConditions = ConditionsResult()
    interface_stats = list(filter(lambda device: device.device_id == agent_id, task.devices))[0].device_metrics.interface_stats

    alterflow_conditions = subtasks.alertflow_conditions

    # Bandwidth
    if subtasks.bandwidth and subtasks.bandwidth.is_server == False:
        log(f"Calculating Bandwidth for task ({task.id}).")
        result.set_bandwidth(calculate_bandwidth(subtasks.bandwidth))

    # Jitter
    if subtasks.jitter and subtasks.jitter.is_server == False:
        log(f"Calculating Jitter for task ({task.id}).")
        result.set_jitter(calculate_jitter(subtasks.jitter))
        resultConditions.set_jitter(result.jitter)

    # Packet Loss
    if subtasks.packet_loss and subtasks.packet_loss.is_server == False:
        log(f"Calculating Packet Loss for task ({task.id}).")
        result.set_packet_loss(calculate_packet_loss(subtasks.packet_loss))
        resultConditions.set_packet_loss(result.packet_loss)

    # Latency
    if subtasks.latency:
        log(f"Calculating Latency for task ({task.id}).")
        result.set_latency(calculate_latency(subtasks.latency))

    if not result.bandwidth and not result.jitter and not result.packet_loss and not result.latency:
        # No metrics were able to be recorded
        return
    
    # CPU Usage
    log(f"Calculating CPU Usage for task ({task.id}).")
    resultConditions.set_cpu_usage(calculate_cpu_usage())

    # RAM Usage
    log(f"Calculating RAM Usage for task ({task.id}).")
    resultConditions.set_ram_usage(calculate_ram_usage())

    # Interface Stats
    log(f"Calculating Interface Stats for task ({task.id}).")
    resultConditions.set_interface_stats(calculate_interface_stats(interface_stats))

    # Send the results back to the server
    packet = MetricsPacket(task.id, agent_id, result.bandwidth, result.jitter, result.packet_loss, result.latency, int(time.time()))
    udp_server.send_message(packet, server_address)

    alerts = check_critical_changes(resultConditions, alterflow_conditions)
    for alert, alert_type in alerts:
        alert_message = AlertMessage(
            task_id=task.id,
            device_id=agent_id,
            alert_type=alert_type,
            details=alert,
            timestamp=int(time.time())
        )
        tcp_client.send_alert(alert_message)

def check_critical_changes(metrics, thresholds):
    '''
    Checks if any calculated metrics exceed their defined thresholds and generates alerts.

    Args:
        metrics (ConditionsResult): The calculated metrics of the agent (CPU, RAM, jitter, etc.).
        thresholds: The thresholds specified for the task's metrics and conditions.

    Returns:
        list: A list of tuples containing the alert message and its type.
    '''
    alerts = []

    if metrics.cpu_usage > thresholds.cpu_usage:
        alerts.append((f"CPU usage is above the threshold: {round(metrics.cpu_usage, 2)}%", AlertType.HIGH_CPU_USAGE))
    
    if metrics.ram_usage > thresholds.ram_usage:
        alerts.append((f"RAM usage is above the threshold: {round(metrics.ram_usage, 2)}%", AlertType.HIGH_RAM_USAGE))

    if metrics.packet_loss and metrics.packet_loss > thresholds.packet_loss:
        alerts.append((f"Packet loss is above the threshold: {round(metrics.packet_loss, 2)}%", AlertType.HIGH_PACKET_LOSS))

    if metrics.jitter and metrics.jitter > thresholds.jitter:
        alerts.append((f"Jitter is above the threshold: {round(metrics.jitter, 2)}ms", AlertType.HIGH_JITTER))
    
    if metrics.interface_stats > thresholds.interface_stats:
        alerts.append((f"Interface stats are above the threshold: {round(metrics.interface_stats, 2)}", AlertType.HIGH_INTERFACE_STATS))

    return alerts


def run_task_periodically(task, server_address, udp_server, tcp_client):
    '''
    Periodically executes a task based on the defined frequency.

    This function schedules the task runner to execute in a separate thread at regular intervals.

    Args:
        task: The task object containing the task configuration.
        server_address: The server's address to send the metrics.
        udp_server (UDPServer): The UDP server instance used for communication.
        tcp_client (TCPClient): The TCP client instance used for sending alerts.

    Returns:
        None.
    '''
    def run():
        while True:
            # Run task_runner in a separate thread
            threading.Thread(target=task_runner, args=(task, server_address, udp_server, tcp_client), daemon=True).start()
            time.sleep(task.frequency)

    # Start the periodic timer in a separate daemon thread
    threading.Thread(target=run, daemon=True).start()

def maybe_start_iperf_servers(tasks):
    '''
    Starts iperf servers for TCP and UDP if the agent is required to act as a server.

    This function iterates through the tasks to check if the agent is configured as an iperf server.
    If so, it starts the iperf servers for both TCP and UDP in separate threads.

    Args:
        tasks (list): A list of tasks assigned to the agent.

    Returns:
        None.
    '''
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


def agent_packet_handler(message, server_address, server, tcp_client):
    '''
    Handles incoming packets from the NMS server.

    This function processes registration responses and task packets. It sends acknowledgments 
    for received packets and starts tasks in separate threads.

    Args:
        message (Packet): The incoming packet object from the server.
        server_address: The server's address.
        server (UDPServer): The UDP server instance used for communication.
        tcp_client (TCPClient): The TCP client instance used for sending alerts.

    Returns:
        None.
    '''
    if message.ack_number != 0:
        log(f"ACK received for sequence {message.ack_number}")
        return
    
    ack_packet = ACKPacket(message.sequence_number, message.sequence_number)
    server.send_message(ack_packet, server_address)

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
            task_thread = threading.Thread(target=run_task_periodically, args=(task, server_address, server, tcp_client), daemon=True)
            task_thread.start()

    return None

def main():
    '''
    The entry point for the agent program.

    This function initializes the agent, registers it with the NMS server, and starts 
    listening for tasks and metrics on UDP and TCP channels.

    Command-line arguments:
        <server_ip>: The IP address of the server.
        <agent_id>: The unique ID of the agent.

    Returns:
        None.
    '''
    global agent_id
    log("Starting up NMS agent.")

    if len(sys.argv) != 3:
        print("Usage: python " + sys.argv[0] + " <server_ip> <agent_id>")
        sys.exit(1)

    server_ip = sys.argv[1]
    agent_id = sys.argv[2]
    
    tcp_client = TCPClient(server_ip, server_port=9090)

    udp_server = UDPServer("0.0.0.0", 0, lambda msg, addr, srv: agent_packet_handler(msg, addr, srv, tcp_client))
    net_task_thread = threading.Thread(target=udp_server.start, daemon=True)
    net_task_thread.start()

    udp_server.send_message(RegisterAgentPacket(agent_id, None, None), (server_ip, 8080))

    net_task_thread.join()

if __name__ == "__main__":
    main()
