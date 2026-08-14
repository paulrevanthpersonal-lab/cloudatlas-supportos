from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import Case, CaseCreate, CaseUpdate, EventCreate
from .store import add_event, create_case, get_case, initialize, list_cases, list_runbooks, metrics, recent_events, update_case


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
def cases(query: str = "", status: str = "", priority: str = "") -> list[dict]:
    return list_cases(query=query, status=status, priority=priority)


@app.get("/api/cases/{case_id}")
def case_detail(case_id: int) -> dict:
    case = get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.post("/api/cases", response_model=Case, status_code=201)
def add_case(payload: CaseCreate) -> dict:
    return create_case(payload)


@app.patch("/api/cases/{case_id}", response_model=Case)
def change_case(case_id: int, payload: CaseUpdate) -> dict:
    case = update_case(case_id, payload)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.post("/api/cases/{case_id}/events", status_code=201)
def create_event(case_id: int, payload: EventCreate) -> dict:
    event = add_event(case_id, payload.stage, payload.detail)
    if event is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return event


@app.get("/api/metrics")
def case_metrics() -> dict:
    return metrics()


@app.get("/api/events")
def events() -> list[dict]:
    return recent_events()


@app.get("/api/runbooks")
def runbooks(query: str = "") -> list[dict]:
    return list_runbooks(query)
