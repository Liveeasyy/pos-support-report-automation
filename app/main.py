from fastapi import FastAPI

app = FastAPI(title="POS Support Report Automation System")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "pos-support-report-automation"}
