# src/visualization.py
# --- Handles all chart generation using Plotly ---

import plotly.express as px
import pandas as pd

# --- 1️⃣ Average per subject chart ---
def subject_average_chart(df):
    numeric_cols = df.select_dtypes(include=['number']).columns
    subject_means = df[numeric_cols].mean().reset_index()
    subject_means.columns = ["Subject", "Average"]

    fig = px.bar(
        subject_means,
        x="Subject",
        y="Average",
        text="Average",
        title="📚 Average Score per Subject",
        color="Subject",
        template="plotly_white"
    )
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Average Score", xaxis_title="")
    return fig

# --- 2️⃣ Top performers chart ---
def top_performers_chart(top_students_df):
    fig = px.bar(
        top_students_df,
        x="Name",
        y="Average",
        text="Average",
        color="Name",
        title="🏆 Top 5 Performers",
        template="plotly_white"
    )
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Average Score", xaxis_title="")
    return fig

# --- 3️⃣ Individual student performance trend (optional extension) ---
def student_performance_trend(df):
    numeric_cols = df.select_dtypes(include=['number']).columns
    avg_scores = df[["Name"] + list(numeric_cols)].melt(id_vars="Name", var_name="Subject", value_name="Score")

    fig = px.line(
        avg_scores,
        x="Subject",
        y="Score",
        color="Name",
        markers=True,
        title="📈 Student Performance Trend per Subject",
        template="plotly_white"
    )
    return fig
