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

	registerAgent(os.Args[1])
}

func registerAgent(serverIP string) {
	conn, err := net.ListenUDP("udp", nil)
	if err != nil {
		log.Fatalf("Failed to connect to server: %v", err)
	}
	defer conn.Close()

	packetHandler := func(packet transport.Packet, addr *net.UDPAddr, conn *transport.UDPConnection) {
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

	serverAddr, err := net.ResolveUDPAddr("udp", serverIP+":8080")
	if err != nil {
		log.Fatalf("Failed to resolve server address: %v", err)
	}

	server.Start()

	server.SendPacket(&transport.AgentRegisterPacket{}, serverAddr)

	select {}
}
