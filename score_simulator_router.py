import math
import os
import random
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from ossapi import Ossapi
from pydantic import BaseModel
import httpx

load_dotenv()

from pp_calc_router import convert_pp_to_rank

score_simulator_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))


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

class FullUserParams(BaseModel):
    profile: UserProfileParams
    scores: list[UserScore]
    new_score: UserScore

class FullUserParamsDel(BaseModel):
    profile: UserProfileParams
    scores: list[UserScore]
    score_id: int

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

HELPER_URL = "https://that-game-tools-api-production.up.railway.app"
API_KEY = os.getenv("TOOLS_API_KEY")

@score_simulator_router.post("/simulate")
async def simulate_score(params: ScoreParams):
    try:
        async with httpx.AsyncClient() as client:
            if params.scoreId:
                # If scoreId is provided, just forward it to the calculator
                response = await client.post(
                    f"{HELPER_URL}/simulate/new_score",
                    json={"scoreId": params.scoreId},
                    headers={"x-api-key": API_KEY}
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
                calculator_params = {k: v for k, v in calculator_params.items() if v is not None}
                print(calculator_params)
                response = await client.post(
                    f"{HELPER_URL}/simulate/new_score",
                    json=calculator_params,
                    headers={"x-api-key": API_KEY}
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Calculator API error: {response.text}"
                )

            r = response.json()

            beatmap = api.beatmap(r["beatmap_id"])

            returned_score = {
                "is_true_score": False,
                "accuracy": r["accuracy"],
                "score": 0,
                "id": random.randint(1000000, 9999999),
                "beatmap_url": f'https://osu.ppy.sh/beatmaps/{r["beatmap_id"]}',
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



@score_simulator_router.post("/new")
async def new_score(params: FullUserParams):
    try:
        # Copy the user profile and scores
        profile = params.profile.model_copy()
        scores = [score.model_copy() for score in params.scores]
        new_score_copy = params.new_score

        # Sort scores by weight (descending)
        scores.sort(key=lambda x: x.weight, reverse=True)

        # Check if score is worth enough pp to be in top 100
        if len(scores) >= 100 and new_score_copy.pp <= scores[99].pp:
            # If not, return the profile and scores unchanged
            return {
                "profile": profile,
                "scores": scores
            }


        # Flag to track if we're replacing an existing score
        replaced_score = None

        # Check if we're replacing an existing score
        for i, score in enumerate(scores):
            if score.beatmap_url == new_score_copy.beatmap_url:
                if score.pp < new_score_copy.pp:
                    # Store the old score before replacing
                    replaced_score = score
                    # Replace the score
                    scores[i] = new_score_copy
                    # Put the replaced score at the end of the list
                    scores.append(replaced_score)
                break
        else:
            # If no existing score found, add the new score at the right index
            index = 0
            for i, score in enumerate(scores):
                if score.pp < new_score_copy.pp:
                    index = i
                    break
            scores.insert(index, new_score_copy)

        await update_profile_and_scores(profile, scores)

        # Update specific stats based on whether we're replacing a score or adding a new one
        if replaced_score:
            # Subtract old score's stats
            remove_score_grade_from_profile(profile, replaced_score)
        else:
            # If it's a new score, increment play count
            profile.statistics.play_count += 1

        # Add new score's stats
        profile.statistics.ranked_score += new_score_copy.score
        profile.statistics.total_hits += new_score_copy.max_combo
        profile.statistics.maximum_combo = max(profile.statistics.maximum_combo, new_score_copy.max_combo)

        # Increment grade count for new score
        if new_score_copy.grade == "SS":
            profile.grade_counts.SS += 1
        elif new_score_copy.grade == "SSH":
            profile.grade_counts.SSH += 1
        elif new_score_copy.grade == "S":
            profile.grade_counts.S += 1
        elif new_score_copy.grade == "SH":
            profile.grade_counts.SH += 1
        elif new_score_copy.grade == "A":
            profile.grade_counts.A += 1

        return {
            "profile": profile,
            "scores": scores
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@score_simulator_router.delete("/new")
async def delete_score(params: FullUserParamsDel):
    try:
        # Copy the user profile and scores
        profile = params.profile.model_copy()
        scores = [score.model_copy() for score in params.scores]

        score_to_delete = None
        for i, score in enumerate(scores):
            if (not score.is_true_score) & (score.id == params.score_id):
                score_to_delete = score
                scores.pop(i)
                break

        await update_profile_and_scores(profile, scores)

        # Subtract old score's stats
        if score_to_delete:
            profile.statistics.total_hits -= score_to_delete.max_combo
            profile.statistics.ranked_score -= score_to_delete.score
            remove_score_grade_from_profile(profile, score_to_delete)
            profile.statistics.play_count -= 1

        return {
            "profile": profile,
            "scores": scores
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

def remove_score_grade_from_profile(profile, score):
    if score.grade == "SS":
        profile.grade_counts.SS -= 1
    elif score.grade == "SSH":
        profile.grade_counts.SSH -= 1
    elif score.grade == "S":
        profile.grade_counts.S -= 1
    elif score.grade == "SH":
        profile.grade_counts.SH -= 1
    elif score.grade == "A":
        profile.grade_counts.A -= 1

async def update_profile_and_scores(profile, scores):
    # Sort by pp first
    scores.sort(key=lambda x: x.pp, reverse=True)

    # Track seen beatmap_urls and calculate weights
    seen_beatmaps = set()
    rate = 0.95
    acc = 0
    factor = 1
    i = 0  # Keep track of actual position for weight calculation

    for score in scores:
        if score.beatmap_url in seen_beatmaps:
            # Duplicate score - set weight to 0
            score.weight = 0
            score.actual_pp = 0
        else:
            # New unique score - calculate weight normally
            score.weight = 0.95 ** i
            score.actual_pp = score.pp * score.weight
            score.weight *= 100
            acc += score.accuracy/100 * factor
            factor *= rate
            seen_beatmaps.add(score.beatmap_url)
            i += 1  # Only increment position counter for unique scores

    # Sort again by weight (descending)
    scores.sort(key=lambda x: x.weight, reverse=True)

    # Normalize accuracy (formula taken directly from osu! codebase)
    acc *= 100 / (20 * (1 - math.pow(rate, min(len(scores), 100))))

    # Handle floating point precision edge cases
    clamp = lambda x, y, z: max(y, min(z, x))
    acc = clamp(acc, 0, 100)

    profile.statistics.accuracy = acc

    # Bonus pp rewarded for setting many scores on different ranked beatmaps (TODO: Calculate this properly)
    bonus_pp = 416
    # New pp
    profile.pp = sum(score.actual_pp for score in scores) + bonus_pp

    # New global rank
    rank_json = await convert_pp_to_rank(profile.pp)
    rank = rank_json["rank"]
    profile.global_rank = rank
    profile.rank_history[len(profile.rank_history) - 1] = rank

    # New country rank
    profile.country_rank = 0 # As the proof it's not a real user page