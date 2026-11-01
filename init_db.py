# init_db.py
from models import init_db, SessionLocal, Resident, StaffUser

def seed_data():
    session = SessionLocal()
    try:
        # ---- Seed Residents table ----
        if session.query(Resident).count() == 0:
            residents = [
                Resident(
                    id=1,
                    full_name="Kittie Mousdall",
                    email="ecnwokike1@buffs.wtamu.edu",
                    unit_number=101,
                ),
                Resident(
                    id=2,
                    full_name="Claudette Rait",
                    email="ecnwokike1@buffs.wtamu.edu",
                    unit_number=102,
                ),
                Resident(
                    id=3,
                    full_name="Test Resident Three",
                    email="ecnwokike1@buffs.wtamu.edu",
                    unit_number=103,
                ),
            ]
            session.add_all(residents)

        # ---- Seed StaffLogin table ----
        if session.query(StaffUser).count() == 0:
            staff_users = [
                StaffUser(staff_username="alice", staff_password="alice123"),
                StaffUser(staff_username="bob", staff_password="bob123"),
            ]
            session.add_all(staff_users)

        session.commit()
        print("Sample residents and staff users inserted.")
    finally:
        session.close()


if __name__ == "__main__":
    init_db()   # creates Residents, StaffLogin, Packages tables
    seed_data()
    print("Database initialized and seeded.")
