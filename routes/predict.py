from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from model_loader import ml_loader

from utils import (
    calculate_point_risk,
    calculate_overall_analysis
)


router = APIRouter()


class PredictPointRequest(BaseModel):

    latitude: float
    longitude: float

    weekday: str

    part_of_day: str

    radius: int = 300


@router.post("/predict-point")
def predict_point(data: PredictPointRequest):

    try:

        features = ml_loader.prepare_features(
            latitude=data.latitude,
            longitude=data.longitude,
            weekday=data.weekday,
            part_of_day=data.part_of_day
        )

        prediction = float(
            ml_loader.model.predict(features)[0]
        )

        historical = calculate_point_risk(
            lat=data.latitude,
            lon=data.longitude,
            weekday=data.weekday,
            part_of_day=data.part_of_day,
            radius=data.radius
        )

        overall = calculate_overall_analysis(
            historical,
            prediction
        )

        

        return {

            "success": True,

            "location": {

                "latitude": data.latitude,

                "longitude": data.longitude

            },

            "historical_analysis": historical,

            "ml_prediction": {

                "estimated_crime_count": round(
                    prediction,
                    2
                )

            },

    "overall_analysis": overall

}

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )