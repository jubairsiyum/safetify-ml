import joblib
import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.neighbors import BallTree

BASE_DIR = Path(__file__).resolve().parent
ML_DIR = BASE_DIR / "ml"

EARTH_RADIUS = 6371000


class MLLoader:

    def __init__(self):

        self.model = None
        self.weekday_encoder = None
        self.part_encoder = None

        self.dataset = None
        self.hotspots = None

        self.tree = None

    def load(self):

        print("Loading ML Resources...")

        self.model = joblib.load(
            ML_DIR / "crime_risk_model.pkl"
        )

        self.weekday_encoder = joblib.load(
            ML_DIR / "weekday_encoder.pkl"
        )

        self.part_encoder = joblib.load(
            ML_DIR / "part_encoder.pkl"
        )

        self.dataset = pd.read_csv(
            ML_DIR / "crime_dataset_clustered.csv"
        )

        self.hotspots = pd.read_csv(
            ML_DIR / "hotspots_with_risk.csv"
        )

        coords = np.radians(
            self.dataset[
                ["latitude", "longitude"]
            ].values
        )

        self.tree = BallTree(
            coords,
            metric="haversine"
        )

        print("Random Forest Loaded")

        print("Encoders Loaded")

        print("Dataset Loaded")

        print("Hotspots Loaded")

        print("BallTree Created")
    
    def prepare_features(
        self,
        latitude,
        longitude,
        weekday,
        part_of_day
    ):

        weekday = weekday.lower()
        part_of_day = part_of_day.lower()

        weekday_encoded = self.weekday_encoder.transform([weekday])[0]
        part_encoded = self.part_encoder.transform([part_of_day])[0]

        return [[
            latitude,
            longitude,
            weekday_encoded,
            part_encoded
    ]]


ml_loader = MLLoader()