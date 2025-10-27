# app.py
# --- Student Performance Dashboard (Integrated Version) ---

import streamlit as st
import pandas as pd
from src.data_processing import compute_statistics
from src.visualization import subject_average_chart, top_performers_chart, student_performance_trend

# --- 🧭 Page setup ---
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- 🎓 Header ---
st.title("🎓 Student Performance Dashboard")
st.markdown("Analyze student grades, attendance, and performance trends easily.")

# --- 📁 File upload ---
st.sidebar.header("📂 Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])

# --- ⚙️ Main logic ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    result = compute_statistics(df)

    st.subheader("📄 Data Preview")
    st.dataframe(result["df"].head())

    # --- 📊 Summary Stats ---
    st.markdown("### 📈 Key Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Average", f"{result['overall_average']}")
    col2.metric("Pass Rate", f"{result['pass_rate']}%")
    col3.metric("Total Students", f"{len(result['df'])}")

    # --- 🏅 Top Performers ---
    st.markdown("### 🥇 Top 5 Performers")
    st.dataframe(result["top_students"])

    # --- 📚 Subject Average Chart ---
    st.plotly_chart(subject_average_chart(result["df"]), use_container_width=True)

    # --- 🧑‍🎓 Top Performer Chart ---
    st.plotly_chart(top_performers_chart(result["top_students"]), use_container_width=True)

    # --- 📈 Trend Chart ---
    with st.expander("📊 Show Performance Trend by Student"):
        st.plotly_chart(student_performance_trend(result["df"]), use_container_width=True)

        # --- 💾 Export Options ---
        # --- 💾 Export & Download Options ---
    st.markdown("### 💾 Export and Download Reports")
    from src.export_utils import export_to_pdf, export_to_excel
    import base64

    # Export files
    pdf_path = export_to_pdf(result, result["top_students"])
    excel_path = export_to_excel(result["df"])

    # --- PDF Download ---
    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
        st.download_button(
            label="📄 Download Summary as PDF",
            data=pdf_bytes,
            file_name="student_summary.pdf",
            mime="application/pdf"
        )

    # --- Excel Download ---
    with open(excel_path, "rb") as excel_file:
        excel_bytes = excel_file.read()
        st.download_button(
            label="📘 Download Data as Excel",
            data=excel_bytes,
            file_name="student_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("👈 Upload a CSV file from the sidebar to start analysis.")
