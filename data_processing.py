import pandas as pd
# -----------------------------------
# FEATURE ENGINEERING
# -----------------------------------
def prepare_features(df, feature_columns):
    df = df.copy()
    # Validate columns
    required_cols = ["Weight", "Pieces", "Volume"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Feature engineering
    df["Weight per Piece"] = df["Weight"] / df["Pieces"]
    df["Weight per Piece"] = df["Weight per Piece"].replace([float("inf"), -float("inf")], 0).fillna(0)

    # Weekend pickup
    if "Shipment Pickup_DOW" in df.columns:
        df["Weekend_Pickup"] = df["Shipment Pickup_DOW"].isin([6,7]).astype(int)
    else:
        df["Weekend_Pickup"] = 0

    # Pickup weekday fallback
    if "Shipment Pickup Date" in df.columns:
        df["Pickup Weekday Number"] = pd.to_datetime(df["Shipment Pickup Date"]).dt.weekday + 1

    # SLA feature
    if "Delivery_Window" in df.columns and "Shipment Pickup Date" in df.columns:
        df["Days_to_Commit"] = df["Delivery_Window"]

    # Service priority flag
    if "Service" in df.columns:
      df["Is_IP"] = (df.get("Service", "") == "IP").astype(int)
    else:
        df["Is_IP"] = 0

    df["weight_to_capacity"] = 0
    df["volume_to_capacity"] = 0

    # Capacity features
    if "Capacity_KG" in df.columns and df["Capacity_KG"].notna().any():
        df["weight_to_capacity"] = df["Weight"]/df["Capacity_KG"]
        
        
    if "Volume" in df.columns and "Capacity_KG" in df.columns :
        df["volume_to_capacity"] = df["Volume"] / df["Capacity_KG"]
        
        
    df["weight_to_capacity"] = df["weight_to_capacity"].replace([float("inf"), -float("inf")], 0).fillna(0)
    df["volume_to_capacity"] = df["volume_to_capacity"].replace([float("inf"), -float("inf")], 0).fillna(0)
    
    
    # Safe categorical encoding
    cat_cols = ["Weight_Category","Service","Destination_Hub"]

    for col in cat_cols:
        if col not in df.columns:
            df[col] = "Unknown"

    df = pd.get_dummies(
        df,
        columns=cat_cols,
        drop_first=False
    )

    drop_cols = [# IDs
    "AWB",
    "Flight_Number",
    "Flight_Label",

    # future leakage
    "Shipment Pickup Date",
    "Commit Date",
    "Flight_Takeoff_Date",
    "Shipment received date by the CLH team",
    "Shipment Handover date to Ramp by the CLH Team",
    "Shipment handover day to the ramp",
    #"Days_to_Commit",

    # derived leakage
    #"NO.Of Days between Pickup Date and Flight Takeoff",
    #"NO.OF DAYS BETWEEN FLIGHT TAKEOFF AND COMMIT DATE",
    "Delivery_Window",
    "Takeoff_Weekday",
    "Split",
    # capacity leakage
    "Capacity_KG",
    "Loaded_So_Far",
    "Remaining_Capacity",
    "Load_Percentage",
    "Capacity_Ratio",
    "Flight_Full",
    'weight_to_capacity',
    'volume_to_capacity',
    "L",
    "B",
    "H",
    "Capacity_Volume",
    "Loaded_Volume",
    "Invoice Value",
    "Weekend_Pickup",
    #"Weight per Piece",

    # redundant
    "Airline_Code",
    "Route_Type",
    "Day_of_Week",
    "Shipment Pickup_DOW",

    # optional remove
    "Urgency_Level",
    "Service_Priority"

    ]

    df = df.drop(columns=[col for col in drop_cols if col in df.columns])
    
    # Align columns
    
    if feature_columns is not None: # Only reindex if feature_columns is provided (i.e., during prediction)
        df = df.reindex(columns=feature_columns, fill_value=0)  # Ensure all expected columns are present, fill missing with 0
    # DROP NON-NUMERIC / USELESS COLUMNS
    
    # Convert all to numeric (safety)
    
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    

    # Safety
    if df.shape[0] == 0:
        raise ValueError("No data after feature processing")
    
    return df


