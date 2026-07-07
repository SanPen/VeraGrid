from __future__ import annotations

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Distance between two lat,lon points
    :param lat1:
    :param lon1:
    :param lat2:
    :param lon2:
    :return:
    """
    R = 6371  # Earth radius in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def closest_point_on_segment(lat1, lon1, lat2, lon2, lat3, lon3):
    """
    Find the closest point on a line segment to a given point using geographic coordinates.

    :param lat1, lon1: Coordinates of the first endpoint of the segment
    :param lat2, lon2: Coordinates of the second endpoint of the segment
    :param lat3, lon3: Coordinates of the point to find the closest point to
    :return: (closest_lat, closest_lon), distance_in_km
    """
    # For very short segments, just return the midpoint
    if haversine_distance(lat1, lon1, lat2, lon2) < 0.001:  # Less than 1 meter
        closest_lat = (lat1 + lat2) / 2
        closest_lon = (lon1 + lon2) / 2
        distance = haversine_distance(closest_lat, closest_lon, lat3, lon3)
        return (closest_lat, closest_lon), distance

    # Calculate distances to the endpoints
    dist_to_p1 = haversine_distance(lat1, lon1, lat3, lon3)
    dist_to_p2 = haversine_distance(lat2, lon2, lat3, lon3)

    # Convert to radians for spherical calculations
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    lat3_rad = math.radians(lat3)
    lon3_rad = math.radians(lon3)

    # Earth's radius in km
    R = 6371.0

    # Calculate the bearing from point 1 to point 2
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(
        lon2_rad - lon1_rad)
    bearing_1_to_2 = math.atan2(y, x)

    # Calculate the bearing from point 1 to point 3
    y = math.sin(lon3_rad - lon1_rad) * math.cos(lat3_rad)
    x = math.cos(lat1_rad) * math.sin(lat3_rad) - math.sin(lat1_rad) * math.cos(lat3_rad) * math.cos(
        lon3_rad - lon1_rad)
    bearing_1_to_3 = math.atan2(y, x)

    # Calculate the angular distance from point 1 to point 3
    angular_dist_1_to_3 = math.acos(
        math.sin(lat1_rad) * math.sin(lat3_rad) +
        math.cos(lat1_rad) * math.cos(lat3_rad) * math.cos(lon3_rad - lon1_rad)
    )

    # Calculate the cross-track distance (perpendicular distance to the great circle path)
    cross_track_dist = math.asin(
        math.sin(angular_dist_1_to_3) * math.sin(bearing_1_to_3 - bearing_1_to_2)
    )

    # Calculate the along-track distance (distance from point 1 to the closest point)
    along_track_dist = math.acos(
        math.cos(angular_dist_1_to_3) / math.cos(cross_track_dist)
    )

    # Calculate the total distance of the segment
    segment_dist_rad = math.acos(
        math.sin(lat1_rad) * math.sin(lat2_rad) +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    )

    # Check if the closest point is on the segment
    if along_track_dist > segment_dist_rad:
        # Closest point is beyond point 2
        return (lat2, lon2), dist_to_p2
    elif along_track_dist < 0:
        # Closest point is before point 1
        return (lat1, lon1), dist_to_p1
    else:
        # Closest point is on the segment
        # Calculate the position of the closest point
        closest_lat_rad = math.asin(
            math.sin(lat1_rad) * math.cos(along_track_dist) +
            math.cos(lat1_rad) * math.sin(along_track_dist) * math.cos(bearing_1_to_2)
        )

        closest_lon_rad = lon1_rad + math.atan2(
            math.sin(bearing_1_to_2) * math.sin(along_track_dist) * math.cos(lat1_rad),
            math.cos(along_track_dist) - math.sin(lat1_rad) * math.sin(closest_lat_rad)
        )

        closest_lat = math.degrees(closest_lat_rad)
        closest_lon = math.degrees(closest_lon_rad)

        # Calculate the distance from point 3 to the closest point
        distance = R * math.acos(
            math.sin(lat3_rad) * math.sin(closest_lat_rad) +
            math.cos(lat3_rad) * math.cos(closest_lat_rad) * math.cos(closest_lon_rad - lon3_rad)
        )

        return (closest_lat, closest_lon), distance