import os
import re
import sqlite3

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.basename(BASE_DIR).lower() == "templates":
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    TEMPLATE_FOLDER = BASE_DIR
else:
    PROJECT_DIR = BASE_DIR
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")

UPLOAD_FOLDER = os.path.join(PROJECT_DIR, "uploads")
DATABASE = os.path.join(PROJECT_DIR, "hiring.db")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    template_folder=TEMPLATE_FOLDER
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            department TEXT,
            location TEXT,
            job_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            mobile TEXT,
            location TEXT,
            job_role TEXT,
            resume_filename TEXT,
            score INTEGER,
            decision TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# ALLOWED FILE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# RESUME TEXT EXTRACTION
# =========================================================

def extract_resume_text(filepath):

    extension = filepath.rsplit(".", 1)[1].lower()

    # PDF
    if extension == "pdf":

        try:
            import PyPDF2

            text = ""

            with open(filepath, "rb") as file:

                reader = PyPDF2.PdfReader(file)

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

            return text

        except ImportError:

            raise Exception(
                "PyPDF2 is not installed."
            )

    # DOCX
    elif extension == "docx":

        try:
            from docx import Document

            document = Document(filepath)

            text = []

            for paragraph in document.paragraphs:

                text.append(paragraph.text)

            return "\n".join(text)

        except ImportError:

            raise Exception(
                "python-docx is not installed."
            )

    return ""


# =========================================================
# SKILLS
# =========================================================

SKILLS = [

    "python",
    "java",
    "javascript",
    "html",
    "css",
    "react",
    "node.js",
    "node",
    "sql",
    "mysql",
    "mongodb",
    "flask",
    "django",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data science",
    "data analysis",
    "excel",
    "power bi",
    "tableau",
    "git",
    "github",
    "aws",
    "azure",
    "docker",
    "c++",
    "rest api"
]


def detect_skills(text):

    text_lower = text.lower()

    found_skills = []

    for skill in SKILLS:

        if skill == "c++":

            if "c++" in text_lower:
                found_skills.append(skill)

            continue

        if skill == "node.js":

            if "node.js" in text_lower:
                found_skills.append(skill)

            continue

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text_lower):

            found_skills.append(skill)

    return found_skills


# =========================================================
# JOB REQUIREMENTS
# =========================================================

JOB_REQUIREMENTS = {

    "Software Developer": [
        "python",
        "java",
        "javascript",
        "sql",
        "git"
    ],

    "Python Developer": [
        "python",
        "flask",
        "django",
        "sql",
        "git"
    ],

    "Java Developer": [
        "java",
        "sql",
        "git"
    ],

    "Web Developer": [
        "html",
        "css",
        "javascript",
        "sql",
        "git"
    ],

    "Data Analyst": [
        "python",
        "sql",
        "excel",
        "data analysis",
        "power bi"
    ],

    "Data Scientist": [
        "python",
        "sql",
        "machine learning",
        "data science",
        "data analysis"
    ],

    "Machine Learning Engineer": [
        "python",
        "machine learning",
        "deep learning",
        "sql",
        "git"
    ],

    "AI Engineer": [
        "python",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "git"
    ],

    "Full Stack Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "node.js",
        "sql",
        "git",
        "github",
        "rest api",
        "mongodb"
    ],

    "Backend Developer": [
        "python",
        "flask",
        "sql",
        "mongodb",
        "rest api",
        "git"
    ],

    "Frontend Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "git"
    ]
}


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def home():

    conn = get_db()

    candidate_count = conn.execute(
        "SELECT COUNT(*) FROM candidates"
    ).fetchone()[0]

    job_count = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    selected_count = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE decision = 'SELECT'"
    ).fetchone()[0]

    analysed_count = conn.execute(
        "SELECT COUNT(*) FROM candidates WHERE score IS NOT NULL"
    ).fetchone()[0]

    jobs = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    candidates = conn.execute("""
        SELECT *
        FROM candidates
        ORDER BY id DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        candidate_count=candidate_count,
        job_count=job_count,
        selected_count=selected_count,
        analysed_count=analysed_count,
        jobs=jobs,
        candidates=candidates
    )


# =========================================================
# ADD CANDIDATE
# =========================================================

@app.route("/candidate", methods=["GET", "POST"])
def candidate():

    job_roles = list(JOB_REQUIREMENTS.keys())

    if request.method == "GET":

        return render_template(
            "candidate.html",
            job_roles=job_roles
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    mobile = request.form.get(
        "mobile",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    job_role = request.form.get(
        "job_role",
        ""
    ).strip()

    resume = request.files.get("resume")

    if not name:

        return "Candidate name is required."

    if not email:

        return "Email is required."

    if not job_role:

        return "Job role is required."

    if not resume:

        return "Please upload a resume."

    if resume.filename == "":

        return "Please select a resume file."

    if not allowed_file(resume.filename):

        return "Only PDF and DOCX files are allowed."

    # Save resume
    filename = secure_filename(resume.filename)

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    resume.save(filepath)

    # Extract resume text
    try:

        resume_text = extract_resume_text(filepath)

    except Exception as error:

        return f"Resume processing error: {error}"

    # Detect skills
    found_skills = detect_skills(
        resume_text
    )

    # Required skills
    required_skills = JOB_REQUIREMENTS.get(
        job_role,
        []
    )

    # Match skills
    found_lower = [
        skill.lower()
        for skill in found_skills
    ]

    matched_skills = []

    for skill in required_skills:

        if skill.lower() in found_lower:

            matched_skills.append(skill)

    # Score
    if len(required_skills) > 0:

        score = round(
            (
                len(matched_skills)
                /
                len(required_skills)
            )
            * 100
        )

    else:

        score = 0

    # Decision
    if score >= 60:

        decision = "SELECT"

    else:

        decision = "REJECT"

    # Save candidate
    conn = get_db()

    conn.execute("""
        INSERT INTO candidates
        (
            name,
            email,
            mobile,
            location,
            job_role,
            resume_filename,
            score,
            decision
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        mobile,
        location,
        job_role,
        filename,
        score,
        decision
    ))

    conn.commit()
    conn.close()

    return render_template(
        "resume_result.html",

        name=name,
        email=email,
        mobile=mobile,
        location=location,

        job_role=job_role,

        filename=filename,

        required_skills=required_skills,

        found_skills=found_skills,

        score=score,

        decision=decision
    )


# =========================================================
# ADD JOB
# =========================================================

@app.route("/add-job", methods=["GET", "POST"])
def add_job():

    if request.method == "GET":

        return render_template(
            "add_job.html"
        )

    job_title = request.form.get(
        "job_title",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()

    if not job_title:

        return "Job title is required."

    # Save job
    conn = get_db()

    conn.execute("""
        INSERT INTO jobs
        (
            job_title,
            department,
            location,
            job_description
        )
        VALUES (?, ?, ?, ?)
    """, (
        job_title,
        department,
        location,
        job_description
    ))

    conn.commit()
    conn.close()

    # Return dashboard
    return home()


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    <a href="/">Go to Dashboard</a>
    """, 404


@app.errorhandler(413)
def file_too_large(error):

    return """
    <h1>File Too Large</h1>
    <p>Please upload a resume smaller than 10 MB.</p>
    """, 413


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("=" * 60)
    print("AI SMART HIRING SYSTEM")
    print("=" * 60)

    print("App location:")
    print(BASE_DIR)

    print("Template folder:")
    print(TEMPLATE_FOLDER)

    print("Database:")
    print(DATABASE)

    print("Upload folder:")
    print(UPLOAD_FOLDER)

    print("Port:")
    print(port)

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )