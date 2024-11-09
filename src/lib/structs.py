class Task:
    def __init__(self, taskR):
        self.task_id = taskR.get("task_id")
        self.task_frequency = taskR.get("frequency")
        self.devices = [Device(deviceR["device_id"], deviceR["device_metrics"], deviceR["link_metrics"]) for deviceR in taskR.get("devices", [])]

    def show(self):
        print(f"Task:\n Task_ID: {self.task_id} \n frequecy: {self.task_frequency}")
        for device in self.devices:
            device.show()

class Device:
    def __init__(self, device_id, device_metrics, link_metrics):
        self.device_id = device_id
        if isinstance(device_metrics, dict):
            self.device_metrics = DeviceMetrics(**device_metrics)  # Converte dicionário em objeto
        elif isinstance(device_metrics, DeviceMetrics):
            self.device_metrics = device_metrics  # Já é um objeto, então usa diretamente
        else:
            raise ValueError("device_metrics deve ser um dicionário ou um objeto DeviceMetrics")
        
        # Verifica se link_metrics é um dicionário ou já é um objeto LinkMetrics
        if isinstance(link_metrics, dict):
            self.link_metrics = LinkMetrics(**link_metrics)  # Converte dicionário em objeto
        elif isinstance(link_metrics, LinkMetrics):
            self.link_metrics = link_metrics  # Já é um objeto, então usa diretamente
        else:
            raise ValueError("link_metrics deve ser um dicionário ou um objeto LinkMetrics")
    
    
    def show(self):
        print(f"  Device_ID: {self.device_id}")
        print("  Device_metrics:")
        self.device_metrics.show()
        print("  Link_metrics:")
        self.link_metrics.show()

class DeviceMetrics:
    def __init__(self, cpu_usage, ram_usage, interface_stats):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats

    def show(self):
        print(f"    CPU_usage: {self.cpu_usage}")
        print(f"    RAM_usage: {self.ram_usage}")
        print(f"    Interface_stats: {', '.join(self.interface_stats)}")

class LinkMetrics:
    def __init__(self, bandwidth, jitter, packet_loss, latency, alertflow_conditions):
        self.bandwidth = BandwidthMetric(**bandwidth)
        self.jitter = JitterMetric(**jitter)
        self.packet_loss = PacketLossMetric(**packet_loss)
        self.latency = LatencyMetric(**latency)
        self.alertflow_conditions = AlertFlowConditions(**alertflow_conditions)

    def show(self):
        print("    Bandwith:")
        self.bandwidth.show()
        print("    Jitter:")
        self.jitter.show()
        print("   Packet_loss:")
        self.packet_loss.show()
        print("    Latency:")
        self.latency.show()
        print("    AlertFlow_conditions:")
        self.alertflow_conditions.show()

class BandwidthMetric:
    def __init__(self, tool, is_server, server_address, duration, transport, frequency):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def show(self):
        print(f"      Tool: {self.tool}, Is_Server: {self.is_server}, Server_Address: {self.server_address}")
        print(f"      Duration: {self.duration}, Transport: {self.transport}, Frequency: {self.frequency}")

class JitterMetric():
    def __init__(self, tool, is_server, server_address, duration, transport, frequency):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def show(self):
        print(f"      Tool: {self.tool}, Is_Server: {self.is_server}, Server_Address: {self.server_address}")
        print(f"      Duration: {self.duration}, Transport: {self.transport}, Frequency: {self.frequency}")

class PacketLossMetric():
    def __init__(self, tool, is_server, server_address, duration, transport, frequency):
        self.tool = tool
        self.is_server = is_server
        self.server_address = server_address
        self.duration = duration
        self.transport = transport
        self.frequency = frequency

    def show(self):
        print(f"      Tool: {self.tool}, Is_Server: {self.is_server}, Server_Address: {self.server_address}")
        print(f"      Duration: {self.duration}, Transport: {self.transport}, Frequency: {self.frequency}")

class LatencyMetric:
    def __init__(self, tool, destination_address, packet_count, frequency):
        self.tool = tool
        self.destination_address = destination_address
        self.packet_count = packet_count
        self.frequency = frequency

    def show(self):
        print(f"      Tool: {self.tool}, Destination_address: {self.destination_address}")
        print(f"      Packet_count: {self.packet_count}, Frequency: {self.frequency}")

class AlertFlowConditions:
    def __init__(self, cpu_usage, ram_usage, interface_stats, packet_loss, jitter):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats
        self.packet_loss = packet_loss
        self.jitter = jitter

    def show(self):
        print(f"      CPU_usage: {self.cpu_usage}, RAM_usage: {self.ram_usage}")
        print(f"      Interface_Stats: {self.interface_stats}, Packet_loss: {self.packet_loss}")
        print(f"      Jitter: {self.jitter}")
