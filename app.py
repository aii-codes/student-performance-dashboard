import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processing import compute_statistics, clean_data
from src.visualization import subject_average_chart, top_performers_chart, student_performance_trend
from src.export_utils import export_to_pdf_with_charts, export_to_excel_with_charts

# Custom color generation function
def generate_colors(n):
    """
    Generate n distinct colors for bar charts
    Uses HSL color space for maximum distinction
    """
    import colorsys
    colors = []
    for i in range(n):
        hue = i / n  # Distribute hues evenly across color wheel
        saturation = 0.7 + (i % 3) * 0.1  # Vary saturation slightly
        lightness = 0.5 + (i % 2) * 0.1   # Vary lightness slightly
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        colors.append(f'rgb({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)})')
    return colors

# --- 🧭 Page setup ---
st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("🎓 Student Performance Dashboard")
st.markdown("Analyze student grades, attendance, and performance trends easily.")

# --- 📂 File upload ---
st.sidebar.header("📂 Upload CSV File")

# Track file changes to reset passing grade
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file)

        if df.empty or len(df.columns) == 0:
            st.error("The uploaded file is empty or has no columns. Please upload a valid CSV.")
            st.stop()

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # Reset passing grade and rank input when new file is uploaded
    if st.session_state.uploaded_filename != uploaded_file.name:
        st.session_state.uploaded_filename = uploaded_file.name
        st.session_state.passing_grade = 75
        st.session_state.passing_input = 75
        st.session_state.slider_input = 75
        # Reset rank navigation to default
        st.session_state.rank_range_input = ""
        st.session_state.use_custom_range = False
        st.session_state.last_valid_range = ""
        st.session_state.rank_input_key = 0

    # --- 🔒 Safety limits ---
    MAX_ROWS = 2000
    MAX_COLUMNS = 30
    num_rows, num_cols = df.shape

    if num_rows > MAX_ROWS:
        st.error(f"🚫 The uploaded file has {num_rows} rows, exceeding the {MAX_ROWS}-row limit.")
        st.stop()
    if num_cols > MAX_COLUMNS:
        st.error(f"The uploaded file has {num_cols} columns, exceeding the {MAX_COLUMNS}-column limit.")
        st.stop()

    # --- 🧑‍🎓 CLEAN DATA FIRST (ensures Name column exists) ---
    df = clean_data(df)
    df_original = df.copy()  # Preserve original for dropdown

    # --- 🧑‍🎓 Student Selector (searchable multi-select) ---
    all_students = sorted(df_original["Name"].astype(str).unique().tolist())

    selected_students = st.sidebar.multiselect(
        "🎯 Select specific students to view",
        options=all_students,
        default=[]
    )

    # --- Filter dataset for selected students (applied globally) ---
    if selected_students:
        df = df_original[df_original["Name"].isin(selected_students)].copy()
    else:
        df = df_original.copy()

    # --- Calculate global rankings from full dataset ---
    global_rankings = df_original[["Name", "Average"]].copy() if "Average" in df_original.columns else None

    if global_rankings is None:
        # Compute average if not already in df_original
        numeric_cols = df_original.select_dtypes(include=["number"]).columns
        df_original_temp = df_original.copy()
        df_original_temp["Average"] = df_original_temp[numeric_cols].mean(axis=1)
        global_rankings = df_original_temp[["Name", "Average"]].copy()

    global_rankings = global_rankings.sort_values("Average", ascending=False).reset_index(drop=True)
    global_rankings["Global_Rank"] = range(1, len(global_rankings) + 1)
    
    # --- ⚙️ Sidebar Settings ---
    all_cols = list(df.columns)
    numeric_cols = df.select_dtypes(include=["number"]).columns
    max_grade = int(df[numeric_cols].max().max()) if len(numeric_cols) > 0 else 100

    # Ensure passing grade doesn't exceed max_grade of current dataset
    if "passing_grade" in st.session_state and st.session_state.passing_grade > max_grade:
        st.session_state.passing_grade = max_grade
        st.session_state.passing_input = max_grade
        st.session_state.slider_input = max_grade

    # --- 🧮 Reactive Passing Grade ---
    st.sidebar.subheader("📊 Passing Grade")

    # Initialize session state with proper defaults
    if "passing_grade" not in st.session_state:
        st.session_state.passing_grade = 75
    if "passing_input" not in st.session_state:
        st.session_state.passing_input = st.session_state.passing_grade
    if "slider_input" not in st.session_state:
        st.session_state.slider_input = st.session_state.passing_grade

    # Clamp values to valid range before synchronization
    st.session_state.passing_grade = max(0, min(st.session_state.passing_grade, max_grade))
    st.session_state.passing_input = max(0, min(st.session_state.passing_input, max_grade))
    st.session_state.slider_input = max(0, min(st.session_state.slider_input, max_grade))

    # Ensure synchronization on every run
    if st.session_state.passing_input != st.session_state.passing_grade:
        st.session_state.passing_input = st.session_state.passing_grade
    if st.session_state.slider_input != st.session_state.passing_grade:
        st.session_state.slider_input = st.session_state.passing_grade

    def update_from_number():
        st.session_state.passing_grade = st.session_state.passing_input
        st.session_state.slider_input = st.session_state.passing_input

    st.sidebar.number_input(
        "Set Passing Grade (type manually)",
        min_value=0,
        max_value=max_grade,
        step=1,
        value=st.session_state.passing_input,
        key="passing_input",
        on_change=update_from_number
    )

    def update_from_slider():
        st.session_state.passing_grade = st.session_state.slider_input
        st.session_state.passing_input = st.session_state.slider_input

    st.sidebar.slider(
        "Adjust Passing Grade (slider)",
        min_value=0,
        max_value=max_grade,
        value=st.session_state.slider_input,
        step=1,
        key="slider_input",
        on_change=update_from_slider
    )

    passing_grade = st.session_state.passing_grade

    # 🚫 Column exclusion
    exclude_cols = st.sidebar.multiselect(
        "Select columns to exclude (insignificant columns with numeric data will affect the outcome)",
        options=all_cols,
        default=[]
    )

    # --- 📊 Process the data ---
    # Data is already cleaned, so we pass cleaned df directly
    result = compute_statistics(df, passing_grade, exclude_cols, top_n=10, already_cleaned=True)

    # --- 📄 Data Preview ---
    st.subheader(f"📄 Data Preview")

    display_df = result["df"].copy()
    display_df.index = range(1, len(display_df) + 1)
    st.dataframe(display_df)

    # --- 📈 Key Statistics ---
    st.markdown(f"### 📊 Key Statistics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Overall Average", f"{result['overall_average']}")
    c2.metric("Pass Rate", f"{result['pass_rate']}%")
    c3.metric("Total Students", f"{len(result['df'])}")

    # --- 🥇 Student Ranking with Enhanced Controls ---
    st.markdown(f"### 🥇 Student Ranking")

    # Initialize session state
    if "rank_range_input" not in st.session_state:
        st.session_state.rank_range_input = ""
    if "use_custom_range" not in st.session_state:
        st.session_state.use_custom_range = False
    if "last_valid_range" not in st.session_state:  
        st.session_state.last_valid_range = ""
    if "rank_input_key" not in st.session_state:
        st.session_state.rank_input_key = 0      

   # Get all students sorted by average
    all_ranked = result["df"][["Name", "Average"]].sort_values("Average", ascending=False).reset_index(drop=True)
    total_students = len(all_ranked)
    total_students_global = len(global_rankings)  # Total from full dataset

    # Merge with global rankings to get true rank numbers
    all_ranked = all_ranked.merge(global_rankings[["Name", "Global_Rank"]], on="Name", how="left")

    # --- Ultra-Compact CSS Styling ---
    st.markdown("""
    <style>
    /* Remove gaps between columns */
    [data-testid="column"] {
        padding: 0px 2px !important;
    }
    /* Make buttons plain arrows with no background */
    .stButton button {
        background: none !important;
        border: none !important;
        padding: 0px 5px !important;
        font-size: 18px !important;
        cursor: pointer !important;
        color: #262730 !important;
        box-shadow: none !important;
        min-height: 0px !important;
        height: auto !important;
    }
    .stButton button:hover {
        color: #FF4B4B !important;
        background: none !important;
    }
    /* Make selectbox smaller */
    .stSelectbox > div > div {
        padding: 2px 8px !important;
        min-height: 30px !important;
    }
    /* Make text input smaller */
    .stTextInput input {
        padding: 2px 8px !important;
        min-height: 30px !important;
        text-align: center !important;
    }
    /* Reduce vertical spacing */
    .element-container {
        margin-bottom: 0px !important;
    }
    /* Align text vertically */
    p {
        margin-top: 5px !important;
        margin-bottom: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- CONDITIONAL RENDERING: Only show rank navigation if NO students selected ---
    if not selected_students:
        # --- Custom Range Input: Showing: Ranks [1-10] of 25 ---
        range_cols = st.columns([3, 0.5, 1.2, 1, 3])

        with range_cols[1]:
            st.markdown("Rank")

        with range_cols[2]:
            def parse_rank_range(range_str, max_rank):
                """
                Parse rank range input (e.g., "1", "5-10")
                Returns (start, end) tuple or None if invalid
                """
                range_str = range_str.strip()
                if not range_str:
                    return None
                
                try:
                    if '-' in range_str:
                        parts = range_str.split('-')
                        if len(parts) != 2:
                            return None
                        start = int(parts[0].strip())
                        end = int(parts[1].strip())
                    else:
                        start = end = int(range_str)
                    
                    # Check if numbers exceed max
                    if start > max_rank or end > max_rank:
                        return None
                    
                    # Validate range
                    if start < 1 or end < 1 or start > end:
                        return None
                    
                    return (start, end)
                except ValueError:
                    return None
                
            # Auto-display current range if not custom
            if not st.session_state.use_custom_range:
                # Default to showing ranks 1-10 on first load
                display_value = f"1-{min(10, total_students)}"
                st.session_state.rank_range_input = display_value
                st.session_state.last_valid_range = display_value
            else:
                display_value = st.session_state.rank_range_input

            rank_input = st.text_input(
                "rank_range",
                value=display_value,
                key=f"rank_input_field_{st.session_state.rank_input_key}",
                label_visibility="collapsed",
                max_chars=9
            )

            # Only trigger on Enter key or focus loss (not every character)
            if rank_input != st.session_state.rank_range_input:
                # Handle blank input - restore last valid range
                if not rank_input.strip():
                    st.session_state.rank_range_input = st.session_state.last_valid_range
                    st.session_state.rank_input_key += 1
                    st.rerun()
                else:
                    parsed = parse_rank_range(rank_input, total_students_global)
                    if parsed:
                        st.session_state.rank_range_input = rank_input
                        st.session_state.last_valid_range = rank_input
                        st.session_state.use_custom_range = True
                        st.rerun()
                    else:
                        st.session_state.rank_range_input = st.session_state.last_valid_range
                        st.session_state.rank_input_key += 1
                        st.rerun()

        with range_cols[3]:
            st.markdown(f"of {total_students_global}")

    # --- Display Chart and Store for Export ---
    ranking_chart = None
    
    if selected_students:
        # When filtering students, show all selected students
        custom_df = all_ranked.copy()
        
        if 'Global_Rank' in custom_df.columns:
            custom_df['Rank'] = custom_df['Global_Rank']
        else:
            custom_df['Rank'] = range(1, len(custom_df) + 1)
        
        custom_df['Label'] = custom_df.apply(
            lambda row: f"{row['Name']}<br>Rank {row['Rank']}", 
            axis=1
        )
        
        num_students = len(custom_df)
        custom_colors = generate_colors(num_students)
        
        ranking_chart = px.bar(
            custom_df,
            x="Label",
            y="Average",
            text="Average",
            template="plotly_white"
        )
        
        ranking_chart.update_traces(
            texttemplate='%{text:.2f}', 
            textposition='outside',
            showlegend=False,
            marker_color=custom_colors
        )
        
        ranking_chart.update_layout(
            yaxis_title="Average Score", 
            xaxis_title="",
            height=500
        )
        
        st.plotly_chart(ranking_chart, use_container_width=True)

    else:
        # Normal ranking navigation
        if not st.session_state.use_custom_range:
            st.session_state.rank_range_input = f"1-{min(10, total_students)}"
            st.session_state.use_custom_range = True

        parsed = parse_rank_range(st.session_state.rank_range_input, total_students_global)
        if parsed:
            start_rank, end_rank = parsed
            st.session_state.last_valid_range = st.session_state.rank_range_input
            
            custom_df = all_ranked.iloc[start_rank-1:end_rank].copy()
            
            if 'Global_Rank' in custom_df.columns:
                custom_df['Rank'] = custom_df['Global_Rank']
            else:
                custom_df['Rank'] = range(start_rank, end_rank + 1)
            
            custom_df['Label'] = custom_df.apply(
                lambda row: f"{row['Name']}<br>Rank {row['Rank']}", 
                axis=1
            )
            
            num_students = len(custom_df)
            custom_colors = generate_colors(num_students)
            
            ranking_chart = px.bar(
                custom_df,
                x="Label",
                y="Average",
                text="Average",
                template="plotly_white"
            )
            
            ranking_chart.update_traces(
                texttemplate='%{text:.2f}', 
                textposition='outside',
                showlegend=False,
                marker_color=custom_colors
            )
            
            ranking_chart.update_layout(
                yaxis_title="Average Score", 
                xaxis_title="",
                height=500
            )
            
            st.plotly_chart(ranking_chart, use_container_width=True)
        else:
            st.error("❌ Invalid rank range. Use format: 1 or 5-10")
            st.session_state.rank_range_input = st.session_state.last_valid_range
        
    # --- 🥧 Subject Performance Distribution ---
    st.markdown(f"### 📚 Subject Performance Distribution")
    subject_chart = subject_average_chart(result["df"])
    st.plotly_chart(subject_chart, use_container_width=True)

    # --- 📈 Student Performance Trend ---
    st.markdown(f"### 📈 Student Performance Trend")
    trend_chart = student_performance_trend(result["df"])
    st.plotly_chart(trend_chart, use_container_width=True)

    # --- 💾 Export Buttons with All Charts ---
    st.markdown("### 💾 Export Complete Reports")
    
    # Prepare charts dictionary for export
    charts_to_export = {
        'Student_Ranking': ranking_chart,
        'Subject_Performance_Distribution': subject_chart,
        'Student_Performance_Trend': trend_chart
    }
    
    # Remove None values from charts
    charts_to_export = {k: v for k, v in charts_to_export.items() if v is not None}
    
    # Prepare summary statistics
    summary_stats = {
        'overall_average': result['overall_average'],
        'pass_rate': result['pass_rate'],
        'df': result['df']
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            pdf_path = export_to_pdf_with_charts(
                summary_stats, 
                result["top_students"], 
                charts_to_export
            )
            
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="📄 Download PDF Report (Incomplete Data Preview w/ Visuals)",
                    data=pdf_file.read(),
                    file_name="student_summary_complete.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"PDF export failed: {e}")
    
    with col2:
        try:
            excel_path = export_to_excel_with_charts(
                result["df"],
                charts_to_export,
                summary_stats
            )
            
            with open(excel_path, "rb") as excel_file:
                st.download_button(
                    label="📘 Download Excel Report (Complete Data Preview w/ Visuals)",
                    data=excel_file.read(),
                    file_name="student_report_complete.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Excel export failed: {e}")

else:
    st.info("👈 Upload a CSV file from the sidebar to start analysis.")