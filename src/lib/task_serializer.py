from lib.task import *

class TaskSerializer:
    def serialize(task):
        task_bytes = b''
        task_id_bytes = task.id.encode('utf-8')
        task_bytes += len(task_id_bytes).to_bytes(4, byteorder='big')
        task_bytes += task_id_bytes

        task_bytes += task.frequency.to_bytes(4, byteorder='big')

        # Number of devices first
        task_bytes += len(task.devices).to_bytes(4, byteorder='big')
        for device in task.devices:
            device_id_bytes = device.device_id.encode('utf-8')
            task_bytes += len(device_id_bytes).to_bytes(4, byteorder='big')
            task_bytes += device_id_bytes

            device_metrics = device.device_metrics
            task_bytes += DeviceMetricsSerializer.serialize(device_metrics)

            link_metrics = device.link_metrics
            task_bytes += LinkMetricsSerializer.serialize(link_metrics)

        return task_bytes
    
    def deserialize(data, index):
        task_id_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4

        if task_id_len <= 0 or task_id_len > len(data) - index:
            raise ValueError("Invalid task ID length")
        
        task_id = data[index:index+task_id_len].decode('utf-8')
        index += task_id_len

        task_frequency = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        num_devices = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        devices = []
        for _ in range(num_devices):
            device_id_len = int.from_bytes(data[index:index+4], byteorder='big')
            index += 4
            device_id = data[index:index+device_id_len].decode('utf-8')
            index += device_id_len

            device_metrics, index = DeviceMetricsSerializer.deserialize(data, index)
            link_metrics, index = LinkMetricsSerializer.deserialize(data, index)
            device = Device(device_id,device_metrics,link_metrics)
            devices.append(device.__dict__)

        task = Task({
            "task_id": task_id,
            "frequency": task_frequency,
            "devices": devices
        })

        return task, index

class DeviceMetricsSerializer:
    def serialize(device_metrics):
        device_metrics_bytes = b''
        device_metrics_bytes += (1 if device_metrics.cpu_usage else 0).to_bytes(1, byteorder='big')
        device_metrics_bytes += (1 if device_metrics.ram_usage else 0).to_bytes(1, byteorder='big')

        interfaces = device_metrics.interface_stats
        device_metrics_bytes += len(interfaces).to_bytes(4, byteorder='big')
        for interface in interfaces:
            interface_len = len(interface)
            device_metrics_bytes += interface_len.to_bytes(4, byteorder='big')
            device_metrics_bytes += interface.encode('utf-8')

        return device_metrics_bytes
    
    def deserialize(data, index):
        cpu_usage = int.from_bytes(data[index:index+1], byteorder='big') == 1
        index += 1
        ram_usage = int.from_bytes(data[index:index+1], byteorder='big') == 1
        index += 1
        num_interfaces = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        interfaces = []
        for _ in range(num_interfaces):
            interface_len = int.from_bytes(data[index:index+4], byteorder='big')
            index += 4
            interface_name = data[index:index+interface_len].decode('utf-8')
            interfaces.append(interface_name)
            index += interface_len

        device_metrics = DeviceMetrics(cpu_usage,ram_usage,interfaces)

        return device_metrics, index

