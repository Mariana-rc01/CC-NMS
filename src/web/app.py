from flask import Flask, render_template, request
import sqlite3

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
    # Consultar métricas
    metrics_query = "SELECT * FROM packets"
    metrics = query_db(metrics_query)

    # Consultar alertas
    alerts_query = "SELECT * FROM alertflow"
    alerts = query_db(alerts_query)

    return render_template("index.html", metrics=metrics, alerts=alerts)


@app.route('/metrics')
def metrics():
    query = "SELECT * FROM packets"
    data = query_db(query)
    return render_template("metrics.html", metrics=data)

@app.route('/alerts')
def alerts():
    alert_type = request.args.get('type')
    task_id = request.args.get('task_id')
    device_id = request.args.get('device_id')

    query = "SELECT * FROM alertflow"
    params = []

    filters = []
    if alert_type:
        filters.append("alert_type = ?")
        params.append(alert_type)
    if task_id:
        filters.append("task_id = ?")
        params.append(task_id)
    if device_id:
        filters.append("device_id = ?")
        params.append(device_id)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY timestamp DESC"

    data = query_db(query, params)
    return render_template("alerts.html", alerts=data)

def run_flask(database_path):
    global DB_PATH
    DB_PATH = database_path
    app.run(host="0.0.0.0", port=5000)