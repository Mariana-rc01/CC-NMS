package transport

import (
	"bytes"
	"net"
	"sync"
)

// Maximum size of a UDP packet
const (
	UDPMaxPacketSize = 65535
)

// UDPPacketHandler defines a function type to handle incoming packets
type UDPPacketHandler func(packet Packet, addr *net.UDPAddr, conn *UDPConnection)

// UDPConnection manages the UDP connection, buffering, and packet handling
type UDPConnection struct {
	connection    *net.UDPConn
	readBuffer    []byte
	packetHandler UDPPacketHandler
	onClose       func()
	wg            sync.WaitGroup
}

// InitializeUDPConnection sets up a UDPConnection with the given UDPConn
func InitializeUDPConnection(conn *net.UDPConn, handler UDPPacketHandler, onClose func()) *UDPConnection {
	return &UDPConnection{
		connection:    conn,
		readBuffer:    make([]byte, UDPMaxPacketSize),
		packetHandler: handler,
		onClose:       onClose,
	}
}

// Start launches the read and write loops in separate goroutines
func (srv *UDPConnection) Start() {
	srv.wg.Add(1)
	go srv.readLoop()
}

// Stop closes the connection and waits for loops to end
func (srv *UDPConnection) Stop() {
	srv.connection.Close()
	srv.wg.Wait()
	if srv.onClose != nil {
		srv.onClose()
	}
}

// readLoop listens for incoming packets and calls the packet handler
func (srv *UDPConnection) readLoop() {
	defer srv.wg.Done()
	for {
		n, addr, err := srv.connection.ReadFromUDP(srv.readBuffer)
		if err != nil {
			return // Exit loop on read error (e.g., connection closed)
		}
		packet, err := DeserializePacket(srv.readBuffer[:n])

		if err == nil && srv.packetHandler != nil {
			srv.packetHandler(packet, addr, srv)
		}
	}
}

func (srv *UDPConnection) SendPacket(packet Packet, addr *net.UDPAddr) {
	buffer := new(bytes.Buffer)
	err := SerializePacket(buffer, packet)
	if err != nil {

		return
	}

	_, err = srv.connection.WriteToUDP(buffer.Bytes(), addr)
	if err != nil {
	}
}
