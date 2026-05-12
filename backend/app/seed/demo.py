"""Seed demo project — kế hoạch xây nhà nhỏ, để test CPM scheduler."""
from datetime import datetime

from sqlalchemy.orm import Session
from app.db.session import Base, SessionLocal, engine
from app.models import (
    Project, Task, TaskConstraint, TaskDependency, LinkType,
    Resource, ResourceType, Assignment,
)


def seed_demo() -> int:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        db.query(Project).filter(Project.name == "Demo — Xây nhà").delete()
        db.commit()
        p = Project(name="Demo — Xây nhà", description="Project mẫu CPM",
                    start_date=datetime(2026, 5, 4, 8, 0))
        db.add(p); db.flush()
        r_kts = Resource(project_id=p.id, name="Kiến trúc sư", initials="KTS",
                         type=ResourceType.WORK, max_units=1.0, standard_rate=50.0)
        r_xd = Resource(project_id=p.id, name="Đội xây dựng", initials="XD",
                        type=ResourceType.WORK, max_units=3.0, standard_rate=20.0)
        r_dn = Resource(project_id=p.id, name="Đội điện nước", initials="DN",
                        type=ResourceType.WORK, max_units=2.0, standard_rate=25.0)
        r_son = Resource(project_id=p.id, name="Thợ sơn", initials="ST",
                         type=ResourceType.WORK, max_units=2.0, standard_rate=18.0)
        db.add_all([r_kts, r_xd, r_dn, r_son]); db.flush()
        t1 = Task(project_id=p.id, name="Thiết kế", duration_hours=40, sort_order=1)
        t2 = Task(project_id=p.id, name="Xin phép xây dựng", duration_hours=80, sort_order=2)
        t3 = Task(project_id=p.id, name="Đào móng", duration_hours=24, sort_order=3)
        t4 = Task(project_id=p.id, name="Đổ bê tông móng", duration_hours=16, sort_order=4)
        t5 = Task(project_id=p.id, name="Xây tường", duration_hours=120, sort_order=5)
        t6 = Task(project_id=p.id, name="Lắp điện nước", duration_hours=56, sort_order=6)
        t7 = Task(project_id=p.id, name="Sơn nội thất", duration_hours=40, sort_order=7)
        t8 = Task(project_id=p.id, name="Bàn giao", is_milestone=True, duration_hours=0, sort_order=8)
        db.add_all([t1, t2, t3, t4, t5, t6, t7, t8]); db.flush()
        deps = [
            (t1, t2, LinkType.FS, 0), (t1, t3, LinkType.FS, 0),
            (t2, t4, LinkType.FS, 0), (t3, t4, LinkType.FS, 0),
            (t4, t5, LinkType.FS, 8), (t5, t6, LinkType.SS, 40),
            (t5, t7, LinkType.FS, 0), (t6, t8, LinkType.FS, 0),
            (t7, t8, LinkType.FS, 0),
        ]
        for pre, suc, lt, lag in deps:
            db.add(TaskDependency(predecessor_id=pre.id, successor_id=suc.id,
                                   link_type=lt, lag_hours=lag))
        assigns = [
            (t1.id, r_kts.id, 1.0, 40), (t2.id, r_kts.id, 0.5, 40),
            (t3.id, r_xd.id, 2.0, 48), (t4.id, r_xd.id, 3.0, 48),
            (t5.id, r_xd.id, 3.0, 360), (t6.id, r_dn.id, 2.0, 112),
            (t7.id, r_son.id, 2.0, 80),
        ]
        for tid, rid, units, hours in assigns:
            db.add(Assignment(task_id=tid, resource_id=rid, units=units, work_hours=hours))
        db.commit()
        return p.id
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Created demo project id={seed_demo()}")
