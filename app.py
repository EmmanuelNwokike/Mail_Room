import secrets
import os
# app.py
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash
)
from services import MailroomService

app = Flask(__name__)

# Secret key for sessions (you can change this to any random string)
app.secret_key = os.environ.get("MAILROOM_SECRET_KEY") or secrets.token_hex(32)

# Our business layer
service = MailroomService()


# ---------- HELPER: LOGIN REQUIRED DECORATOR (simple version) ----------

def login_required(view_func):
    """
    Very simple 'login required' wrapper.
    Redirects to /login if no staff user is in session.
    """
    from functools import wraps

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "staff_username" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


# ---------- ROUTES ----------

@app.route("/")
def index():
    """
    If logged in, go to pending packages; otherwise go to login page.
    """
    if "staff_username" in session:
        return redirect(url_for("pending_packages"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Staff login page.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if service.login_staff(username, password):
            session["staff_username"] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for("pending_packages"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """
    Log the staff user out and redirect to login.
    """
    session.pop("staff_username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/packages/pending")
@login_required
def pending_packages():
    """
    Show all PENDING packages.
    """
    packages = service.get_pending_packages()
    return render_template("pending.html", packages=packages)

@app.route("/packages/new", methods=["GET", "POST"])
@login_required
def new_package():
    """
    Form to record a newly delivered package for a known resident.
    Uses resident full name + unit number to find the resident.
    """
    if request.method == "POST":
        resident_name = request.form.get("resident_name", "").strip()
        unit_number = request.form.get("unit_number", "").strip()
        label_name = request.form.get("label_name", "").strip()
        carrier = request.form.get("carrier", "").strip()
        tracking_number = request.form.get("tracking_number", "").strip() or None

        # Basic validation
        if not resident_name or not unit_number or not label_name or not carrier:
            flash("Please fill in all required fields.", "warning")
            return render_template("new_package.html")

        try:
            unit_number_int = int(unit_number)
        except ValueError:
            flash("Unit number must be a number.", "warning")
            return render_template("new_package.html")

        try:

            pkg, resident_email = service.record_delivered_package(
                resident_name=resident_name,
                unit_number=unit_number_int,
                label_name=label_name,
                carrier=carrier,
                tracking_number=tracking_number,
            )
            flash(
                f"Package #{pkg.id} recorded and email sent to {resident_email}.",
                "success",
            )
            return redirect(url_for("pending_packages"))
        except ValueError as e:
            flash(str(e), "danger")


    return render_template("new_package.html")


@app.route("/packages/unknown/new", methods=["GET", "POST"])
@login_required
def new_unknown_package():
    """
    Form to record a package addressed to a non-resident (UNKNOWN area).
    """
    if request.method == "POST":
        label_name = request.form.get("label_name", "").strip()
        carrier = request.form.get("carrier", "").strip()
        tracking_number = request.form.get("tracking_number", "").strip() or None

        if not label_name or not carrier:
            flash("Please fill in all required fields.", "warning")
            return render_template("new_unknown.html")

        pkg = service.record_unknown_package(
            label_name=label_name,
            carrier=carrier,
            tracking_number=tracking_number,
        )
        flash(f"Unknown package #{pkg.id} recorded.", "success")
        return redirect(url_for("pending_packages"))

    return render_template("new_unknown.html")


@app.route("/packages/pickup/<int:package_id>", methods=["POST"])
@login_required
def pickup_package(package_id):
    """
    Mark a package as picked up.
    """
    success = service.mark_package_picked_up(package_id)
    if success:
        flash(f"Package #{package_id} marked as picked up.", "success")
    else:
        flash(f"Package #{package_id} not found.", "danger")
    return redirect(url_for("pending_packages"))


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """
    Search for package history by resident name + unit number.
    """
    packages = []
    resident_name = ""
    unit_number = ""

    if request.method == "POST":
        resident_name = request.form.get("resident_name", "").strip()
        unit_number = request.form.get("unit_number", "").strip()

        if resident_name and unit_number:
            try:
                unit_number_int = int(unit_number)
                packages = service.get_package_history(resident_name, unit_number_int)
                if not packages:
                    flash("No packages found for that resident/unit.", "info")
            except ValueError:
                flash("Unit number must be a number.", "warning")
        else:
            flash("Please enter resident name and unit number.", "warning")

    return render_template(
        "history.html",
        packages=packages,
        resident_name=resident_name,
        unit_number=unit_number,
    )

@app.route("/unknown")
@login_required
def unknown_packages():
    packages = service.get_unknown_packages()
    return render_template("unknown.html", packages=packages)






if __name__ == "__main__":
    # Run the Flask development server
    app.run(debug=True)
