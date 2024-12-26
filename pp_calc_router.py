import os
import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
import httpx
from typing import Optional

from ossapi import Ossapi
from pydantic import BaseModel

pp_data_router = APIRouter()

calculator_url = "http://osu-tools-calculator-api.org"

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))

class ScoreParams(BaseModel):
    scoreId: Optional[str] = None
    beatmapId: Optional[int] = None
    mods: list[str] = []
    accPercent: Optional[float] = None
    n50: Optional[int] = None
    n100: Optional[int] = None
    combo: Optional[int] = None
    nmiss: Optional[int] = None
    sliderTailMiss: Optional[int] = 0
    largeTickMiss: Optional[int] = 0


@pp_data_router.post("/simulate")
async def simulate_score(params: ScoreParams):
    try:
        async with httpx.AsyncClient() as client:
            if params.scoreId:
                # If scoreId is provided, just forward it to the calculator
                response = await client.post(
                    f"{calculator_url}/calculate",
                    json={"scoreId": params.scoreId}
                )
            else:
                # Forward all other parameters
                calculator_params = {
                    "beatmapId": params.beatmapId,
                    "mods": params.mods,
                    "accPercent": params.accPercent,
                    "n50": params.n50,
                    "n100": params.n100,
                    "combo": params.combo,
                    "nmiss": params.nmiss,
                    "sliderTailMiss": params.sliderTailMiss,
                    "largeTickMiss": params.largeTickMiss
                }
                response = await client.post(
                    f"{calculator_url}/calculate",
                    json=calculator_params
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Calculator API error: {response.text}"
                )

            r = response.json()

            beatmap = api.beatmap(params.beatmapId)

            returned_score = {
                "is_true_score": False,
                "accuracy": r["accuracy"],
                "score": 0,
                "id": random.randint(0, 1000000),
                "beatmap_url": f'https://osu.ppy.sh/beatmaps/{params.beatmapId}',
                "title": beatmap.beatmapset().title,
                "artist": beatmap.beatmapset().artist,
                "version": beatmap.version,
                "date": datetime.now(timezone.utc),
                "mods": params.mods,
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


@pp_data_router.get("/pp-for-rank")
async def get_pp_for_rank(rank: int, mode: Optional[str] = "osu"):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{calculator_url}/pp-for-rank",
                params={"rank": rank, "mode": mode}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Calculator API error: {response.text}"
                )

            return response.json()

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

@pp_data_router.get("/rank-from-pp")
async def get_rank_from_pp(pp: float, mode: Optional[str] = "osu"):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{calculator_url}/rank-from-pp",
                params={"pp": pp, "mode": mode}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Calculator API error: {response.text}"
                )

            return response.json()

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