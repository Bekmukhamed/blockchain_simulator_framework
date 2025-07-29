import math
def haversine():
    base_latency = 0.001  # 1ms base processing delay
    
    # Calculate distance-based latency
    lat1, lon1 = self.coordinates
    lat2, lon2 = other_node.coordinates
    
    # Haversine formula for distance
    R = 6378  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c

    return distance_km
