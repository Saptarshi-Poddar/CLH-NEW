import pandas as pd

from business_rules import service_allowed

from datetime import timedelta

    
def valid_route(flight, origin, destination, routes_df):
# Route validation function to check if the flight has a valid route (direct or via hub) for the given origin and destination

    flight = str(flight).replace(" ", "").strip()

    df = routes_df.copy()
    
    df["Flight_Number"] = df["Flight_Number"].astype(str).str.replace(" ", "").str.strip()
    
    # Filter routes for that flight
    flight_rows = df[df["Flight_Number"] == flight]

    if flight_rows.empty:
        return False

    # Build graph for this flight
    graph = {}
    for _, row in flight_rows.iterrows():
        o = row["Origin"]
        d = row["Destination"]

        if o not in graph:
            graph[o] = []
        graph[o].append(d)

    # BFS traversal to check reachability
    from collections import deque
    max_hops = 2  # Allow direct or 1-hop routes
    
    queue = deque([(origin, 0)])  # (node, hops)
    visited = set()

    while queue:
        node, depth = queue.popleft()
        if node in visited:
            continue
        visited.add(node)

        if depth > max_hops:
            continue

        if node == destination:
            return True

        for neighbor in graph.get(node, []):
            queue.append((neighbor, depth + 1))

    return False


