package transport

import (
	"bytes"
	"encoding/binary"
	"errors"
	"io"
)

// Packet types
const (
	AgentRegister = 0
	AgentStart    = 1
	Task          = 2
	Confirmation  = 3
)

type Packet interface {
	getType() int
	Serialize() ([]byte, error)
}

type AgentRegisterPacket struct{}

func (p *AgentRegisterPacket) getType() int {
	return AgentRegister
}

func (p *AgentRegisterPacket) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	// Write packet type
	if err := binary.Write(&buf, binary.LittleEndian, int32(AgentRegister)); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}

type AgentStartPacket struct {
	ID int
}

func (p *AgentStartPacket) getType() int {
	return AgentStart
}

func (p *AgentStartPacket) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	// Write packet type
	if err := binary.Write(&buf, binary.LittleEndian, int32(AgentStart)); err != nil {
		return nil, err
	}
	// Write ID
	if err := binary.Write(&buf, binary.LittleEndian, int32(p.ID)); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}

type TaskPacket struct {
	Data []byte
}

func (p *TaskPacket) getType() int {
	return Task
}

func (p *TaskPacket) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	if err := binary.Write(&buf, binary.LittleEndian, int32(Task)); err != nil {
		return nil, err
	}
	buf.Write(p.Data)
	return buf.Bytes(), nil
}

type ConfirmationPacket struct {
	Message string
}

func (p *ConfirmationPacket) getType() int {
	return Confirmation
}

func (p *ConfirmationPacket) Serialize() ([]byte, error) {
	var buf bytes.Buffer
	if err := binary.Write(&buf, binary.LittleEndian, int32(Confirmation)); err != nil {
		return nil, err
	}
	buf.WriteString(p.Message)
	return buf.Bytes(), nil
}

func SerializePacket(writer io.Writer, packet Packet) error {
	data, err := packet.Serialize()
	if err != nil {
		return err
	}
	_, err = writer.Write(data)
	return err
}

func DeserializePacket(data []byte) (Packet, error) {
	if len(data) < 4 {
		return nil, errors.New("packet too small")
	}

	// Determine the packet type
	packetType := binary.LittleEndian.Uint32(data[:4])
	switch packetType {
	case AgentRegister:
		return &AgentRegisterPacket{}, nil
	case AgentStart:
		if len(data) < 8 {
			return nil, errors.New("packet too small")
		}
		id := int(binary.LittleEndian.Uint32(data[4:8]))
		return &AgentStartPacket{ID: id}, nil
	case Task:
		return &TaskPacket{Data: data[4:]}, nil
	case Confirmation:
		return &ConfirmationPacket{Message: string(data[4:])}, nil
	default:
		return nil, errors.New("unknown packet type")
	}
}
