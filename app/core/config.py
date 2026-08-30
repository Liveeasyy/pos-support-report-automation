import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", "3306"))
        self.DB_NAME = os.getenv("DB_NAME", "pos_support_db")
        self.DB_USER = os.getenv("DB_USER", "root")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "")
        self.TESSERACT_CMD = os.getenv(
            "TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
        self.TESSERACT_TIMEOUT_SECONDS = int(os.getenv("TESSERACT_TIMEOUT_SECONDS", "30"))
        self.MICROSOFT_FORMS_SUBMISSION_URL = os.getenv(
            "MICROSOFT_FORMS_SUBMISSION_URL", ""
        )
        self.MICROSOFT_FORMS_SUBMISSION_TIMEOUT_SECONDS = int(
            os.getenv("MICROSOFT_FORMS_SUBMISSION_TIMEOUT_SECONDS", "30")
        )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
