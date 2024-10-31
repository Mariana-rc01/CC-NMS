package main

import (
	"cc-nms/lib/transport"
	"fmt"
	"log"
	"net"
)

func main() {
	fmt.Println("Hello, from NMS Agent!")
	registerAgent()

	select {}
}

func registerAgent() {
	// Dial UDP connection to the server
	conn, err := net.ListenUDP("udp", nil)
	if err != nil {
		log.Fatalf("Failed to connect to server: %v", err)
	}
	defer conn.Close()

	packetHandler := func(packet transport.Packet, addr *net.UDPAddr, conn *transport.UDPConnection) {
		fmt.Print("Received packet from ", addr.String(), ": ")
		switch p := packet.(type) {
		case *transport.AgentStartPacket:
			fmt.Printf("Assigned ID is %d.\n", p.ID)
		default:
			fmt.Printf("Unknown packet type from %s\n", addr)
		}
	}

	server := transport.InitializeUDPConnection(conn, packetHandler, func() {
		fmt.Println("Server connection closed")
	})

	serverAddr, err := net.ResolveUDPAddr("udp", "127.0.0.1:8080")
	if err != nil {
		log.Fatalf("Failed to resolve server address: %v", err)
	}

	server.Start()

	server.SendPacket(&transport.AgentRegisterPacket{}, serverAddr)
}
