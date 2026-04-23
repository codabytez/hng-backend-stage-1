import json
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import engine, Base
from app.models.profile import Profile
import uuid_utils as uuid
from datetime import datetime, timezone

load_dotenv()

Base.metadata.create_all(bind=engine)

with open("seed_profiles.json", "r") as f:
    data = json.load(f)

profiles = data["profiles"]

with Session(engine) as db:
    inserted = 0
    skipped = 0

    for p in profiles:
        existing = db.query(Profile).filter(Profile.name == p["name"]).first()
        if existing:
            skipped += 1
            continue

        profile = Profile(
            id=str(uuid.uuid7()),
            name=p["name"],
            gender=p.get("gender"),
            gender_probability=p.get("gender_probability"),
            sample_size=None,
            age=p.get("age"),
            age_group=p.get("age_group"),
            country_id=p.get("country_id"),
            country_name=p.get("country_name"),
            country_probability=p.get("country_probability"),
            created_at=datetime.now(timezone.utc),
        )
        db.add(profile)
        inserted += 1

    db.commit()
    print(f"Done — inserted: {inserted}, skipped: {skipped}")