from app.core.database import SessionLocal
from app.models.staff import Staff


def seed_default_staff() -> None:
    session = SessionLocal()
    try:
        existing = session.query(Staff).filter(Staff.name == "Ezekiel Adebola").first()
        if existing is None:
            staff = Staff(name="Ezekiel Adebola", location="ABUJA")
            session.add(staff)
            session.commit()
    finally:
        session.close()
