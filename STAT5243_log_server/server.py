from flask import Flask, request, jsonify
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

@app.route("/")
def hello():
    return "📊 STAT5243 Log Server is running!"

@app.route("/log", methods=["POST"])
def receive_log():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON received"}), 400

        now = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(LOG_DIR, f"session_log_{now}.csv")

        df = pd.DataFrame([data])
        write_header = not os.path.exists(log_file)

        df.to_csv(log_file, mode='a', index=False, header=write_header)
        return jsonify({"status": "✅ Log saved"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 默认5000，但Render会注入PORT变量
    app.run(host="0.0.0.0", port=port, debug=True)
