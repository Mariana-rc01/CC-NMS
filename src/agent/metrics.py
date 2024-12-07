from lib.logging import log
from agent.tools import iperf, ping

class MetricsResult:
    '''
    Represents the result of a metrics collection process, including bandwidth, jitter, packet loss, and latency.

    Attributes:
        latency (float): The measured latency in milliseconds.
        packet_loss (float): The measured packet loss percentage.
        jitter (float): The measured jitter in milliseconds.
        bandwidth (float): The measured bandwidth in Mbps.
    '''
    def __init__(self):
        '''
        Initializes a MetricsResult instance with all metrics set to None.
        '''
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
    '''
    Calculates the bandwidth using the specified tool in the configuration.

    Args:
        config: The configuration object containing bandwidth calculation parameters.

    Returns:
        float: The measured bandwidth in Mbps, or None if not applicable.
    '''
    if config.tool == "iperf":
        if config.is_server:
            return None

        iperf_result = iperf(config.is_server, config.server_address, config.duration, config.transport)
        if iperf_result.bandwidth is not None:
            return iperf_result.bandwidth
    else:
        log(f"{config.tool} tool is not supported for bandwidth.", "ERROR")

def calculate_jitter(config):
    '''
    Calculates the jitter using the specified tool in the configuration.

    Args:
        config: The configuration object containing jitter calculation parameters.

    Returns:
        float: The measured jitter in milliseconds, or None if not applicable.
    '''
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
    '''
    Calculates the packet loss using the specified tool in the configuration.

    Args:
        config: The configuration object containing packet loss calculation parameters.

    Returns:
        float: The measured packet loss percentage, or None if not applicable.
    '''
    if config.tool == "iperf":
        if config.is_server:
            return None
        
        iperf_result = iperf(config.is_server, config.server_address, config.duration, config.transport)
        if iperf_result.packet_loss is not None:
            return iperf_result.packet_loss
    else:
        log(f"{config.tool} tool is not supported for packet loss.", "ERROR")

def calculate_latency(config):
    '''
    Calculates the latency using the specified tool in the configuration.

    Args:
        config: The configuration object containing latency calculation parameters.

    Returns:
        float: The measured latency in milliseconds, or None if not applicable.
    '''
    if config.tool == "ping":
        ping_result = ping(config.destination_address, config.packet_count, config.frequency)
        if ping_result.latency is not None:
            return ping_result.latency
    elif config.tool == "iperf":
        log(f"{config.tool} tool is not supported for latency.", "ERROR")