class LinkMetricsSerializer:
    def serialize(link_metrics):
        link_metrics_bytes = b''

        # Serialize Bandwidth
        if link_metrics.bandwidth is not None:
            link_metrics_bytes += b'\x01'
            link_metrics_bytes += BandwidthSerializer.serialize(link_metrics.bandwidth)
        else:
            link_metrics_bytes += b'\x00'

        # Serialize Jitter
        if link_metrics.jitter is not None:
            link_metrics_bytes += b'\x01'
            link_metrics_bytes += JitterSerializer.serialize(link_metrics.jitter)
        else:
            link_metrics_bytes += b'\x00'

        # Serialize Packet Loss
        if link_metrics.packet_loss is not None:
            link_metrics_bytes += b'\x01'
            link_metrics_bytes += PacketLossSerializer.serialize(link_metrics.packet_loss)
        else:
            link_metrics_bytes += b'\x00'

        # Serialize Latency
        if link_metrics.latency is not None:
            link_metrics_bytes += b'\x01'
            link_metrics_bytes += LatencySerializer.serialize(link_metrics.latency)
        else:
            link_metrics_bytes += b'\x00'

        # Serialize Alert Flow Conditions
        if link_metrics.alertflow_conditions is not None:
            link_metrics_bytes += b'\x01'
            link_metrics_bytes += AlertFlowConditionsSerializer.serialize(link_metrics.alertflow_conditions)
        else:
            link_metrics_bytes += b'\x00'

        return link_metrics_bytes

    def deserialize(data, index):
        # Deserialize Bandwidth
        has_bandwidth = data[index] == 1
        index += 1
        bandwidth = None
        if has_bandwidth:
            bandwidth, index = BandwidthSerializer.deserialize(data, index)

        # Deserialize Jitter
        has_jitter = data[index] == 1
        index += 1
        jitter = None
        if has_jitter:
            jitter, index = JitterSerializer.deserialize(data, index)

        # Deserialize Packet Loss
        has_packet_loss = data[index] == 1
        index += 1
        packet_loss = None
        if has_packet_loss:
            packet_loss, index = PacketLossSerializer.deserialize(data, index)

        # Deserialize Latency
        has_latency = data[index] == 1
        index += 1
        latency = None
        if has_latency:
            latency, index = LatencySerializer.deserialize(data, index)

        # Deserialize Alert Flow Conditions
        has_alertflow_conditions = data[index] == 1
        index += 1
        alertflow_conditions = None
        if has_alertflow_conditions:
            alertflow_conditions, index = AlertFlowConditionsSerializer.deserialize(data, index)

        link_metrics = LinkMetrics(
            bandwidth=bandwidth.__dict__ if bandwidth else None,
            jitter=jitter.__dict__ if jitter else None,
            packet_loss=packet_loss.__dict__ if packet_loss else None,
            latency=latency.__dict__ if latency else None,
            alertflow_conditions=alertflow_conditions.__dict__ if alertflow_conditions else None
        )

        return link_metrics, index


class BandwidthSerializer:
    def serialize(bandwidth):
        bandwidth_bytes = b''

        bandwidth_tool_bytes = bandwidth.tool.encode('utf-8')
        bandwidth_bytes += len(bandwidth_tool_bytes).to_bytes(4, byteorder='big')
        bandwidth_bytes += bandwidth_tool_bytes

        bandwidth_bytes += (1 if bandwidth.is_server else 0).to_bytes(1, byteorder='big')
       
        server_address_bytes = bandwidth.server_address.encode('utf-8')
        bandwidth_bytes += len(server_address_bytes).to_bytes(4, byteorder='big')
        bandwidth_bytes += server_address_bytes

        bandwidth_bytes += bandwidth.duration.to_bytes(4, byteorder='big')

        transport_bytes = bandwidth.transport.encode('utf-8')
        bandwidth_bytes += len(transport_bytes).to_bytes(4, byteorder='big')
        bandwidth_bytes += transport_bytes

        bandwidth_bytes += bandwidth.frequency.to_bytes(4, byteorder='big')

        return bandwidth_bytes
    
    def deserialize(data, index):
        tool_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        tool = data[index:index+tool_len].decode('utf-8')
        index += tool_len

        is_server = int.from_bytes(data[index:index+1], byteorder='big') == 1
        index += 1

        server_address_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        server_address = data[index:index+server_address_len].decode('utf-8')
        index += server_address_len

        duration = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4

        transport_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        transport = data[index:index+transport_len].decode('utf-8')
        index += transport_len

        frequency = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        bandwidth = BandwidthMetric(
            tool = tool,
            is_server = is_server,
            server_address = server_address,
            duration = duration,
            transport = transport,
            frequency = frequency
        )

        return bandwidth, index

class JitterSerializer:
    def serialize(jitter):
        jitter_bytes = b''

        jitter_tool_bytes = jitter.tool.encode('utf-8')
        jitter_bytes += len(jitter_tool_bytes).to_bytes(4, byteorder='big')
        jitter_bytes += jitter_tool_bytes

        jitter_bytes += (1 if jitter.is_server else 0).to_bytes(1, byteorder='big')
       
        server_address_bytes = jitter.server_address.encode('utf-8')
        jitter_bytes += len(server_address_bytes).to_bytes(4, byteorder='big')
        jitter_bytes += server_address_bytes

        jitter_bytes += jitter.duration.to_bytes(4, byteorder='big')

        transport_bytes = jitter.transport.encode('utf-8')
        jitter_bytes += len(transport_bytes).to_bytes(4, byteorder='big')
        jitter_bytes += transport_bytes

        jitter_bytes += jitter.frequency.to_bytes(4, byteorder='big')

        return jitter_bytes
    
    def deserialize(data, index):
        tool_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        tool = data[index:index+tool_len].decode('utf-8')
        index += tool_len

        is_server = int.from_bytes(data[index:index+1], byteorder='big') == 1
        index += 1

        server_address_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        server_address = data[index:index+server_address_len].decode('utf-8')
        index += server_address_len

        duration = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4

        transport_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        transport = data[index:index+transport_len].decode('utf-8')
        index += transport_len

        frequency = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        jitter = JitterMetric(
            tool = tool,
            is_server = is_server,
            server_address = server_address,
            duration = duration,
            transport = transport,
            frequency = frequency
        )

        return jitter, index

