import requests
from datetime import datetime
import uuid

log_data = {
    "user_id": str(uuid.uuid4()),
    "group": "A",
    "session_start_time": datetime.now().isoformat(),
    "session_end_time": datetime.now().isoformat(),
    "total_session_time": 123.45,
    "apply_fe_button_clicked_count": 5,
    "revert_button_clicked_count": 2,
    "download_button_clicked_count": 1,
    "apply_fe_button_error_count": 0,
    "revert_button_error_count": 1,
    "download_button_error_count": 0,
    "download_button_clicked_time": datetime.now().isoformat(),
    "apply_fe_button_clicked_rate": 0.04,
    "revert_button_clicked_rate": 0.02,
    "download_button_clicked_rate": 0.008
}

res = requests.post("https://stat5243-project3-1.onrender.com/log", json=log_data)

print("Status Code:", res.status_code)
print("Response:", res.text)
