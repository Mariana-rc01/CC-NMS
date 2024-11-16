import json
from lib.task import Task

def load_tasks_json(json_file):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
        print("Json File loaded successfully.")
        return [Task(task_data) for task_data in data]
    except FileNotFoundError:
        print("Error: Json file not found.")
        return []
    except json.JSONDecodeError as e:
        print("Error on the parsing.")
        return []