"""Pydantic schemas — project / task / dependency / resource / assignment / baseline."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskConstraint, TaskType
from app.models.dependency import LinkType
from app.models.resource import ResourceType


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    start_date: datetime
    calendar_id: int | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    status_date: datetime | None = None
    calendar_id: int | None = None


class ProjectOut(ORMBase):
    id: int
    name: str
    description: str | None
    start_date: datetime
    finish_date: datetime | None
    status_date: datetime | None
    calendar_id: int | None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    project_id: int
    name: str
    parent_id: int | None = None
    duration_hours: float = 8.0
    is_milestone: bool = False
    is_summary: bool = False
    task_type: TaskType = TaskType.FIXED_UNITS
    constraint_type: TaskConstraint = TaskConstraint.ASAP
    constraint_date: datetime | None = None
    deadline: datetime | None = None
    priority: int = 500
    notes: str | None = None
    sort_order: int = 0
    outline_level: int = 1
    wbs: str | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    duration_hours: float | None = None
    is_milestone: bool | None = None
    is_summary: bool | None = None
    task_type: TaskType | None = None
    constraint_type: TaskConstraint | None = None
    constraint_date: datetime | None = None
    deadline: datetime | None = None
    priority: int | None = None
    percent_complete: float | None = Field(default=None, ge=0, le=100)
    actual_start: datetime | None = None
    actual_finish: datetime | None = None
    notes: str | None = None
    sort_order: int | None = None
    wbs: str | None = None


class TaskOut(ORMBase):
    id: int
    project_id: int
    parent_id: int | None
    wbs: str | None
    outline_level: int
    sort_order: int
    name: str
    notes: str | None
    duration_hours: float
    is_milestone: bool
    is_summary: bool
    task_type: TaskType
    start_date: datetime | None
    finish_date: datetime | None
    early_start: datetime | None
    early_finish: datetime | None
    late_start: datetime | None
    late_finish: datetime | None
    total_slack_hours: float
    free_slack_hours: float
    is_critical: bool
    constraint_type: TaskConstraint
    constraint_date: datetime | None
    deadline: datetime | None
    percent_complete: float
    actual_start: datetime | None
    actual_finish: datetime | None
    actual_work_hours: float
    actual_cost: float
    fixed_cost: float
    priority: int
    calendar_id: int | None


class DependencyCreate(BaseModel):
    predecessor_id: int
    successor_id: int
    link_type: LinkType = LinkType.FS
    lag_hours: float = 0.0


class DependencyUpdate(BaseModel):
    link_type: LinkType | None = None
    lag_hours: float | None = None


class DependencyOut(ORMBase):
    id: int
    predecessor_id: int
    successor_id: int
    link_type: LinkType
    lag_hours: float


class ResourceCreate(BaseModel):
    project_id: int
    name: str
    initials: str | None = None
    type: ResourceType = ResourceType.WORK
    group: str | None = None
    email: str | None = None
    max_units: float = 1.0
    standard_rate: float = 0.0
    overtime_rate: float = 0.0
    cost_per_use: float = 0.0
    calendar_id: int | None = None


class ResourceUpdate(BaseModel):
    name: str | None = None
    initials: str | None = None
    type: ResourceType | None = None
    group: str | None = None
    email: str | None = None
    max_units: float | None = None
    standard_rate: float | None = None
    overtime_rate: float | None = None
    cost_per_use: float | None = None
    calendar_id: int | None = None


class ResourceOut(ORMBase):
    id: int
    project_id: int
    name: str
    initials: str | None
    type: ResourceType
    group: str | None
    email: str | None
    max_units: float
    standard_rate: float
    overtime_rate: float
    cost_per_use: float
    calendar_id: int | None


class AssignmentCreate(BaseModel):
    task_id: int
    resource_id: int
    units: float = 1.0
    work_hours: float = 0.0


class AssignmentUpdate(BaseModel):
    units: float | None = None
    work_hours: float | None = None
    actual_work_hours: float | None = None
    cost: float | None = None


class AssignmentOut(ORMBase):
    id: int
    task_id: int
    resource_id: int
    units: float
    work_hours: float
    actual_work_hours: float
    cost: float


class BaselineCreate(BaseModel):
    project_id: int
    number: int = Field(ge=0, le=10)
    name: str | None = None


class BaselineOut(ORMBase):
    id: int
    project_id: int
    number: int
    name: str
    snapshot_date: datetime


class ScheduleResult(BaseModel):
    n_tasks: int
    n_critical: int
    project_start: str | None = None
    project_finish: str | None = None
