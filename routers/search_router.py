import os
from ossapi import Ossapi
from fastapi import APIRouter
from dotenv import load_dotenv

load_dotenv()
search_router = APIRouter()

api = Ossapi(int(os.getenv("OSU_CLIENT_ID")), os.getenv("OSU_CLIENT_SECRET"))

@search_router.get("/user")
async def get_user_info(query: str):
    try:
        users = api.search(query, mode="user")
        users = users.users.data
        users_data = []
        for user in users:
            users_data.append({
                "username": user.username,
                "avatar_url": user.avatar_url,
                "osu_id": user.id,
                "country_code": user.country_code,
            })

        return users_data

    except Exception as e:
        return {
            "error": str(e)
        }


@search_router.get("/beatmap")
async def get_beatmaps(query: str, mode: int = 0):
    try:
        beatmapsets = api.search_beatmapsets(query, mode=mode, category="ranked")
        beatmapsets = beatmapsets.beatmapsets
        beatmapsets_data = []
        for beatmapset in beatmapsets:
            data = {
                "artist": beatmapset.artist,
                "title": beatmapset.title,
                "creator": beatmapset.creator,
                "cover": beatmapset.covers.list,
                "beatmapset_id": beatmapset.id,
                "beatmaps": []
            }
            for beatmap in beatmapset.beatmaps:
                data["beatmaps"].append({
                    "beatmap_id": beatmap.id,
                    "version": beatmap.version,
                    "stars": beatmap.difficulty_rating,
                })
            beatmapsets_data.append(data)

        return beatmapsets_data
    except Exception as e:
        return {
            "error": str(e)
        }

