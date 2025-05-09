from shiny import App, ui, render, reactive, req, session as shiny_session

import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from bs4 import BeautifulSoup
import re
from sklearn.datasets import load_iris, load_wine, load_breast_cancer, load_diabetes
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import json
import io
import base64
import warnings 
import atexit
import os
import uuid
warnings.filterwarnings('ignore')
import atexit

LOG_SERVER_URL = "https://stat5243-project3-1.onrender.com/log"


session_log = {}
def log_button_click(action):
    global session_log
    session_log[f"{action}_clicked_count"] += 1
    if action == "download_button" and session_log["download_button_clicked_time"] is None:
        session_log["download_button_clicked_time"] = datetime.now()

def log_button_error(action):
    global session_log
    session_log[f"{action}_error_count"] += 1
log_written = False
def log_session_summary():
    global session_log, log_written
    if log_written or not session_log:
        return
    log_written = True

    session_log["session_end_time"] = datetime.now()
    session_log["total_session_time"] = (session_log["session_end_time"] - session_log["session_start_time"]).total_seconds()

    total_time = session_log["total_session_time"] or 1
    session_log["apply_fe_button_clicked_rate"] = session_log["apply_fe_button_clicked_count"] / total_time
    session_log["revert_button_clicked_rate"] = session_log["revert_button_clicked_count"] / total_time
    session_log["download_button_clicked_rate"] = session_log["download_button_clicked_count"] / total_time

    # ✅ 修正这部分
    operation_log = {}
    names = session_log.get("operation_names", [])
    errors = session_log.get("operation_errors", [])
    for i, (name, err) in enumerate(zip(names, errors), 1):
        operation_log[f"operation_name{i}"] = name
        operation_log[f"operation_is_error{i}"] = err

    log_data = {**session_log, **operation_log}

    log_df = pd.DataFrame([log_data])
    log_file = os.path.join(os.getcwd(), "session_log.csv")
    write_header = not os.path.exists(log_file)
    log_df.to_csv(log_file, mode='a', index=False, header=write_header)

    try:
        import requests
        post_data = {
            k: (v.isoformat() if isinstance(v, datetime) else v)
            for k, v in log_data.items()
        }
        requests.post(LOG_SERVER_URL, json=post_data)
        print("📤 Session log successfully sent to server!")
    except Exception as e:
        print(f"⚠️ Failed to send log to server: {e}")

import atexit



try:
    import pyreadr  
    HAS_PYREADR = True
except ImportError:
    HAS_PYREADR = False
    print("Note: pyreadr not installed. RDS files will not be supported.")

try:
    import openpyxl  
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    print("Note: openpyxl not installed. Modern Excel files will not be supported.")


# Define CSS for the modern UI
app_css = """
body {
    font-family: Arial, sans-serif;
    background-color: #f5f7fa;
    color: #333;
}

.btn-primary {
    background-color: #4a6fa5;
    color: white;
}

.checkbox-group {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 8px;
    margin-bottom: 15px;
}

.card {
    margin-bottom: 20px;
    border: 1px solid #dee2e6;
    border-radius: 5px;
}

.card-header {
    background-color: #4a6fa5;
    color: white;
    padding: 10px 15px;
    font-weight: bold;
}

.card-body {
    padding: 15px;
}

.feature-result {
    background-color: #f0f7ff;
    border-left: 4px solid #4a6fa5;
    padding: 10px;
    font-family: monospace;
}

h3.section-title {
    color: #395682;
    border-bottom: 2px solid #4a6fa5;
    padding-bottom: 8px;
    margin-bottom: 15px;
}

.sidebar {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    border: 1px solid #dee2e6;
}

.main-panel {
    padding: 15px;
}
"""

# Built-in dataset loader
def get_builtin_dataset(name):
    """Load built-in dataset"""
    try:
        if name == "iris":
            data = load_iris(as_frame=True)
            df = pd.DataFrame(data.data, columns=data.feature_names)
        elif name == "wine":
            data = load_wine(as_frame=True)
            df = pd.DataFrame(data.data, columns=data.feature_names)
        elif name == "breast_cancer":
            data = load_breast_cancer(as_frame=True)
            df = pd.DataFrame(data.data, columns=data.feature_names)
        elif name == "diabetes":
            data = load_diabetes(as_frame=True)
            df = pd.DataFrame(data.data, columns=data.feature_names)
        else:
            print(f"⚠️ Unknown dataset: {name}")
            return None

        df["target"] = data.target
        print(f"✓ Successfully loaded {name} dataset\n")
        print(f"✓ Shape: {df.shape}")
        return df

    except Exception as e:
        print(f"❌ Error loading {name} dataset: {str(e)}")
        return None

