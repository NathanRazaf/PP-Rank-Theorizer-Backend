from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from search_router import search_router
from user_data_router import user_data_router
from pp_calc_router import pp_calc_router
from score_simulator_router import score_simulator_router
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_data_router, prefix="/user")
app.include_router(pp_calc_router, prefix="/convert")
app.include_router(score_simulator_router, prefix="/score")
app.include_router(search_router, prefix="/search")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