class PacketLossSerializer:
    def serialize(packet_loss):
        packet_loss_bytes = b''
        
        packet_loss_tool_bytes = packet_loss.tool.encode('utf-8')
        packet_loss_bytes += len(packet_loss_tool_bytes).to_bytes(4, byteorder='big')
        packet_loss_bytes += packet_loss_tool_bytes

        packet_loss_bytes += (1 if packet_loss.is_server else 0).to_bytes(1, byteorder='big')
       
        server_address_bytes = packet_loss.server_address.encode('utf-8')
        packet_loss_bytes += len(server_address_bytes).to_bytes(4, byteorder='big')
        packet_loss_bytes += server_address_bytes

        packet_loss_bytes += packet_loss.duration.to_bytes(4, byteorder='big')

        transport_bytes = packet_loss.transport.encode('utf-8')
        packet_loss_bytes += len(transport_bytes).to_bytes(4, byteorder='big')
        packet_loss_bytes += transport_bytes

        packet_loss_bytes += packet_loss.frequency.to_bytes(4, byteorder='big')

        return packet_loss_bytes
    
    def deserialize(data, index):
        tool_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        tool = data[index:index+tool_len].decode('utf-8')
        index += tool_len

        is_server = int.from_bytes(data[index:index+1], byteorder='big') == 1
        index += 1

        server_address_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        server_address = data[index:index+server_address_len].decode('utf-8')
        index += server_address_len

        duration = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4

        transport_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        transport = data[index:index+transport_len].decode('utf-8')
        index += transport_len

        frequency = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        packet_loss = PacketLossMetric(
            tool = tool,
            is_server = is_server,
            server_address = server_address,
            duration = duration,
            transport = transport,
            frequency = frequency
        )

        return packet_loss, index

class LatencySerializer:
    def serialize(latency):
        latency_bytes = b''

        latency_tool_bytes = latency.tool.encode('utf-8')
        latency_bytes += len(latency_tool_bytes).to_bytes(4, byteorder='big')
        latency_bytes += latency_tool_bytes

        latency_destination_address_bytes = latency.destination_address.encode('utf-8')
        latency_bytes += len(latency_destination_address_bytes).to_bytes(4, byteorder='big')
        latency_bytes += latency_destination_address_bytes

        latency_bytes += latency.packet_count.to_bytes(4, byteorder='big')
        latency_bytes += latency.frequency.to_bytes(4, byteorder='big')

        return latency_bytes
    
    def deserialize(data, index):
        tool_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        tool = data[index:index+tool_len].decode('utf-8')
        index += tool_len
        
        destination_address_len = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        destination_address = data[index:index+destination_address_len].decode('utf-8')
        index += destination_address_len
        
        packet_count = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        frequency = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        latency = LatencyMetric(
            tool = tool,
            destination_address = destination_address,
            packet_count = packet_count,
            frequency = frequency
        )

        return latency, index


class AlertFlowConditionsSerializer:
    def serialize(alertflow_conditions):
        alertflow_bytes = b''
        alertflow_bytes += alertflow_conditions.cpu_usage.to_bytes(4, byteorder='big')
        alertflow_bytes += alertflow_conditions.ram_usage.to_bytes(4, byteorder='big')
        alertflow_bytes += alertflow_conditions.interface_stats.to_bytes(4, byteorder='big')
        alertflow_bytes += alertflow_conditions.packet_loss.to_bytes(4, byteorder='big')
        alertflow_bytes += alertflow_conditions.jitter.to_bytes(4, byteorder='big')
        
        return alertflow_bytes
    
    def deserialize(data, index):
        cpu_usage = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        ram_usage = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        interface_stats = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        packet_loss = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        jitter = int.from_bytes(data[index:index+4], byteorder='big')
        index += 4
        
        alertflow_conditions = AlertFlowConditions(
            cpu_usage = cpu_usage,
            ram_usage = ram_usage,
            interface_stats = interface_stats,
            packet_loss = packet_loss,
            jitter = jitter
        )

        return alertflow_conditions, index

