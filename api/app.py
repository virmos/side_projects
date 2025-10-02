import fastapi

from api.middleware import LoggerMiddleware
from api.routers.pricing import router as pricing_router
from models.db.price_trie import TriePriceDB
from services.price_loader import TextPriceListLoader
from config.manager import settings


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI(title="Value Checker Service", version="1.0.0")
    app.add_middleware(LoggerMiddleware)
    app.include_router(pricing_router)

    @app.on_event("startup")
    async def on_startup():
        async def load_db_from_file(price_loader_service, db_url):
            if settings.USE_DB_FAST_LOAD:
                await price_loader_service.load_from_file_fast(db_url)
            else:
                await price_loader_service.load_from_file(db_url)

        async def get_db_file_loc():
            if settings.USE_TEST_DB:
                return settings.TEST_PRICING_DB
            else:
                return settings.PROD_PRICING_DB
            
        price_loader_service = TextPriceListLoader(batch_size=100000, db=TriePriceDB())
        await load_db_from_file(price_loader_service, await get_db_file_loc())

    return app


app = create_app()
