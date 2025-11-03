# src/export_utils.py
# --- Handles exporting results to Excel or PDF with charts (Chrome-free, Streamlit-ready) ---
# type: ignore

import pandas as pd
from fpdf import FPDF
import datetime
import os
import tempfile
import kaleido
import plotly.colors as pc


# --- Helper: Convert Plotly chart to image bytes (Chrome-free, persistent colors) ---
def plotly_to_image(fig, format="png"):
    """
    Converts Plotly figure to image bytes safely.
    Fixes missing colors in multi-line charts by applying color sequence manually.
    """

    try:
        # Force consistent colors for multi-line trend charts
        if any(trace.type == "scatter" and trace.mode == "lines" for trace in fig.data):
            color_seq = pc.qualitative.Plotly + pc.qualitative.Pastel1
            for i, trace in enumerate(fig.data):
                if not getattr(trace, "line", None) or not getattr(trace.line, "color", None):
                    trace.line.color = color_seq[i % len(color_seq)]

        return fig.to_image(format=format, width=1200, height=600)

    except Exception as e:
        print(f"Kaleido failed initially: {e}")

        try:
            print("💡 Attempting Chrome auto-install for Kaleido...")
            kaleido.get_chrome_sync()
            return fig.to_image(format=format, width=1200, height=600)
        except Exception as e2:
            print(f"Chrome install or export failed: {e2}")
            return None


