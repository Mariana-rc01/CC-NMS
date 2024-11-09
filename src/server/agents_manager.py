import threading

class AgentManager:
    def __init__(self):
        self.agent_ids = set()
        self.lock = threading.Lock()
        self.agent_addresses = {}

    def register_agent(self, agent_id, client_address):
        with self.lock:
            if agent_id in self.agent_ids:
                return False
            else:
                self.agent_ids.add(agent_id)
                self.agent_addresses[agent_id] = client_address
                return True

    def get_agents(self):
        with self.lock:
            return list(self.agent_ids)
        
    def get_agent_by_id(self, agent_id):
        with self.lock:
            return self.agent_addresses.get(agent_id)
        