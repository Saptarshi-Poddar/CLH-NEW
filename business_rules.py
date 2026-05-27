def service_allowed(service, flight):
    flight = str(flight)
    airline = flight[:2]   # Extract airline code from flight number

    # Indigo restriction
    if airline == "6E":
        if service in ["IE", "IEF"]:
            return True
        else:
            return False

    # All other airlines allowed
    return True
