# src/data_processing.py
# --- Handles all data cleaning and computation logic ---

import pandas as pd

# --- 1️⃣ Load and clean data ---
def clean_data(df):
    """
    Clean and prepare the uploaded DataFrame.
    """
    df = df.copy()
    df.columns = df.columns.str.strip()  # remove extra spaces in column names
    df.dropna(how="all", inplace=True)   # drop empty rows
    return df

# --- 2️⃣ Compute summary stats ---
def compute_statistics(df, passing_score=75):
    """
    Compute average, top performers, and pass rate.
    Assumes 'Name' column for student name and subjects as numeric columns.
    """
    df = clean_data(df)

    # Get only numeric columns (subjects)
    numeric_cols = df.select_dtypes(include=['number']).columns

    # Per-student average
    df["Average"] = df[numeric_cols].mean(axis=1)

    # Overall class average
    overall_average = df["Average"].mean()

    # Pass rate
    passed = df[df["Average"] >= passing_score]
    pass_rate = len(passed) / len(df) * 100

    # Top performers (top 5)
    top_students = df.nlargest(5, "Average")[["Name", "Average"]]

    return {
        "df": df,
        "overall_average": round(overall_average, 2),
        "pass_rate": round(pass_rate, 2),
        "top_students": top_students
    }
