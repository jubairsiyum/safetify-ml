import numpy as np
from model_loader import ml_loader
from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2

EARTH_RADIUS = 6371000
DEFAULT_CRIME_WEIGHT = 30


def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return EARTH_RADIUS * c



def find_nearby_incidents(lat, lon, radius=300):

    point = np.radians([[lat, lon]])

    indices, distances = ml_loader.tree.query_radius(
        point,
        r=radius / EARTH_RADIUS,
        return_distance=True
    )

    nearby = ml_loader.dataset.iloc[indices[0]].copy()

    nearby["distance"] = distances[0] * EARTH_RADIUS

    return nearby


CRIME_WEIGHT = {
    "murder": 100,
    "rape": 90,
    "kidnap": 80,
    "robbery": 65,
    "assault": 45,
    "bodyfound": 30
}


def calculate_point_risk(
    lat,
    lon,
    weekday,
    part_of_day,
    radius=300
):

    nearby = find_nearby_incidents(
        lat,
        lon,
        radius
    )

    if weekday:
        nearby = nearby[
            nearby["incident_weekday"].str.lower() == weekday.lower()
        ]

    if part_of_day:
        nearby = nearby[
            nearby["part_of_the_day"].str.lower() == part_of_day.lower()
        ]

    if len(nearby) == 0:

        return {
            "incident_count": 0,
            "dominant_crime": None,
            "severity_score": 0,
            "nearest_distance": 9999,
            "risk_score": 0
        }

    score = 0

    for _, row in nearby.iterrows():

        score += CRIME_WEIGHT.get(
            row["crime"],
            DEFAULT_CRIME_WEIGHT
        )

    severity_scores = [
        CRIME_WEIGHT.get(c, DEFAULT_CRIME_WEIGHT)
        for c in nearby["crime"]
    ]

    average_severity = sum(severity_scores) / len(severity_scores)

    nearest_distance = nearby["distance"].min()

    return {

        "incident_count": len(nearby),

        "dominant_crime": nearby["crime"].mode()[0],

        "severity_score": round(average_severity, 2),

        "nearest_distance": round(nearest_distance, 2),

        "risk_score": round(
            average_severity * min(len(nearby), 5) / 5, 2
        )
    }


def calculate_overall_analysis(
    historical,
    estimated_crime_count
):

    severity = historical["severity_score"]

    incident_count = historical["incident_count"]

    distance = historical["nearest_distance"]

    # -------------------------
    # Frequency
    # -------------------------

    frequency_score = min(
        incident_count * 15,
        100
    )

    # -------------------------
    # Distance
    # -------------------------

    if distance <= 50:
        distance_score = 100

    elif distance <= 100:
        distance_score = 80

    elif distance <= 200:
        distance_score = 60

    elif distance <= 300:
        distance_score = 40

    else:
        distance_score = 20

    # -------------------------
    # ML Score
    # -------------------------

    ml_score = min(
        estimated_crime_count * 10,
        100
    )

    # -------------------------
    # Final Weighted Score
    # -------------------------

    final_score = (

        severity * 0.40 +

        frequency_score * 0.25 +

        distance_score * 0.20 +

        ml_score * 0.15

    )

    if final_score < 35:

        level = "LOW"

        color = "GREEN"

        recommendation = "Safe to travel."

    elif final_score < 70:

        level = "MEDIUM"

        color = "YELLOW"

        recommendation = "Proceed carefully."

    else:

        level = "HIGH"

        color = "RED"

        recommendation = "Choose another route if possible."

    return {

        "overall_score": round(final_score, 2),

        "risk_level": level,

        "color": color,

        "recommendation": recommendation,

        "components": {

            "severity": round(severity, 2),

            "frequency": frequency_score,

            "distance": distance_score,

            "ml_prediction": round(ml_score, 2)

        }

    }