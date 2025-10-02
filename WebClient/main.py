from fastapi import FastAPI
from .api.v1 import juiceShop

app = FastAPI(title="Juice Box API REST")

# Se incluyen las rutas
app.include_router(juiceShop.router, prefix="/api/v1/juice-shop", tags=["JuiceShop"])
