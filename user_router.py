from fastapi import APIRouter, HTTPException
from ossapi import Ossapi, UserLookupKey, ScoreType, GameMode
from dotenv import load_dotenv
import os

load_dotenv()
main_data_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))

@main_data_router.get("/{name}")
async def get_user_info(name: str):
    try:
        user = api.user(name, key=UserLookupKey.USERNAME)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"User '{name}' not found",
                "error": str(e)
            }
        )

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
    try:
        user = api.user(name, key=UserLookupKey.USERNAME)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"User '{name}' not found",
                "error": str(e)
            }
        )

    try:
        scores = api.user_scores(user.id, type=ScoreType.BEST, mode=GameMode.OSU, limit=100)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Could not retrieve scores for user '{name}'",
                "error": str(e)
            }
        )

    if not scores:
        return []

    returned_scores = []
    for score in scores:
        mods = [mod.acronym for mod in score.mods]
        formatted_score = {
            "is_true_score": True,
            "accuracy": score.accuracy * 100,
            "total_hits": (score.statistics.great or 0) +
                          (score.statistics.good or 0) +
                          (score.statistics.ok or 0) +
                          (score.statistics.meh or 0) +
                          (score.statistics.perfect or 0) +
                          (score.statistics.small_tick_hit or 0) +
                          (score.statistics.large_tick_hit or 0) +
                          (score.statistics.slider_tail_hit or 0),
            "score": score.total_score,
            "id": score.id,
            "beatmap_url": score.beatmap.url,
            "title": score.beatmapset.title,
            "artist": score.beatmapset.artist,
            "version": score.beatmap.version,
            "date": score.ended_at,
            "mods": mods,
            "pp": score.pp,
            "max_combo": score.max_combo,
            "grade": score.rank.name,
            "weight": score.weight.percentage,
            "actual_pp": score.weight.pp,
        }
        returned_scores.append(formatted_score)

    return returned_scores