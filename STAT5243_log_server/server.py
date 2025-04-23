from flask import Flask, request, jsonify
import pandas as pd
import os
from datetime import datetime
import glob

app = Flask(__name__)
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

@app.route("/")
def hello():
    return " STAT5243 Log Server is running!"

@app.route("/log", methods=["POST"])
def receive_log():
    try:
        data = request.get_json()
        print(" Received log:", data)
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        now = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(LOG_DIR, f"session_log_{now}.csv")

        df = pd.DataFrame([data])
        write_header = not os.path.exists(log_file)
        df.to_csv(log_file, mode='a', index=False, header=write_header)

        return jsonify({"status": " Log saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    try:
        log_files = sorted(glob.glob(os.path.join(LOG_DIR, "session_log_*.csv")))
        if not log_files:
            return {"error": "No log files found"}, 404

        latest_file = log_files[-1]
        df = pd.read_csv(latest_file)

        last_logs = df.tail(3).to_dict(orient="records")

        return {
            "columns": df.columns.tolist(),
            "total_logs": len(df),
            "latest_time": df["session_end_time"].max() if "session_end_time" in df.columns else None,
            "last_logs": last_logs 
        }
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
