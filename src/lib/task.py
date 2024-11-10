class Task:
    def __init__(self, taskR):
        self.task_id = taskR.get("task_id")
        self.task_frequency = taskR.get("frequency")
        self.devices = [
            Device(deviceR["device_id"], deviceR["device_metrics"], deviceR["link_metrics"])
            for deviceR in taskR.get("devices", [])
        ]

    def __str__(self):
        devices_str = "\n\t".join([str(device).replace("\n", "\n\t") for device in self.devices])
        return f"Task:\n\tID: {self.task_id}\n\tFrequency: {self.task_frequency}\n\tDevices:\n\t{devices_str}"


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
    def __init__(self, cpu_usage, ram_usage, interface_stats):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats

    def __str__(self):
        return (
            f"CPU Usage: {self.cpu_usage}\n\tRAM Usage: {self.ram_usage}\n\tInterface Stats: {self.interface_stats}"
        )


class LinkMetrics:
    def __init__(self, bandwidth, jitter, packet_loss, latency, alertflow_conditions):
        self.bandwidth = BandwidthMetric(**bandwidth)
        self.jitter = JitterMetric(**jitter)
        self.packet_loss = PacketLossMetric(**packet_loss)
        self.latency = LatencyMetric(**latency)
        self.alertflow_conditions = AlertFlowConditions(**alertflow_conditions)

    def __str__(self):
        return (
            f"Bandwidth:\n\t{self.bandwidth}\n\tJitter:\n\t{self.jitter}\n\tPacket Loss:\n\t{self.packet_loss}"
            f"\n\tLatency:\n\t{self.latency}\n\tAlert Flow Conditions:\n\t{self.alertflow_conditions}"
        )


class BandwidthMetric:
    def __init__(self, tool, is_server, server_address, duration, transport, frequency):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool}\n\tIs Server: {self.is_server}\n\tServer Address: {self.server_address}"
            f"\n\tDuration: {self.duration}\n\tTransport: {self.transport}\n\tFrequency: {self.frequency}"
        )


class JitterMetric:
    def __init__(self, tool, is_server, server_address, duration, transport, frequency):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool}\n\tIs Server: {self.is_server}\n\tServer Address: {self.server_address}"
            f"\n\tDuration: {self.duration}\n\tTransport: {self.transport}\n\tFrequency: {self.frequency}"
        )


class PacketLossMetric:
    def __init__(self, tool, is_server, server_address, duration, transport, frequency):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool}\n\tIs Server: {self.is_server}\n\tServer Address: {self.server_address}"
            f"\n\tDuration: {self.duration}\n\tTransport: {self.transport}\n\tFrequency: {self.frequency}"
        )


class LatencyMetric:
    def __init__(self, tool, destination_address, packet_count, frequency):
        self.tool = tool
        self.destination_address = destination_address
        self.packet_count = packet_count
        self.frequency = frequency

    def __str__(self):
        return (
            f"Tool: {self.tool}\n\tDestination Address: {self.destination_address}\n\tPacket Count: {self.packet_count}"
            f"\n\tFrequency: {self.frequency}"
        )


class AlertFlowConditions:
    def __init__(self, cpu_usage, ram_usage, interface_stats, packet_loss, jitter):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats
        self.packet_loss = packet_loss
        self.jitter = jitter

    def __str__(self):
        return (
            f"CPU Usage: {self.cpu_usage}\n\tRAM Usage: {self.ram_usage}\n\tInterface Stats: {self.interface_stats}"
            f"\n\tPacket Loss: {self.packet_loss}\n\tJitter: {self.jitter}"
        )