def get_feasible_flights(
    top3,
    shipment_weight,
    shipment_volume,
    capacity_df,
    ready_date,
    service,
    destination,
    routes_df,
    origin,
    schedule_df,
    pod_lookup,
    days_to_commit=None,
    same_airline_attempts=2,
    fallback_extra_days=6
):

    #routes_df = routes_df.copy()

    day_map = {
        "Monday":1, "Tuesday":2, "Wednesday":3,
        "Thursday":4, "Friday":5, "Saturday":6, "Sunday":7
    }

    capacity_df = capacity_df.copy()
   
    
    feasible_flights = []
    debug_log = []
    blocked_airlines = set()

    if "Loaded_Volume" not in capacity_df.columns:
        capacity_df["Loaded_Volume"] = 0
    if "Loaded_So_Far" not in capacity_df.columns:
        capacity_df["Loaded_So_Far"] = 0
    
    capacity_df["Day_Num"] = capacity_df["Day_of_Week"].map(day_map)

    #  Normalize once (avoid repeated string ops)
    capacity_df["Flight_Number"] = capacity_df["Flight_Number"].astype(str).str.replace(" ","").str.strip()
    schedule_df["Flight_Number"] = schedule_df["Flight_Number"].astype(str).str.replace(" ","").str.strip()
    routes_df["Flight_Number"] = routes_df["Flight_Number"].astype(str).str.replace(" ","").str.strip()

    # ==============================
    # STEP 1: TRY TOP 3
    # ==============================
    top3 = top3.copy()
    top3["Flight"] = top3["Flight"].astype(str).str.replace(" ","").str.strip()
    top3 = top3[~top3["Flight"].str.startswith("FX")]

    for flight in top3["Flight"]:
    
        flight = str(flight).replace(" ", "").strip()

        if not service_allowed(service, flight):
            debug_log.append(f"{flight}  → Rejected (Service Not Allowed)")
            continue

        if not valid_route(flight, origin, destination, routes_df):
            debug_log.append(f"{flight}  → Rejected (Invalid Route)")
            continue

        valid_days = schedule_df[
            schedule_df["Flight_Number"] == flight
        ]["Operating_Day"]

        valid_days_num = [
            day_map[d.strip()]
            for d in valid_days.astype(str)
            if d.strip() in day_map
        ]

        rows = capacity_df[
            capacity_df["Flight_Number"] == flight
        ].copy()

        # Keep only future valid dates
        rows = rows[
            rows["Actual_Date"] > pd.Timestamp(ready_date)
        ]

        # Sort by actual calendar date
        rows = rows.sort_values("Actual_Date")

        # Keep only nearest opportunities
        #rows = rows.head(same_airline_attempts)
        
        current_day = ready_date.weekday() + 1
        
        if len(valid_days_num) == 0:
            debug_log.append(f"{flight}  → Rejected (No schedule)")
            continue
        
        
        if rows.empty:
            debug_log.append(f"{flight}  → Rejected (No further opportunity given)")
            blocked_airlines.add(flight)
            continue
        
        # ==============================
        # LOAD BALANCING
        # ==============================
        rows["Load_Percentage"] = rows["Loaded_So_Far"] / rows["Capacity_KG"]
        rows["Volume_Usage"] = rows["Loaded_Volume"] / rows["Capacity_Volume"]

        #  Add POD-aware sorting (NEW IMPROVEMENT)
        
        
        clean_flight = str(flight).replace(" ","").strip()
        rows["pod_days"] = rows["Day_Num"].apply(
            lambda d: pod_lookup.get((clean_flight, int(d)), 999)
        )
        rows["total_days"] = rows["pod_days"]
        
        rows["day_gap"] = (pd.to_datetime(rows["Actual_Date"]) - pd.Timestamp(ready_date)).dt.days
        

        rows = rows.sort_values(
            ["day_gap","pod_days","Load_Percentage","Volume_Usage"]
        )
        best_failure_reason = None
        best_failure_delay = float("inf")
        
        for idx in rows.index:

            day_num = rows.loc[idx, "Day_Num"]
   
            # ==============================
            # POD + SLA CHECK
            # ==============================
            if days_to_commit is not None:

                pod_days = pod_lookup.get((clean_flight,int(day_num)))

                if pod_days is None:
                    debug_log.append(f"{flight}  → Rejected (POD missing)")
                    continue

                actual_flight_date = pd.to_datetime(rows.loc[idx, "Actual_Date"])
                
                day_gap = (actual_flight_date - pd.Timestamp(ready_date)).days

                total_days = pod_days + day_gap
                
                debug_log.append(f"{flight} on day {day_num} → POD days: {pod_days}, Day gap: {day_gap}, Total days: {total_days}")

                if total_days > days_to_commit:
                    if total_days <  best_failure_delay:
                        best_failure_delay = total_days
                        best_failure_reason = f"SLA fail:{total_days} > {days_to_commit}"
                    continue
                
            capacity = capacity_df.loc[idx,"Capacity_KG"]
            
            WEIGHT_BUFFER = capacity * 0.14 # Add a 14% buffer to account for weight estimation errors and ensure we don't overcommit flights
            remaining_weight = (
               (capacity + WEIGHT_BUFFER) 
                - capacity_df.loc[idx, "Loaded_So_Far"])
            
            remaining_volume = (
                capacity_df.loc[idx, "Capacity_Volume"]
                - capacity_df.loc[idx, "Loaded_Volume"]
                
            ) if "Capacity_Volume" in capacity_df.columns else float("inf")
            # Your Rule :weight first ,volume constrint second
            if (
                remaining_weight >= shipment_weight and
                remaining_volume >= shipment_volume
            ):  
                feasible_flights.append((
                flight,
                idx,
                day_num,
                capacity_df.loc[idx, "Day_of_Week"],
                capacity_df.loc[idx, "Actual_Date"]
            ))
                
                debug_log.append(f"{flight}  → Selected Candidate")
                break  # Stop after finding the first feasible flight in top 3 (can be adjusted to find more if needed)      
            else:
                debug_log.append(f"{flight}  → Rejected (Capacity full)")
                blocked_airlines.add(flight)
                
        if best_failure_reason is not None:
            debug_log.append(f"{flight}  → Rejected ({best_failure_reason})")
                    
    # ==============================
    # STEP 2: FALLBACK
    # ==============================
    
    debug_log.append("--------- Expanding search beyond ML Top3 -----------")
    
    possible_flights = capacity_df["Flight_Number"].unique()
    
    top3_set = set(top3["Flight"])
    
    for flight in possible_flights:
        
        flight = str(flight).replace(" ", "").strip()
        
        if flight in top3_set:
            continue
        
        if flight.startswith("FX"):
            debug_log.append(f"{flight}  → Rejected (FedEx skipped)")
            continue

        if not valid_route(flight, origin, destination, routes_df):
            debug_log.append(f"{flight}  → Rejected (Invalid Route)")
            continue

        if not service_allowed(service, flight):
            debug_log.append(f"{flight}  → Rejected (Service Not Allowed)")
            continue

        valid_days = schedule_df[
            schedule_df["Flight_Number"] == flight
        ]["Operating_Day"]

        valid_days_num = [
            day_map[d.strip()]
            for d in valid_days.astype(str)
            if d.strip() in day_map
        ]

        rows = capacity_df[
            capacity_df["Flight_Number"] == flight
        ].copy()

        # Keep only future valid dates
        rows = rows[
            rows["Actual_Date"] > pd.Timestamp(ready_date)
        ]

        # Sort by actual calendar date
        rows = rows.sort_values("Actual_Date")

        # Keep only nearest opportunities
        #rows = rows.head(same_airline_attempts)

        if rows.empty:
            debug_log.append(f"{flight}  → Rejected (No Schedule)")
            continue

        current_day = ready_date.weekday() + 1
        
        
        if len(valid_days_num) == 0:
            debug_log.append(f"{flight} → Rejected (No schedule)")
            continue


        if rows.empty:
            debug_log.append(f"{flight} → Rejected (Not available on next schedule)")
            continue
        
      
        rows["Load_Percentage"] = rows["Loaded_So_Far"] / rows["Capacity_KG"]
        rows["Volume_Usage"] = rows["Loaded_Volume"] / rows["Capacity_Volume"]
        
        #  POD-aware sorting here also
        clean_flight = str(flight).replace(" ","").strip()
        rows["pod_days"] = rows["Day_Num"].apply(
            lambda d: pod_lookup.get((clean_flight, int(d)), 999)
        )
        rows["total_days"] = rows["pod_days"]

        rows["day_gap"] = (pd.to_datetime(rows["Actual_Date"]) - pd.Timestamp(ready_date)).dt.days
        

        rows = rows.sort_values(
            ["day_gap","pod_days","Load_Percentage","Volume_Usage"]
        )
        
        best_failure_reason = None
        best_failure_delay = float("inf")
        
        for idx in rows.index:   

            day_num = rows.loc[idx, "Day_Num"]
            

            if days_to_commit is not None:

                pod_days = pod_lookup.get((clean_flight,int(day_num)))

                if pod_days is None:
                    debug_log.append(f"{flight}  → Rejected (POD missing)")
                    continue

                actual_flight_date = pd.to_datetime(rows.loc[idx, "Actual_Date"])
                day_gap = (actual_flight_date - pd.Timestamp(ready_date)).days
                    
                total_days = pod_days + day_gap
                
                debug_log.append(f"{flight} on day {day_num} → POD days: {pod_days}, Day gap: {day_gap}, Total days: {total_days}")

                if total_days > days_to_commit:
                    if total_days <  best_failure_delay:
                        best_failure_delay = total_days
                        best_failure_reason = f"SLA fail:{total_days} > {days_to_commit}"
                    continue

            capacity = capacity_df.loc[idx,"Capacity_KG"]
            
            WEIGHT_BUFFER = capacity * 0.14
            
            remaining_weight = (
               (capacity + WEIGHT_BUFFER) 
                - capacity_df.loc[idx, "Loaded_So_Far"])
            
            remaining_volume = (
                capacity_df.loc[idx, "Capacity_Volume"]
                - capacity_df.loc[idx, "Loaded_Volume"]
                
            ) if "Capacity_Volume" in capacity_df.columns else float("inf")  # If volume data is missing, ignore volume constraint
            
            # Your Rule :weight first ,volume constrint second
            if (
                remaining_weight >= shipment_weight and
                remaining_volume >= shipment_volume
            ):  
                feasible_flights.append((
                flight,
                idx,
                day_num,
                capacity_df.loc[idx, "Day_of_Week"],
                capacity_df.loc[idx, "Actual_Date"]
            ))
                debug_log.append(f"{flight}  → Selected Candidate")
                break  # Stop after finding the first feasible flight in top 3 (can be adjusted to find more if needed)      
            else:
                debug_log.append(f"{flight}  → Rejected (Capacity full)")
        if best_failure_reason is not None:
            debug_log.append(f"{flight} → Rejected ({best_failure_reason})")     
                     
    unique = {}
    for f , idx, day_num,day, actual_date in feasible_flights:
        key = (f,str(actual_date))
        if key not in unique:
            unique[key] = (f, idx, day_num, day, actual_date)
            
    feasible_flights = list(unique.values())
    
    if len(feasible_flights) == 0:
      debug_log.append("No feasible flights → FedEx fallback")
    return feasible_flights,list(dict.fromkeys(debug_log))

