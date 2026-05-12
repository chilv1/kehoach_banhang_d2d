"""Seed demo project — kế hoạch xây nhà nhỏ, để test CPM scheduler."""
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import Base, SessionLocal, engine
from app.models import (
    Project, Task, TaskConstraint, TaskDependency, LinkType,
    Resource, ResourceType, Assignment,
)


def seed_demo() -> int:
    """Tạo project demo 'Xây nhà' với 8 task + dependencies + resources."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Xoá cũ nếu có
        db.query(Project).filter(Project.name == "Demo — Xây nhà").delete()
        db.commit()

        # Project
        p = Project(
            name="Demo — Xây nhà",
            description="Project mẫu để test CPM engine",
            start_date=datetime(2026, 5, 4, 8, 0),  # Mon
        )
        db.add(p)
        db.flush()

        # Resources
        r_kts = Resource(project_id=p.id, name="Kiến trúc sư",
                         initials="KTS", type=ResourceType.WORK,
                         max_units=1.0, standard_rate=50.0)
        r_xd = Resource(project_id=p.id, name="Đội xây dựng",
                        initials="XD", type=ResourceType.WORK,
                        max_units=3.0, standard_rate=20.0)
        r_dn = Resource(project_id=p.id, name="Đội điện nước",
                        initials="DN", type=ResourceType.WORK,
                        max_units=2.0, standard_rate=25.0)
        r_son = Resource(project_id=p.id, name="Thợ sơn",
                         initials="ST", type=ResourceType.WORK,
                         max_units=2.0, standard_rate=18.0)
        db.add_all([r_kts, r_xd, r_dn, r_son])
        db.flush()

        # Tasks (8h = 1 ngày làm việc)
        t1 = Task(project_id=p.id, name="Thiết kế",
                  duration_hours=40, sort_order=1, outline_level=1)
        t2 = Task(project_id=p.id, name="Xin phép xây dựng",
                  duration_hours=80, sort_order=2, outline_level=1)
        t3 = Task(project_id=p.id, name="Đào móng",
                  duration_hours=24, sort_order=3, outline_level=1)
        t4 = Task(project_id=p.id, name="Đổ bê tông móng",
                  duration_hours=16, sort_order=4, outline_level=1)
        t5 = Task(project_id=p.id, name="Xây tường",
                  duration_hours=120, sort_order=5, outline_level=1)
        t6 = Task(project_id=p.id, name="Lắp điện nước",
                  duration_hours=56, sort_order=6, outline_level=1)
        t7 = Task(project_id=p.id, name="Sơn nội thất",
                  duration_hours=40, sort_order=7, outline_level=1)
        t8 = Task(project_id=p.id, name="Bàn giao", is_milestone=True,
                  duration_hours=0, sort_order=8, outline_level=1)
        db.add_all([t1, t2, t3, t4, t5, t6, t7, t8])
        db.flush()

        # Dependencies
        # 1 → 2 (FS): xong thiết kế mới xin phép
        # 1 → 3 (FS): xong thiết kế mới đào móng (parallel với 2)
        # 2 → 4 (FS): xong xin phép mới đổ bê tông
        # 3 → 4 (FS): xong đào móng mới đổ bê tông
        # 4 → 5 (FS lag 8h): đổ xong, chờ 8h khô rồi xây
        # 5 → 6 (SS lag 40h): xây được 5 ngày bắt đầu điện nước
        # 5 → 7 (FS): xong tường mới sơn
        # 6 → 8 (FS), 7 → 8 (FS)
        deps = [
            (t1, t2, LinkType.FS, 0),
            (t1, t3, LinkType.FS, 0),
            (t2, t4, LinkType.FS, 0),
            (t3, t4, LinkType.FS, 0),
            (t4, t5, LinkType.FS, 8),
            (t5, t6, LinkType.SS, 40),
            (t5, t7, LinkType.FS, 0),
            (t6, t8, LinkType.FS, 0),
            (t7, t8, LinkType.FS, 0),
        ]
        for pre, suc, lt, lag in deps:
            db.add(TaskDependency(
                predecessor_id=pre.id, successor_id=suc.id,
                link_type=lt, lag_hours=lag,
            ))

        # Assignments
        assigns = [
            (t1.id, r_kts.id, 1.0, 40),
            (t2.id, r_kts.id, 0.5, 40),
            (t3.id, r_xd.id, 2.0, 48),
            (t4.id, r_xd.id, 3.0, 48),
            (t5.id, r_xd.id, 3.0, 360),
            (t6.id, r_dn.id, 2.0, 112),
            (t7.id, r_son.id, 2.0, 80),
        ]
        for tid, rid, units, hours in assigns:
            db.add(Assignment(task_id=tid, resource_id=rid,
                              units=units, work_hours=hours))

        db.commit()
        return p.id
    finally:
        db.close()


if __name__ == "__main__":
    pid = seed_demo()
    print(f"Created demo project id={pid}")
