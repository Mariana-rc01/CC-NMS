package transport

import (
	"bufio"
	"log"
	"net"
	"sync"
)

// TCPConnection manages TCP connection and his operations.
type TCPConnection struct {
	conn    net.Conn
	onClose func()
	wg      sync.WaitGroup
}

// InitializeTCPConnection creates a TCPConnection.
func InitializeTCPConnection(conn net.Conn, onClose func()) *TCPConnection {
	return &TCPConnection{
		conn:    conn,
		onClose: onClose,
	}
}

// Start inicialize data listening.
func (tcp *TCPConnection) Start(handler func([]byte)) {
	tcp.wg.Add(1)
	go func() {
		defer tcp.wg.Done()
		scanner := bufio.NewScanner(tcp.conn)
		for scanner.Scan() {
			handler(scanner.Bytes())
		}
		if err := scanner.Err(); err != nil {
			log.Printf("Connection error: %v", err)
		}
	}()
}

// SendData sends alerts from agent via TCP.
func (tcp *TCPConnection) SendData(data []byte) error {
	_, err := tcp.conn.Write(append(data, '\n')) // Add new line of separation
	if err != nil {
		log.Printf("Failed to send data: %v", err)
	}
	return err
}

// Stop closes the connection and waits for the exchange to finish.
func (tcp *TCPConnection) Stop() {
	tcp.conn.Close()
	tcp.wg.Wait()
	if tcp.onClose != nil {
		tcp.onClose()
	}
}
