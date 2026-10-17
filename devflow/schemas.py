"""Pydantic models. These are the 'explicit tool schemas' the resume mentions."""
from typing import List, Literal
from pydantic import BaseModel, Field

Priority = Literal["High", "Medium", "Low"]
TicketType = Literal["Story", "Task", "Bug", "Test"]


class UserStory(BaseModel):
    as_a: str
    i_want: str
    so_that: str


class Requirements(BaseModel):
    feature_title: str
    summary: str
    detected_capabilities: List[str] = Field(default_factory=list)
    user_stories: List[UserStory]
    functional_requirements: List[str]
    non_functional_requirements: List[str]
    acceptance_criteria: List[str]
    assumptions: List[str]
    open_questions: List[str]


class Ticket(BaseModel):
    key: str
    type: TicketType
    title: str
    description: str
    priority: Priority
    story_points: int = Field(ge=1, le=13)
    labels: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)


class TicketBundle(BaseModel):
    project_key: str
    feature_title: str
    tickets: List[Ticket]
    total_story_points: int
    saved_to: str


class Endpoint(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path: str
    purpose: str
    auth_required: bool = True


class DataModel(BaseModel):
    name: str
    fields: List[str]


class BackendPlan(BaseModel):
    feature_title: str
    endpoints: List[Endpoint]
    data_models: List[DataModel]
    implementation_tasks: List[str]
    risks: List[str]


class ChecklistItem(BaseModel):
    category: str
    item: str
    required: bool = True


class ReleaseChecklist(BaseModel):
    feature_title: str
    risk_level: Literal["low", "medium", "high"]
    items: List[ChecklistItem]
    rollback_plan: List[str]


class StepResult(BaseModel):
    step: str
    status: Literal["ok", "failed"]
    error: str | None = None


class WorkflowResult(BaseModel):
    feature_request: str
    steps: List[StepResult]
    requirements: Requirements | None = None
    tickets: TicketBundle | None = None
    backend_plan: BackendPlan | None = None
    release_checklist: ReleaseChecklist | None = None
    all_steps_ok: bool
