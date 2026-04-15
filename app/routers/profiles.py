from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileListItem
from app.services.external import fetch_gender, fetch_age, fetch_nationality
from typing import Optional
import uuid_utils as uuid
from datetime import timezone

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("", status_code=201)
async def create_profile(body: ProfileCreate, db: Session = Depends(get_db)):
    name = body.name.strip().lower()

    if not name:
        raise HTTPException(status_code=400, detail={"status": "error", "message": "Missing or empty name"})

    # Check if profile already exists
    existing = db.query(Profile).filter(Profile.name == name).first()
    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": ProfileResponse.model_validate(existing)
        }

    # Fetch from all 3 APIs concurrently
    import asyncio
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


@router.get("")
def get_profiles(
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Profile)

    if gender:
        query = query.filter(Profile.gender == gender.lower())
    if country_id:
        query = query.filter(Profile.country_id == country_id.upper())
    if age_group:
        query = query.filter(Profile.age_group == age_group.lower())

    profiles = query.all()

    return {
        "status": "success",
        "count": len(profiles),
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