import json
from lib.task import Task
from lib.logging import log

def load_tasks_json(json_file):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
        log("Tasks json file loaded successfully.")
        return [Task(task_data) for task_data in data]
    except FileNotFoundError:
        log("Tasks json file not found.", "ERROR")
        return []
    except json.JSONDecodeError as e:
        log("Couldn't parse tasks json file.", "ERROR")
        return []