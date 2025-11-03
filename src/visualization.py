import plotly.express as px
import pandas as pd
import plotly.colors as pc
import plotly.graph_objects as go

def subject_average_chart(df):
    """
    Displays average score per subject as a modern donut chart.
    Excludes 'Average' and 'Status' columns.
    Handles any number of subjects with dynamic color cycling.
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    for col in ["Average", "Status"]:
        if col in numeric_cols:
            numeric_cols.remove(col)

    if not numeric_cols:
        return px.scatter(title="No valid numeric columns to visualize.")

    subject_means = df[numeric_cols].mean().reset_index()
    subject_means.columns = ["Subject", "Score"]

    # 🔹 Dynamic color palette — repeat colors if there are more subjects
    base_colors = pc.qualitative.Set3 + pc.qualitative.Pastel1 + pc.qualitative.Safe
    color_sequence = (base_colors * ((len(subject_means) // len(base_colors)) + 1))[: len(subject_means)]

    fig = px.pie(
        subject_means,
        values="Score",
        names="Subject",
        hole=0.45,
        color_discrete_sequence=color_sequence
    )

    fig.update_traces(
        textinfo="label+percent",
        textfont_size=13,
        hovertemplate="<b>%{label}</b><br>%{value:.2f}",
        marker=dict(line=dict(color="white", width=2))
    )

    # 🧩 Move legend below chart to avoid overlap
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            y=-0.25,
            x=0.5,
            xanchor="center",
            font=dict(size=11),
            traceorder="normal"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def top_performers_chart(top_students_df, page=1, per_page=10):
    """
    Bar chart showing top performers with ranking numbers and pagination.
    
    Args:
        top_students_df: DataFrame with Name and Average columns, sorted by Average descending
        page: Current page number (1-indexed)
        per_page: Number of students to show per page
    
    Returns:
        Plotly figure object
    """
    # Calculate pagination
    total_students = len(top_students_df)
    total_pages = (total_students + per_page - 1) // per_page  # Ceiling division
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_students)
    
    # Get current page data
    page_df = top_students_df.iloc[start_idx:end_idx].copy()
    
    # Add rank numbers (starting from actual rank, not page rank)
    page_df['Rank'] = range(start_idx + 1, end_idx + 1)
    
    # Create custom x-axis labels: "Name\nRank #"
    page_df['Label'] = page_df.apply(
        lambda row: f"{row['Name']}<br>Rank {row['Rank']}", 
        axis=1
    )
    
    fig = px.bar(
        page_df,
        x="Label",
        y="Average",
        text="Average",
        color="Name",
        template="plotly_white"
    )
    
    fig.update_traces(
        texttemplate='%{text:.2f}', 
        textposition='outside',
        showlegend=False  # Hide legend since names are on x-axis
    )
    
    # Update layout with page info
    title_text = f"Rank {start_idx + 1}-{end_idx} of {total_students}"
    
    fig.update_layout(
        yaxis_title="Average Score", 
        xaxis_title="",
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=14)
        ),
        height=500
    )
    
    return fig, total_pages, page


def student_performance_trend(df):
    """
    Line chart showing each student's numeric performance trend across subjects.
    - 10 active students initially for clarity
    - All students visible in legend (scrollable)
    - Clicking legend toggles line visibility interactively
    - Only numeric columns are plotted
    """
    # --- Identify numeric columns ---
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    for col in ["Average", "Status"]:
        if col in numeric_cols:
            numeric_cols.remove(col)

    if not numeric_cols:
        return px.scatter(title="No numeric columns to plot.")

    all_students = df["Name"].unique().tolist()
    MAX_ACTIVE = 10

    # Base data for first 10 visible students
    active_students = all_students[:MAX_ACTIVE]

    long_df = df.melt(
        id_vars="Name",
        value_vars=numeric_cols,
        var_name="Subject",
        value_name="Score"
    )

    # --- Build Plotly figure manually for better control ---
    fig = go.Figure()

    # Add traces for all students
    for i, student in enumerate(all_students):
        student_data = long_df[long_df["Name"] == student]
        visible = True if i < MAX_ACTIVE else "legendonly"  # show first 10 only
        fig.add_trace(
            go.Scatter(
                x=student_data["Subject"],
                y=student_data["Score"],
                mode="lines",
                name=student,
                line=dict(width=1.5),
                visible=visible,
            )
        )

    # --- Layout settings ---
    legend_config = dict(
        orientation="v",
        y=1,
        x=1.02,
        yanchor="top",
        xanchor="left",
        font=dict(size=10),
        maxheight=300,  # enables scrollbar if legend too tall
        title_text="Students"
    )

    fig.update_layout(
        title=" ",
        title_x=0.5,
        legend=legend_config,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=600,
        margin=dict(r=100, t=80, b=80, l=80),
        font=dict(size=12)
    )

    return fig