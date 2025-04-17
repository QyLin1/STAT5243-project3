from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)
LOG_FILE = "received_logs.csv"

@app.route("/")
def index():
    return "<p>✅ Flask Server is Running!</p>"

@app.route("/log", methods=["POST"])
def log():
    data = request.get_json()
    print("📩 Received log:", data)

    df = pd.DataFrame([data])
    file_exists = os.path.exists(LOG_FILE)
    df.to_csv(LOG_FILE, mode='a', index=False, header=not file_exists)
    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
