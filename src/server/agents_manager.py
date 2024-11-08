import threading

class AgentManager:
    def __init__(self):
        self.agent_ids = set()
        self.lock = threading.Lock()

    def register_agent(self, agent_id):
        with self.lock:
            if agent_id in self.agent_ids:
                return False
            else:
                self.agent_ids.add(agent_id)
                return True

    def get_agents(self):
        with self.lock:
            return list(self.agent_ids)