import pandas as pd
import io
import numpy as np
from datetime import datetime
from scipy import stats
from shiny import App, ui, render, reactive

# DEFINE UI
app_ui = ui.page_fluid(
    ui.input_file("file", "Upload Dataset", multiple=False, accept=[".csv"]),
    ui.input_select("column", "Select Column for Feature Engineering", choices=[]),
    ui.output_table("preview_column"),
    ui.input_select("operation", "Select Feature Engineering Operation", choices=[
        "Normalize", "One-Hot", "Date", "Box-Cox"
    ]),
    ui.input_action_button("apply_transform", "Apply Feature Engineering"),
    ui.input_numeric("input_year", "Input year (YYYY)", value=2025),
    ui.input_numeric("input_month", "Input month (MM)", value=3),
    ui.input_numeric("input_day", "Input day (DD)", value=7),
    ui.input_selectize("multi_columns", "Select Multiple Columns for New Feature Creation", choices=[], multiple=True),
    ui.input_select("extra_operation", "Select New Feature Operation", choices=[
        "None", "Average", "Interactions"
    ]),
    ui.input_action_button("apply_extra_transform", "Create New Feature"),
    ui.output_table("table")
)

def server(input, output, session):
    data = reactive.Value(None)
    
    @reactive.effect
    def update_data():
        """Automatically update data and column choices when file is uploaded"""
        file = input.file()
        if not file:
            return
        
        try:
            file_path = file[0]["datapath"]
            df = pd.read_csv(file_path)
            data.set(df)
            
            # Update column choices automatically
            ui.update_select("column", choices=df.columns.tolist())
            ui.update_selectize("multi_columns", choices=df.columns.tolist())
            
            print("✓ Dataset loaded successfully")
            print(f"✓ Shape: {df.shape}")
            print(f"✓ Columns: {', '.join(df.columns)}")
        except Exception as e:
            print(f"❌ Error loading file: {str(e)}")

    # DISPLAY DATA
    @output
    @render.table
    def preview_column():
        df = data.get()
        if df is None:
            return pd.DataFrame({'Message': ['Please upload a dataset']})
        column = input.column()
        if not column or column not in df.columns:
            return pd.DataFrame({'Message': ['Please select a column']})
        return df[[column]].head(10)

    @reactive.Calc
    @reactive.event(input.apply_transform)
    def transformed_data():
        df = data.get()
        if df is None:
            print("❌ No dataset loaded")
            return None

        column = input.column()
        operation = input.operation()

        if not column or column not in df.columns:
            print("⚠️ Please select a valid column")
            return df

        try:
            df = df.copy()  # Create a copy to avoid modifying original data
            
            if operation == "Normalize":
                df[column] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())
                print(f"✓ Normalized column: {column}")

            elif operation == "One-Hot":
                df = pd.get_dummies(df, columns=[column])
                print(f"✓ One-hot encoded column: {column}")

            elif operation == "Date":
                df[column] = pd.to_datetime(df[column], errors="coerce")
                df[f"{column}_year"] = df[column].dt.year
                df[f"{column}_month"] = df[column].dt.month
                df[f"{column}_day"] = df[column].dt.day

                input_year = input.input_year()
                input_month = input.input_month()
                input_day = input.input_day()

                try:
                    input_date = datetime(input_year, input_month, input_day)
                    df[f"{column}_days_since_input_date"] = (input_date - df[column]).dt.days
                    print(f"✓ Created date features for column: {column}")
                except ValueError as e:
                    print(f"⚠️ Invalid date input: {str(e)}")
                    input_date = datetime.today()
                
                df.drop(columns=[column], inplace=True)

            elif operation == "Box-Cox":
                df[column] = pd.to_numeric(df[column], errors="coerce")
                if df[column].min() <= 0:
                    shift = abs(df[column].min()) + 1
                    df[column] += shift
                    print(f"✓ Shifted data by {shift} to make all values positive")

                df[column], _ = stats.boxcox(df[column])
                print(f"✓ Applied Box-Cox transformation to column: {column}")

            return df
            
        except Exception as e:
            print(f"❌ Error during transformation: {str(e)}")
            return df

    @reactive.Calc
    @reactive.event(input.apply_extra_transform)
    def extra_transformed_data():
        df = transformed_data()
        if df is None:
            print("❌ No dataset available for new feature creation")
            return None
            
        selected_columns = list(input.multi_columns())
        extra_operation = input.extra_operation()

        if len(selected_columns) < 2:
            print("⚠️ Please select at least two columns for new feature creation")
            return df

        try:
            df = df.copy()  # Create a copy to avoid modifying original data
            
            if extra_operation == "Average":
                df["weighted_avg"] = df[selected_columns].mean(axis=1)
                print(f"✓ Created weighted average of columns: {', '.join(selected_columns)}")

            elif extra_operation == "Interactions":
                col1, col2 = selected_columns[:2]
                df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
                print(f"✓ Created interaction feature: {col1}_x_{col2}")

            return df
            
        except Exception as e:
            print(f"❌ Error creating new feature: {str(e)}")
            return df

    @output
    @render.table
    def table():
        df = extra_transformed_data()
        if df is None:
            return pd.DataFrame({'Message': ['No data available']})
        return df.head()

# Shiny App
app = App(app_ui, server)





