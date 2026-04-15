# HNG Backend Stage 1 — Data Persistence & API Design

A REST API that accepts a name, calls three external APIs, classifies the result, stores it in PostgreSQL, and exposes endpoints to manage profiles.

## Live URL

[https://hng-backend-stage-1-production-6999.up.railway.app](https://hng-backend-stage-1-production-6999.up.railway.app)

## Tech Stack

- Python 3.14
- FastAPI
- PostgreSQL
- SQLAlchemy
- Railway (hosting + database)

## Endpoints

| Method | Endpoint           | Description                   |
| ------ | ------------------ | ----------------------------- |
| POST   | /api/profiles      | Create a profile              |
| GET    | /api/profiles      | Get all profiles (filterable) |
| GET    | /api/profiles/{id} | Get single profile            |
| DELETE | /api/profiles/{id} | Delete a profile              |

## Filters

GET /api/profiles?gender=male

GET /api/profiles?country_id=NG

GET /api/profiles?age_group=adult

## Running Locally

    git clone https://github.com/codabytez/hng-backend-stage-1.git
    cd hng-backend-stage-1
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload

## Environment Variables

    DATABASE_URL=your_postgresql_url
