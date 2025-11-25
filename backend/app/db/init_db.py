import json
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.db.session import Base, engine, SessionLocal
from backend.app.db.models import Tenant, User, UserTenantRole
from backend.app.core.security import hash_password

def load_tenants_from_config():
    cfg = Path("config/tenants.json")
    data = json.loads(cfg.read_text(encoding="utf-8"))
    return data.get("tenants", [])

def seed(db: Session):
    for t in load_tenants_from_config():
        if not db.get(Tenant, t["id"]):
            db.add(Tenant(id=t["id"], display_name=t["id"], policy_id=t["policy_id"], active=t.get("active", True)))
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin", email="admin@example.com", password_hash=hash_password("admin"))
        db.add(admin)
        db.flush()
        for t in db.query(Tenant).filter(Tenant.active == True).all():  # noqa: E712
            db.add(UserTenantRole(user_id=admin.id, tenant_id=t.id, role="admin"))

def main():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
        db.commit()

if __name__ == "__main__":
    main()