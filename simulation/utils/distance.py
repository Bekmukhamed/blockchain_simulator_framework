import math
import simulation.globals as sim_globals

def calculate_distance(node1, node2):
    lat1, lon1 = node1.coordinates
    lat2, lon2 = node2.coordinates

    # Haversine formula for distance
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = sim_globals.RADIUS * c

    return distance_km
