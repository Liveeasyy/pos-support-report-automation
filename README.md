# POS Support Report Automation System

Initial backend foundation for the POS Support Report Automation System.

## Stack
- FastAPI
- SQLAlchemy
- PyMySQL
- Alembic

## Setup
1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set your MySQL connection values.
4. Run `alembic upgrade head` to apply the initial migration.
