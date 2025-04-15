import os
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from ossapi import Ossapi
from pydantic import BaseModel
import httpx

load_dotenv()

score_simulator_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))

# Base models
class UserStats(BaseModel):
    accuracy: float
    ranked_score: int
    total_score: int
    replays_watched: int
    total_hits: int
    maximum_combo: int
    play_count: int

class UserGradeCounts(BaseModel):
    SS: int
    SSH: int
    S: int
    SH: int
    A: int

class UserProfileParams(BaseModel):
    username: str
    avatar_url: str
    cover_url: str
    country_code: str
    country_name: str
    num_medals: int
    play_time: int
    support_level: int
    statistics: UserStats
    rank_history: list[int]
    grade_counts: UserGradeCounts
    pp: float
    global_rank: int
    country_rank: int
    level: int
    level_progress: int

class UserScore(BaseModel):
    is_true_score: bool
    accuracy: float
    score: int
    id: int
    beatmap_url: str
    title: str
    artist: str
    version: str
    date: str
    mods: list[str]
    pp: float
    max_combo: int
    grade: str
    weight: float
    actual_pp: float

class GameMode(str, Enum):
    OSU = "osu"
    TAIKO = "taiko"
    CATCH = "catch"
    MANIA = "mania"

# Mode-specific parameter models
class BaseScoreParams(BaseModel):
    scoreId: Optional[str] = None
    beatmapId: Optional[int] = None
    mods: List[str] = []
    accPercent: Optional[float] = None
    combo: Optional[int] = None
    nmiss: Optional[int] = None

class OsuScoreParams(BaseScoreParams):
    n50: Optional[int] = None
    n100: Optional[int] = None
    sliderTailMiss: Optional[int] = 0
    largeTickMiss: Optional[int] = 0

class TaikoScoreParams(BaseScoreParams):
    n100: Optional[int] = None

class CatchScoreParams(BaseScoreParams):
    droplets: Optional[int] = None
    tinyDroplets: Optional[int] = None

class ManiaScoreParams(BaseScoreParams):
    n300: Optional[int] = None
    n100: Optional[int] = None
    n50: Optional[int] = None

# Constants
HELPER_URL = "https://that-game-tools-api-production.up.railway.app"
API_KEY = os.getenv("TOOLS_API_KEY")

# Helper function to simulate a score
async def simulate_score(game_mode: GameMode, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic function to simulate a score for any game mode
    """
    try:
        async with httpx.AsyncClient() as client:
            if "scoreId" in params and params["scoreId"]:
                # If scoreId is provided, just forward it to the calculator
                response = await client.post(
                    f"{HELPER_URL}/simulate/new_score/{game_mode.value}",
                    json={"scoreId": params["scoreId"]},
                    headers={"x-api-key": API_KEY}
                )
            else:
                # Filter out None values
                calculator_params = {k: v for k, v in params.items() if v is not None}
                response = await client.post(
                    f"{HELPER_URL}/simulate/new_score/{game_mode.value}",
                    json=calculator_params,
                    headers={"x-api-key": API_KEY}
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Calculator API error: {response.text}"
                )

            r = response.json()

            # Get beatmap info
            beatmap = api.beatmap(r["beatmap_id"])

            # Construct the response
            returned_score = {
                "is_true_score": False,
                "accuracy": r["accuracy"],
                "score": 0,
                "id": random.randint(-9999999, -1000000),
                "beatmap_url": f'https://osu.ppy.sh/beatmaps/{r["beatmap_id"]}',
                "title": beatmap.beatmapset().title,
                "artist": beatmap.beatmapset().artist,
                "version": beatmap.version,
                "date": datetime.now(timezone.utc),
                "mods": params.get("mods", []),
                "pp": r["pp"],
                "max_combo": r["combo"],
                "grade": r["grade"],
            }

            return returned_score

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with calculator API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

# Endpoints for each game mode
@score_simulator_router.post("/simulate/osu")
async def simulate_osu_score(params: OsuScoreParams):
    """Simulate an osu! standard score"""
    return await simulate_score(
        GameMode.OSU,
        params.model_dump(exclude_none=True)
    )

@score_simulator_router.post("/simulate/taiko")
async def simulate_taiko_score(params: TaikoScoreParams):
    """Simulate a taiko score"""
    return await simulate_score(
        GameMode.TAIKO,
        params.model_dump(exclude_none=True)
    )

@score_simulator_router.post("/simulate/catch")
async def simulate_catch_score(params: CatchScoreParams):
    """Simulate a catch (ctb) score"""
    return await simulate_score(
        GameMode.CATCH,
        params.model_dump(exclude_none=True)
    )

@score_simulator_router.post("/simulate/mania")
async def simulate_mania_score(params: ManiaScoreParams):
    """Simulate a mania score"""
    return await simulate_score(
        GameMode.MANIA,
        params.model_dump(exclude_none=True)
    )