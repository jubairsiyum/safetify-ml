from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from utils import (
    calculate_point_risk,
    calculate_overall_analysis
)

from model_loader import ml_loader

router = APIRouter()


class RoutePoint(BaseModel):
    latitude: float
    longitude: float


class PredictRouteRequest(BaseModel):

    weekday: str

    part_of_day: str

    radius: int = 300

    route: List[RoutePoint]


@router.post("/predict-route")
def predict_route(data: PredictRouteRequest):

    results = []

    for point in data.route:

        # ML Feature
        features = ml_loader.prepare_features(
            latitude=point.latitude,
            longitude=point.longitude,
            weekday=data.weekday,
            part_of_day=data.part_of_day
        )

        # Random Forest Prediction
        estimated_crime_count = float(
            ml_loader.model.predict(features)[0]
        )

        # Historical Analysis
        historical = calculate_point_risk(
            lat=point.latitude,
            lon=point.longitude,
            weekday=data.weekday,
            part_of_day=data.part_of_day,
            radius=data.radius
        )

        # Overall Analysis
        overall = calculate_overall_analysis(
            historical,
            estimated_crime_count
        )

        results.append({

            "latitude": point.latitude,

            "longitude": point.longitude,

            "historical": historical,

            "ml_prediction": round(
                estimated_crime_count,
                2
            ),

            "overall": overall

        })

    risk_scores = [
        p["overall"]["overall_score"]
        for p in results
    ]

    average_risk = sum(risk_scores) / len(risk_scores)

    highest_risk = max(risk_scores)

    high_points = sum(
        1
        for p in results
        if p["overall"]["risk_level"] == "HIGH"
    )

    medium_points = sum(
        1
        for p in results
        if p["overall"]["risk_level"] == "MEDIUM"
    )

    low_points = sum(
        1
        for p in results
        if p["overall"]["risk_level"] == "LOW"
    )

    if average_risk < 35:

        route_level = "LOW"

    elif average_risk < 70:

        route_level = "MEDIUM"

    else:

        route_level = "HIGH"

    return {

    "success": True,

    "total_points": len(results),

    "route_summary": {

        "average_risk_score": round(
            average_risk,
            2
        ),

        "highest_risk_score": round(
            highest_risk,
            2
        ),

        "high_risk_points": high_points,

        "medium_risk_points": medium_points,

        "low_risk_points": low_points,

        "overall_route_risk": route_level

    },

    "points": results

}