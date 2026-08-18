import os
import re
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "hiring_system.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}

app = Flask(__name__)
app.secret_key = "ai-smart-hiring-system-secret-key"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


# ============================================================
# CREATE REQUIRED FOLDERS
# ============================================================

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Jobs table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            skills TEXT DEFAULT '',
            location TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )

    # Candidates table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            resume_filename TEXT DEFAULT '',
            resume_text TEXT DEFAULT '',
            score REAL DEFAULT 0,
            status TEXT DEFAULT 'New',
            created_at TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):
    if not filename:
        return False

    extension = filename.rsplit(".", 1)[-1].lower()

    return extension in ALLOWED_EXTENSIONS


def clean_filename(filename):
    """
    Simple safe filename function.
    """
    filename = os.path.basename(filename)
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return filename


def extract_text_from_pdf(filepath):
    """
    Extract text from a PDF resume.
    """

    if PdfReader is None:
        return ""

    try:
        reader = PdfReader(filepath)

        text = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text.append(page_text)

        return "\n".join(text)

    except Exception as error:
        print("PDF extraction error:", error)
        return ""


def extract_text_from_file(filepath, extension):
    """
    Extract text from supported files.
    """

    extension = extension.lower()

    if extension == "pdf":
        return extract_text_from_pdf(filepath)

    if extension == "txt":
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()
        except Exception:
            return ""

    # DOCX support
    if extension == "docx":
        try:
            from docx import Document

            document = Document(filepath)

            paragraphs = []

            for paragraph in document.paragraphs:
                paragraphs.append(paragraph.text)

            return "\n".join(paragraphs)

        except Exception as error:
            print("DOCX extraction error:", error)
            return ""

    return ""


def extract_email(text):
    """
    Find an email address in resume text.
    """

    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    return ""


def extract_phone(text):
    """
    Find a phone number in resume text.
    """

    pattern = r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"

    match = re.search(pattern, text)

    if match:
        phone = match.group(0).strip()

        return phone

    return ""


def extract_name(text):
    """
    Basic name extraction.

    This is intentionally simple and can later be replaced
    with a more advanced NLP resume parser.
    """

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    if not lines:
        return "Unknown Candidate"

    # Ignore obvious headings
    ignored = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "personal details",
    }

    for line in lines[:10]:

        lower_line = line.lower()

        if lower_line in ignored:
            continue

        # Avoid lines that look like emails
        if "@" in line:
            continue

        # Avoid very long lines
        if len(line) > 60:
            continue

        # Name should mostly contain letters
        if re.match(r"^[A-Za-z .'-]+$", line):

            words = line.split()

            if 2 <= len(words) <= 5:
                return line

    return "Unknown Candidate"


# ============================================================
# AI MATCHING
# ============================================================

def calculate_match_score(resume_text, job_description, job_skills):
    """
    Simple AI-style keyword matching.

    Score is calculated from matching skills/keywords.

    This can later be replaced by your ai_matching.py model.
    """

    resume = resume_text.lower()

    description = job_description.lower()

    skills_text = job_skills.lower()

    # Extract words from job information
    job_words = set(
        re.findall(
            r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}",
            description + " " + skills_text,
        )
    )

    # Remove common words
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "are",
        "you",
        "your",
        "will",
        "have",
        "has",
        "our",
        "job",
        "role",
        "work",
        "years",
        "year",
        "experience",
        "required",
        "preferred",
    }

    useful_words = {
        word for word in job_words
        if word not in stop_words and len(word) >= 3
    }

    if not useful_words:
        return 0

    matched_words = []

    for word in useful_words:
        if word in resume:
            matched_words.append(word)

    score = (len(matched_words) / len(useful_words)) * 100

    return round(min(score, 100), 2)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    conn = get_db()

    jobs = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()

    total_jobs = conn.execute(
        "SELECT COUNT(*) AS count FROM jobs"
    ).fetchone()["count"]

    total_candidates = conn.execute(
        "SELECT COUNT(*) AS count FROM candidates"
    ).fetchone()["count"]

    shortlisted = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM candidates
        WHERE status = 'Shortlisted'
        """
    ).fetchone()["count"]

    selected = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM candidates
        WHERE status = 'Selected'
        """
    ).fetchone()["count"]

    conn.close()

    stats = {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
        "shortlisted": shortlisted,
        "selected": selected,
    }

    return render_template(
        "index.html",
        jobs=jobs,
        stats=stats,
    )


