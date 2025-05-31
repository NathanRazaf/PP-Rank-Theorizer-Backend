from fastapi import APIRouter, HTTPException
from ossapi import Ossapi, UserLookupKey, ScoreType, GameMode
from dotenv import load_dotenv
import os

load_dotenv()
user_data_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))


async def get_user_info(name: str, game_mode: GameMode = GameMode.OSU):
    try:
        user = api.user(name, key=UserLookupKey.USERNAME, mode=game_mode)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"User '{name}' not found",
                "error": str(e)
            }
        )


    response = {
        "id": user.id,
        "username": user.username,
        "preferred_mode": user.playmode,
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
        "rank_history": user.rank_history.data if user.rank_history else [],
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


async def get_scores(name: str, game_mode: GameMode = GameMode.OSU):
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
        scores = api.user_scores(user.id, type=ScoreType.BEST, mode=game_mode, limit=100)
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



@user_data_router.get("/info/{name}/osu")
async def get_user_info_osu(name: str):
    return await get_user_info(name, GameMode.OSU)

@user_data_router.get("/info/{name}/taiko")
async def get_user_info_taiko(name: str):
    return await get_user_info(name, GameMode.TAIKO)

@user_data_router.get("/info/{name}/catch")
async def get_user_info_fruits(name: str):
    return await get_user_info(name, GameMode.CATCH)

@user_data_router.get("/info/{name}/mania")
async def get_user_info_mania(name: str):
    return await get_user_info(name, GameMode.MANIA)



@user_data_router.get("/scores/{name}/osu")
async def get_user_scores_osu(name: str):
    return await get_scores(name, GameMode.OSU)

@user_data_router.get("/scores/{name}/taiko")
async def get_user_scores_taiko(name: str):
    return await get_scores(name, GameMode.TAIKO)

@user_data_router.get("/scores/{name}/catch")
async def get_user_scores_fruits(name: str):
    return await get_scores(name, GameMode.CATCH)

@user_data_router.get("/scores/{name}/mania")
async def get_user_scores_mania(name: str):
    return await get_scores(name, GameMode.MANIA)
