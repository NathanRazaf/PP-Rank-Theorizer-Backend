from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from routers.search_router import search_router
from routers.user_data_router import user_data_router
from routers.pp_calc_router import pp_calc_router
from routers.score_simulator_router import score_simulator_router
from fastapi.middleware.cors import CORSMiddleware

from routers.user_update_router import user_update_router

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(exc: RequestValidationError):
    errors = exc.errors()
    print("Validation errors:", errors)
    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://osu-pp-theorizer.netlify.app",
        "http://localhost:5173",
                   ],  # Only allow the frontend and the React local server to access the API
    allow_credentials=True, # Allow cookies
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
)
app.include_router(user_data_router, prefix="/user")
app.include_router(user_update_router, prefix="/update")
app.include_router(pp_calc_router, prefix="/convert")
app.include_router(score_simulator_router, prefix="/score")
app.include_router(search_router, prefix="/search")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