# ============================================================
# ADD JOB
# ============================================================

@app.route("/add-job", methods=["GET", "POST"])
def add_job():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        skills = request.form.get("skills", "").strip()
        location = request.form.get("location", "").strip()

        if not title:
            flash("Job title is required.", "danger")

            return redirect(url_for("add_job"))

        if not description:
            flash("Job description is required.", "danger")

            return redirect(url_for("add_job"))

        conn = get_db()

        conn.execute(
            """
            INSERT INTO jobs
            (title, description, skills, location, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                skills,
                location,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        conn.commit()
        conn.close()

        flash("Job added successfully.", "success")

        return redirect(url_for("index"))

    return render_template("add_job.html")


# ============================================================
# JOB DETAILS
# ============================================================

@app.route("/job/<int:job_id>")
def job_detail(job_id):

    conn = get_db()

    job = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()

    candidates = conn.execute(
        """
        SELECT *
        FROM candidates
        WHERE job_id = ?
        ORDER BY score DESC
        """,
        (job_id,),
    ).fetchall()

    conn.close()

    if job is None:
        flash("Job not found.", "danger")

        return redirect(url_for("index"))

    return render_template(
        "candidates.html",
        job=job,
        candidates=candidates,
    )


# ============================================================
# UPLOAD RESUME
# ============================================================

@app.route("/upload-resume", methods=["GET", "POST"])
def upload_resume():

    conn = get_db()

    jobs = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()

    job = None
    selected_job_id = request.args.get("job_id") or request.form.get("job_id")

    if selected_job_id:
        try:
            selected_job_id = int(selected_job_id)
            job = conn.execute(
                """
                SELECT *
                FROM jobs
                WHERE id = ?
                """,
                (selected_job_id,),
            ).fetchone()
        except ValueError:
            job = None

    conn.close()

    if request.method == "POST":

        job_id = request.form.get("job_id")

        file = request.files.get("resume")

        if not job_id:
            flash("Please select a job.", "danger")

            return render_template(
                "upload_resume.html",
                jobs=jobs,
                job=None,
            )

        if not file or not file.filename:
            flash("Please select a resume file.", "danger")

            return render_template(
                "upload_resume.html",
                jobs=jobs,
                job=job,
            )

        if not allowed_file(file.filename):
            flash(
                "Only PDF, TXT and DOCX files are allowed.",
                "danger",
            )

            return redirect(url_for("upload_resume"))

        # Get selected job
        conn = get_db()

        job = conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()

        if job is None:
            conn.close()

            flash("Selected job does not exist.", "danger")

            return redirect(url_for("upload_resume"))

        # Create safe filename
        original_filename = clean_filename(file.filename)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        filename = f"{timestamp}_{original_filename}"

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename,
        )

        # Save file
        file.save(filepath)

        extension = filename.rsplit(".", 1)[-1].lower()

        # Extract resume text
        resume_text = extract_text_from_file(
            filepath,
            extension,
        )

        # Extract candidate information
        name = extract_name(resume_text)

        email = extract_email(resume_text)

        phone = extract_phone(resume_text)

        # Calculate AI match
        score = calculate_match_score(
            resume_text,
            job["description"],
            job["skills"],
        )

        # Decide initial status
        if score >= 75:
            status = "Shortlisted"
        elif score >= 50:
            status = "Review"
        else:
            status = "New"

        # Insert candidate
        conn.execute(
            """
            INSERT INTO candidates
            (
                job_id,
                name,
                email,
                phone,
                resume_filename,
                resume_text,
                score,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                name,
                email,
                phone,
                filename,
                resume_text,
                score,
                status,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            ),
        )

        conn.commit()
        conn.close()

        flash(
            f"Resume uploaded successfully. Match score: {score}%",
            "success",
        )

        return redirect(
            url_for(
                "job_detail",
                job_id=job_id,
            )
        )

    return render_template(
        "upload_resume.html",
        jobs=jobs,
        job=job,
    )


# ============================================================
# ALL CANDIDATES
# ============================================================

