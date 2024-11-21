from agent.tools import iperf, ping

class MetricsResult:
    def __init__(self):
        self.latency = None
        self.packet_loss = None
        self.jitter = None
        self.bandwidth = None

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def set_jitter(self, jitter):
        self.jitter = jitter
    
    def set_packet_loss(self, packet_loss):
        self.packet_loss = packet_loss

    def set_latency(self, latency):
        self.latency = latency

def calculate_bandwidth(config):
    if config.tool == "iperf":
        if config.is_server:
            return None

        iperf_result = iperf(config.is_server, config.server_address, config.duration, config.transport)
        if iperf_result.bandwidth is not None:
            return iperf_result.bandwidth
    else:
        print(f"{config.tool} tool is not supported for bandwidth.")

def calculate_jitter(config):
    if config.tool == "iperf":
        if config.transport == "tcp":
            print("jitter is only supported for UDP.")
            return None
        
        if config.is_server:
            return None

        iperf_result = iperf(config.is_server, config.server_address, config.duration, config.transport)
        if iperf_result.jitter is not None:
            return iperf_result.jitter
    else:
        print(f"{config.tool} tool is not supported for jitter.")

def calculate_packet_loss(config):
    if config.tool == "ping":
        ping_result = ping(config.destination_address, config.packet_count, config.frequency)
        if ping_result.packet_loss is not None:
            return ping_result.packet_loss
    elif config.tool == "iperf":
        print("iperf tool is not implemented yet.")

def calculate_latency(config):
    if config.tool == "ping":
        ping_result = ping(config.destination_address, config.packet_count, config.frequency)
        if ping_result.latency is not None:
            return ping_result.latency
    elif config.tool == "iperf":
        print("iperf tool is not implemented yet.")