import json
from lib.structs import Task

def load_tasks_json(fileJson):
    """ Carrega ficheiros"""
    try:
        with open(fileJson, 'r') as file:
            data = json.load(file)
        print("Json File loaded successfully.")
        return [Task(task_data) for task_data in data]
    except FileNotFoundError:
        print("Error: Json file not found.")
        return []
    except json.JSONDecodeError as e:
        print("Error on the parsing.")
        return []

def show_tasks(tasks):
    for task in tasks: task.show()

