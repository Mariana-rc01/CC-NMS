import subprocess
import re
import time
from logging import log

class PingResult:
    '''
    Represents the result of a ping operation.

    Attributes:
        packet_loss (int): The percentage of packet loss during the ping.
        latency (float): The average latency in milliseconds.
        error (str): An error message, if any occurred during the ping operation.
    '''
    def __init__(self, packet_loss, latency, error):
        '''
        Initializes a PingResult instance.

        Args:
            packet_loss (int): Percentage of packet loss.
            latency (float): Average latency in milliseconds.
            error (str): Error message if the ping failed.
        '''
        self.packet_loss = packet_loss
        self.latency = latency
        self.error = error

def ping(destination_address, packet_count, frequency):
    '''
    Executes a ping command and parses the output to extract metrics.

    Args:
        destination_address (str): The destination IP address or hostname to ping.
        packet_count (int): The number of packets to send.
        frequency (float): The interval between each ping in seconds.

    Returns:
        PingResult: The parsed result of the ping operation, including packet loss, latency, and any error message.
    '''
    try:
        command = ["ping", "-c", str(packet_count), "-i", str(frequency), destination_address]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return PingResult(None, None, f"ping command failed: {result.stderr}")
        
        # Extract packet loss information from the output
        packet_loss = None
        output = result.stdout
        match = re.search(r"(\d+)% packet loss", output)

        if match:
            packet_loss = int(match.group(1))

        # Extract average latency information from the output
        latency = None
        match = re.search(r"min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms", output)

        if match:
            latency = float(match.group(1))

        if packet_loss is None or latency is None:
            return PingResult(packet_loss, latency, f"failed to parse ping output: {output}")
        
        return PingResult(packet_loss, latency, None)
    except Exception as e:
        log(f"Failed to execute ping command: {str(e)}", "ERROR")
        return PingResult(None, None, f"failed to execute ping command: {str(e)}")
    
class IperfResult:
    '''
    Represents the result of an iperf operation.

    Attributes:
        bandwidth (float): The measured bandwidth in Mbps.
        jitter (float): The measured jitter in milliseconds (UDP only).
        packet_loss (float): The percentage of packet loss (UDP only).
        error (str): An error message, if any occurred during the iperf operation.
    '''
    def __init__(self, bandwidth, jitter, packet_loss, error):
        '''
        Initializes an IperfResult instance.

        Args:
            bandwidth (float): Measured bandwidth in Mbps.
            jitter (float): Measured jitter in milliseconds (UDP only).
            packet_loss (float): Percentage of packet loss (UDP only).
            error (str): Error message if the iperf operation failed.
        '''
        self.bandwidth = bandwidth
        self.jitter = jitter
        self.packet_loss = packet_loss
        self.error = error

def iperf(is_server, server_address=None, duration=10, transport_type="tcp"):
    '''
    Executes an iperf command to measure network performance.

    Args:
        is_server (bool): Whether to run iperf in server mode.
        server_address (str, optional): The address of the iperf server (client mode only). Defaults to None.
        duration (int, optional): The duration of the iperf test in seconds. Defaults to 10.
        transport_type (str, optional): The transport protocol to use ('tcp' or 'udp'). Defaults to "tcp".

    Returns:
        IperfResult: The parsed result of the iperf operation, including bandwidth, jitter, packet loss, and any error message.
    '''
    try:
        if is_server:
            command = ["iperf", "-s", "-i", "1"]
            if transport_type.lower() == "udp":
                command.append("-u")
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return IperfResult(None, None, None)
        else:
            if not server_address:
                return IperfResult(None, None, "Server address is required for client mode.")
            command = ["iperf", "-c", server_address, "-t", str(duration)]
            if transport_type.lower() == "udp":
                command.append("-u")

            # Attempt to run iperf client up to 4 times
            for attempt in range(4):
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    # If successful, break out of the loop
                    break
                else:
                    if attempt < 3:  # Wait 1 second before the next try if not the last attempt
                        time.sleep(1)
            else:
                # If all attempts fail
                return IperfResult(None, None, "iperf command failed after 4 attempts")

        # Extract bandwidth, jitter and packet loss (only for UDP server)
        bandwidth = None
        jitter = None
        packet_loss = None
        output = result.stdout

        if transport_type.lower() == "udp":
            # Extract jitter
            match = re.search(r"([\d.]+ ms)", output)
            if match:
                jitter = float(match.group(1).replace(" ms", ""))

            # Extract packet loss
            match = re.search(r"(\d+)%", output)
            if match:
                packet_loss = float(match.group(1))

        # Extract bandwidth for both TCP and UDP
        match = re.search(r"([\d.]+ \w+/sec)", output)
        if match:
            bandwidth = float(match.group(1).replace(" Mbits/sec", ""))

        return IperfResult(bandwidth, jitter, packet_loss, None)
    except Exception as e:
        return IperfResult(None, None, None, f"Failed to execute iperf command: {str(e)}")