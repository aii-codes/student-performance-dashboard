# src/export_utils.py
# --- Handles exporting results to Excel or PDF ---

import pandas as pd
from fpdf import FPDF
import datetime
import os

# --- 1️⃣ Export DataFrame to Excel ---
def export_to_excel(df, filename="student_report.xlsx"):
    """Export student data to an Excel file inside the reports folder."""
    os.makedirs("reports", exist_ok=True)
    path = os.path.join("reports", filename)
    df.to_excel(path, index=False)
    return path


# --- 2️⃣ Generate PDF Summary Report ---
def export_to_pdf(summary, top_students, filename="student_summary.pdf"):
    """Generate a PDF summary report with overall statistics and top performers."""
    os.makedirs("reports", exist_ok=True)
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Student Performance Summary", ln=True, align="C")
    pdf.ln(10)

    # Date
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # --- Summary stats ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Key Statistics", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 8, f"Overall Average: {summary['overall_average']}", ln=True)
    pdf.cell(200, 8, f"Pass Rate: {summary['pass_rate']}%", ln=True)
    pdf.cell(200, 8, f"Total Students: {len(summary['df'])}", ln=True)
    pdf.ln(10)

    # --- Top performers table ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Top 5 Performers", ln=True)
    pdf.set_font("Arial", "", 12)
    for _, row in top_students.iterrows():
        pdf.cell(200, 8, f"{row['Name']}: {row['Average']}", ln=True)

    # Save PDF
    path = os.path.join("reports", filename)
    pdf.output(path)
    return path
