"""
Patient Appointment & Queue Management System
Flask backend - connects UI, database, and DSA logic.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

# DSA
from dsa.scheduler import get_optimized_queue_list

PRIORITIES = ("normal", "accident", "emergency", "critical")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "hospital-queue-secret-key-2024"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"



def get_db() -> sqlite3.Connection:
    """Return a DB connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db_path() -> None:
    """Use temp-dir DB if project DB causes disk I/O (e.g. OneDrive lock)."""
    global DB_PATH
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        conn.execute("CREATE TABLE IF NOT EXISTS _db_check (x INT)")
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        fallback = Path(tempfile.gettempdir()) / "hospital_queue.db"
        DB_PATH = fallback


def init_db() -> None:
    """Create tables and preload accounts + sample data. Idempotent."""
    _ensure_db_path()
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT
        )
    """)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN doctor_id INTEGER")
    except sqlite3.OperationalError:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            priority TEXT NOT NULL,
            created_at TEXT NOT NULL,
            doctor_id INTEGER REFERENCES doctors(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            priority TEXT NOT NULL,
            patient_user_id INTEGER REFERENCES users(id),
            doctor_id INTEGER REFERENCES doctors(id),
            status TEXT NOT NULL DEFAULT 'scheduled',
            created_at TEXT NOT NULL
        )
    """)

    pw_doc = generate_password_hash("ke123")
    cur.execute(
        "INSERT OR IGNORE INTO users (email, password, role, full_name) VALUES (?, ?, ?, ?)",
        ("fayerakena@doctor.gmail.com", pw_doc, "doctor", "Kena Fayera"),
    )
    pw_pat = generate_password_hash("patient123")
    cur.execute(
        "INSERT OR IGNORE INTO users (email, password, role, full_name) VALUES (?, ?, ?, ?)",
        ("tamiratyisakor@gmail.com", pw_pat, "patient", "Yisakor Tamirat"),
    )

    cur.execute("SELECT COUNT(*) FROM doctors")
    if cur.fetchone()[0] == 0:
        for d in ("Kena Fayera", "Daniel Dea", "Abdurahman Muktar",
                  "Abel Yeshewalem", "Gersam Mussie", "Leulekal Nahusenay"):
            cur.execute("INSERT INTO doctors (name) VALUES (?)", (d,))

    cur.execute("SELECT id FROM users WHERE email = ?", ("fayerakena@doctor.gmail.com",))
    doc_row = cur.fetchone()
    if doc_row:
        cur.execute("UPDATE users SET doctor_id = 1 WHERE id = ?", (doc_row["id"],))

    cur.execute("SELECT COUNT(*) FROM appointments")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT id FROM users WHERE email = ?", ("tamiratyisakor@gmail.com",))
        pat_row = cur.fetchone()
        pat_uid = pat_row["id"] if pat_row else None
        now = datetime.now(timezone.utc)

        # name, date, time, priority, patient_user_id, doctor_id
        # We deliberately attach all sample appointments to the same
        # demo patient user (pat_uid) so that:
        #   - they are visible in the **My Appointments** table, and
        #   - they also appear in the doctor's queue table.
        samples = [
            # Logged‑in sample patient with multiple priorities.
            ("Yisakor Tamirat", "2025-02-01", "09:00", "normal", pat_uid, 1),
            ("Yisakor Tamirat", "2025-02-03", "14:30", "emergency", pat_uid, 1),
            # Required preloaded patient data so they appear in tables/queues.
            ("NAOL MULISA", "2025-02-02", "10:00", "accident", pat_uid, 1),
            ("SEWYISHAL NETSANET", "2025-02-02", "11:00", "normal", pat_uid, 1),
            ("Wirtu Borana", "2025-02-01", "08:30", "critical", pat_uid, 1),
            ("YISAKOR TAMIRAT", "2025-02-04", "09:30", "emergency", pat_uid, 1),
            ("Surafiel nigus", "2025-02-01", "10:30", "emergency", pat_uid, 1),
            ("Semere hailu", "2025-02-03", "11:30", "normal", pat_uid, 1),
        ]
        for i, (name, d, t, prio, puid, did) in enumerate(samples):
            cur.execute(
                """INSERT INTO appointments (patient_name, appointment_date, appointment_time,
                   priority, patient_user_id, doctor_id, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?)""",
                (name, d, t, prio, puid, did, (now + timedelta(seconds*i)).isoformat()),
            )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def login_required(f):
    """Require user to be logged in."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return wrapped


def doctor_required(f):
    """Require logged-in user to have doctor role."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        if session.get("role") != "doctor":
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return wrapped


