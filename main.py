import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from ossapi import Ossapi, ScoreType, GameMode
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

@app.get("/osu-test-test-test/{name}")
async def osu_test(name: str):
    api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))

    user = api.user(name)

    user_scores = api.user_scores(user.id, type=ScoreType.BEST, limit=5, mode=GameMode.OSU)

    print(user_scores)

    scores = []

    for score in user_scores:
        scores.append({
            "accuracy": score.beatmap.accuracy,
            "ar": score.beatmap.ar,
            "cs": score.beatmap.cs,
            "drain": score.beatmap.drain,
            "difficulty_rating": score.beatmap.difficulty_rating,
            "score": {
                "accuracy": score.accuracy * 100,
                "score": score.total_score,
            },
            "beatmap": {
                "id": score.beatmap.id,
                "url": score.beatmap.url,
                "cover": score.beatmapset.covers.cover_2x,
                "title": score.beatmapset.title,
                "artist": score.beatmapset.artist,
                "version": score.beatmap.version,
                "bpm": score.beatmap.bpm,
                "playcount": score.beatmap.playcount,
                "pass_percentage": score.beatmap.passcount / score.beatmap.playcount * 100,
            }
        })

    return {
        "user": {
            "name": user.username,
            "id": user.id,
            "avatar_url": user.avatar_url,
            "cover_url": user.cover_url,
            "country_code": user.country_code,
            "country_name": user.country.name,
        },
        "scores": scores,
    }