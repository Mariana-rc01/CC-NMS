import sqlite3

from lib.logging import log

def setup_database(path):
    '''
    Initializes the database by creating the necessary tables if they do not exist.

    Creates two tables:
    - `packets`: Stores metrics data such as bandwidth, jitter, packet loss, latency, and timestamps.
    - `alertflow`: Stores alert data including task ID, device ID, alert type, details, and timestamps.

    Args:
        path (str): The file path to the SQLite database.

    Returns:
        None
    '''
    # Connect to the database (creates it if it doesn't exist)
    connection = sqlite3.connect(path)
    cursor = connection.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packets (
            task_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            bandwidth REAL,
            jitter REAL,
            loss REAL,
            latency REAL,
            timestamp DATETIME NOT NULL
        )
    ''')

    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alertflow (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')

    connection.commit()

    log("Metrics and AlertFlow database started successfully.")
    connection.close()

def insert_metrics(path, task_id, device_id, bandwidth, jitter, loss, latency, timestamp):
    '''
    Inserts a new row of metrics data into the `packets` table.

    Args:
        path (str): The file path to the SQLite database.
        task_id (str): The ID of the task associated with the metrics.
        device_id (str): The ID of the device generating the metrics.
        bandwidth (float or None): The bandwidth metric in Mbps (rounded to 2 decimal places).
        jitter (float or None): The jitter metric in ms (rounded to 3 decimal places).
        loss (float or None): The packet loss percentage.
        latency (float or None): The latency metric in ms (rounded to 3 decimal places).
        timestamp (str): The timestamp of the metrics record.

    Returns:
        None
    '''
    connection = sqlite3.connect(path)
    cursor = connection.cursor()

    if bandwidth is not None:
        bandwidth = round(bandwidth, 2)

    if jitter is not None:
        jitter = round(jitter, 3)

    if latency is not None:
        latency = round(latency, 3)

    cursor.execute('''
        INSERT INTO packets (task_id, device_id, bandwidth, jitter, loss, latency, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (task_id, device_id, bandwidth, jitter, loss, latency, timestamp))

    connection.commit()
    connection.close()

def insert_alert(path, task_id, device_id, alert_type, details, timestamp):
    '''
    Inserts a new row of alert data into the `alertflow` table.

    Args:
        path (str): The file path to the SQLite database.
        task_id (str): The ID of the task associated with the alert.
        device_id (str): The ID of the device generating the alert.
        alert_type (str): The type of alert (e.g., high jitter, high packet loss).
        details (str): Additional details about the alert.
        timestamp (str): The timestamp of the alert record.

    Returns:
        None
    '''
    connection = sqlite3.connect(path)
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO alertflow (task_id, device_id, alert_type, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (task_id, device_id, alert_type, details, timestamp))

    connection.commit()
    connection.close()
