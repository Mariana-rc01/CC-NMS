from lib.logging import log
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
        log(f"{config.tool} tool is not supported for bandwidth.", "ERROR")

def calculate_jitter(config):
    if config.tool == "iperf":
        if config.transport == "tcp":
            log("jitter is only supported for UDP.", "ERROR")
            return None
        
        if config.is_server:
            return None

        iperf_result = iperf(config.is_server, config.server_address, config.duration, config.transport)
        if iperf_result.jitter is not None:
            return iperf_result.jitter
    else:
        log(f"{config.tool} tool is not supported for jitter.", "ERROR")

def calculate_packet_loss(config):
    if config.tool == "iperf":
        if config.is_server:
            return None
        
        iperf_result = iperf(config.is_server, config.server_address, config.duration, config.transport)
        if iperf_result.packet_loss is not None:
            return iperf_result.packet_loss
    else:
        log(f"{config.tool} tool is not supported for packet loss.", "ERROR")

def calculate_latency(config):
    if config.tool == "ping":
        ping_result = ping(config.destination_address, config.packet_count, config.frequency)
        if ping_result.latency is not None:
            return ping_result.latency
    elif config.tool == "iperf":
        log(f"{config.tool} tool is not supported for latency.", "ERROR")