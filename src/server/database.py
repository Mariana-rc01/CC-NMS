import sqlite3

from lib.logging import log

def setup_database(path):
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
    connection.commit()

    log("Metrics database started successfully.")
    connection.close()

def insert_metrics(path, task_id, device_id, bandwidth, jitter, loss, latency, timestamp):
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
