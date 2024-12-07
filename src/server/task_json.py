import json
from lib.task import Task
from lib.logging import log

def load_tasks_json(json_file):
    '''
    Loads tasks from a JSON file and converts them into Task objects.

    Args:
        json_file (str): Path to the JSON file containing task definitions.

    Returns:
        list[Task]: A list of Task objects parsed from the JSON file.
                    Returns an empty list if the file does not exist or is invalid.
    '''
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