def parse_time(time_str):
    # Parses "MM:SS" or "HH:MM:SS" or "SS" to seconds
    parts = list(map(int, time_str.split(':')))
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0
