"""Pure functions that turn a feature request into structured artifacts."""
import json
import re
from pathlib import Path
from typing import List

from .capabilities import BASE_CHECKLIST, CAPABILITIES, CORE, HIGH_RISK_EXTRA
from .schemas import (BackendPlan, ChecklistItem, DataModel, Endpoint, ReleaseChecklist,
                      Requirements, Ticket, TicketBundle, UserStory)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def detect_capabilities(request: str) -> List[str]:
    text = f" {request.lower()} "
    return [name for name, cap in CAPABILITIES.items()
            if any(k in text for k in cap["keywords"])]


def make_title(request: str) -> str:
    first = re.split(r"[.\n!?]", request.strip())[0].strip()
    if len(first) > 50:  # cut at a word boundary, not mid-word
        first = first[:50].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return first[:1].upper() + first[1:]


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "feature"


def _parts(caps: List[str]) -> List[dict]:
    parts = [CAPABILITIES[c] for c in caps]
    return parts if parts else [CORE]


def build_requirements(request: str, target_users: str = "end user") -> Requirements:
    caps = detect_capabilities(request)
    parts = _parts(caps)
    stories, functional, nonfunc = [], [], []
    for p in parts:
        who, want, why = p["story"]
        stories.append(UserStory(as_a=who if caps else target_users, i_want=want, so_that=why))
        functional += p["functional"]
        nonfunc += p["non_functional"]
    nonfunc += ["Input validation on all endpoints", "Unit-test coverage for core logic"]
    functional = list(dict.fromkeys(functional))
    nonfunc = list(dict.fromkeys(nonfunc))
    acceptance = [f"GIVEN valid input WHEN the user does: '{f}' THEN it succeeds with a clear confirmation"
                  for f in functional[:4]]
    acceptance.append("GIVEN invalid input WHEN submitted THEN a descriptive error is returned and nothing is saved")
    return Requirements(
        feature_title=make_title(request),
        summary=f"Deliver the following for {target_users}s: {request}",
        detected_capabilities=caps or ["core_crud (no specific capability detected)"],
        user_stories=stories,
        functional_requirements=functional,
        non_functional_requirements=nonfunc,
        acceptance_criteria=acceptance,
        assumptions=["An existing backend and database are available",
                     "Standard web/mobile client consumes the API",
                     f"Primary user type: {target_users}"],
        open_questions=["Which roles/permissions apply?",
                        "Are there expected traffic or data-volume numbers?",
                        "Any deadlines or compliance constraints?"],
    )


def build_tickets(request: str, project_key: str, save: bool = True) -> TicketBundle:
    reqs = build_requirements(request)
    parts = _parts(detect_capabilities(request))
    tickets: List[Ticket] = []

    def add(type_, title, desc, prio, pts, labels, ac=None):
        tickets.append(Ticket(key=f"{project_key}-{len(tickets) + 1}", type=type_, title=title,
                              description=desc, priority=prio, story_points=pts,
                              labels=labels, acceptance_criteria=ac or []))

    add("Story", f"{reqs.feature_title}: user-facing feature",
        reqs.summary, "High", 8, ["feature"], reqs.acceptance_criteria)
    add("Task", "Design API contract and data model",
        "Finalise endpoints, request/response schemas and DB tables.", "High", 3, ["backend", "design"])
    for p in parts:
        for t in p["tasks"]:
            add("Task", t, f"Part of: {reqs.feature_title}", "Medium", 3, ["backend"])
    add("Test", "Write unit and integration tests",
        "Cover happy paths, validation errors and failure modes.", "High", 3, ["testing"])
    add("Task", "Update documentation and release notes",
        "API docs, README and changelog.", "Low", 1, ["docs"])
    path = ""
    bundle = TicketBundle(project_key=project_key, feature_title=reqs.feature_title, tickets=tickets,
                          total_story_points=sum(t.story_points for t in tickets), saved_to=path)
    if save:
        DATA_DIR.mkdir(exist_ok=True)
        file = DATA_DIR / f"tickets_{project_key}_{slugify(reqs.feature_title)}.json"
        bundle.saved_to = str(file)
        file.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")
    return bundle


def build_backend_plan(request: str) -> BackendPlan:
    parts = _parts(detect_capabilities(request))
    endpoints, models, tasks, risks = [], [], [], []
    for p in parts:
        endpoints += [Endpoint(method=m, path=path, purpose=pur, auth_required=a)
                      for m, path, pur, a in p["endpoints"]]
        models += [DataModel(name=n, fields=f) for n, f in p["models"]]
        tasks += p["tasks"]
        risks += p["risks"]
    return BackendPlan(
        feature_title=make_title(request),
        endpoints=endpoints,
        data_models=models,
        implementation_tasks=list(dict.fromkeys(
            ["Create database migrations"] + tasks +
            ["Add request validation and error handling", "Write tests", "Add structured logging"])),
        risks=list(dict.fromkeys(risks)),
    )


def build_checklist(request: str, risk_level: str = "medium") -> ReleaseChecklist:
    items = list(BASE_CHECKLIST)
    for p in _parts(detect_capabilities(request)):
        items += p["checks"]
    if risk_level in ("medium", "high"):
        items.append(("Rollout", "Rollback plan reviewed by the team"))
    if risk_level == "high":
        items += HIGH_RISK_EXTRA
    rollback = ["Disable the feature flag or redeploy the previous version",
                "Run the down-migration only if data is not lost",
                "Notify stakeholders and open an incident note"]
    return ReleaseChecklist(
        feature_title=make_title(request), risk_level=risk_level,
        items=[ChecklistItem(category=c, item=i) for c, i in items],
        rollback_plan=rollback)


def list_saved(directory: Path = DATA_DIR) -> List[str]:
    return sorted(p.name for p in directory.glob("tickets_*.json")) if directory.exists() else []


def read_saved(name: str, directory: Path = DATA_DIR) -> dict:
    if not re.fullmatch(r"tickets_[A-Za-z0-9_\-]+\.json", name):  # blocks path traversal
        raise FileNotFoundError("Invalid file name.")
    file = directory / name
    if not file.exists():
        raise FileNotFoundError(f"No saved ticket file named '{name}'.")
    return json.loads(file.read_text(encoding="utf-8"))
