import logging
import subprocess
import psutil

class ConditionsResult:
    def __init__(self):
        self.cpu_usage = None
        self.ram_usage = None
        self.interface_stats = None
        self.packet_loss = None
        self.jitter = None

    def set_cpu_usage(self, cpu_usage):
        self.cpu_usage = cpu_usage
    
    def set_ram_usage(self, ram_usage):
        self.ram_usage = ram_usage
    
    def set_interface_stats(self, interface_stats):
        self.interface_stats = interface_stats
    
    def set_packet_loss(self, packet_loss):
        self.packet_loss = packet_loss
    
    def set_jitter(self, jitter):
        self.jitter = jitter

def calculate_cpu_usage():
    # Using the 'top' command to get CPU usage
    result = subprocess.run(['top', '-bn1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    top_output = result.stdout.decode('utf-8')

    # Searching for the line with CPU information
    for line in top_output.splitlines():
        if "Cpu(s)" in line:
            # The line contains CPU usage information
            cpu_usage = line.split(',')[1].strip().split(' ')[0]  # Ex: 15.1%
            return float(cpu_usage)  # Returns the CPU usage percentage
    return 0.0  # If it fails to capture, it will return 0%

def calculate_ram_usage():
    result = subprocess.run(['free', '-m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    free_output = result.stdout.decode('utf-8')

    # Searching for the line with memory information
    for line in free_output.splitlines():
        if "Mem" in line:
            # The line contains memory information
            memory_info = line.split()
            total_memory = int(memory_info[1])  # Total memory
            used_memory = int(memory_info[2])   # Used memory
            return (used_memory / total_memory) * 100  # Returns the RAM usage percentage
    return 0.0  # If it fails to capture, it will return 0%

def calculate_interface_stats(interfaces=None):
    #Calculate the total number of packets sent and received for the provided interfaces.
    #Uses the psutil library to get network stats.

    total_packets = 0

    if interfaces is None or len(interfaces) == 0:
        logging.info("No interfaces provided for calculation.")
        return total_packets

    for interface in interfaces:
        try:
            # Get network stats for each interface
            net_io = psutil.net_io_counters(pernic=True)
            
            if interface in net_io:
                interface_stats = net_io[interface]
                # Sum the number of packets sent and received
                total_packets += interface_stats.packets_sent + interface_stats.packets_recv
                logging.info(f"Interface {interface} - Sent: {interface_stats.packets_sent} | Received: {interface_stats.packets_recv}")
            else:
                logging.warning(f"Interface {interface} not found in network stats.")
                
        except Exception as e:
            logging.error(f"Error reading stats for {interface}: {e}")
            continue  # If an error occurs, continue to the next interface

    return total_packets