# --- 1️⃣ Excel Export with Charts (Safe Image Handling) ---
def export_to_excel_with_charts(df, charts_dict, summary_stats, filename="student_report.xlsx"):
    """
    Exports student data and charts to Excel with professional layout:
    - Sheet 1: Full Student Data
    - Sheet 2: Key Statistics Summary
    - Next Sheets: Each chart in its own sheet
    """
    import xlsxwriter
    import plotly.colors as pc

    os.makedirs("reports", exist_ok=True)
    image_dir = os.path.join("reports", "temp_images")
    os.makedirs(image_dir, exist_ok=True)

    path = os.path.join("reports", filename)
    writer = pd.ExcelWriter(path, engine="xlsxwriter")
    workbook = writer.book

    # --- Sheet 1: Student Data ---
    df.to_excel(writer, sheet_name="Student Data", index=False)
    ws_data = writer.sheets["Student Data"]

    header_format = workbook.add_format({
        "bold": True, "font_size": 13, "bg_color": "#4CAF50",
        "font_color": "white", "align": "center"
    })
    data_format = workbook.add_format({"font_size": 11})

    for col_num, value in enumerate(df.columns.values):
        ws_data.write(0, col_num, value, header_format)

    for i, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
        ws_data.set_column(i, i, min(max_length, 30))

    ws_data.autofilter(0, 0, len(df), len(df.columns) - 1)
    ws_data.freeze_panes(1, 0)

    # --- Sheet 2: Key Statistics ---
    ws_summary = workbook.add_worksheet("Summary")
    title_format = workbook.add_format({"bold": True, "font_size": 16, "align": "center"})
    header_format_2 = workbook.add_format({
        "bold": True, "font_size": 14, "bg_color": "#2196F3",
        "font_color": "white", "align": "center"
    })

    ws_summary.merge_range("A1:D1", "Student Performance Summary Report", title_format)
    ws_summary.write("A2", f"Generated: {datetime.date.today()}", data_format)

    ws_summary.write("A4", "Key Statistics", header_format_2)
    ws_summary.write("A5", "Overall Average:", data_format)
    ws_summary.write("B5", f"{summary_stats.get('overall_average', 0):.2f}", data_format)
    ws_summary.write("A6", "Pass Rate:", data_format)
    ws_summary.write("B6", f"{summary_stats.get('pass_rate', 0):.2f}%", data_format)
    ws_summary.write("A7", "Total Students:", data_format)
    ws_summary.write("B7", len(df), data_format)

    ws_summary.set_column("A:A", 25)
    ws_summary.set_column("B:B", 20)

    # --- Sheets 3–N: Charts ---
    if charts_dict:
        color_seq = pc.qualitative.Plotly + pc.qualitative.Pastel1

        for idx, (chart_name, fig) in enumerate(charts_dict.items(), start=3):
            if fig is not None:
                # 🔧 Force white background + consistent line colors
                fig.update_layout(
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font=dict(color="black"),
                )

                for i, trace in enumerate(fig.data):
                    if hasattr(trace, "line") and not getattr(trace.line, "color", None):
                        trace.line.color = color_seq[i % len(color_seq)]

                img_bytes = plotly_to_image(fig, format="png")
                if not img_bytes:
                    continue

                img_path = os.path.join(image_dir, f"{chart_name}.png")
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                # Create new sheet per chart
                chart_title = chart_name.replace("_", " ").title()
                ws_chart = workbook.add_worksheet(chart_title[:31])  # Excel sheet name limit

                # --- Write and style the chart title dynamically ---
                title_row = 0
                title_col = 0

                # Estimate number of columns needed based on title length
                approx_columns = max(4, len(chart_title) // 10)

                # Merge cells horizontally for long titles
                merge_range = xlsxwriter.utility.xl_range(title_row, title_col, title_row, title_col + approx_columns)
                ws_chart.merge_range(merge_range, chart_title, header_format_2)

                # Adjust column widths for readability
                for i in range(approx_columns + 1):
                    ws_chart.set_column(i, i, 15)

                # Insert the image below the title
                ws_chart.insert_image("A3", img_path, {"x_scale": 0.8, "y_scale": 0.8})


    # ✅ Save file
    writer.close()

    # 🧹 Cleanup
    for f in os.listdir(image_dir):
        os.remove(os.path.join(image_dir, f))

    return path



# --- 2️⃣ PDF Report (Data Preview before Summary, 2-decimal averages) ---
def export_to_pdf_with_charts(summary, _unused, charts_dict, filename="student_summary.pdf"):
    os.makedirs("reports", exist_ok=True)
    pdf = FPDF()
    pdf.add_page()

    # --- Title ---
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 20, "Student Performance Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Generated: {datetime.date.today().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.ln(10)

    df = summary["df"]

    # --- Data Preview (FIRST) ---
    pdf.set_fill_color(33, 150, 243)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Data Preview", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.ln(3)

    preview_df = df.head(10)
    columns = preview_df.columns.tolist()

    # Header
    for col in columns:
        pdf.cell(190 / len(columns), 8, str(col)[:15], border=1, align="C")
    pdf.ln(8)

    # Rows
    for _, row in preview_df.iterrows():
        for col in columns:
            value = row[col]
            if isinstance(value, (float, int)):
                value = f"{value:.2f}"
            pdf.cell(190 / len(columns), 8, str(value)[:15], border=1, align="C")
        pdf.ln(8)

    pdf.ln(10)

    # --- Executive Summary (SECOND) ---
    pdf.set_fill_color(76, 175, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Key Statistics", ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 12)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(95, 10, "Metric", border=1, align="C")
    pdf.cell(95, 10, "Value", border=1, align="C", ln=True)
    pdf.set_font("Arial", "", 12)

    pdf.cell(95, 10, "Overall Average Score", border=1)
    pdf.cell(95, 10, f"{summary['overall_average']:.2f}", border=1, align="C", ln=True)
    pdf.cell(95, 10, "Pass Rate", border=1)
    pdf.cell(95, 10, f"{summary['pass_rate']:.2f}%", border=1, align="C", ln=True)
    pdf.cell(95, 10, "Total Students Analyzed", border=1)
    pdf.cell(95, 10, str(len(summary["df"])), border=1, align="C", ln=True)
    pdf.ln(10)

    # --- Charts ---
    if charts_dict:
        for chart_name, fig in charts_dict.items():
            if fig is not None:
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 15, chart_name.replace("_", " ").title(), ln=True, align="C")
                pdf.ln(5)

                img_bytes = plotly_to_image(fig, format="png")
                if img_bytes:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(img_bytes)
                        tmp.flush()
                        pdf.image(tmp.name, x=10, y=pdf.get_y(), w=190)
                        os.unlink(tmp.name)
                else:
                    pdf.set_font("Arial", "", 12)
                    pdf.cell(0, 10, "Chart export failed", ln=True)


    path = os.path.join("reports", filename)
    pdf.output(path)
    return path
