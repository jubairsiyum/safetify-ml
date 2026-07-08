from fastapi import FastAPI
from model_loader import ml_loader
from routes.predict import router as predict_router
from routes.route import router as route_router


app = FastAPI(
    title="Safetify ML API",
    version="1.0.0"
)


@app.on_event("startup")
def startup():

    ml_loader.load()

    print("Server Ready")
    app.include_router(
    predict_router,
    prefix="/api"
)
    app.include_router(
    route_router,
    prefix="/api",
    tags=["Route Prediction"]
)


@app.get("/")
def root():

    return {
        "status": "running",
        "service": "Safetify ML API"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model_loaded": ml_loader.model is not None,
        "dataset_size": len(
            ml_loader.dataset
        ),
        "hotspots": len(
            ml_loader.hotspots
        )
    }

