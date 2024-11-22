import subprocess
import re
import time
from logging import log

class PingResult:
    def __init__(self, packet_loss, latency, error):
        self.packet_loss = packet_loss
        self.latency = latency
        self.error = error

def ping(destination_address, packet_count, frequency):
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
    def __init__(self, bandwidth, jitter, packet_loss, error):
        self.bandwidth = bandwidth
        self.jitter = jitter
        self.packet_loss = packet_loss
        self.error = error

def iperf(is_server, server_address=None, duration=10, transport_type="tcp"):
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
            bandwidth = match.group(1)

        return IperfResult(bandwidth, jitter, packet_loss, None)
    except Exception as e:
        return IperfResult(None, None, None, f"Failed to execute iperf command: {str(e)}")