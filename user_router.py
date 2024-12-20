from fastapi import APIRouter
from ossapi import Ossapi, UserLookupKey, ScoreType, GameMode
from dotenv import load_dotenv
import os

load_dotenv()
main_data_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))
@main_data_router.get("/{name}")
async def get_user_info(name: str):
    user = api.user(name, key=UserLookupKey.USERNAME)
    response = {
        "username": user.username,
        "avatar_url": user.avatar_url,
        "cover_url": user.cover_url,
        "country_code": user.country_code,
        "country_name": user.country.name,
        "num_medals": len(user.user_achievements),
        "play_time": user.statistics.play_time,
        "support_level": user.support_level,
        "statistics": {
            "accuracy": user.statistics.hit_accuracy,
            "ranked_score": user.statistics.ranked_score,
            "total_score": user.statistics.total_score,
            "replays_watched": user.statistics.replays_watched_by_others,
            "total_hits": user.statistics.total_hits,
            "maximum_combo": user.statistics.maximum_combo,
            "play_count": user.statistics.play_count,
        },
        "rank_history": user.rank_history.data,
        "grade_counts": {
            "SS": user.statistics.grade_counts.ss,
            "SSH": user.statistics.grade_counts.ssh,
            "S": user.statistics.grade_counts.s,
            "SH": user.statistics.grade_counts.sh,
            "A": user.statistics.grade_counts.a,
        },
        "pp": user.statistics.pp,
        "global_rank": user.statistics.global_rank,
        "country_rank": user.statistics.country_rank,
        "level": user.statistics.level.current,
        "level_progress": user.statistics.level.progress,
    }
    return response

@main_data_router.get("/{name}/scores")
async def get_scores(name: str):
    user = api.user(name, key=UserLookupKey.USERNAME)
    scores = api.user_scores(user.id, type=ScoreType.BEST, mode=GameMode.OSU, limit=100)

    returned_scores = []
    for score in scores:
        mods = [mod.acronym for mod in score.mods]
        formatted_score = {
            "accuracy": score.accuracy * 100,
            "score": score.total_score,
            "beatmap_url": score.beatmap.url,
            "title": score.beatmapset.title_unicode,
            "artist": score.beatmapset.artist_unicode,
            "version": score.beatmap.version,
            "mods": mods,
            "pp": score.pp,
            "max_combo": score.max_combo,
            "grade": score.rank.name,
        }
        returned_scores.append(formatted_score)

    return returned_scores