package lib

// Task represents a task that is assigned to NMS_Agents.
type Task struct {
	Task_ID   string   `json:"task_id"`   // Unique id task
	Frequency int      `json:"frequency"` // Frequency (seconds)
	Devices   []Device `json:"devices"`   // List of devices included in the task
}

// Device represents a network device (router for example) and the metrics that are to be monitored.
type Device struct {
	Device_ID      string         `json:"device_id"`      // Unique id device
	Device_Metrics Device_Metrics `json:"device_metrics"` // Metrics of the device
	Link_Metrics   Link_Metrics   `json:"link_metrics"`   // Network link metrics for inter-device communication
}

// Device_Metrics holds resource information for a network device.
type Device_Metrics struct {
	CPU_Usage       bool     `json:"cpu_usage"`       // Indicates if CPU is active
	RAM_Usage       bool     `json:"ram_usage"`       // Indicates if RAM is active
	Interface_Stats []string `json:"interface_stats"` // List of network interface names to monitor
}

// Link_Metrics represents network metrics for communication between devices.
type Link_Metrics struct {
	Bandwidth            Metric_Test_Config `json:"bandwidth"`            // Configuration for bandwidth testing
	Jitter               Metric_Test_Config `json:"jitter"`               // Configuration for jitter measurement
	Packet_Loss          Metric_Test_Config `json:"packet_loss"`          // Configuration for packet loss measurement
	Latency              Metric_Test_Config `json:"latency"`              // Configuration for latency measurement
	AlertFlow_Conditions Alert_Conditions   `json:"alertflow_conditions"` // Alert conditions for each metric
}

// Metric_Test_Config represents the configuration settings for network tests.
type Metric_Test_Config struct {
	Tool           string `json:"tool"`           // Name of the tool used for the test (iperf, etc.)
	Is_Client      bool   `json:"is_client"`      // True if the device is a client in this test
	Server_Address string `json:"server_address"` // Server address for the test
	Duration       int    `json:"duration"`       // Duration of the test (seconds)
	Transport_Type string `json:"transport_type"` // Type of transport protocol
	Frequency      int    `json:"frequency"`      // Frequency of the test (seconds)
}

// Alert_Conditions defines the limit for triggering alerts based on specific metrics.
// If any metric exceeds its limit, the NMS_Agent will notify the NMS_Server.
type Alert_Conditions struct {
	CPU_Usage       int `json:"cpu_usage"`       // CPU usage limit (%)
	RAM_Usage       int `json:"ram_usage"`       // RAM usage limit (%)
	Interface_Stats int `json:"interface_stats"` // Limit for packets per second on interfaces
	Packet_Loss     int `json:"packet_loss"`     // Packet loss limit (%)
	Jitter          int `json:"jitter"`          // Jitter limit (milliseconds)
}
