"""Map endpoints — geo data for Leaflet/Mapbox."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.sales_planner.models import CampaignTask, Location
from app.sales_planner.services.constraint_solver import haversine_km

router = APIRouter(prefix="/map", tags=["sales-map"])


@router.get("/locations")
def map_locations(db: Session = Depends(get_db)):
    locs = (
        db.query(Location)
        .filter(Location.latitud.is_not(None))
        .filter(Location.longitud.is_not(None))
        .all()
    )
    return [
        {
            "id": l.id, "code": l.code,
            "lat": float(l.latitud), "lng": float(l.longitud),
            "distrito": l.distrito, "tipo_df_cp": l.tipo_df_cp,
            "prioridad": l.prioridad,
            "bc": l.business_center.code if l.business_center else None,
            "br": l.branch.code if l.branch else None,
            "horario_traffico": l.horario_traffico,
        }
        for l in locs
    ]


@router.post("/route-optimize")
def route_optimize(payload: dict, db: Session = Depends(get_db)):
    """Cluster nearby locations greedily by 30km radius.

    Body: { "location_ids": [int, ...], "max_per_day": 5 }
    """
    ids = payload.get("location_ids", [])
    max_per_day = int(payload.get("max_per_day", 5))
    locs = db.query(Location).filter(Location.id.in_(ids)).all()
    points = [
        (l.id, float(l.latitud), float(l.longitud))
        for l in locs if l.latitud and l.longitud
    ]
    clusters: list[list[int]] = []
    used: set[int] = set()
    for i, (id_a, lat_a, lng_a) in enumerate(points):
        if id_a in used:
            continue
        cluster = [id_a]
        used.add(id_a)
        for id_b, lat_b, lng_b in points[i + 1:]:
            if id_b in used or len(cluster) >= max_per_day:
                continue
            if haversine_km((lat_a, lng_a), (lat_b, lng_b)) <= 30.0:
                cluster.append(id_b)
                used.add(id_b)
        clusters.append(cluster)
    return {"clusters": clusters}
