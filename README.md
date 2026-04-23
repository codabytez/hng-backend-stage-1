# HNG Backend Stage 2 — Intelligence Query Engine

Advanced filtering, sorting, pagination, and natural language search over 2026 demographic profiles.

## Live URL

<https://hng-backend-stage-1-production-6999.up.railway.app>

## Tech Stack

- Python 3.14
- FastAPI
- PostgreSQL
- SQLAlchemy
- Railway

## Endpoints

| Method | Endpoint             | Description                                        |
| ------ | -------------------- | -------------------------------------------------- |
| POST   | /api/profiles        | Create a profile                                   |
| GET    | /api/profiles        | Get all profiles with filters, sorting, pagination |
| GET    | /api/profiles/search | Natural language search                            |
| GET    | /api/profiles/{id}   | Get single profile                                 |
| DELETE | /api/profiles/{id}   | Delete a profile                                   |

## GET /api/profiles — Query Parameters

| Parameter               | Type   | Description                             |
| ----------------------- | ------ | --------------------------------------- |
| gender                  | string | male or female                          |
| age_group               | string | child, teenager, adult, senior          |
| country_id              | string | ISO 2-letter code (NG, KE, etc.)        |
| min_age                 | int    | Minimum age                             |
| max_age                 | int    | Maximum age                             |
| min_gender_probability  | float  | Minimum gender confidence               |
| min_country_probability | float  | Minimum country confidence              |
| sort_by                 | string | age, created_at, gender_probability     |
| order                   | string | asc or desc (default: asc)              |
| page                    | int    | Page number (default: 1)                |
| limit                   | int    | Results per page (default: 10, max: 50) |

## Natural Language Search — /api/profiles/search?q=

### How it works

Rule-based keyword parsing using regex. No AI or LLMs involved. The query string is lowercased, then matched against patterns in this order:

1. Gender keywords
2. Age group keywords
3. Relative age expressions (above/below/over/under)
4. Special age ranges (young = 16–24)
5. Country extraction (from [country name])

### Supported Keywords

| Keyword                          | Maps to                |
| -------------------------------- | ---------------------- |
| male, males                      | gender=male            |
| female, females, women, woman    | gender=female          |
| child, children, kids            | age_group=child        |
| teenager, teenagers, teens       | age_group=teenager     |
| adult, adults                    | age_group=adult        |
| senior, seniors, elderly         | age_group=senior       |
| young                            | min_age=16, max_age=24 |
| above X, over X, older than X    | min_age=X              |
| below X, under X, younger than X | max_age=X              |
| from [country]                   | country_id=ISO code    |

### Example Queries

    GET /api/profiles/search?q=young males from nigeria
    → gender=male, min_age=16, max_age=24, country_id=NG

    GET /api/profiles/search?q=females above 30
    → gender=female, min_age=30

    GET /api/profiles/search?q=adult males from kenya
    → gender=male, age_group=adult, country_id=KE

    GET /api/profiles/search?q=teenagers from ghana
    → age_group=teenager, country_id=GH

### Supported Countries

Nigeria (NG), Ghana (GH), Kenya (KE), Ethiopia (ET), Tanzania (TZ), Uganda (UG),
South Africa (ZA), Cameroon (CM), Angola (AO), Mozambique (MZ), Madagascar (MG),
Mali (ML), Sudan (SD), Senegal (SN), Zimbabwe (ZW), Zambia (ZM), Guinea (GN),
Benin (BJ), Togo (TG), Niger (NE), Chad (TD), Rwanda (RW), Burundi (BI),
Somalia (SO), Egypt (EG), Morocco (MA), Algeria (DZ), Tunisia (TN), Libya (LY),
Cape Verde (CV), Congo (CG), United States (US), United Kingdom (GB), India (IN),
China (CN), Brazil (BR), France (FR), Germany (DE), Italy (IT), Spain (ES), Portugal (PT)

### Limitations

- Only supports a fixed list of country names — unmapped countries won't be recognized
- "young" is a parsing alias for ages 16–24, not a stored age group
- Cannot handle complex boolean logic (e.g. "males OR females")
- Cannot handle negations (e.g. "not from nigeria")
- Cannot combine two countries in one query
- Ambiguous queries with no recognizable keywords return: `{"status": "error", "message": "Unable to interpret query"}`
- Country names must match exactly (e.g. "united states" works, "america" does not)

## Running Locally

    git clone https://github.com/codabytez/hng-backend-stage-1.git
    cd hng-backend-stage-1
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload

## Seeding the Database

    python3 seed.py

Re-running seed will skip existing records — no duplicates created.

## Environment Variables

    DATABASE_URL=your_postgresql_url
