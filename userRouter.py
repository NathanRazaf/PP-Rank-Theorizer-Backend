from fastapi import APIRouter
from ossapi import Ossapi, UserLookupKey, ScoreType, GameMode
from dotenv import load_dotenv
import os

load_dotenv()
main_data_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))
@main_data_router.get("/{name}")
async def login(name: str):
    user = api.user(name, key=UserLookupKey.USERNAME)

    scores = api.user_scores(user.id, type=ScoreType.BEST, mode=GameMode.OSU, limit=100)

    returned_scores = []
    for score in scores:
        mods = [mod.acronym for mod in score.mods]
        formatted_score = {
            "accuracy": score.accuracy * 100,
            "score": score.total_score,
            "beatmap_id": score.beatmap.id,
            "mods": mods,
            "pp": score.pp,
            "max_combo": score.max_combo,
            "grade": score.rank.name,
        }
        returned_scores.append(formatted_score)

    response = {
        "username": user.username,
        "avatar_url": user.avatar_url,
        "cover_url": user.cover_url,
        "country_code": user.country_code,
        "pp": user.statistics.pp,
        "global_rank": user.statistics.global_rank,
        "country_rank": user.statistics.country_rank,
        "accuracy": user.statistics.hit_accuracy,
        "level": user.statistics.level.current,
        "levelProgress": user.statistics.level.progress,
        "scores": returned_scores
    }
    return response