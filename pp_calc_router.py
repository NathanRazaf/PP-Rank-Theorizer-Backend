import os

from fastapi import APIRouter, HTTPException
import httpx
from typing import Optional

from ossapi import Ossapi
from dotenv import load_dotenv

load_dotenv()
pp_calc_router = APIRouter()

HELPER_URL = "https://that-game-tools-api-production.up.railway.app"
API_KEY = os.getenv("TOOLS_API_KEY")

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))

@pp_calc_router.get("/to-pp")
async def convert_rank_to_pp(rank: int, mode: Optional[int] = 0):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HELPER_URL}/convert/to-pp",
                params={"rank": rank, "mode": mode},
                headers={"x-api-key": API_KEY}
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

@pp_calc_router.get("/to-rank")
async def convert_pp_to_rank(pp: float, mode: Optional[int] = 0):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HELPER_URL}/convert/to-rank",
                params={"pp": pp, "mode": mode},
                headers={"x-api-key": API_KEY}
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