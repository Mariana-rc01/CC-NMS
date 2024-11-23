import sys
import sqlite3
from tabulate import tabulate

def main():
    if len(sys.argv) != 2:
        print("Usage: python " + sys.argv[0] + " <metrics-db-file>")
        sys.exit(1)

    database_path = sys.argv[1]

    try:
        # Connect to the database
        database_connection = sqlite3.connect(database_path)
        cursor = database_connection.cursor()

        # Fetch data from the packets table
        cursor.execute("SELECT * FROM packets")
        data = cursor.fetchall()

        # Fetch column names for pretty printing
        column_names = [description[0] for description in cursor.description]

        if data:
            # Pretty print the data in a tabular format
            print(tabulate(data, headers=column_names, tablefmt="grid"))
        else:
            print("No data found in the 'packets' table.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the database connection
        if database_connection:
            database_connection.close()

if __name__ == "__main__":
    main()
