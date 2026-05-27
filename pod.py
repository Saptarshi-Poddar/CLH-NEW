import pandas as pd

def create_pod_lookup(pod_input):

    # STEP 1: Detect input type
    if isinstance(pod_input, pd.DataFrame):
        pod_df = pod_input

    else:
        # It is a file → handle normally
        if hasattr(pod_input, "name"):
            file_name = pod_input.name.lower()
        else:
            file_name = str(pod_input).lower()

        if file_name.endswith(".csv"):
            pod_df = pd.read_csv(pod_input)
        elif file_name.endswith((".xlsx", ".xls")):
            pod_df = pd.read_excel(pod_input)
        else:
            raise ValueError("Unsupported file format")

    # =========================
    # CLEAN DATA
    # =========================
    pod_df.columns = pod_df.columns.str.strip()

    pod_df["Flight_Number"] = (
        pod_df["Flight_Number"]
        .astype(str)
        .str.replace(" ", "")
        .str.strip()
    )

    pod_df["Takeoff_Weekday"] = pd.to_numeric(
        pod_df["Takeoff_Weekday"], errors="coerce"
    )

    pod_df["POD"] = pd.to_numeric(
        pod_df["POD"], errors="coerce"
    )

    # Drop invalid rows
    pod_df = pod_df.dropna(subset=["Flight_Number", "Takeoff_Weekday", "POD"])

    # =========================
    # CREATE LOOKUP DICTIONARY
    # =========================
    pod_lookup = {}

    for _, row in pod_df.iterrows():
        key = (
            row["Flight_Number"],
            int(row["Takeoff_Weekday"])
        )
        pod_lookup[key] = int(row["POD"])

    return pod_lookup