# models.py
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# --- Database configuration ---
# This creates mailroom.db in the current folder (SQLite file)
DATABASE_URL = "sqlite:///mailroom.db"

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

Base = declarative_base()


# --- Models matching your assignment tables ---

class Resident(Base):
    """
    Maps to the Residents table from the assignment:

    CREATE TABLE Residents (
        id INT,
        full_name VARCHAR(30) NOT NULL,
        email VARCHAR(30) NOT NULL,
        unit_number INT NOT NULL,
        PRIMARY KEY (id)
    );
    """
    __tablename__ = "Residents"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(30), nullable=False)
    email = Column(String(30), nullable=False)
    unit_number = Column(Integer, nullable=False)

    # One resident -> many packages
    packages = relationship("Package", back_populates="resident")

    def __repr__(self):
        return f"<Resident {self.full_name} (Unit {self.unit_number})>"


class StaffUser(Base):
    """
    Maps to the StaffLogin table:

    CREATE TABLE StaffLogin (
        staff_username VARCHAR(30),
        staff_password VARCHAR(30) NOT NULL,
        PRIMARY KEY (staff_username)
    );
    """
    __tablename__ = "StaffLogin"

    staff_username = Column(String(30), primary_key=True)
    staff_password = Column(String(30), nullable=False)

    def __repr__(self):
        return f"<StaffUser {self.staff_username}>"


class Package(Base):
    """
    New Packages table for mailroom operations.
    Stores Pending, UNKNOWN, PickedUp, Returned packages.
    """
    __tablename__ = "Packages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # For known residents: link to Residents.id
    # For UNKNOWN packages: resident_id will be NULL
    resident_id = Column(Integer, ForeignKey("Residents.id"), nullable=True)

    label_name = Column(String(50), nullable=False)      # Name printed on the package
    carrier = Column(String(20), nullable=False)         # e.g., 'FedEx', 'UPS', 'USPS'
    tracking_number = Column(String(50), nullable=True)

    delivery_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    pickup_date = Column(DateTime, nullable=True)

    # Status to support Pending area, UNKNOWN area, history
    status = Column(String(20), nullable=False, default="PENDING")
    # Allowed values (by convention): 'PENDING', 'UNKNOWN', 'PICKED_UP', 'RETURNED'

    # Back reference to Resident object
    resident = relationship("Resident", back_populates="packages")

    def __repr__(self):
        return f"<Package id={self.id} status={self.status}>"


def init_db():
    """
    Create all tables in the SQLite database.
    - Residents
    - StaffLogin
    - Packages
    """
    Base.metadata.create_all(bind=engine)
