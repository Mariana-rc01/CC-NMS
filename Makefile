GOCMD := go
AGENT_FOLDER = applications/agent
SERVER_FOLDER = applications/server

.PHONY: build agent server clean

build: agent server

agent:
	@mkdir -p bin
	@$(GOCMD) build -o bin/agent ./$(AGENT_FOLDER)
	@echo "Agent built."

server:
	@mkdir -p bin
	@$(GOCMD) build -o bin/server ./$(SERVER_FOLDER)
	@echo "Server built."

format:
	@$(GOCMD) fmt ./...
	@echo "Files formatted."

clean:
	@rm -rf bin
	@echo "Build files cleared."