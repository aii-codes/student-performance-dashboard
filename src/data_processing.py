import pandas as pd

def clean_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    df.dropna(how="all", inplace=True)

    first_col = df.columns[0]
    if pd.api.types.is_numeric_dtype(df[first_col]):
        df.insert(0, "Name", [f"Student {i+1}" for i in range(len(df))])
    else:
        df.rename(columns={first_col: "Name"}, inplace=True)
    return df


def compute_statistics(df, passing_grade=75, exclude_cols=None, top_n=10, already_cleaned=False):
    if not already_cleaned:
        df = clean_data(df)
    else:
        df = df.copy()  # Just copy to avoid modifying original

    if exclude_cols:
        df = df.drop(columns=[c for c in exclude_cols if c in df.columns], errors="ignore")

    numeric_cols = df.select_dtypes(include=["number"]).columns
    df["Average"] = df[numeric_cols].mean(axis=1)
    df["Status"] = df["Average"].apply(lambda x: "Passed" if x >= passing_grade else "Failed")

    # Reorder columns (Average & Status at end)
    cols = [c for c in df.columns if c not in ["Average", "Status"]] + ["Average", "Status"]
    df = df[cols]

    overall_avg = df["Average"].mean()
    pass_rate = (df["Average"] >= passing_grade).mean() * 100

    top_students = df.nlargest(top_n, "Average")[["Name", "Average"]]

    return {
        "df": df,
        "overall_average": round(overall_avg, 2),
        "pass_rate": round(pass_rate, 2),
        "top_students": top_students
    }
