from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileListItem
from app.services.external import fetch_gender, fetch_age, fetch_nationality
from typing import Optional
import uuid_utils as uuid
import asyncio
import re

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

COUNTRY_NAME_TO_ID = {
    "nigeria": "NG", "ghana": "GH", "kenya": "KE", "ethiopia": "ET",
    "tanzania": "TZ", "uganda": "UG", "south africa": "ZA", "cameroon": "CM",
    "angola": "AO", "mozambique": "MZ", "madagascar": "MG", "mali": "ML",
    "sudan": "SD", "senegal": "SN", "zimbabwe": "ZW", "zambia": "ZM",
    "guinea": "GN", "benin": "BJ", "togo": "TG", "niger": "NE",
    "chad": "TD", "rwanda": "RW", "burundi": "BI", "somalia": "SO",
    "egypt": "EG", "morocco": "MA", "algeria": "DZ", "tunisia": "TN",
    "libya": "LY", "cape verde": "CV", "congo": "CG",
    "united states": "US", "usa": "US", "uk": "GB", "united kingdom": "GB",
    "india": "IN", "china": "CN", "brazil": "BR", "france": "FR",
    "germany": "DE", "italy": "IT", "spain": "ES", "portugal": "PT",
}


def parse_natural_language(q: str) -> dict:
    q = q.lower().strip()
    filters = {}
    matched = False

    # Gender
    if re.search(r'\bmales?\b', q):
        filters["gender"] = "male"
        matched = True
    elif re.search(r'\bfemales?\b', q) or re.search(r'\bwomen\b', q) or re.search(r'\bwoman\b', q):
        filters["gender"] = "female"
        matched = True

    # Age groups
    if re.search(r'\bchildren\b|\bchild\b|\bkids?\b', q):
        filters["age_group"] = "child"
        matched = True
    elif re.search(r'\bteenagers?\b|\bteens?\b', q):
        filters["age_group"] = "teenager"
        matched = True
    elif re.search(r'\badults?\b', q):
        filters["age_group"] = "adult"
        matched = True
    elif re.search(r'\bseniors?\b|\bolderly\b|\bold people\b', q):
        filters["age_group"] = "senior"
        matched = True
    elif re.search(r'\byoung\b', q):
        filters["min_age"] = 16
        filters["max_age"] = 24
        matched = True

    # Min age from "above X" or "over X" or "older than X"
    above_match = re.search(r'\b(?:above|over|older than)\s+(\d+)\b', q)
    if above_match:
        filters["min_age"] = int(above_match.group(1))
        matched = True

    # Max age from "below X" or "under X" or "younger than X"
    below_match = re.search(r'\b(?:below|under|younger than)\s+(\d+)\b', q)
    if below_match:
        filters["max_age"] = int(below_match.group(1))
        matched = True

    # Country
    from_match = re.search(r'\bfrom\s+([a-z\s]+?)(?:\s+(?:above|below|over|under|who|that|and|$))', q)
    if not from_match:
        from_match = re.search(r'\bfrom\s+([a-z\s]+)$', q)
    if from_match:
        country_raw = from_match.group(1).strip()
        country_id = COUNTRY_NAME_TO_ID.get(country_raw)
        if country_id:
            filters["country_id"] = country_id
            matched = True
        else:
            # Try 2-letter code directly
            if len(country_raw) == 2:
                filters["country_id"] = country_raw.upper()
                matched = True

    if not matched:
        return {}

    return filters


@router.post("", status_code=201)
async def create_profile(body: ProfileCreate, db: Session = Depends(get_db)):
    name = body.name.strip().lower()

    if not name:
        raise HTTPException(status_code=400, detail={"status": "error", "message": "Missing or empty name"})

    existing = db.query(Profile).filter(Profile.name == name).first()
    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": ProfileResponse.model_validate(existing)
        }

    gender_data, age_data, nationality_data = await asyncio.gather(
        fetch_gender(name),
        fetch_age(name),
        fetch_nationality(name),
    )

    profile = Profile(
        id=str(uuid.uuid7()),
        name=name,
        **gender_data,
        **age_data,
        **nationality_data,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(profile)
    }


@router.get("/search")
def search_profiles(
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail={"status": "error", "message": "Missing or empty query"})

    filters = parse_natural_language(q)

    if not filters:
        raise HTTPException(status_code=422, detail={"status": "error", "message": "Unable to interpret query"})

    query = db.query(Profile)

    if "gender" in filters:
        query = query.filter(Profile.gender == filters["gender"])
    if "age_group" in filters:
        query = query.filter(Profile.age_group == filters["age_group"])
    if "country_id" in filters:
        query = query.filter(Profile.country_id == filters["country_id"])
    if "min_age" in filters:
        query = query.filter(Profile.age >= filters["min_age"])
    if "max_age" in filters:
        query = query.filter(Profile.age <= filters["max_age"])

    total = query.count()
    profiles = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": [ProfileListItem.model_validate(p) for p in profiles]
    }


@router.get("")
def get_profiles(
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    country_id: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    sort_by: Optional[str] = Query(default=None, pattern="^(age|created_at|gender_probability)$"),
    order: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Profile)

    if gender:
        query = query.filter(Profile.gender == gender.lower())
    if age_group:
        query = query.filter(Profile.age_group == age_group.lower())
    if country_id:
        query = query.filter(Profile.country_id == country_id.upper())
    if min_age is not None:
        query = query.filter(Profile.age >= min_age)
    if max_age is not None:
        query = query.filter(Profile.age <= max_age)
    if min_gender_probability is not None:
        query = query.filter(Profile.gender_probability >= min_gender_probability)
    if min_country_probability is not None:
        query = query.filter(Profile.country_probability >= min_country_probability)

    # Sorting
    sort_column = {
        "age": Profile.age,
        "created_at": Profile.created_at,
        "gender_probability": Profile.gender_probability,
    }.get(sort_by or "", Profile.created_at)

    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    total = query.count()
    profiles = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        "data": [ProfileListItem.model_validate(p) for p in profiles]
    }


@router.get("/{profile_id}")
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Profile not found"})

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(profile)
    }


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "Profile not found"})

    db.delete(profile)
    db.commit()
    return Response(status_code=204)