def receptionist_or_doctor(f):
    """Allow receptionist and doctor only (patients cannot register others)."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        if session.get("role") == "patient":
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return wrapped


def patient_required(f):
    """Require logged-in user to have patient role."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        if session.get("role") != "patient":
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Public homepage."""
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Simple login."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password, role, full_name, doctor_id FROM users WHERE email = ?",
            (email,),
        )
        row = cur.fetchone()
        conn.close()

        if not row or not check_password_hash(row["password"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = row["id"]
        session["email"] = row["email"]
        session["role"] = row["role"]
        session["full_name"] = row["full_name"] or ""
        session["doctor_id"] = dict(row).get("doctor_id")

        next_url = request.args.get("next") or url_for("index")
        if session["role"] == "doctor":
            next_url = url_for("doctor_dashboard")
        elif session["role"] == "patient":
            next_url = url_for("patient_dashboard")
        elif next_url and "doctor" in next_url:
            next_url = url_for("index")
        return redirect(next_url)

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Simple signup (receptionist or doctor)."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        full_name = (request.form.get("full_name") or "").strip()
        role = (request.form.get("role") or "receptionist").strip().lower()
        if role not in ("receptionist", "doctor"):
            role = "receptionist"

        if not email or not password:
            return render_template("signup.html", error="Email and password are required.")

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (email, password, role, full_name) VALUES (?, ?, ?, ?)",
                (email, generate_password_hash(password), role, full_name),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("signup.html", error="Email already registered.")
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    """Clear session and redirect home."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/register-patient", methods=["GET", "POST"])
@receptionist_or_doctor
def register_patient():
    """Add appointment (receptionist/doctor): name, date, time, priority, doctor."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM doctors ORDER BY name")
    doctors = [{"id": r["id"], "name": r["name"]} for r in cur.fetchall()]
    conn.close()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        appt_date = (request.form.get("appointment_date") or "").strip()
        appt_time = (request.form.get("appointment_time") or "").strip()
        priority = (request.form.get("priority") or "normal").strip().lower()
        if priority not in PRIORITIES:
            priority = "normal"
        doctor_id = request.form.get("doctor_id")
        try:
            doctor_id = int(doctor_id) if doctor_id else None
        except ValueError:
            doctor_id = None

        if not name or not appt_date or not appt_time:
            return render_template(
                "register_patient.html",
                doctors=doctors,
                priorities=PRIORITIES,
                error="Patient name, date, and time are required.",
            )

        created = datetime.now(timezone.utc)
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO appointments (patient_name, appointment_date, appointment_time,
               priority, patient_user_id, doctor_id, status, created_at)
               VALUES (?, ?, ?, ?, NULL, ?, 'scheduled', ?)""",
            (name, appt_date, appt_time, priority, doctor_id, created.isoformat()),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("register_patient") + "?success=1")

    success = request.args.get("success")
    return render_template(
        "register_patient.html",
        doctors=doctors,
        priorities=PRIORITIES,
        success=success,
    )


def _appointment_rows_to_dicts(rows) -> list:
    return [
        {
            "id": r["id"],
            "name": r["patient_name"],
            "appointment_date": r["appointment_date"],
            "appointment_time": r["appointment_time"],
            "priority": r["priority"],
            "status": r["status"],
            "created_at": r["created_at"],
            "doctor_id": r["doctor_id"],
        }
        for r in rows
    ]


