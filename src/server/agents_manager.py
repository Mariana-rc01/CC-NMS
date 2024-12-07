import threading

class AgentManager:
    '''
    Manages the registration and retrieval of agents in a thread-safe manner.
    Keeps track of agent IDs and their associated client addresses.
    '''

    def __init__(self):
        '''
        Initializes the AgentManager with empty sets for agent IDs and a dictionary
        for agent addresses. A threading lock ensures thread-safe operations.
        '''
        self.agent_ids = set()
        self.lock = threading.Lock()
        self.agent_addresses = {}

    def register_agent(self, agent_id, client_address):
        '''
        Registers a new agent with the specified ID and client address.

        Ensures that the registration process is thread-safe and checks if
        the agent is already registered.

        Args:
            agent_id (str): The unique identifier for the agent.
            client_address (tuple): The address of the client (IP and port).

        Returns:
            bool: True if the agent was successfully registered, False if the agent
            is already registered.
        '''
        with self.lock:
            if agent_id in self.agent_ids:
                return False
            else:
                self.agent_ids.add(agent_id)
                self.agent_addresses[agent_id] = client_address
                return True

    def get_agents(self):
        '''
        Retrieves a list of all registered agent IDs.

        Ensures thread-safe access to the agent IDs.

        Returns:
            list: A list of all registered agent IDs.
        '''
        with self.lock:
            return list(self.agent_ids)
        
    def get_agent_by_id(self, agent_id):
        '''
        Retrieves the client address associated with a given agent ID.

        Ensures thread-safe access to the agent addresses.

        Args:
            agent_id (str): The unique identifier for the agent.

        Returns:
            tuple or None: The client address (IP and port) if the agent is found,
            or None if the agent ID does not exist.
        '''
        with self.lock:
            return self.agent_addresses.get(agent_id)
        