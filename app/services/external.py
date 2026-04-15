import httpx
from fastapi import HTTPException

async def fetch_gender(name: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"https://api.genderize.io?name={name}", timeout=5.0)
            data = res.json()
        except Exception:
            raise HTTPException(status_code=502, detail={"status": "error", "message": "Genderize returned an invalid response"})

    if not data.get("gender") or data.get("count", 0) == 0:
        raise HTTPException(status_code=502, detail={"status": "error", "message": "Genderize returned an invalid response"})

    return {
        "gender": data["gender"],
        "gender_probability": data["probability"],
        "sample_size": data["count"],
    }

async def fetch_age(name: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"https://api.agify.io?name={name}", timeout=5.0)
            data = res.json()
        except Exception:
            raise HTTPException(status_code=502, detail={"status": "error", "message": "Agify returned an invalid response"})

    if data.get("age") is None:
        raise HTTPException(status_code=502, detail={"status": "error", "message": "Agify returned an invalid response"})

    age = data["age"]
    if age <= 12:
        age_group = "child"
    elif age <= 19:
        age_group = "teenager"
    elif age <= 59:
        age_group = "adult"
    else:
        age_group = "senior"

    return {"age": age, "age_group": age_group}

async def fetch_nationality(name: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"https://api.nationalize.io?name={name}", timeout=5.0)
            data = res.json()
        except Exception:
            raise HTTPException(status_code=502, detail={"status": "error", "message": "Nationalize returned an invalid response"})

    countries = data.get("country", [])
    if not countries:
        raise HTTPException(status_code=502, detail={"status": "error", "message": "Nationalize returned an invalid response"})

    top = max(countries, key=lambda x: x["probability"])

    return {
        "country_id": top["country_id"],
        "country_probability": top["probability"],
    }