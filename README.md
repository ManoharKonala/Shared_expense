# Shared Expenses Tracker

A production-quality shared expenses web application built for flatmates. This app handles complex scenarios like time-bound memberships, diverse expense splitting algorithms, and robust CSV anomaly detection.

## Tech Stack
- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Auth:** JWT-based access + refresh tokens, bcrypt hashing

## Local Setup

The easiest way to run the entire stack locally is using Docker Compose.

### 1. Using Docker Compose
1. Ensure Docker is installed and running.
2. Run `docker-compose up --build`
3. The backend API will be available at `http://localhost:8000`
4. The frontend will be available at `http://localhost:5173`

### 2. Manual Setup (Without Docker)

**Backend:**
1. `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `alembic upgrade head`
6. Seed the database: `python -m app.seed`
7. Start server: `uvicorn app.main:app --reload`

**Frontend:**
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Database Migrations
Migrations are managed via Alembic.
- To generate a new migration: `alembic revision --autogenerate -m "message"`
- To apply migrations: `alembic upgrade head`
- To rollback one migration: `alembic downgrade -1`

## Test Data
The application comes with a seed script (`backend/app/seed.py`) that sets up a test group ("Flatmates") and the required users:
- Aisha
- Rohan
- Priya
- Meera
- Sam
- Dev
**Passwords:** Their first name in lowercase (e.g., `aisha`, `rohan`).

## Deployment URLs
- **Frontend:** (To be deployed via Vercel/Netlify)
- **Backend API:** (To be deployed via Render/Railway)
- **Database:** (To be hosted on Supabase/Railway)

## Environment Variables
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/shared_expenses
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=shared_expenses

# Security
JWT_SECRET=dev-secret-key-not-for-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Importing the CSV
The project includes a robust anomaly detection pipeline to handle the messy `expenses_export.csv`. 
1. Log in as a user (e.g. `aisha` / `aisha`).
2. Navigate to the Flatmates group.
3. Click "Import CSV" and upload `expenses_export.csv`.
4. Review the detected anomalies (such as missing currency, missing members, and negative amounts).
5. Choose decisions for each anomaly and click "Finalize Import".

## Documentation
- `SCOPE.md`: Project requirements and core constraints.
- `DECISIONS.md`: Architectural decisions and trade-offs.
- `AI_USAGE.md`: Reflection on AI usage and limitations.
