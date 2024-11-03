package main

import (
	"cc-nms/lib"
	"cc-nms/lib/transport"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"os"
)

type Agent struct {
	Id      int
	Address net.UDPAddr
}

var agents []Agent

// loadTasks reads the configuration file, parses it, and returns the tasks.
func loadTasks(filename string) ([]lib.Task, error) {
	file, err := os.Open(filename) // opens json file
	if err != nil {                //checks if there was an error opening the file
		return nil, err
	}
	defer file.Close()

	fileContent, err := io.ReadAll(file)
	if err != nil {
		return nil, err // Return an error if we can't read the file
	}

	// Create an instance of the struct task to hold the parsed data
	var tasks []lib.Task

	// Parse the JSON data into the struct task
	err = json.Unmarshal(fileContent, &tasks)
	if err != nil { //checks if there was a error decoding the task
		return nil, err
	}

	return tasks, nil
}

func main() {
	fmt.Println("Hello, from NMS Server!")

	tasks, err := loadTasks("tasks.json")
	if err != nil {
		fmt.Println("Error loading tasks:", err)
		return
	}

	fmt.Println("Tasks loaded successfully:")
	for _, task := range tasks { // _, because we don't need the index of the task
		fmt.Printf("Task ID: %s, Frequency: %d\n", task.Task_ID, task.Frequency)
		for _, device := range task.Devices {
			fmt.Printf("  Device ID: %s\n", device.Device_ID)
			fmt.Printf("  CPU Usage Monitoring: %t\n", device.Device_Metrics.CPU_Usage)
			fmt.Printf("  RAM Usage Monitoring: %t\n", device.Device_Metrics.RAM_Usage)
			fmt.Println("  Interface Stats:", device.Device_Metrics.Interface_Stats)
			fmt.Println("  Link Metrics:", device.Link_Metrics)
		}
	}

	go receiver()

	go startTCPAlertReceiver()

	select {}
}

func receiver() {
	// Resolve UDP address and listen on it
	addr, err := net.ResolveUDPAddr("udp", ":8080")
	if err != nil {
		log.Fatalf("Failed to resolve address: %v", err)
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatalf("Failed to listen on address: %v", err)
	}
	defer conn.Close()

	packetHandler := func(packet transport.Packet, addr *net.UDPAddr, server *transport.UDPConnection) {
		switch p := packet.(type) {
		case *transport.AgentRegisterPacket:
			_ = p // remover
			fmt.Printf("Received UDP packet to register a new agent from %s\n", addr)
			go handleRegisterAgent(server, addr)
		default:
			fmt.Printf("Unknown packet type from %s\n", addr)
		}
	}

	// Create and start the UDP connection
	server := transport.InitializeUDPConnection(conn, packetHandler, func() {
		fmt.Println("Server connection closed")
	})
	server.Start()

	// Keep server running indefinitely
	select {}
}

func handleRegisterAgent(server *transport.UDPConnection, address *net.UDPAddr) {
	fmt.Printf("New agent (%s) registered with ID %d\n", address, len(agents)+1)
	agents = append(agents, Agent{Id: len(agents) + 1, Address: *address})

	server.SendPacket(&transport.AgentStartPacket{ID: len(agents)}, address)
}

func startTCPAlertReceiver() {
	listener, err := net.Listen("tcp", ":8081")
	if err != nil {
		log.Fatalf("Failed to start TCP server: %v", err)
	}
	defer listener.Close()

	fmt.Println("TCP server listening on port 8081")

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		go handleTCPConnection(conn)
	}
}

func handleTCPConnection(conn net.Conn) {
	defer conn.Close()
	buffer := make([]byte, 4096)

	for {
		n, err := conn.Read(buffer)
		if err != nil {
			log.Printf("Connection closed by %s: %v", conn.RemoteAddr(), err)
			return
		}
		fmt.Printf("Received alert from %s: %s\n", conn.RemoteAddr(), string(buffer[:n]))
	}
}