@app.route("/patient-dashboard", methods=["GET", "POST"])
@patient_required
def patient_dashboard():
    """Appointment table for logged-in patient; add appointment if none; search."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, patient_name, appointment_date, appointment_time, priority, status, created_at, doctor_id
           FROM appointments WHERE patient_user_id = ? AND status = 'scheduled'
           ORDER BY appointment_date, appointment_time""",
        (session["user_id"],),
    )
    rows = cur.fetchall()
    conn.close()

    appointments = _appointment_rows_to_dicts(rows)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = (request.form.get("patient_name") or "").strip() or (session.get("full_name") or "")
            appt_date = (request.form.get("appointment_date") or "").strip()
            appt_time = (request.form.get("appointment_time") or "").strip()
            priority = (request.form.get("priority") or "normal").strip().lower()
            if priority not in PRIORITIES:
                priority = "normal"
            if not name or not appt_date or not appt_time:
                return render_template(
                    "patient_dashboard.html",
                    appointments=appointments,
                    priorities=PRIORITIES,
                    search_q=request.args.get("q", "").strip(),
                    error="Name, date, and time are required.",
                )
            created = datetime.now(timezone.utc)
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO appointments (patient_name, appointment_date, appointment_time,
                   priority, patient_user_id, doctor_id, status, created_at)
                   VALUES (?, ?, ?, ?, ?, NULL, 'scheduled', ?)""",
                (name, appt_date, appt_time, priority, session["user_id"], created.isoformat()),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("patient_dashboard") + "?success=1")

    search_q = (request.args.get("q") or "").strip().lower()
    if search_q:
        appointments = [
            a for a in appointments
            if search_q in (a["name"] or "").lower()
            or search_q in (a["appointment_date"] or "").lower()
            or search_q in (a["appointment_time"] or "").lower()
            or search_q in (a["priority"] or "").lower()
        ]

    success = request.args.get("success")
    return render_template(
        "patient_dashboard.html",
        appointments=appointments,
        priorities=PRIORITIES,
        search_q=search_q,
        success=success,
    )


@app.route("/doctor-dashboard", methods=["GET", "POST"])
@doctor_required
def doctor_dashboard():
    """Doctor's patient list (appointments); complete, reschedule; search."""
    doctor_id = session.get("doctor_id") or 1
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, patient_name, appointment_date, appointment_time, priority, status, created_at, doctor_id
           FROM appointments WHERE doctor_id = ? AND status = 'scheduled'
           ORDER BY id""",
        (doctor_id,),
    )
    rows = cur.fetchall()
    conn.close()

    raw = _appointment_rows_to_dicts(rows)

    # DSA: order by priority then arrival
    ordered = get_optimized_queue_list(raw)

    if request.method == "POST":
        action = request.form.get("action")
        aid = request.form.get("appointment_id")
        if action == "complete" and aid:
            try:
                aid = int(aid)
                conn = get_db()
                cur = conn.cursor()
                cur.execute("UPDATE appointments SET status = 'completed' WHERE id = ? AND doctor_id = ?", (aid, doctor_id))
                conn.commit()
                conn.close()
            except (ValueError, TypeError):
                pass
            return redirect(url_for("doctor_dashboard"))

        if action == "reschedule" and aid:
            try:
                aid = int(aid)
            except (ValueError, TypeError):
                aid = None
            new_date = (request.form.get("new_date") or "").strip()
            new_time = (request.form.get("new_time") or "").strip()
            if aid and new_date and new_time:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE appointments SET appointment_date = ?, appointment_time = ? WHERE id = ? AND doctor_id = ?",
                    (new_date, new_time, aid, doctor_id),
                )
                conn.commit()
                conn.close()
            return redirect(url_for("doctor_dashboard"))

    search_q = (request.args.get("q") or "").strip().lower()
    if search_q:
        ordered = [
            a for a in ordered
            if search_q in (a.get("name") or "").lower()
            or search_q in (a.get("appointment_date") or "").lower()
            or search_q in (a.get("appointment_time") or "").lower()
            or search_q in (a.get("priority") or "").lower()
        ]

    return render_template("doctor_dashboard.html", queue=ordered, search_q=search_q, priorities=PRIORITIES)


# ---------------------------------------------------------------------------
# Init & run
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
