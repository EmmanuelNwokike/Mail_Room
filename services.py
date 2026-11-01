# services.py
from datetime import datetime
from typing import List, Optional

from models import SessionLocal, Resident, StaffUser, Package
from sqlalchemy.orm import Session
from email_service import EmailService
from sqlalchemy.orm import joinedload


class MailroomService:
    """
    Business logic layer for the Mailroom Management system.

    - Talks to the database via SQLAlchemy models (Residents, StaffLogin, Packages)
    - Uses EmailService to send notification emails when a package is delivered
    """

    def __init__(self):
        # Session factory from models.py
        self.Session = SessionLocal
        # Email sender (wraps the sample code from the assignment)
        self.email_service = EmailService()

    # ----------------------------------------------------------------------
    # STAFF LOGIN
    # ----------------------------------------------------------------------
    def login_staff(self, username: str, password: str) -> bool:
        """
        Check if the username/password match a StaffUser in StaffLogin table.
        Returns True for success, False otherwise.
        """
        session = self.Session()
        try:
            user = (
                session.query(StaffUser)
                .filter_by(staff_username=username)
                .first()
            )
            if user is None:
                return False
            return user.staff_password == password
        finally:
            session.close()

    # ----------------------------------------------------------------------
    # RECORD DELIVERED PACKAGE (KNOWN RESIDENT)
    # ----------------------------------------------------------------------
    def record_delivered_package(
        self,
        resident_name: str,
        unit_number: int,
        label_name: str,
        carrier: str,
        tracking_number: Optional[str] = None,
    ):
        """
        Find resident by full name + unit_number.
        If found, create a new Package with status='PENDING'.

        Returns:
            (package, resident_email)

        Raises:
            ValueError: if resident is not found.
        """
        session = self.Session()
        try:
            # Look up the resident
            resident = (
                session.query(Resident)
                .filter(
                    Resident.full_name == resident_name,
                    Resident.unit_number == unit_number,
                )
                .first()
            )

            if resident is None:
                raise ValueError(
                    "Resident not found for the given name and unit number."
                )

            # Copy simple values so we don't depend on ORM objects after session close
            resident_email = resident.email
            resident_full_name = resident.full_name

            # Create the package row
            new_package = Package(
                resident_id=resident.id,
                label_name=label_name,
                carrier=carrier,
                tracking_number=tracking_number,
                delivery_date=datetime.utcnow(),
                status="PENDING",
            )

            session.add(new_package)
            session.commit()
            session.refresh(new_package)
        finally:
            # Close session BEFORE sending email so DB resources are freed
            session.close()

        # Send notification email using plain strings
        self.email_service.send_package_notification(
            to_email=resident_email,
            resident_name=resident_full_name,
        )

        # Return both the package object and the email address
        return new_package, resident_email

    # ----------------------------------------------------------------------
    # RECORD UNKNOWN PACKAGE
    # ----------------------------------------------------------------------
    def record_unknown_package(
        self,
        label_name: str,
        carrier: str,
        tracking_number: Optional[str] = None,
    ) -> Package:
        """
        Record a package for a non-resident (UNKNOWN area).

        resident_id stays NULL, status = 'UNKNOWN'.
        """
        session = self.Session()
        try:
            new_package = Package(
                resident_id=None,
                label_name=label_name,
                carrier=carrier,
                tracking_number=tracking_number,
                delivery_date=datetime.utcnow(),
                status="UNKNOWN",
            )

            session.add(new_package)
            session.commit()
            session.refresh(new_package)
            return new_package
        finally:
            session.close()

    # ----------------------------------------------------------------------
    # MARK PACKAGE AS PICKED UP
    # ----------------------------------------------------------------------
    def mark_package_picked_up(self, package_id: int) -> bool:
        """
        Mark a package as picked up:
          - status = 'PICKED_UP'
          - pickup_date = now

        Returns True if package was found and updated, False otherwise.
        """
        session = self.Session()
        try:
            pkg = session.query(Package).filter_by(id=package_id).first()
            if pkg is None:
                return False

            pkg.status = "PICKED_UP"
            pkg.pickup_date = datetime.utcnow()

            session.commit()
            return True
        finally:
            session.close()

    # ----------------------------------------------------------------------
    # GET PENDING PACKAGES
    # ----------------------------------------------------------------------
    def get_pending_packages(self) -> List[Package]:
        """
        Return a list of all packages whose status = 'PENDING'.

        Uses joinedload to eagerly load the resident relationship so
        templates can safely access pkg.resident after the session is closed.
        """
        session = self.Session()
        try:
            pending = (
                session.query(Package)
                .options(joinedload(Package.resident))
                .filter_by(status="PENDING")
                .all()
            )
            return pending
        finally:
            session.close()

    # ----------------------------------------------------------------------
    # GET UNKNOWN PACKAGES
    # ----------------------------------------------------------------------
    def get_unknown_packages(self) -> List[Package]:
        """
        Return a list of all packages whose status = 'UNKNOWN'.
        """
        session = self.Session()
        try:
            unknown = (
                session.query(Package)
                .options(joinedload(Package.resident))
                .filter_by(status="UNKNOWN")
                .all()
            )
            return unknown
        finally:
            session.close()

    # ----------------------------------------------------------------------
    # GET PACKAGE HISTORY FOR A RESIDENT
    # ----------------------------------------------------------------------
    def get_package_history(
        self,
        resident_name: str,
        unit_number: int,
    ) -> List[Package]:
        """
        Get all packages for the resident identified by full name + unit number.

        Returns an empty list if no resident or no packages are found.
        """
        session = self.Session()
        try:
            resident = (
                session.query(Resident)
                .filter(
                    Resident.full_name == resident_name,
                    Resident.unit_number == unit_number,
                )
                .first()
            )

            if resident is None:
                return []

            history = (
                session.query(Package)
                .options(joinedload(Package.resident))
                .filter(Package.resident_id == resident.id)
                .order_by(Package.delivery_date.desc())
                .all()
            )
            return history
        finally:
            session.close()


# --------------------------------------------------------------------------
# Simple manual test of the business layer
# --------------------------------------------------------------------------
if __name__ == "__main__":
    service = MailroomService()

    print("=== Testing staff login ===")
    print("alice / alice123 ->", service.login_staff("alice", "alice123"))
    print("alice / wrong     ->", service.login_staff("alice", "wrong"))

    print("\n=== Recording a delivered package for 'Kittie Mousdall', unit 101 ===")
    try:
        pkg, email = service.record_delivered_package(
            resident_name="Kittie Mousdall",
            unit_number=101,
            label_name="Kittie Mousdall",
            carrier="FedEx",
            tracking_number="FDX123456",
        )
        print(f"Created package: {pkg} (email sent to {email})")
    except ValueError as e:
        print("Error:", e)

    print("\n=== Current pending packages ===")
    for p in service.get_pending_packages():
        # pkgs have resident eagerly loaded, safe to access p.resident
        print(p, "| Resident:", p.resident.full_name if p.resident else "Unknown")

    print("\n=== Recording an UNKNOWN package ===")
    unknown_pkg = service.record_unknown_package(
        label_name="Unknown Person",
        carrier="UPS",
        tracking_number="UPS999999",
    )
    print("Created unknown package:", unknown_pkg)

    print("\n=== Unknown packages ===")
    for p in service.get_unknown_packages():
        print(p, "| Resident:", p.resident.full_name if p.resident else "Unknown")



