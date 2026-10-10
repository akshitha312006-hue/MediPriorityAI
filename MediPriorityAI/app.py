from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import sqlite3, os, json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "medipriority.db")
app = Flask(__name__)
app.secret_key = os.environ.get("MEDIPRIORITY_SECRET", "change-this-secret-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

URGENCY = {
    "Immediate attention": {"class": "critical", "note": "Potential warning signs detected. Alert a qualified clinician immediately and follow local emergency protocol."},
    "Priority clinical review": {"class": "priority", "note": "Prompt assessment is recommended. Notify the clinical team and reassess if symptoms worsen."},
    "Standard clinical review": {"class": "standard", "note": "No listed high-risk trigger was selected. Continue normal intake and clinician review; this is not a diagnosis."}
}

RED_FLAGS = {
    "chest_pain": "Chest pain or pressure",
    "breathing": "Severe difficulty breathing",
    "stroke": "Sudden weakness, facial droop, or speech difficulty",
    "unconscious": "Unconsciousness, seizure, or severe confusion",
    "bleeding": "Severe or uncontrolled bleeding",
    "allergy": "Severe allergic reaction or swelling of tongue/throat"
}
PRIORITY_FLAGS = {
    "high_fever": "High fever",
    "severe_pain": "Severe or rapidly worsening pain",
    "dehydration": "Signs of dehydration",
    "persistent_vomiting": "Persistent vomiting",
    "pregnancy": "Pregnancy-related concern",
    "infant": "Patient is under 3 months old",
    "injury": "Significant injury or fall",
    "immunocompromised": "Immunocompromised or on chemotherapy"
}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Reception',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_code TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            phone TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            duration TEXT,
            temperature REAL,
            pulse INTEGER,
            oxygen INTEGER,
            medical_history TEXT,
            flags TEXT NOT NULL DEFAULT '[]',
            urgency TEXT NOT NULL,
            urgency_note TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting',
            assigned_to TEXT DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(created_by) REFERENCES users(id)
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            con.execute("INSERT INTO users(full_name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                        ("Demo Receptionist", "demo@medipriority.ai", generate_password_hash("Demo@123"), "Reception", datetime.now().isoformat(timespec="seconds")))
        pcount = con.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        if pcount == 0:
            uid = con.execute("SELECT id FROM users WHERE email=?", ("demo@medipriority.ai",)).fetchone()["id"]
            now = datetime.now().isoformat(timespec="seconds")
            samples = [
                ("MP-1001","Riya Sharma",34,"Female","9876501234","Fever and body aches","2 days",38.4,98,98,"Asthma",["high_fever"],"Priority clinical review","Prompt assessment is recommended. Notify the clinical team and reassess if symptoms worsen.","Waiting","Dr. Meera"),
                ("MP-1002","Arjun Rao",52,"Male","9876502345","Chest tightness and shortness of breath","30 minutes",None,112,93,"Hypertension",["chest_pain","breathing"],"Immediate attention","Potential warning signs detected. Alert a qualified clinician immediately and follow local emergency protocol.","Escalated","On-call clinician"),
                ("MP-1003","Nisha Patel",27,"Female","9876503456","Mild headache","Since morning",36.8,76,99,"None reported",[],"Standard clinical review","No listed high-risk trigger was selected. Continue normal intake and clinician review; this is not a diagnosis.","Waiting",""),
            ]
            for s in samples:
                con.execute("""INSERT INTO patients(patient_code,full_name,age,sex,phone,symptoms,duration,temperature,pulse,oxygen,medical_history,flags,urgency,urgency_note,status,assigned_to,created_by,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*s[:11], json.dumps(s[11]), *s[12:], uid, now, now))

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("full_name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        # Public self-registration cannot grant elevated roles.
        role = "Reception"
        if len(name) < 2 or "@" not in email or "." not in email.split("@")[-1] or len(password) < 8:
            flash("Enter a valid name and email. Password must contain at least 8 characters.", "error")
            return render_template("signup.html")
        try:
            with db() as con:
                con.execute("INSERT INTO users(full_name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                            (name,email,generate_password_hash(password),role,datetime.now().isoformat(timespec="seconds")))
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    with db() as con:
        rows = con.execute("SELECT * FROM patients ORDER BY CASE urgency WHEN 'Immediate attention' THEN 1 WHEN 'Priority clinical review' THEN 2 ELSE 3 END, created_at DESC").fetchall()
        counts = {
            "total": con.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "immediate": con.execute("SELECT COUNT(*) FROM patients WHERE urgency='Immediate attention' AND status!='Completed'").fetchone()[0],
            "priority": con.execute("SELECT COUNT(*) FROM patients WHERE urgency='Priority clinical review' AND status!='Completed'").fetchone()[0],
            "waiting": con.execute("SELECT COUNT(*) FROM patients WHERE status='Waiting'").fetchone()[0],
            "completed": con.execute("SELECT COUNT(*) FROM patients WHERE status='Completed'").fetchone()[0]
        }
    return render_template("dashboard.html", patients=rows, counts=counts, user_name=session.get("full_name","Staff"), current_page="dashboard")

@app.route("/patients/new", methods=["GET","POST"])
@login_required
def new_patient():
    if request.method == "POST":
        name = request.form.get("full_name","").strip()
        try:
            age = int(request.form.get("age","0"))
            temp = float(request.form["temperature"]) if request.form.get("temperature","").strip() else None
            pulse = int(request.form["pulse"]) if request.form.get("pulse","").strip() else None
            oxygen = int(request.form["oxygen"]) if request.form.get("oxygen","").strip() else None
        except ValueError:
            flash("Check the age and vital-sign fields. Use numbers only.", "error")
            return render_template("new_patient.html", red_flags=RED_FLAGS, priority_flags=PRIORITY_FLAGS, current_page="new")
        sex = request.form.get("sex","Prefer not to say")
        phone = request.form.get("phone","").strip()
        symptoms = request.form.get("symptoms","").strip()
        duration = request.form.get("duration","").strip()
        history = request.form.get("medical_history","").strip()
        flags = request.form.getlist("flags")
        if not name or age < 0 or age > 120 or not phone or not symptoms:
            flash("Please complete the patient name, valid age, phone, and symptoms.", "error")
            return render_template("new_patient.html", red_flags=RED_FLAGS, priority_flags=PRIORITY_FLAGS, current_page="new")
        red_selected = [f for f in flags if f in RED_FLAGS]
        priority_selected = [f for f in flags if f in PRIORITY_FLAGS]
        # Transparent screening support only: clinician must verify and can override.
        if red_selected or (oxygen is not None and oxygen < 90) or (pulse is not None and (pulse < 40 or pulse > 140)):
            urgency = "Immediate attention"
        elif priority_selected or (temperature is not None and temperature >= 39.0) or (oxygen is not None and oxygen < 94) or (pulse is not None and (pulse < 50 or pulse > 120)):
            urgency = "Priority clinical review"
        else:
            urgency = "Standard clinical review"
        note = URGENCY[urgency]["note"]
        now = datetime.now().isoformat(timespec="seconds")
        with db() as con:
            last = con.execute("SELECT id FROM patients ORDER BY id DESC LIMIT 1").fetchone()
            code = f"MP-{1000 + (last['id'] + 1 if last else 1)}"
            con.execute("""INSERT INTO patients(patient_code,full_name,age,sex,phone,symptoms,duration,temperature,pulse,oxygen,medical_history,flags,urgency,urgency_note,status,assigned_to,created_by,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (code,name,age,sex,phone,symptoms,duration,temp,pulse,oxygen,history,json.dumps(flags),urgency,note,"Waiting","",session["user_id"],now,now))
        flash(f"Patient {code} registered. Screening level: {urgency}. Confirm with clinical staff.", "success")
        return redirect(url_for("patient_detail", patient_id=con.execute("SELECT last_insert_rowid()").fetchone()[0]))
    return render_template("new_patient.html", red_flags=RED_FLAGS, priority_flags=PRIORITY_FLAGS, current_page="new")

@app.route("/patients/<int:patient_id>")
@login_required
def patient_detail(patient_id):
    with db() as con:
        patient = con.execute("SELECT p.*,u.full_name AS created_by_name FROM patients p LEFT JOIN users u ON p.created_by=u.id WHERE p.id=?", (patient_id,)).fetchone()
    if not patient:
        flash("Patient record not found.", "error")
        return redirect(url_for("dashboard"))
    return render_template("patient_detail.html", p=patient, flags=json.loads(patient["flags"] or "[]"), current_page="")

@app.route("/patients/<int:patient_id>/update", methods=["POST"])
@login_required
def update_patient(patient_id):
    status = request.form.get("status","Waiting")
    assigned = request.form.get("assigned_to","").strip()
    urgency = request.form.get("urgency","")
    allowed_status = {"Waiting","In consultation","Escalated","Completed"}
    allowed_urgency = set(URGENCY)
    with db() as con:
        p = con.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        if not p:
            flash("Patient record not found.", "error")
            return redirect(url_for("dashboard"))
        if status not in allowed_status: status = p["status"]
        if urgency not in allowed_urgency: urgency = p["urgency"]
        note = URGENCY[urgency]["note"]
        con.execute("UPDATE patients SET status=?,assigned_to=?,urgency=?,urgency_note=?,updated_at=? WHERE id=?",
                    (status,assigned,urgency,note,datetime.now().isoformat(timespec="seconds"),patient_id))
    flash("Patient record updated.", "success")
    return redirect(url_for("patient_detail", patient_id=patient_id))

@app.route("/api/patients")
@login_required
def api_patients():
    q = request.args.get("q","").strip()
    urgency = request.args.get("urgency","")
    with db() as con:
        sql = "SELECT id,patient_code,full_name,age,symptoms,urgency,status,created_at FROM patients WHERE 1=1"
        args = []
        if q:
            sql += " AND (full_name LIKE ? OR patient_code LIKE ? OR phone LIKE ? OR symptoms LIKE ?)"
            args.extend([f"%{q}%"]*4)
        if urgency in URGENCY:
            sql += " AND urgency=?"; args.append(urgency)
        sql += " ORDER BY created_at DESC"
        rows = con.execute(sql,args).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/patients")
@login_required
def patients():
    return redirect(url_for("dashboard"))

@app.route("/health")
def health():
    return jsonify({"status":"ok","app":"MediPriority AI"})

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