@app.route("/candidates")
def candidates():

    conn = get_db()

    candidates_list = conn.execute(
        """
        SELECT
            candidates.*,
            jobs.title AS job_title
        FROM candidates
        LEFT JOIN jobs
            ON candidates.job_id = jobs.id
        ORDER BY candidates.score DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "candidates.html",
        candidates=candidates_list,
    )


# ============================================================
# CANDIDATE DETAILS
# ============================================================

@app.route("/candidate/<int:candidate_id>")
def candidate_detail(candidate_id):

    conn = get_db()

    candidate = conn.execute(
        """
        SELECT
            candidates.*,
            jobs.title AS job_title,
            jobs.description AS job_description,
            jobs.skills AS job_skills
        FROM candidates
        LEFT JOIN jobs
            ON candidates.job_id = jobs.id
        WHERE candidates.id = ?
        """,
        (candidate_id,),
    ).fetchone()

    conn.close()

    if candidate is None:
        flash("Candidate not found.", "danger")

        return redirect(url_for("candidates"))

    return render_template(
        "candidate_detail.html",
        candidate=candidate,
    )


# ============================================================
# UPDATE CANDIDATE STATUS
# ============================================================

@app.route(
    "/candidate/<int:candidate_id>/status",
    methods=["POST"],
)
def update_candidate_status(candidate_id):

    status = request.form.get("status", "").strip()

    allowed_statuses = {
        "New",
        "Review",
        "Shortlisted",
        "Rejected",
        "Selected",
    }

    if status not in allowed_statuses:
        flash("Invalid candidate status.", "danger")

        return redirect(
            url_for(
                "candidate_detail",
                candidate_id=candidate_id,
            )
        )

    conn = get_db()

    conn.execute(
        """
        UPDATE candidates
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            candidate_id,
        ),
    )

    conn.commit()

    candidate = conn.execute(
        """
        SELECT job_id
        FROM candidates
        WHERE id = ?
        """,
        (candidate_id,),
    ).fetchone()

    conn.close()

    flash(
        "Candidate status updated successfully.",
        "success",
    )

    if candidate and candidate["job_id"]:
        return redirect(
            url_for(
                "job_detail",
                job_id=candidate["job_id"],
            )
        )

    return redirect(url_for("candidates"))


# ============================================================
# DELETE CANDIDATE
# ============================================================

@app.route(
    "/candidate/<int:candidate_id>/delete",
    methods=["POST"],
)
def delete_candidate(candidate_id):

    conn = get_db()

    candidate = conn.execute(
        """
        SELECT *
        FROM candidates
        WHERE id = ?
        """,
        (candidate_id,),
    ).fetchone()

    if candidate is None:
        conn.close()

        flash("Candidate not found.", "danger")

        return redirect(url_for("candidates"))

    job_id = candidate["job_id"]

    # Delete uploaded resume
    filename = candidate["resume_filename"]

    if filename:

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename,
        )

        if os.path.exists(filepath):

            try:
                os.remove(filepath)
            except Exception as error:
                print(
                    "Could not delete resume:",
                    error,
                )

    # Delete candidate
    conn.execute(
        """
        DELETE FROM candidates
        WHERE id = ?
        """,
        (candidate_id,),
    )

    conn.commit()
    conn.close()

    flash(
        "Candidate deleted successfully.",
        "success",
    )

    if job_id:
        return redirect(
            url_for(
                "job_detail",
                job_id=job_id,
            )
        )

    return redirect(url_for("candidates"))


# ============================================================
# API - GET JOBS
# ============================================================

@app.route("/api/jobs")
def api_jobs():

    conn = get_db()

    jobs = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    result = []

    for job in jobs:

        result.append(
            {
                "id": job["id"],
                "title": job["title"],
                "description": job["description"],
                "skills": job["skills"],
                "location": job["location"],
                "created_at": job["created_at"],
            }
        )

    return jsonify(result)


# ============================================================
# API - GET CANDIDATES
# ============================================================

@app.route("/api/candidates")
def api_candidates():

    conn = get_db()

    candidates = conn.execute(
        """
        SELECT
            candidates.*,
            jobs.title AS job_title
        FROM candidates
        LEFT JOIN jobs
            ON candidates.job_id = jobs.id
        ORDER BY candidates.score DESC
        """
    ).fetchall()

    conn.close()

    result = []

    for candidate in candidates:

        result.append(dict(candidate))

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)