app_ui = ui.page_fluid(
    ui.tags.style(app_css),
    
    ui.tags.h1("Data Analysis", 
              style="color: #4a6fa5; text-align: center; margin: 20px 0;"),
    
    # Tab selector
    ui.tags.div(
        ui.input_radio_buttons(
            "active_tab", 
            "Select Tab:", 
            {"data_cleaning": "Data Cleaning", "feature_engineering": "Feature Engineering", "visualization": "EDA"},
            selected="data_cleaning",
            inline=True
        ),
        style="text-align: center; margin-bottom: 20px;"
    ),
    
    # Data Cleaning UI
    ui.panel_conditional(
        "input.active_tab === 'data_cleaning'",
        ui.row(
            # Sidebar
            ui.column(4,
                ui.tags.div(
                    ui.tags.h3("Data Loading and Cleaning", class_="section-title"),
                    ui.input_text("group", "Group Parameter (Optional)", value=""),
                    ui.input_file("file1", "Select Data File", 
                               accept=[".csv", ".xlsx", ".xls", ".json", ".rds"]),
                    ui.input_select("builtinDataset", "Choose Built-in Dataset",
                                  choices=["None", "iris", "wine", "breast_cancer", "diabetes"], 
                                  selected="None"),
                    ui.tags.h4("Select Variables to Keep:"),
                    ui.tags.div(
                        ui.input_checkbox_group("varSelect", "", choices=[]),
                        class_="checkbox-group"
                    ),
                    ui.tags.div(
                        ui.input_action_button("selectAll", "Select All"),
                        ui.input_action_button("deselectAll", "Deselect All"),
                        style="display: flex; gap: 10px; margin-bottom: 15px;"
                    ),
                    ui.input_select("missingDataOption", "Handle Missing Values:",
                                  choices=["None", "Convert Common Missing Values to NA", 
                                         "Listwise Deletion", "Mean Imputation", "Mode Imputation"], 
                                  selected="None"),
                    ui.tags.h4("Additional Cleaning Steps:"),
                    ui.tags.div(
                        ui.input_checkbox_group("dataProcessingOptions", "",
                                           choices=["Remove Duplicates", "Standardize Data", 
                                                  "Normalize Data", "One-Hot Encoding"]),
                        class_="checkbox-group"
                    ),
                    ui.tags.div(
                        ui.input_action_button("processData", "Clean Data", 
                                             class_="btn-primary"),
                        ui.input_action_button("revertCleaningChange", "Revert Last Change",
                                             class_="btn-warning",
                                             style="margin-left: 10px;"),
                        style="margin-bottom: 15px;"
                    ),
                    class_="sidebar"
                )
            ),
            # Main content
            ui.column(8,
                ui.tags.div(
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Data Summary"),
                        ui.tags.div(
                            ui.tags.pre(ui.output_text("dataSummary")),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Data Types and Missing Values"),
                        ui.tags.div(
                            ui.output_table("dataTypesTable"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Numerical Columns Summary"),
                        ui.tags.div(
                            ui.output_table("numericalSummary"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Sample Data Preview"),
                        ui.tags.div(
                            ui.output_table("dataTable"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    class_="main-panel"
                )
            )
        )
    ),
    
    # Feature Engineering UI
    ui.panel_conditional(
        "input.active_tab === 'feature_engineering'",
        ui.row(
            # Sidebar
            ui.column(4,
                ui.tags.div(
                    ui.tags.h3("Feature Engineering Operations", class_="section-title"),
                    ui.tags.div(
                        ui.input_select("featureColumn", "Select Column for Feature Engineering", 
                                     choices=[]),
                        ui.input_select("featureOperation", "Select Operation", 
                                     choices=["Normalize", "One-Hot", "Convert Date Format", "Box-Cox"]),
                        ui.panel_conditional(
                            "input.featureOperation === 'Normalize'",
                            ui.p("Scales the selected column to range [0,1]. Useful for features with different scales.", 
                                 style="color: #666; font-style: italic; margin: 10px 0;"),
                            ui.p("Note: Only works with numerical columns.", 
                                 style="color: red; font-style: italic;"),
                        ),
                        ui.panel_conditional(
                            "input.featureOperation === 'One-Hot'",
                            ui.p("Creates binary columns for each unique value in the selected categorical column.", 
                                 style="color: #666; font-style: italic; margin: 10px 0;"),
                            ui.p("Best used for categorical columns with limited unique values.", 
                                 style="color: red; font-style: italic;"),
                        ),
                        ui.panel_conditional(
                            "input.featureOperation === 'Convert Date Format'",
                            ui.p("Specify a reference date to calculate the number of days between your date column and this reference date.", 
                                 style="color: #666; font-style: italic; margin: 10px 0;"),
                            ui.p("Please make sure the selected column is a date column.", 
                                style="color: red; font-style: italic; margin: 10px 0;"),
                            ui.input_numeric("input_year", "Input year (YYYY)", value=2025),
                            ui.input_numeric("input_month", "Input month (MM)", value=3),
                            ui.input_numeric("input_day", "Input day (DD)", value=7),
                        ),
                        ui.panel_conditional(
                            "input.featureOperation === 'Box-Cox'",
                            ui.p("Transforms data to be more normally distributed. Useful for skewed numerical data.", 
                                 style="color: #666; font-style: italic; margin: 10px 0;"),
                            ui.p("Note: Only works with positive numerical values. Negative values will be shifted.", 
                                 style="color: red; font-style: italic;"),
                        ),
                        style="background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin-bottom: 20px;"
                    ),
                    ui.tags.hr(),
                    ui.tags.h3("Add New Features from Multiple Columns", class_="section-title"),
                    ui.tags.div(
                        ui.input_selectize("multiColumns", "Select Columns for New Feature", 
                                        choices=[], multiple=True),
                        ui.input_select("extraOperation", "Create New Feature", 
                                     choices=["None", "Average", "Interactions"]),
                        ui.panel_conditional(
                            "input.extraOperation === 'Average'",
                            ui.p("Creates a new column with the average value of selected columns. Useful for combining related features.", 
                                 style="color: #666; font-style: italic; margin: 10px 0;"),
                            ui.p("Note: Select at least 2 numerical columns. Non-numerical columns will be ignored.", 
                                 style="color: red; font-style: italic;"),
                        ),
                        ui.panel_conditional(
                            "input.extraOperation === 'Interactions'",
                            ui.p("Creates a new column by multiplying two selected columns. Useful for capturing feature relationships.", 
                                 style="color: #666; font-style: italic; margin: 10px 0;"),
                            ui.p("Note: Select exactly 2 numerical columns. Only the first two selected columns will be used.", 
                                 style="color: red; font-style: italic;"),
                        ),
                        style="background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin-bottom: 20px;"
                    ),
                    ui.input_action_button("applyFeatureEng", "Apply Feature Engineering",
                                         class_="btn-primary"),
                    ui.input_action_button("revertChange", "Revert Last Change",
                                         class_="btn-warning",
                                         style="margin-left: 10px;"),
                    ui.tags.hr(),
                    ui.download_button(
                        id="downloadData",
                        label="Download Processed Data",
                        class_="btn-primary"
                    ),
                    class_="sidebar"
                )
            ),
            # Main content
            ui.column(8,
                ui.tags.div(
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Feature Engineering Results"),
                        ui.tags.div(
                            ui.tags.pre(ui.output_text("featureStatus"), 
                                     class_="feature-result"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Updated Data Preview"),
                        ui.tags.div(
                            ui.output_table("featureDataTable"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    class_="main-panel"
                )
            )
        )
    ),
    
    # Visualization UI
    ui.panel_conditional(
        "input.active_tab === 'visualization'",
        ui.row(
            # Sidebar
            ui.column(4,
                ui.tags.div(
                    ui.tags.h3("Visualization Controls", class_="section-title"),
                    
                    # Add Data Filters Section
                    ui.tags.h4("Data Filters", style="margin-top: 20px;"),
                    ui.output_ui("viz_filter_ui"),
                    ui.tags.hr(),
                    
                    ui.input_select(
                        "plot_type", 
                        "Plot Type",
                        choices={
                            "line": "Line Chart", 
                            "bar": "Bar Chart",
                            "scatter": "Scatter Plot",
                            "histogram": "Histogram",
                            "heatmap": "Correlation Heatmap"  # Add heatmap option
                        },
                        selected="line"
                    ),
                    
                    # Show x/y selections only for non-heatmap plots
                    ui.panel_conditional(
                        "input.plot_type !== 'heatmap'",
                        ui.tags.div(
                            ui.input_select(
                                "x_var", 
                                "X-axis Variable",
                                choices=[]
                            ),
                            style="margin-bottom: 15px;"
                        ),
                        ui.tags.div(
                            ui.input_select(
                                "y_var", 
                                "Y-axis Variable",
                                choices=[]
                            ),
                            style="margin-bottom: 15px;"
                        ),
                    ),
                    
                    ui.input_action_button("update_plot", "Update Plot"),
                    ui.tags.hr(),
                    ui.tags.h3("Summary Statistics", class_="section-title"),
                    ui.input_select(
                        "summary_var", 
                        "Select Variable for Summary",
                        choices=[]
                    ),
                    class_="sidebar"
                )
            ),
            # Main content
            ui.column(8,
                ui.tags.div(
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Data Visualization"),
                        ui.tags.div(
                            ui.output_ui("main_plot"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Summary Statistics"),
                        ui.tags.div(
                            ui.output_table("summary_stats"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    ui.tags.div(
                        ui.tags.div(class_="card-header", children="Data Distribution"),
                        ui.tags.div(
                            ui.output_ui("distribution_plot"),
                            class_="card-body"
                        ),
                        class_="card"
                    ),
                    class_="main-panel"
                )
            )
        )
    )
)

def server(input, output, session):
    global session_log
    @session.on_ended
    async def handle_disconnect():
        print("🧠 Session disconnected, logging...")
        log_session_summary()
    # 初始化用户 ID
    user_id = str(uuid.uuid4())
    @session.on_ended
    async def handle_disconnect():
        print("🔌 Session disconnected, logging...")
        log_session_summary()

    @reactive.Calc
    def user_group():
        try:
            return input.group()
        except:
            return np.random.choice(["A", "B"])
        

    # 日志初始结构（group 先设为 None，稍后赋值）
    session_log = {
    "user_id": user_id,
    "group": None,
    "session_start_time": datetime.now(),
    "session_end_time": None,
    "total_session_time": None,
    "apply_fe_button_clicked_count": 0,
    "revert_button_clicked_count": 0,
    "download_button_clicked_count": 0,
    "apply_fe_button_error_count": 0,
    "revert_button_error_count": 0,
    "download_button_error_count": 0,
    "download_button_clicked_time": None,
    "operation_names": [],
    "operation_errors": [],
}
    for i in range(1, 11):
        session_log[f"operation_name{i}"] = None
        session_log[f"operation_is_error{i}"] = None
    session_log["has_error"] = False
    @reactive.effect
    def update_group_value():
        session_log["group"] = user_group()
    data = reactive.Value(None)
    processing_status = reactive.Value("")
    feature_status = reactive.Value("")
    previous_data = reactive.Value(None)
    cleaning_history = reactive.Value(None)
    
    def clean_text(text):
        """ Remove HTML content and keep only ASCII characters """
        if pd.isna(text):
            return text
        text = BeautifulSoup(text, "html.parser").get_text()
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        return text.strip()

    def read_dataset(file_path, file_ext):
        """Read dataset from various file formats"""
        try:
            if file_ext == "csv":
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        print(f"✓ Successfully read CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        raise Exception(f"Error reading CSV: {str(e)}")
                
            elif file_ext in ["xlsx", "xls"]:
                try:
                    df = pd.read_excel(file_path, engine='openpyxl' if file_ext == 'xlsx' else 'xlrd')
                    print(f"✓ Successfully read {file_ext.upper()} file")
                except Exception as e:
                    raise Exception(f"Error reading Excel file: {str(e)}")
                
            elif file_ext == "json":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame([data])
                    print("✓ Successfully read JSON file")
                except:
                    df = pd.read_json(file_path, lines=True)
                    print("✓ Successfully read JSON Lines file")
                
            elif file_ext == "rds":
                result = pyreadr.read_r(file_path)
                df = result[None] if None in result else result[list(result.keys())[0]]
                print("✓ Successfully read RDS file")
                
            else:
                raise Exception(f"Unsupported file format: {file_ext}")

            if df.empty:
                raise Exception("Loaded data is empty")
                
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.columns = df.columns.astype(str)
            print(f"✓ Loaded data shape: {df.shape}")
            return df

        except Exception as e:
            print(f"❌ Error reading file: {str(e)}")
            raise e
        @session.on_disconnect
        def on_disconnect():
            log_session_summary()

    @reactive.effect
    def update_data():
        """Read the file or load built-in dataset"""
        file_info = input.file1()
        builtin_selected = input.builtinDataset()
        
        if builtin_selected != "None":
            df = get_builtin_dataset(builtin_selected)
            if df is not None:
                update_ui_with_data(df)
                processing_status.set(f"✓ Successfully loaded {builtin_selected} dataset\n")
            return

        if file_info:
            ui.update_select("builtinDataset", selected="None")
            try:
                file_path = file_info[0]["datapath"]
                file_ext = file_info[0]["name"].split(".")[-1].lower()
                df = read_dataset(file_path, file_ext)
                update_ui_with_data(df)
                processing_status.set(f"✓ Successfully loaded {file_ext.upper()} file\n")
            except Exception as e:
                processing_status.set(f"❌ Error: {str(e)}")

    def update_ui_with_data(df):
        """Update UI elements when new data is loaded"""
        ui.update_checkbox_group("varSelect", choices=df.columns.tolist(), 
                               selected=df.columns.tolist())
        ui.update_select("featureColumn", choices=df.columns.tolist())
        ui.update_selectize("multiColumns", choices=df.columns.tolist())
        
        ui.update_select("x_var", choices=df.columns.tolist())
        ui.update_select("y_var", choices=df.columns.tolist())
        ui.update_select("summary_var", choices=df.columns.tolist())
        
        data.set(df)

    @reactive.effect
    @reactive.event(input.applyFeatureEng)
    def apply_feature_engineering():
        """Apply feature engineering operations"""
        log_button_click("apply_fe_button")
        df = data.get()
        if df is None:
            feature_status.set("❌ No data available for feature engineering")
            return

        previous_data.set(df.copy())
        df = df.copy()
        status_messages = []

        column = input.featureColumn()
        operation = input.featureOperation()

        try:
            if column and operation != "None":
                op_name = operation.lower().replace(" ", "_")
                op_error = ""

                try:
                    if operation == "Normalize":
                        df[column] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())
                        status_messages.append(f"✓ Normalized column: {column}")

                    elif operation == "One-Hot":
                        df = pd.get_dummies(df, columns=[column])
                        status_messages.append(f"✓ One-hot encoded column: {column}")

                    elif operation == "Convert Date Format":
                        df[column] = pd.to_datetime(df[column], errors="coerce")
                        df[f"{column}_year"] = df[column].dt.year
                        df[f"{column}_month"] = df[column].dt.month
                        df[f"{column}_day"] = df[column].dt.day

                        try:
                            input_date = datetime(input.input_year(),
                                                input.input_month(),
                                                input.input_day())
                            df[f"{column}_days_since_input_date"] = (input_date - df[column]).dt.days
                            status_messages.append(f"✓ Created date features for: {column}")
                        except ValueError as e:
                            op_error = f"⚠️ Invalid date input: {str(e)}"
                            status_messages.append(op_error)

                        df.drop(columns=[column], inplace=True)

                    elif operation == "Box-Cox":
                        df[column] = pd.to_numeric(df[column], errors="coerce")
                        if df[column].min() <= 0:
                            shift = abs(df[column].min()) + 1
                            df[column] += shift
                            status_messages.append(f"✓ Shifted data by {shift}")
                        df[column], _ = stats.boxcox(df[column])
                        status_messages.append(f"✓ Applied Box-Cox transformation")

                except Exception as op_err:
                    log_button_error("apply_fe_button")
                    op_error = str(op_err)
                    status_messages.append(f"❌ Error during '{operation}': {op_error}")

                # 记录 operation 名和错误信息
                session_log.setdefault("operation_names", []).append(op_name)
                session_log.setdefault("operation_errors", []).append(op_error)

            # 多列操作
            selected_columns = list(input.multiColumns())
            extra_operation = input.extraOperation()
            if len(selected_columns) >= 2 and extra_operation != "None":
                op_name = extra_operation.lower().replace(" ", "_")
                op_error = ""
                try:
                    if extra_operation == "Average":
                        df["weighted_avg"] = df[selected_columns].mean(axis=1)
                        status_messages.append(f"✓ Created weighted average of: {', '.join(selected_columns)}")

                    elif extra_operation == "Interactions":
                        col1, col2 = selected_columns[:2]
                        df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
                        status_messages.append(f"✓ Created interaction: {col1}_x_{col2}")

                except Exception as e:
                    log_button_error("apply_fe_button")
                    op_error = str(e)
                    status_messages.append(f"❌ Error during '{extra_operation}': {op_error}")

                session_log.setdefault("operation_names", []).append(op_name)
                session_log.setdefault("operation_errors", []).append(op_error)

            data.set(df)
            update_ui_with_data(df)
            feature_status.set("\n".join(status_messages))

        except Exception as e:
            log_button_error("apply_fe_button")
            session_log.setdefault("operation_names", []).append(operation.lower().replace(" ", "_"))
            session_log.setdefault("operation_errors", []).append(str(e))
            feature_status.set(f"❌ Error in feature engineering: {str(e)}")

    @reactive.effect
    @reactive.event(input.revertChange)
    def revert_last_change():
        log_button_click("revert_button")  

        try:
            prev_df = previous_data.get()
            if prev_df is None:
                feature_status.set("⚠️ No previous state available to revert to")
                return

            data.set(prev_df)
            update_ui_with_data(prev_df)
            feature_status.set("✓ Reverted to previous state")
        except Exception as e:
            log_button_error("revert_button") 
            feature_status.set(f"❌ Error during revert: {str(e)}")

    @output
    @render.download(
        filename=lambda: f"processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        media_type="text/csv"
    )
    def downloadData():
        print("📥 Download triggered")
        log_button_click("download_button")

        df = data.get()
        if df is not None:
            try:
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                print(f"✅ Type of returned object: {type(csv_bytes)}")

                # ✅ Yield the bytes instead of returning them
                yield csv_bytes
            except Exception as e:
                log_button_error("download_button")
                print("❌ Download error:", str(e))
                yield b"Error occurred while downloading data"
        else:
            yield b"No data available"




    @output
    @render.text
    def featureStatus():
        return feature_status.get()

    # @output
    # @render.table
    # def operationLogTable():
    #     names = session_log.get("operation_names", [])
    #     errors = session_log.get("operation_errors", [])
    #     if not names:
    #         return pd.DataFrame({"Message": ["No operation logs yet."]})
        
    #     rows = []
    #     for i, (name, err) in enumerate(zip(names, errors), 1):
    #         rows.append({
    #             "operation_name": f"operation_name{i}",
    #             "operation_value": name,
    #             "operation_is_error": err
    #         })
        
    #     return pd.DataFrame(rows)

    @reactive.effect
    @reactive.event(input.processData)
    def process_data():
        """Process data: keep selected variables and handle missing values dynamically"""
        df = data.get()
        if df is None:
            processing_status.set("❌ No data loaded")
            return

        cleaning_history.set(df.copy())
        
        selected_vars = input.varSelect()
        if not selected_vars:
            processing_status.set("⚠️ Error: Please select at least one variable to proceed\n")
            return

        df = df.copy()
        status_messages = []

        valid_vars = [col for col in selected_vars if col in df.columns]
        if not valid_vars:
            status_messages.append("⚠️ No valid columns selected")
            return
        else:
            df = df.loc[:, valid_vars].copy()
            status_messages.append(f"✓ Selected {len(valid_vars)} variables")

        missing_option = input.missingDataOption()
        if missing_option == "Convert Common Missing Values to NA":
            missing_values = ["", "-9", "-99", "NA", "N/A", "nan", "NaN", "null", "NULL", "None"]
            original_na_count = df.isna().sum().sum()
            df.replace(missing_values, pd.NA, inplace=True)
            
            string_cols = df.select_dtypes(include=['object']).columns
            for col in string_cols:
                df[col] = df[col].apply(lambda x: pd.NA if isinstance(x, str) and x.strip() == "" else x)
            
            new_na_count = df.isna().sum().sum()
            status_messages.append(f"✓ Converted {new_na_count - original_na_count} values to NA")
                
        elif missing_option == "Listwise Deletion":
            original_rows = len(df)
            df = df.dropna()
            rows_dropped = original_rows - len(df)
            status_messages.append(f"✓ Dropped {rows_dropped} rows with missing values")
            
        elif missing_option == "Mean Imputation":
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            imputed_count = 0
            for col in numeric_cols:
                if df[col].isna().any():
                    mean_val = df[col].mean()
                    na_count = df[col].isna().sum()
                    df[col].fillna(mean_val, inplace=True)
                    imputed_count += na_count
            if imputed_count > 0:
                status_messages.append(f"✓ Imputed {imputed_count} missing values with mean values")
                    
        elif missing_option == "Mode Imputation":
            imputed_count = 0
            for col in df.columns:
                if df[col].isna().any():
                    mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else None
                    if mode_val is not None:
                        na_count = df[col].isna().sum()
                        df[col].fillna(mode_val, inplace=True)
                        imputed_count += na_count
            if imputed_count > 0:
                status_messages.append(f"✓ Imputed {imputed_count} missing values with mode values")

        selected_processing_options = input.dataProcessingOptions()
        if "Remove Duplicates" in selected_processing_options:
            original_rows = len(df)
            df = df.drop_duplicates()
            rows_dropped = original_rows - len(df)
            if rows_dropped > 0:
                status_messages.append(f"✓ Removed {rows_dropped} duplicate rows")
            
        if "Standardize Data" in selected_processing_options:
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if not numeric_cols.empty:
                scaler = StandardScaler()
                df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
                status_messages.append(f"✓ Standardized {len(numeric_cols)} numeric columns")
                
        if "Normalize Data" in selected_processing_options:
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if not numeric_cols.empty:
                scaler = MinMaxScaler()
                df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
                status_messages.append(f"✓ Normalized {len(numeric_cols)} numeric columns")
                
        if "One-Hot Encoding" in selected_processing_options:
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if not categorical_cols.empty:
                original_cols = df.shape[1]
                df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
                new_cols = df.shape[1] - original_cols
                status_messages.append(f"✓ One-hot encoding added {new_cols} new columns")

        status_messages.append(f"\n✅ Processing complete! New shape: {df.shape}\n")
        processing_status.set("\n".join(status_messages))
        data.set(df)

    @output
    @render.text
    def dataSummary():
        df = data.get()
        status = processing_status.get()
        
        if df is None or df.empty:
            return "No data loaded"
        
        summary = f"""{'=' * 40}
                    DATASET OVERVIEW
                    {'=' * 40}

                    Dataset Shape:           {df.shape[0]} rows × {df.shape[1]} columns
                    Memory Usage:           {df.memory_usage().sum() / 1024**2:.2f} MB
                    Number of Duplicate Rows: {df.duplicated().sum()}

                    {'=' * 40}
                    COLUMN TYPES
                    {'=' * 40}

                    Numerical Columns:  {len(df.select_dtypes(include=['int64', 'float64']).columns)}
                    Categorical Columns: {len(df.select_dtypes(include=['object', 'category']).columns)}
                    DateTime Columns:    {len(df.select_dtypes(include=['datetime64']).columns)}

                    """
        columns = df.columns.tolist()
        column_list = '\n'.join(f"{i:3d}. {col}" for i, col in enumerate(columns, 1))
        
        if status:
            summary += f"\n{'=' * 40}\nPROCESSING STATUS\n{'=' * 40}\n\n{status}"
            
        return summary + column_list

    @output
    @render.table
    def dataTypesTable():
        df = data.get()
        if df is None or df.empty:
            return pd.DataFrame()

        dtype_info = []
        for column in df.columns:
            missing_count = df[column].isna().sum()
            missing_percentage = (missing_count / len(df)) * 100
            unique_count = df[column].nunique()
            
            dtype_info.append({
                "Column Name": column,
                "Data Type": str(df[column].dtype),
                "Missing Values": f"{missing_count} ({missing_percentage:.1f}%)",
                "Unique Values": unique_count
            })
        
        return pd.DataFrame(dtype_info)

    @output
    @render.table
    def numericalSummary():
        df = data.get()
        if df is None or df.empty:
            return pd.DataFrame()

        numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numerical_cols) == 0:
            return pd.DataFrame({'Message': ['No numerical columns found']})

        summary_stats = []
        for col in numerical_cols:
            stats = df[col].describe()
            summary_stats.append({
                'Column': col,
                'Mean': f"{stats['mean']:.2f}",
                'Std': f"{stats['std']:.2f}",
                'Min': f"{stats['min']:.2f}",
                'Q1': f"{stats['25%']:.2f}",
                'Median': f"{stats['50%']:.2f}",
                'Q3': f"{stats['75%']:.2f}",
                'Max': f"{stats['max']:.2f}"
            })
        
        return pd.DataFrame(summary_stats)

    @output
    @render.table
    def dataTable():
        df = data.get()
        if df is None or df.empty:
            return pd.DataFrame()
        
        preview_df = df.head(10).copy()
        for col in preview_df.select_dtypes(include=['object']).columns:
            preview_df[col] = preview_df[col].apply(
                lambda x: str(x)[:50] + '...' if len(str(x)) > 50 else str(x)
            )
        return preview_df
        
    @output
    @render.ui
    def main_plot():
        df = get_filtered_data()
        if df is None or df.empty:
            fig = go.Figure()
            fig.update_layout(title="No data to display")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        
        try:
            plot_type = input.plot_type()
            
            if plot_type == "heatmap":
                numeric_data = df.select_dtypes(include=['number'])
                if numeric_data.shape[1] < 2:
                    fig = go.Figure()
                    fig.update_layout(title="Need at least 2 numeric columns for correlation heatmap")
                    return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                
                corr = numeric_data.corr()
                fig = px.imshow(corr,
                              labels=dict(color="Correlation"),
                              x=corr.columns,
                              y=corr.columns,
                              color_continuous_scale="RdBu")
                fig.update_layout(title="Correlation Heatmap")
                
            else:
                if not input.x_var() or (plot_type != "histogram" and not input.y_var()):
                    fig = go.Figure()
                    fig.update_layout(title="Please select variables for plotting")
                    return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                    
                x_col = input.x_var()
                y_col = input.y_var() if plot_type != "histogram" else None
                
                if plot_type == "line":
                    fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                elif plot_type == "bar":
                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                elif plot_type == "scatter":
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                elif plot_type == "histogram":
                    fig = px.histogram(df, x=x_col, title=f"Distribution of {x_col}")
                
                fig.update_layout(
                    xaxis_title=x_col,
                    yaxis_title=y_col if y_col else "Count",
                    template="plotly_white"
                )
                
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        except Exception as e:
            fig = go.Figure()
            fig.update_layout(title=f"Error creating plot: {str(e)}")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            
    @output
    @render.table
    def summary_stats():
        df = data.get()
        if df is None or df.empty or not input.summary_var():
            return pd.DataFrame({'Message': ['No data available or variable selected']})
            
        try:
            var = input.summary_var()
            
            if pd.api.types.is_numeric_dtype(df[var]):
                stats_df = pd.DataFrame({
                    'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                    'Value': [
                        df[var].count(),
                        df[var].mean(),
                        df[var].std(),
                        df[var].min(),
                        df[var].quantile(0.25),
                        df[var].median(),
                        df[var].quantile(0.75),
                        df[var].max()
                    ]
                })
            else:
                value_counts = df[var].value_counts().reset_index()
                value_counts.columns = ['Value', 'Count']
                stats_df = value_counts
                
            return stats_df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
            
    @output
    @render.ui
    def distribution_plot():
        df = data.get()
        if df is None or df.empty or not input.summary_var():
            fig = go.Figure()
            fig.update_layout(title="No data to display")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            
        try:
            var = input.summary_var()
            
            if pd.api.types.is_numeric_dtype(df[var]):
                fig = px.histogram(
                    df, x=var,
                    title=f"Distribution of {var}",
                    marginal="box"
                )
            else:
                value_counts = df[var].value_counts().reset_index()
                fig = px.bar(
                    value_counts, 
                    x='index', 
                    y=var,
                    title=f"Distribution of {var}"
                )
                fig.update_xaxes(title="Value")
                fig.update_yaxes(title="Count")
                
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        except Exception as e:
            fig = go.Figure()
            fig.update_layout(title=f"Error creating plot: {str(e)}")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))

    @reactive.effect
    @reactive.event(input.deselectAll)
    def deselect_all_variables():
        df = data.get()
        if df is not None:
            ui.update_checkbox_group("varSelect", selected=[])

    @reactive.effect
    @reactive.event(input.selectAll)
    def select_all_variables():
        df = data.get()
        if df is not None:
            ui.update_checkbox_group("varSelect", selected=df.columns.tolist())
            

    @output
    @render.ui
    def viz_filter_ui():
        df = data.get()
        if df is None:
            return ui.TagList()
        
        filter_inputs = ui.TagList()
        
        for col in df.columns:
            try:
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_data = df[col].replace([np.inf, -np.inf], np.nan).dropna()
                    
                    if len(col_data) == 0:
                        continue
                    
                    min_val = float(col_data.min())
                    max_val = float(col_data.max())
                    
                    if not np.isfinite(min_val) or not np.isfinite(max_val) or min_val == max_val:
                        continue
                    
                    if max_val - min_val > 1e10:
                        continue
                        
                    filter_inputs.append(
                        ui.input_slider(f"viz_filter_{col}", f"Filter {col}:", 
                                      min=min_val, max=max_val, 
                                      value=[min_val, max_val])
                    )
                elif pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    unique_vals = df[col].dropna().unique().tolist()
                    if len(unique_vals) < 15 and len(unique_vals) > 0:
                        choices = {str(val): str(val) for val in unique_vals}
                        filter_inputs.append(
                            ui.input_checkbox_group(f"viz_filter_{col}", f"Filter {col}:", 
                                                  choices=choices))
            except Exception:
                continue
        
        return filter_inputs
    
    @reactive.Calc
    def get_filtered_data():
        df = data.get()
        if df is None:
            return None
        
        try:
            for col in df.columns:
                if hasattr(input, f"viz_filter_{col}"):
                    try:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            range_val = getattr(input, f"viz_filter_{col}")()
                            if range_val and len(range_val) == 2:
                                mask = df[col].notna() & (df[col] >= range_val[0]) & (df[col] <= range_val[1])
                                df = df[mask]
                        elif pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                            selected = getattr(input, f"viz_filter_{col}")()
                            if selected and len(selected) > 0:
                                df = df[df[col].isin(selected)]
                    except Exception:
                        continue
            
            return df
        except Exception:
            return df
    
    @output
    @render.ui
    def main_plot():
        df = get_filtered_data()
        if df is None or df.empty:
            fig = go.Figure()
            fig.update_layout(title="No data to display")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        
        try:
            plot_type = input.plot_type()
            
            if plot_type == "heatmap":
                numeric_data = df.select_dtypes(include=['number'])
                if numeric_data.shape[1] < 2:
                    fig = go.Figure()
                    fig.update_layout(title="Need at least 2 numeric columns for correlation heatmap")
                    return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                
                corr = numeric_data.corr()
                fig = px.imshow(corr,
                              labels=dict(color="Correlation"),
                              x=corr.columns,
                              y=corr.columns,
                              color_continuous_scale="RdBu")
                fig.update_layout(title="Correlation Heatmap")
                
            else:
                if not input.x_var() or (plot_type != "histogram" and not input.y_var()):
                    fig = go.Figure()
                    fig.update_layout(title="Please select variables for plotting")
                    return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
                    
                x_col = input.x_var()
                y_col = input.y_var() if plot_type != "histogram" else None
                
                if plot_type == "line":
                    fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                elif plot_type == "bar":
                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                elif plot_type == "scatter":
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                elif plot_type == "histogram":
                    fig = px.histogram(df, x=x_col, title=f"Distribution of {x_col}")
                
                fig.update_layout(
                    xaxis_title=x_col,
                    yaxis_title=y_col if y_col else "Count",
                    template="plotly_white"
                )
                
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))
        except Exception as e:
            fig = go.Figure()
            fig.update_layout(title=f"Error creating plot: {str(e)}")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))

    @output
    @render.table
    def summary_stats():
        df = get_filtered_data()
        if df is None:
            return pd.DataFrame({'Message': ['No data available']})
        
        stats = df.describe().transpose()
        return stats.reset_index().rename(columns={'index': 'Statistic'})

    @output
    @render.ui
    def distribution_plot():
        df = get_filtered_data()
        if df is None:
            return ui.HTML("<p>No data available for distribution plot</p>")
        
        fig = px.histogram(df, x=input.summary_var(), title=f"Distribution of {input.summary_var()}")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs='cdn'))

    @reactive.effect
    @reactive.event(input.revertCleaningChange)
    def revert_cleaning_change():
        prev_df = cleaning_history.get()
        if prev_df is None:
            processing_status.set("⚠️ No previous state available to revert to\n")
            return
        
        data.set(prev_df)
        update_ui_with_data(prev_df)
        processing_status.set("✓ Reverted to previous state\n")

app = App(app_ui, server)
