from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import Case, CaseCreate, CaseUpdate
from .store import create_case, initialize, list_cases, metrics, recent_events, update_case


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    yield


app = FastAPI(
    title="CloudAtlas SupportOS",
    description="Evidence-driven incident operations API",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(WEB / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "cloudatlas-supportos"}


@app.get("/api/cases", response_model=list[Case])
def cases() -> list[dict]:
    return list_cases()


@app.post("/api/cases", response_model=Case, status_code=201)
def add_case(payload: CaseCreate) -> dict:
    return create_case(payload)


@app.patch("/api/cases/{case_id}", response_model=Case)
def change_case(case_id: int, payload: CaseUpdate) -> dict:
    case = update_case(case_id, payload)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.get("/api/metrics")
def case_metrics() -> dict:
    return metrics()


@app.get("/api/events")
def events() -> list[dict]:
    return recent_events()

