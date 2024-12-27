import os

from fastapi import APIRouter, HTTPException
from ossapi import Ossapi
from pydantic import BaseModel
import httpx

from pp_calc_router import get_rank_from_pp

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


@score_simulator_router.post("/update")
async def new_score(params: FullUserParams):
    try:
        # Copy the user profile and scores
        profile = params.profile.model_copy()
        scores = [score.model_copy() for score in params.scores]
        new_score_copy = params.new_score

        # Sort scores by pp in descending order (highest pp first)
        scores.sort(key=lambda x: x.pp, reverse=True)

        # Check if score is worth enough pp to be in top 100
        if len(scores) >= 100 and new_score_copy.pp <= scores[99].pp:
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
                break
        else:
            # If no existing score found, add the new score at the right index
            index = 0
            for i, score in enumerate(scores):
                if score.pp < new_score_copy.pp:
                    index = i
                    break
            scores.insert(index, new_score_copy)

        # Truncate the scores list to 100 scores
        scores = scores[:100]

        # Recalculate the weight and actual pp for all scores
        for i, score in enumerate(scores):
            score.weight = 0.95 ** i
            score.actual_pp = score.pp * score.weight
            score.weight *= 100

        # New accuracy
        rate = 0.951
        acc = 0
        div = 0
        for i, score in enumerate(scores):
            acc += score.accuracy * (rate ** i)
            div += rate ** i
        acc /= div
        profile.statistics.accuracy = acc

        # Update stats based on whether we're replacing a score or adding a new one
        if replaced_score:
            # Subtract old score's stats before adding new ones
            profile.statistics.total_hits -= replaced_score.max_combo
            # Decrement the grade count for the old score
            if replaced_score.grade == "SS":
                profile.grade_counts.SS -= 1
            elif replaced_score.grade == "SSH":
                profile.grade_counts.SSH -= 1
            elif replaced_score.grade == "S":
                profile.grade_counts.S -= 1
            elif replaced_score.grade == "SH":
                profile.grade_counts.SH -= 1
            elif replaced_score.grade == "A":
                profile.grade_counts.A -= 1
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

        # New pp
        profile.pp = sum(score.actual_pp for score in scores)

        # New global rank
        rank_json = await get_rank_from_pp(profile.pp)
        rank = rank_json["rank"]
        profile.global_rank = rank
        profile.rank_history[len(profile.rank_history) - 1] = rank

        # New country rank
        profile.country_rank = 0 # As the proof it's not a real user page

        return {
            "profile": profile,
            "scores": scores
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )