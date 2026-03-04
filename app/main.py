from fastapi.responses import RedirectResponse
from app.api.routes import router as api_router
from app.core.database import close_db, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Mongo on startup so first request is fast.
    await init_db()
    try:
        yield
    finally:
        await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Estate AI - API",
        description="REST API for real estate analysis request and history CRUD.",
        version="1.0.0",
        lifespan=lifespan
    )
    
    app.include_router(api_router, prefix="/api")

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
