package main

import (
	"cc-nms/lib/transport"
	"fmt"
	"log"
	"net"
	"os"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Printf("Usage: %s <server IP>\n", os.Args[0])
		return
	}

	serverIP := os.Args[1]

	go registerAgent(serverIP)

	startTCPAlertFlow(serverIP)
}

func registerAgent(serverIP string) {
	conn, err := net.ListenUDP("udp", nil)
	if err != nil {
		log.Fatalf("Failed to connect to server via UDP: %v", err)
	}
	defer conn.Close()

	packetHandler := func(packet transport.Packet, addr *net.UDPAddr, conn *transport.UDPConnection) {
		switch p := packet.(type) {
		case *transport.AgentStartPacket:
			fmt.Printf("Assigned ID is %d.\n", p.ID)
		case *transport.TaskPacket:
			fmt.Printf("Received task: %s\n", string(p.Data))

			confirmationPacket := &transport.ConfirmationPacket{Message: "Task received"}
			conn.SendPacket(confirmationPacket, addr)
		default:
			fmt.Printf("Unknown packet type from %s\n", addr)
		}
	}

	server := transport.InitializeUDPConnection(conn, packetHandler, func() {
		fmt.Println("Server connection closed")
	})

	serverAddr, err := net.ResolveUDPAddr("udp", serverIP+":8080")
	if err != nil {
		log.Fatalf("Failed to resolve server address: %v", err)
	}

	server.Start()

	server.SendPacket(&transport.AgentRegisterPacket{}, serverAddr)

	select {}
}

func startTCPAlertFlow(serverIP string) {
	conn, err := net.Dial("tcp", serverIP+":8081")
	if err != nil {
		log.Fatalf("Failed to connect to server via TCP: %v", err)
	}
	defer conn.Close()

	tcpConn := transport.InitializeTCPConnection(conn, func() {
		fmt.Println("TCP connection closed")
	})

	// isto aqui é apenas para ver que o TCP funciona
	alertMessage := []byte("Critical alert: Metric threshold exceeded")
	err = tcpConn.SendData(alertMessage)
	if err != nil {
		log.Printf("Failed to send alert: %v", err)
	} else {
		fmt.Println("Alert sent to NMS_Server")
	}

	select {}
}
