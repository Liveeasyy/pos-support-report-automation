import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        s
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
