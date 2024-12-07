import sys
import sqlite3
import matplotlib.pyplot as plt
from collections import Counter

# Dictionary mapping metrics to their units
metrics_units = {
    "bandwidth": "Mbps",
    "jitter": "ms",
    "loss": "%",
    "latency": "ms"
}

def main():
    '''
    Main function to execute the script's logic.
    
    Provides a menu-driven interface to:
    1. View and plot metrics for specific tasks and devices.
    2. View and visualize alert occurrences for specific tasks and devices.
    
    Args:
        None (command-line arguments are used for input).
    
    Returns:
        None. Outputs plots and prints to the terminal.
    '''
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " <metrics-db-file>")
        sys.exit(1)

    database_path = sys.argv[1]

    try:
        # Connect to the database
        database_connection = sqlite3.connect(database_path)
        cursor = database_connection.cursor()

        # Main menu
        print("Select what you want to view:")
        print("1. Metrics")
        print("2. Alerts")
        choice = input("|> ")

        if choice == "1":
            # Fetch data from the packets table (Metrics)
            print("Select task:")
            cursor.execute("SELECT DISTINCT task_id FROM packets")
            tasks = cursor.fetchall()
            for task in tasks:
                print(task[0])
            
            task_id = input("|> ")

            print("Select device:")
            cursor.execute("SELECT DISTINCT device_id FROM packets WHERE task_id=?", (task_id,))
            devices = cursor.fetchall()
            for device in devices:
                print(device[0])
            
            device_id = input("|> ")

            print("Select metric:")
            cursor.execute("SELECT * FROM packets WHERE task_id=? AND device_id=?", (task_id, device_id))
            data = cursor.fetchall()

            column_names = [description[0] for description in cursor.description]
            for column in column_names:
                print(column)

            metric = input("|> ")

            cursor.execute("SELECT timestamp, " + metric + " FROM packets WHERE task_id=? AND device_id=?", (task_id, device_id))
            data = cursor.fetchall()

            if data:
                # Plot data
                x = [row[0] for row in data]
                y = [row[1] for row in data]
                plt.plot(x, y)
                plt.xlabel("Timestamp")
                plt.ylabel(f"{metric.capitalize() + ' (' + metrics_units[metric] + ')'}")
                plt.title(f"{metric.capitalize()} for {task_id} and device {device_id}")
                plt.show()

        elif choice == "2":
            # Fetch data from the alertflow table (Alerts)
            print("Select task:")
            cursor.execute("SELECT DISTINCT task_id FROM alertflow")
            tasks = cursor.fetchall()
            for task in tasks:
                print(task[0])
            
            task_id = input("|> ")

            print("Select device:")
            cursor.execute("SELECT DISTINCT device_id FROM alertflow WHERE task_id=?", (task_id,))
            devices = cursor.fetchall()
            for device in devices:
                print(device[0])
            
            device_id = input("|> ")

            print("Fetching alerts for the selected task and device...")
            cursor.execute("SELECT alert_type FROM alertflow WHERE task_id=? AND device_id=?", (task_id, device_id))
            alerts = cursor.fetchall()

            if alerts:
                # Count the occurrences of each alert type
                alert_counts = Counter(alert[0] for alert in alerts)

                # Prepare data for plotting
                alert_types = list(alert_counts.keys())
                alert_occurrences = list(alert_counts.values())

                # Plot data as a bar chart
                plt.bar(alert_types, alert_occurrences, color='pink')
                plt.xlabel("Alert Type")
                plt.ylabel("Number of Occurrences")
                plt.title(f"Alert Types for Task {task_id} and Device {device_id}")
                plt.show()
            else:
                print("No alerts found for the selected task and device.")

        else:
            print("Invalid choice. Please select 1 or 2.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the database connection
        if database_connection:
            database_connection.close()

if __name__ == "__main__":
    main()
