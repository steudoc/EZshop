import os
os.environ["TESTING"] = "0"  # normal run
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.errors.app_error import AppError  
from app.middleware.error_middleware import error_handler
from app.routes import  user_route, auth_route, balance_route, product_route, order_route, return_route, card_route, customer_route, sale_route
from contextlib import asynccontextmanager
from app.database.database import engine, Base, _import_all_daos
from logging import getLogger

logger = getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    _import_all_daos()  # Import all DAOs before creating tables
    async with engine.begin() as conn:
        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
    yield 
    await engine.dispose()

app = FastAPI(title="EZShop", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # should allow all origins for dev purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# register routers
app.include_router(auth_route.router)
app.include_router(user_route.router)
app.include_router(return_route.router)
app.include_router(balance_route.router)
app.include_router(product_route.router)
app.include_router(order_route.router)
app.include_router(card_route.router)
app.include_router(customer_route.router)
app.include_router(sale_route.router)
app.add_exception_handler(AppError, error_handler)
app.add_exception_handler(Exception, error_handler)


# simple root
@app.get("/")
def read_root():
    return {"message": "FastAPI MVC Demo"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)