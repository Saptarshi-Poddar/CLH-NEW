
import pandas as pd

# ==============================
# 1. PURE ML PREDICTION
# ==============================
def predict_flights(model, encoder, features):

    # Safety check
    if features is None or features.shape[0] == 0:
        raise ValueError("Invalid input features")

    probs = model.predict_proba(features)[0]
    
    print("DEBUG  → model classes:", model.classes_)
    print("DEBUG  → encoder classes:", encoder.classes_)
    
    class_indices = model.classes_
    flights = encoder.inverse_transform(class_indices)  # Assuming encoder was fitted on the same order as model classes

    df = pd.DataFrame({
        "Flight": flights,
        "Probability": probs * 100
    })
    df["Flight"] = df["Flight"].astype(str)
    return df.sort_values("Probability", ascending=False).reset_index(drop=True)


# ==============================
# 2. BUSINESS RULES
# ==============================
def apply_business_rules(df, is_ip=0, days_to_commit=None):  # Add days_to_commit parameter to handle urgent shipments

    df = df.copy()
    
    # Safety
    if df is None or df.empty:
        if days_to_commit is not None and days_to_commit <= 1: # If it's urgent, recommend FedEx Priority as a fallback
            return pd.DataFrame({
                "Flight": ["FedEx_Priority"],
                "Probability": [100]
            })
        return pd.DataFrame({
            "Flight": ["Wait_for_next_flight"],  # Recommend waiting for the next flight if no valid options are available
            "Probability": [100]
    })
    
    
    # IP penalty
    #if is_ip == 1:  
    #    df["Probability"] *= 0.8 # 20% penalty for IP shipments to reflect lower priority (can be tuned based on historical data)
#
    # Normalize
    total = df["Probability"].sum()  # If total is 0 (which can happen if all probabilities were penalized to 0), we should avoid division by zero
    if total > 0:
        df["Probability"] = (df["Probability"] / total) * 100

    return df


# ==============================
# 3. FINAL PIPELINE
# ==============================
def get_top_flights(
    model,
    encoder,
    features,
    is_ip=0,
    days_to_commit=None
):

    df = predict_flights(model, encoder, features)

    df = apply_business_rules(
        df,
        is_ip=is_ip,
        days_to_commit=days_to_commit
    )

    return df.head(3)