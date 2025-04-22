# STAT 5243 Project 3 A/B Testing

Jinze Shi, Qiaoyang Lin, Nan Xiao, Yemin Wang, Sally Liu

This is an interactive data cleaning and feature engineering platform built with Python Shiny, primarily designed for conducting A/B testing experiments. The core objective of the experiment is to test the impact of prompt text color (e.g., red vs. black) on user behavior.

**🔬 A/B Testing Objective:**  
We use the prompt color of the Note (e.g., red vs. black) as the experimental variable, randomly assigning users to two groups:

- Group A: Displays red prompt text (default style)
- Group B: Displays black prompt text (de-emphasized)

**🎯 Measured Metrics:**

Each user session logs the following behavioral metrics via the logging system:

- `apply_fe_button_clicked_count`: Number of clicks to apply feature engineering
- `apply_fe_button_error_count`: Number of errors during clicks
- `revert_button_clicked_count`: Number of clicks to revert changes
- `download_button_clicked_count`: Number of clicks to download data
- `download_button_clicked_time`: Time of the first download button click
- `session_start_time`, `session_end_time`: The beggin and end time of the user session
- ...

Data is written to a local CSV file (`session_log.csv`) and can be sent to a log server via HTTP POST.

**🧩 Functional Modules:**

- Data file upload and built-in data loading (supports CSV, Excel, JSON, RDS, etc.)
- Variable selection and data cleaning
- Missing value handling (convert to NA, mean/mode imputation, listwise deletion)
- Feature engineering operations (Normalization, One-hot encoding, Date Format conversion, Box-Cox transformation)
- Visualization (line charts, bar charts, scatter plots, histograms, correlation heatmaps)
- Logging system automatically records user behavior data for experiment evaluation



---

### 🖥️ Log Server

A lightweight log server built with Flask and deployed on Render, designed to receive and record user behavior data (e.g., click counts, session duration) from the frontend Shiny Web App, supporting A/B testing experiment analysis.


#### 🌍 Project Deployment

- Service Homepage: 
  [`https://stat5243-project3-1.onrender.com`](https://stat5243-project3-1.onrender.com)

- Log Upload Endpoint:  
  `POST https://stat5243-project3-1.onrender.com/log`

- Status Check Endpoint:
  `GET  https://stat5243-project3-1.onrender.com/status`


#### 🔧 Render Configuration Details
 
| Configuration Item    | Value                                   |
|-----------------------|-----------------------------------------|
| Type                  | Web Service                             |
| Build Command         | `pip install -r requirements.txt`       |
| Start Command         | `python server.py`                      |
| Port                  | Automatically bound to Flask's port 5000| 


#### 📁 Data Storage Format

Logs are automatically saved in the `logs/` folder with daily date-based naming:

```bash
logs/session_log_20250418.csv
```

**Example fields**:

| user_id | group | session_start_time | ... | download_button_clicked_count |
|---------|-------|--------------------|-----|-------------------------------|
| abcd123 | B     | 2024-04-18T10:00   | ... | 2                             |


---

### 💡 Statistical Analysis

The cleaned and feature engineered dataset can be found in [ab_test_log_step3_cleaned.csv](ab_test_log_step3_cleaned.csv)

To analyze the logged data, run 
```bash
python ab_test_analysis.py
```

The analysis results and plots will be saved to `AB_Test_results/` folder. 


---


### 📖 Results and Insights

From a statistical perspective, we observe significant results in most core interaction metrics: clicked count, clicked rate, error count, error rate, session time, and overall engagement.

The gray interface outperforms the red interface in both clicked rate and clicked count, indicating that users were more actively engaged with the interface when the prompts were presented in gray. This suggests that a less visually dominant design may encourage users to explore or interact more freely.

On the other hand, the red interface demonstrates superior performance in reducing errors—both in terms of error count and error rate. Users were significantly less likely to make mistakes under the red design, which could be attributed to the caution-inducing nature of red elements.

Session time did not differ significantly between the two groups, indicating that the variation in user behavior was not due to time spent but rather the quality and intent of interaction.

From a design and user experience perspective, this experiment reveals a trade-off between engagement and accuracy. The gray interface facilitates exploration, which can be ideal in discovery phases, low-risk settings, or when gathering behavioral data. The red interface enhances clarity and controllability, making it preferable in tasks that require accuracy, such as payment, financial actions, or data validation. Future iterations could explore a hybrid approach that can adjust the color scheme based on context, user roles, or task criticality to achieve a better balance between interaction and precision. 
