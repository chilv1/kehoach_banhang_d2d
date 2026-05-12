"""Phase 7 — Project XML I/O."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO

from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.models.dependency import LinkType, TaskDependency
from app.models.project import Project
from app.models.resource import Resource, ResourceType
from app.models.task import Task, TaskConstraint


def _txt(parent, tag, value):
    el = ET.SubElement(parent, tag)
    el.text = "" if value is None else str(value)
    return el


def export_project_xml(db: Session, project_id: int) -> bytes:
    p = db.get(Project, project_id)
    if not p: raise ValueError(f"Project {project_id}")
    root = ET.Element("Project", attrib={"schemaVersion": "1.0"})
    _txt(root, "Name", p.name)
    _txt(root, "Description", p.description or "")
    _txt(root, "StartDate", p.start_date.isoformat() if p.start_date else "")
    _txt(root, "FinishDate", p.finish_date.isoformat() if p.finish_date else "")
    tasks_el = ET.SubElement(root, "Tasks")
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.sort_order).all()
    for t in tasks:
        te = ET.SubElement(tasks_el, "Task")
        _txt(te, "UID", t.id); _txt(te, "Name", t.name); _txt(te, "WBS", t.wbs or "")
        _txt(te, "OutlineLevel", t.outline_level); _txt(te, "SortOrder", t.sort_order)
        _txt(te, "ParentUID", t.parent_id or -1)
        _txt(te, "DurationHours", t.duration_hours)
        _txt(te, "IsMilestone", int(bool(t.is_milestone)))
        _txt(te, "IsSummary", int(bool(t.is_summary)))
        _txt(te, "TaskType", t.task_type.value if t.task_type else "FIXED_UNITS")
        _txt(te, "Start", t.start_date.isoformat() if t.start_date else "")
        _txt(te, "Finish", t.finish_date.isoformat() if t.finish_date else "")
        _txt(te, "PercentComplete", t.percent_complete)
        _txt(te, "ConstraintType", t.constraint_type.value if t.constraint_type else "ASAP")
        _txt(te, "ConstraintDate", t.constraint_date.isoformat() if t.constraint_date else "")
        _txt(te, "Priority", t.priority); _txt(te, "FixedCost", t.fixed_cost)
        _txt(te, "ActualCost", t.actual_cost); _txt(te, "Notes", t.notes or "")
    res_el = ET.SubElement(root, "Resources")
    resources = db.query(Resource).filter(Resource.project_id == project_id).all()
    for r in resources:
        re_ = ET.SubElement(res_el, "Resource")
        _txt(re_, "UID", r.id); _txt(re_, "Name", r.name)
        _txt(re_, "Type", r.type.value if r.type else "WORK")
        _txt(re_, "MaxUnits", r.max_units); _txt(re_, "StandardRate", r.standard_rate)
        _txt(re_, "OvertimeRate", r.overtime_rate); _txt(re_, "CostPerUse", r.cost_per_use)
    deps_el = ET.SubElement(root, "Predecessors")
    deps = db.query(TaskDependency).filter(TaskDependency.predecessor_id.in_([t.id for t in tasks])).all()
    for d in deps:
        de = ET.SubElement(deps_el, "Predecessor")
        _txt(de, "PredecessorUID", d.predecessor_id); _txt(de, "SuccessorUID", d.successor_id)
        _txt(de, "Type", d.link_type.value); _txt(de, "LagHours", d.lag_hours)
    asg_el = ET.SubElement(root, "Assignments")
    assigns = db.query(Assignment).filter(Assignment.task_id.in_([t.id for t in tasks])).all()
    for a in assigns:
        ae = ET.SubElement(asg_el, "Assignment")
        _txt(ae, "TaskUID", a.task_id); _txt(ae, "ResourceUID", a.resource_id)
        _txt(ae, "Units", a.units); _txt(ae, "WorkHours", a.work_hours)
        _txt(ae, "Cost", a.cost)
    ET.indent(root, space="  ")
    buf = BytesIO()
    ET.ElementTree(root).write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()


def _get(el, tag, default=""):
    child = el.find(tag)
    return child.text if (child is not None and child.text is not None) else default


def _parse_dt(s):
    if not s: return None
    try: return datetime.fromisoformat(s)
    except ValueError: return None


def import_project_xml(db: Session, data: bytes) -> int:
    root = ET.fromstring(data)
    if root.tag != "Project": raise ValueError("XML root phải là <Project>")
    p = Project(name=_get(root, "Name", "Imported"),
                description=_get(root, "Description", "") or None,
                start_date=_parse_dt(_get(root, "StartDate")) or datetime.utcnow())
    db.add(p); db.flush()
    uid_to_id = {}
    tasks_xml = list(root.findall("Tasks/Task"))
    for te in tasks_xml:
        uid = int(_get(te, "UID", "0"))
        t = Task(project_id=p.id, name=_get(te, "Name", "Task"),
                 wbs=_get(te, "WBS") or None,
                 outline_level=int(_get(te, "OutlineLevel", "1")),
                 sort_order=int(_get(te, "SortOrder", "0") or "0"),
                 duration_hours=float(_get(te, "DurationHours", "8") or "8"),
                 is_milestone=bool(int(_get(te, "IsMilestone", "0") or "0")),
                 is_summary=bool(int(_get(te, "IsSummary", "0") or "0")),
                 percent_complete=float(_get(te, "PercentComplete", "0") or "0"),
                 constraint_type=TaskConstraint(_get(te, "ConstraintType", "ASAP") or "ASAP"),
                 constraint_date=_parse_dt(_get(te, "ConstraintDate")),
                 priority=int(_get(te, "Priority", "500") or "500"),
                 fixed_cost=float(_get(te, "FixedCost", "0") or "0"),
                 notes=_get(te, "Notes") or None)
        db.add(t); db.flush(); uid_to_id[uid] = t.id
    for te in tasks_xml:
        uid = int(_get(te, "UID", "0"))
        parent_uid = int(_get(te, "ParentUID", "-1") or "-1")
        if parent_uid > 0 and parent_uid in uid_to_id:
            db.get(Task, uid_to_id[uid]).parent_id = uid_to_id[parent_uid]
    db.flush()
    res_uid_to_id = {}
    for re_ in root.findall("Resources/Resource"):
        uid = int(_get(re_, "UID", "0"))
        r = Resource(project_id=p.id, name=_get(re_, "Name", "Res"),
                     type=ResourceType(_get(re_, "Type", "WORK") or "WORK"),
                     max_units=float(_get(re_, "MaxUnits", "1.0") or "1.0"),
                     standard_rate=float(_get(re_, "StandardRate", "0") or "0"),
                     overtime_rate=float(_get(re_, "OvertimeRate", "0") or "0"),
                     cost_per_use=float(_get(re_, "CostPerUse", "0") or "0"))
        db.add(r); db.flush(); res_uid_to_id[uid] = r.id
    for de in root.findall("Predecessors/Predecessor"):
        pre_uid = int(_get(de, "PredecessorUID", "0"))
        suc_uid = int(_get(de, "SuccessorUID", "0"))
        if pre_uid in uid_to_id and suc_uid in uid_to_id:
            db.add(TaskDependency(predecessor_id=uid_to_id[pre_uid],
                                   successor_id=uid_to_id[suc_uid],
                                   link_type=LinkType(_get(de, "Type", "FS") or "FS"),
                                   lag_hours=float(_get(de, "LagHours", "0") or "0")))
    for ae in root.findall("Assignments/Assignment"):
        tuid = int(_get(ae, "TaskUID", "0"))
        ruid = int(_get(ae, "ResourceUID", "0"))
        if tuid in uid_to_id and ruid in res_uid_to_id:
            db.add(Assignment(task_id=uid_to_id[tuid], resource_id=res_uid_to_id[ruid],
                              units=float(_get(ae, "Units", "1.0") or "1.0"),
                              work_hours=float(_get(ae, "WorkHours", "0") or "0"),
                              cost=float(_get(ae, "Cost", "0") or "0")))
    db.commit()
    return p.id
