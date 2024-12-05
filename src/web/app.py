from flask import Flask, render_template, request, jsonify
import sqlite3
import sys
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter

metrics_units = {
    "bandwidth": "Mbps",
    "jitter": "ms",
    "loss": "%",
    "latency": "ms"
}

app = Flask(__name__)
DB_PATH = None

def query_db(query, args=(), one=False):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(query, args)
    result = cursor.fetchall()
    connection.close()
    return (result[0] if result else None) if one else result

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/metrics')
def metrics():
    data = query_db("SELECT * FROM packets ORDER BY timestamp DESC")
    return render_template("metrics.html", metrics=data)

@app.route('/alerts')
def alerts():
    data = query_db("SELECT * FROM alertflow ORDER BY timestamp DESC")
    return render_template("alerts.html", alerts=data)

@app.route('/metrics_graphics')
def metrics_graphics():
    tasks = query_db("SELECT DISTINCT task_id FROM packets")
    return render_template("metrics_graphics.html", tasks=tasks)

@app.route('/alerts_graphics')
def alerts_graphics():
    tasks = query_db("SELECT DISTINCT task_id FROM alertflow")
    return render_template("alerts_graphics.html", tasks=tasks)

@app.route('/generate_metrics_graph', methods=['POST'])
def generate_metrics_graph():
    task_id = request.form['task_id']
    device_id = request.form['device_id']
    metric = request.form['metric']

    query = f"SELECT timestamp, {metric} FROM packets WHERE task_id = ? AND device_id = ? ORDER BY timestamp"
    data = query_db(query, (task_id, device_id))

    if not data:
        return jsonify({"error": "No data found for the selected options."})

    timestamps = [row['timestamp'] for row in data]
    values = [row[metric] for row in data]

    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, values, marker='o')
    plt.xlabel("Timestamp")
    plt.ylabel(f"{metric.capitalize()} ({metrics_units.get(metric, '')})")
    plt.title(f"{metric.capitalize()} for Task {task_id} and Device {device_id}")

    # Convert plot to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.read()).decode('utf-8')
    plt.close()

    return jsonify({"image": img_base64})

@app.route('/generate_alerts_graph', methods=['POST'])
def generate_alerts_graph():
    task_id = request.form['task_id']
    device_id = request.form['device_id']

    query = "SELECT alert_type FROM alertflow WHERE task_id = ? AND device_id = ?"
    data = query_db(query, (task_id, device_id))

    if not data:
        return jsonify({"error": "No alerts found for the selected options."})

    alert_counts = Counter(row['alert_type'] for row in data)

    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.bar(alert_counts.keys(), alert_counts.values(), color='pink')
    plt.xlabel("Alert Type")
    plt.ylabel("Occurrences")
    plt.title(f"Alert Types for Task {task_id} and Device {device_id}")

    # Convert plot to base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.read()).decode('utf-8')
    plt.close()

    return jsonify({"image": img_base64})

def run_flask():
    global DB_PATH

    if len(sys.argv) < 2:
        print("Usage: python app.py <path_to_database>")
        sys.exit(1)

    DB_PATH = sys.argv[1]
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_flask()
