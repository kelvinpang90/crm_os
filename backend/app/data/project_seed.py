"""Single source of truth for the project tracking demo seed data.

Singapore-style projects. Timestamps are built relative to a given `now` so the
staleness-based alert colors stay meaningful whenever the data is seeded
(on first startup, or on demand via POST /api/projects/seed-demo).
"""
from datetime import datetime, timedelta

# id, customer_name, address, service_type, project_manager, current_step, stale_days
SEED_PROJECTS = [
    {"id": "p-01", "customer_name": "Rajesh Condo", "address": "100 Orchard Rd, #12-04", "service_type": "Roof leak repair", "project_manager": "Alwin Tan", "current_step": 1, "stale_days": 7},
    {"id": "p-02", "customer_name": "Lim Bungalow", "address": "45 Sunset Way", "service_type": "Full re-roofing", "project_manager": "Sarah Lim", "current_step": 4, "stale_days": 6},
    {"id": "p-03", "customer_name": "Wong Semi-D", "address": "23 Bukit Timah Rd", "service_type": "Roof waterproofing", "project_manager": "Jason Ng", "current_step": 2, "stale_days": 4},
    {"id": "p-04", "customer_name": "Ng Terrace", "address": "90 Telok Kurau Rd", "service_type": "Gutter replacement", "project_manager": "Sarah Lim", "current_step": 6, "stale_days": 3},
    {"id": "p-05", "customer_name": "Fadil Residence", "address": "34 Pasir Ris Dr 3", "service_type": "Metal roof install", "project_manager": "Jason Ng", "current_step": 3, "stale_days": 2},
    {"id": "p-06", "customer_name": "Kumar Landed", "address": "8 Serangoon Gdn Way", "service_type": "Full re-roofing", "project_manager": "Alwin Tan", "current_step": 11, "stale_days": 2},
    {"id": "p-07", "customer_name": "Tan Residence", "address": "12 Jln Kayu", "service_type": "Roof waterproofing", "project_manager": "Alwin Tan", "current_step": 8, "stale_days": 1},
    {"id": "p-08", "customer_name": "Goh Landed", "address": "17 Katong Park", "service_type": "Roof leak repair", "project_manager": "Sarah Lim", "current_step": 9, "stale_days": 1},
    {"id": "p-09", "customer_name": "Chua Factory", "address": "5 Tuas Ave 2", "service_type": "Metal roof install", "project_manager": "Jason Ng", "current_step": 8, "stale_days": 0},
    {"id": "p-10", "customer_name": "Smith Villa", "address": "7 Sentosa Cove", "service_type": "Full re-roofing", "project_manager": "Alwin Tan", "current_step": 12, "stale_days": 8},
]

_GAP_DAYS = 2  # days between step transitions


def photos_for(step_no: int) -> list[str]:
    """Steps 3 (inspection) and 10 (completion) carry photo evidence."""
    if step_no == 3:
        return ["inspection-01.jpg", "inspection-02.jpg", "inspection-03.jpg"]
    if step_no == 10:
        return ["completion-01.jpg", "completion-02.jpg"]
    return []


def build_seed_rows(now: datetime | None = None) -> tuple[list[dict], list[dict]]:
    """Return (project_rows, history_rows) as plain dicts, relative to `now`."""
    now = now or datetime.utcnow()
    projects: list[dict] = []
    history: list[dict] = []
    for s in SEED_PROJECTS:
        last_updated = now - timedelta(days=s["stale_days"])
        total = s["current_step"]
        created = last_updated - timedelta(days=(total - 1) * _GAP_DAYS)
        projects.append({
            "id": s["id"],
            "customer_name": s["customer_name"],
            "address": s["address"],
            "service_type": s["service_type"],
            "project_manager": s["project_manager"],
            "current_step": total,
            "created_at": created,
            "updated_at": last_updated,
            "deleted_at": None,
        })
        for step in range(1, total + 1):
            steps_back = total - step
            entered = last_updated - timedelta(days=steps_back * _GAP_DAYS)
            history.append({
                "id": f'{s["id"]}-s{step}',
                "project_id": s["id"],
                "step_no": step,
                "entered_at": entered,
                "updated_by": s["project_manager"],
                "note": None,
                "photos": photos_for(step),
            })
    return projects, history
