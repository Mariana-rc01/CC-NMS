class Task:
    def __init__(self, taskR):
        self.id = taskR.get("task_id")
        self.frequency = taskR.get("frequency")
        self.devices = [
            Device(deviceR["device_id"], deviceR["device_metrics"], deviceR["link_metrics"])
            for deviceR in taskR.get("devices", [])
        ]

    def __str__(self):
        devices_str = "\n\t".join([str(device).replace("\n", "\n\t") for device in self.devices])
        return f"Task:\n\tID: {self.id}\n\tFrequency: {self.frequency}\n\tDevices:\n\t{devices_str}"


class Device:
    def __init__(self, device_id, device_metrics, link_metrics):
        self.device_id = device_id
        if isinstance(device_metrics, dict):
            self.device_metrics = DeviceMetrics(**device_metrics)
        elif isinstance(device_metrics, DeviceMetrics):
            self.device_metrics = device_metrics
        else:
            raise ValueError("device_metrics must be a dictionary or a DeviceMetrics object")

        if isinstance(link_metrics, dict):
            self.link_metrics = LinkMetrics(**link_metrics)
        elif isinstance(link_metrics, LinkMetrics):
            self.link_metrics = link_metrics
        else:
            raise ValueError("link_metrics must be a dictionary or a LinkMetrics object")

    def __str__(self):
        return (
            f"Device:\n\tID: {self.device_id}\n\tDevice Metrics:\n\t{self.device_metrics}"
            f"\n\tLink Metrics:\n\t{self.link_metrics}"
        )


class DeviceMetrics:
    def __init__(self, cpu_usage=None, ram_usage=None, interface_stats=None):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats

    def __str__(self):
        return (
            f"CPU Usage: {self.cpu_usage or 'Not Provided'}\n\tRAM Usage: {self.ram_usage or 'Not Provided'}"
            f"\n\tInterface Stats: {self.interface_stats or 'Not Provided'}"
        )


class LinkMetrics:
    def __init__(self, bandwidth=None, jitter=None, packet_loss=None, latency=None, alertflow_conditions=None):
        self.bandwidth = BandwidthMetric(**bandwidth) if bandwidth else None
        self.jitter = JitterMetric(**jitter) if jitter else None
        self.packet_loss = PacketLossMetric(**packet_loss) if packet_loss else None
        self.latency = LatencyMetric(**latency) if latency else None
        self.alertflow_conditions = (
            AlertFlowConditions(**alertflow_conditions) if alertflow_conditions else None
        )

    def __str__(self):
        return (
            f"Bandwidth:\n\t{self.bandwidth or 'Not Provided'}\n\tJitter:\n\t{self.jitter or 'Not Provided'}"
            f"\n\tPacket Loss:\n\t{self.packet_loss or 'Not Provided'}\n\tLatency:\n\t{self.latency or 'Not Provided'}"
            f"\n\tAlert Flow Conditions:\n\t{self.alertflow_conditions or 'Not Provided'}"
        )


class BandwidthMetric:
    def __init__(self, tool=None, is_server=None, server_address=None, duration=None, transport=None, frequency=None):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool or 'Not Provided'}\n\tIs Server: {self.is_server or 'Not Provided'}"
            f"\n\tServer Address: {self.server_address or 'Not Provided'}"
            f"\n\tDuration: {self.duration or 'Not Provided'}"
            f"\n\tTransport: {self.transport or 'Not Provided'}"
            f"\n\tFrequency: {self.frequency or 'Not Provided'}"
        )


class JitterMetric:
    def __init__(self, tool=None, is_server=None, server_address=None, duration=None, transport=None, frequency=None):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool or 'Not Provided'}\n\tIs Server: {self.is_server or 'Not Provided'}"
            f"\n\tServer Address: {self.server_address or 'Not Provided'}"
            f"\n\tDuration: {self.duration or 'Not Provided'}"
            f"\n\tTransport: {self.transport or 'Not Provided'}"
            f"\n\tFrequency: {self.frequency or 'Not Provided'}"
        )


class PacketLossMetric:
    def __init__(self, tool=None, is_server=None, server_address=None, duration=None, transport=None, frequency=None):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool or 'Not Provided'}\n\tIs Server: {self.is_server or 'Not Provided'}"
            f"\n\tServer Address: {self.server_address or 'Not Provided'}"
            f"\n\tDuration: {self.duration or 'Not Provided'}"
            f"\n\tTransport: {self.transport or 'Not Provided'}"
            f"\n\tFrequency: {self.frequency or 'Not Provided'}"
        )


class LatencyMetric:
    def __init__(self, tool=None, destination_address=None, packet_count=None, frequency=None):
        self.tool = tool
        self.destination_address = destination_address
        self.packet_count = packet_count
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool or 'Not Provided'}\n\tDestination Address: {self.destination_address or 'Not Provided'}"
            f"\n\tPacket Count: {self.packet_count or 'Not Provided'}\n\tFrequency: {self.frequency or 'Not Provided'}"
        )


class AlertFlowConditions:
    def __init__(self, cpu_usage=None, ram_usage=None, interface_stats=None, packet_loss=None, jitter=None):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats
        self.packet_loss = packet_loss
        self.jitter = jitter

    def __str__(self):
        return (
            f"CPU Usage: {self.cpu_usage or 'Not Provided'}\n\tRAM Usage: {self.ram_usage or 'Not Provided'}"
            f"\n\tInterface Stats: {self.interface_stats or 'Not Provided'}"
            f"\n\tPacket Loss: {self.packet_loss or 'Not Provided'}\n\tJitter: {self.jitter or 'Not Provided'}"
        )
