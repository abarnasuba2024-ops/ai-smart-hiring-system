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
)

# ============================================================
# OPTIONAL PDF LIBRARIES
# ============================================================

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


# ============================================================
# OPTIONAL OCR LIBRARIES
# ============================================================

try:
    import fitz
    import pytesseract
    from PIL import Image
except ImportError:
    fitz = None
    pytesseract = None
    Image = None


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(
    BASE_DIR,
    "hiring_system.db"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "txt",
    "docx"
}


app = Flask(__name__)

app.secret_key = (
    "ai-smart-hiring-system-secret-key"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    10 * 1024 * 1024
)


# ============================================================
# CREATE REQUIRED FOLDERS
# ============================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()

    cursor = conn.cursor()

    # --------------------------------------------------------
    # JOBS TABLE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CANDIDATES TABLE
    # --------------------------------------------------------

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


# Initialize database when application starts
init_db()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[-1].lower()

    return extension in ALLOWED_EXTENSIONS


# ============================================================
# SAFE FILENAME
# ============================================================

def clean_filename(filename):

    filename = os.path.basename(
        filename
    )

    filename = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        filename
    )

    return filename


# ============================================================
# RESUME TEXT FORMATTER
# ============================================================

def format_resume_text(text):
    """
    Clean extracted resume text.

    The purpose of this function is to prevent PDF extraction
    from producing badly formatted text.

    It preserves useful lines and converts common resume
    sections into separate lines.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace(
        "\r\n",
        "\n"
    )

    text = text.replace(
        "\r",
        "\n"
    )

    # Normalize bullet characters
    text = text.replace(
        "•",
        "\n• "
    )

    text = text.replace(
        "▪",
        "\n• "
    )

    text = text.replace(
        "◦",
        "\n• "
    )

    text = text.replace(
        "‣",
        "\n• "
    )

    # Normalize tabs
    text = text.replace(
        "\t",
        " "
    )

    # --------------------------------------------------------
    # Common resume headings
    # --------------------------------------------------------

    headings = [
        "SUMMARY",
        "PROFILE",
        "OBJECTIVE",
        "TECHNICAL SKILLS",
        "SKILLS",
        "PROGRAMMING SKILLS",
        "EXPERIENCE",
        "WORK EXPERIENCE",
        "PROFESSIONAL EXPERIENCE",
        "PROJECTS",
        "ACADEMIC PROJECTS",
        "EDUCATION",
        "CERTIFICATIONS",
        "CERTIFICATION",
        "ACHIEVEMENTS",
        "LANGUAGES",
        "INTERESTS",
        "PERSONAL DETAILS",
        "CONTACT",
        "CONTACT DETAILS",
        "TECH STACK",
    ]

    # Put headings on their own lines
    for heading in headings:

        pattern = (
            r"\s+"
            + re.escape(heading)
            + r"\s*"
        )

        text = re.sub(
            pattern,
            "\n\n" + heading + "\n",
            text,
            flags=re.IGNORECASE
        )

    # --------------------------------------------------------
    # Common labels
    # --------------------------------------------------------

    labels = [
        "Tech Stack:",
        "Technology Stack:",
        "Duration:",
        "Programming:",
        "Libraries:",
        "Database:",
        "Frameworks:",
        "Tools:",
        "Role:",
        "Location:",
    ]

    for label in labels:

        text = text.replace(
            label,
            "\n" + label + " "
        )

    # --------------------------------------------------------
    # Clean excessive spaces
    # --------------------------------------------------------

    lines = []

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            lines.append("")
            continue

        # Multiple spaces -> single space
        line = re.sub(
            r"\s{2,}",
            " ",
            line
        )

        lines.append(line)

    # --------------------------------------------------------
    # Remove excessive blank lines
    # --------------------------------------------------------

    cleaned = []

    blank_count = 0

    for line in lines:

        if line == "":

            blank_count += 1

            if blank_count <= 2:
                cleaned.append("")

        else:

            blank_count = 0

            cleaned.append(line)

    text = "\n".join(
        cleaned
    ).strip()

    return text


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(filepath):
    """
    Extract selectable text from PDF.

    If the PDF has no selectable text, OCR is attempted.
    """

    if PdfReader is None:
        print(
            "PyPDF2 is not installed."
        )

        return ""

    try:

        reader = PdfReader(
            filepath
        )

        text_parts = []

        # ----------------------------------------------------
        # Normal PDF extraction
        # ----------------------------------------------------

        for page in reader.pages:

            try:

                page_text = (
                    page.extract_text()
                )

            except Exception:
                page_text = ""

            if page_text:

                text_parts.append(
                    page_text
                )

        extracted_text = "\n".join(
            text_parts
        ).strip()

        # ----------------------------------------------------
        # If text exists, format and return it
        # ----------------------------------------------------

        if extracted_text:

            return format_resume_text(
                extracted_text
            )

        # ----------------------------------------------------
        # OCR FALLBACK
        # ----------------------------------------------------

        if (
            fitz is None
            or pytesseract is None
            or Image is None
        ):

            print(
                "OCR libraries are not installed."
            )

            return ""

        print(
            "No selectable PDF text found. Starting OCR..."
        )

        document = fitz.open(
            filepath
        )

        ocr_parts = []

        for page in document:

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(
                    2,
                    2
                ),
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                [
                    pixmap.width,
                    pixmap.height
                ],
                pixmap.samples
            )

            page_text = (
                pytesseract.image_to_string(
                    image
                )
            )

            if page_text.strip():

                ocr_parts.append(
                    page_text
                )

        document.close()

        ocr_text = "\n\n".join(
            ocr_parts
        )

        return format_resume_text(
            ocr_text
        )

    except Exception as error:

        print(
            "PDF extraction error:",
            error
        )

        return ""


# ============================================================
# TXT / DOCX / PDF FILE EXTRACTION
# ============================================================

def extract_text_from_file(
    filepath,
    extension
):

    extension = extension.lower()

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if extension == "pdf":

        return extract_text_from_pdf(
            filepath
        )

    # --------------------------------------------------------
    # TXT
    # --------------------------------------------------------

    if extension == "txt":

        try:

            with open(
                filepath,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                text = file.read()

            return format_resume_text(
                text
            )

        except Exception as error:

            print(
                "TXT extraction error:",
                error
            )

            return ""

    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    if extension == "docx":

        try:

            from docx import Document

            document = Document(
                filepath
            )

            paragraphs = []

            for paragraph in document.paragraphs:

                paragraph_text = (
                    paragraph.text.strip()
                )

                if paragraph_text:

                    paragraphs.append(
                        paragraph_text
                    )

            text = "\n".join(
                paragraphs
            )

            return format_resume_text(
                text
            )

        except Exception as error:

            print(
                "DOCX extraction error:",
                error
            )

            return ""

    return ""


# ============================================================
# EMAIL EXTRACTION
# ============================================================

def extract_email(text):

    if not text:
        return ""

    pattern = (
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}"
    )

    match = re.search(
        pattern,
        text
    )

    if match:

        return match.group(
            0
        ).strip()

    return ""


# ============================================================
# PHONE EXTRACTION
# ============================================================

def extract_phone(text):

    if not text:
        return ""

    pattern = (
        r"(?<!\d)"
        r"(?:\+?\d[\d\s().-]{7,}\d)"
        r"(?!\d)"
    )

    matches = re.findall(
        pattern,
        text
    )

    if matches:

        phone = matches[0].strip()

        # Clean excessive spaces
        phone = re.sub(
            r"\s+",
            " ",
            phone
        )

        return phone

    return ""


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(text):
    """
    Basic candidate name detection.
    """

    if not text:
        return "Unknown Candidate"

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:

            lines.append(
                line
            )

    if not lines:

        return "Unknown Candidate"

    ignored = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "personal details",
        "contact",
        "contact details",
    }

    # Look only near the beginning of the resume
    for line in lines[:15]:

        lower_line = (
            line.lower().strip()
        )

        if lower_line in ignored:
            continue

        # Skip emails
        if "@" in line:
            continue

        # Skip URLs
        if (
            "http://" in lower_line
            or "https://" in lower_line
            or "linkedin" in lower_line
            or "github" in lower_line
        ):
            continue

        # Skip lines containing digits
        if any(
            char.isdigit()
            for char in line
        ):
            continue

        # Skip very long sentences
        if len(line) > 50:
            continue

        # Name should mostly contain letters
        if not re.match(
            r"^[A-Za-z .'-]+$",
            line
        ):
            continue

        words = line.split()

        if 2 <= len(words) <= 5:

            # Avoid common headings
            heading_words = {
                "summary",
                "experience",
                "education",
                "skills",
                "projects",
                "certifications",
                "objective",
            }

            if lower_line not in heading_words:

                return line

    return "Unknown Candidate"


# ============================================================
# AI-STYLE MATCHING
# ============================================================

def calculate_match_score(
    resume_text,
    job_description,
    job_skills
):
    """
    Keyword-based AI-style matching.

    This is not a machine-learning model.
    It can later be replaced with an actual AI model.
    """

    if not resume_text:
        return 0

    resume = resume_text.lower()

    description = (
        job_description or ""
    ).lower()

    skills_text = (
        job_skills or ""
    ).lower()

    combined_job_text = (
        description
        + " "
        + skills_text
    )

    # Extract useful words
    job_words = set(
        re.findall(
            r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}",
            combined_job_text
        )
    )

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
        "using",
        "into",
        "about",
        "their",
        "they",
        "them",
        "also",
        "should",
        "must",
        "need",
        "needs",
        "candidate",
        "developer",
    }

    useful_words = {
        word
        for word in job_words
        if (
            word not in stop_words
            and len(word) >= 3
        )
    }

    if not useful_words:
        return 0

    matched_words = []

    for word in useful_words:

        if word in resume:

            matched_words.append(
                word
            )

    score = (
        len(matched_words)
        / len(useful_words)
    ) * 100

    return round(
        min(score, 100),
        2
    )


# ============================================================
# HOME / DASHBOARD
# ============================================================

@app.route("/")
def index():

    conn = get_db()

    # --------------------------------------------------------
    # Get jobs
    # --------------------------------------------------------

    jobs = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_jobs = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM jobs
        """
    ).fetchone()["count"]

    total_candidates = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM candidates
        """
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

    # ========================================================
    # AUTOMATIC GREETING
    # ========================================================

    now = datetime.now()

    current_hour = now.hour

    if 5 <= current_hour < 12:

        greeting = "Good Morning"

    elif 12 <= current_hour < 17:

        greeting = "Good Afternoon"

    else:

        greeting = "Good Evening"

    # ========================================================
    # DATE + TIME
    # ========================================================

    current_date = now.strftime(
        "%A, %d %B %Y"
    )

    current_time = now.strftime(
        "%I:%M %p"
    )

    # ========================================================
    # STATS
    # ========================================================

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
        greeting=greeting,
        current_date=current_date,
        current_time=current_time,
    )


# ============================================================
# ADD JOB
# ============================================================

@app.route(
    "/add-job",
    methods=["GET", "POST"]
)
def add_job():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        skills = request.form.get(
            "skills",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not title:

            flash(
                "Job title is required.",
                "danger"
            )

            return redirect(
                url_for("add_job")
            )

        if not description:

            flash(
                "Job description is required.",
                "danger"
            )

            return redirect(
                url_for("add_job")
            )

        # ----------------------------------------------------
        # Insert job
        # ----------------------------------------------------

        conn = get_db()

        conn.execute(
            """
            INSERT INTO jobs
            (
                title,
                description,
                skills,
                location,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                skills,
                location,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Job added successfully.",
            "success"
        )

        return redirect(
            url_for("index")
        )

    return render_template(
        "add_job.html"
    )


# ============================================================
# JOB DETAILS
# ============================================================

@app.route(
    "/job/<int:job_id>"
)
def job_detail(job_id):

    conn = get_db()

    # --------------------------------------------------------
    # Job
    # --------------------------------------------------------

    job = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    # --------------------------------------------------------
    # Candidates for job
    # --------------------------------------------------------

    candidates = conn.execute(
        """
        SELECT *
        FROM candidates
        WHERE job_id = ?
        ORDER BY score DESC
        """,
        (job_id,)
    ).fetchall()

    conn.close()

    if job is None:

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("index")
        )

    return render_template(
        "candidates.html",
        job=job,
        candidates=candidates,
    )


# ============================================================
# UPLOAD RESUME
# ============================================================

@app.route(
    "/upload-resume",
    methods=["GET", "POST"]
)
def upload_resume():

    conn = get_db()

    # --------------------------------------------------------
    # Get jobs
    # --------------------------------------------------------

    jobs = conn.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()

    job = None

    selected_job_id = (
        request.args.get("job_id")
        or request.form.get("job_id")
    )

    if selected_job_id:

        try:

            selected_job_id = int(
                selected_job_id
            )

            job = conn.execute(
                """
                SELECT *
                FROM jobs
                WHERE id = ?
                """,
                (selected_job_id,)
            ).fetchone()

        except ValueError:

            job = None

    conn.close()

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        job_id = request.form.get(
            "job_id"
        )

        file = request.files.get(
            "resume"
        )

        # ----------------------------------------------------
        # Validate job
        # ----------------------------------------------------

        if not job_id:

            flash(
                "Please select a job.",
                "danger"
            )

            return render_template(
                "upload_resume.html",
                jobs=jobs,
                job=None,
            )

        # ----------------------------------------------------
        # Validate file
        # ----------------------------------------------------

        if not file or not file.filename:

            flash(
                "Please select a resume file.",
                "danger"
            )

            return render_template(
                "upload_resume.html",
                jobs=jobs,
                job=job,
            )

        # ----------------------------------------------------
        # Validate extension
        # ----------------------------------------------------

        if not allowed_file(
            file.filename
        ):

            flash(
                "Only PDF, TXT and DOCX files are allowed.",
                "danger"
            )

            return redirect(
                url_for(
                    "upload_resume"
                )
            )

        # ----------------------------------------------------
        # Get selected job
        # ----------------------------------------------------

        conn = get_db()

        try:

            job_id_int = int(
                job_id
            )

        except ValueError:

            conn.close()

            flash(
                "Invalid job selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "upload_resume"
                )
            )

        job = conn.execute(
            """
            SELECT *
            FROM jobs
            WHERE id = ?
            """,
            (job_id_int,)
        ).fetchone()

        if job is None:

            conn.close()

            flash(
                "Selected job does not exist.",
                "danger"
            )

            return redirect(
                url_for(
                    "upload_resume"
                )
            )

        # ----------------------------------------------------
        # Create safe filename
        # ----------------------------------------------------

        original_filename = (
            clean_filename(
                file.filename
            )
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )

        filename = (
            f"{timestamp}_{original_filename}"
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        # ----------------------------------------------------
        # Save uploaded file
        # ----------------------------------------------------

        try:

            file.save(
                filepath
            )

        except Exception as error:

            conn.close()

            print(
                "File save error:",
                error
            )

            flash(
                "Could not save the uploaded resume.",
                "danger"
            )

            return redirect(
                url_for(
                    "upload_resume"
                )
            )

        # ----------------------------------------------------
        # Extract text
        # ----------------------------------------------------

        extension = (
            filename
            .rsplit(".", 1)[-1]
            .lower()
        )

        resume_text = (
            extract_text_from_file(
                filepath,
                extension
            )
        )

        # ----------------------------------------------------
        # Candidate information
        # ----------------------------------------------------

        name = (
            request.form.get(
                "name",
                ""
            ).strip()
            or extract_name(
                resume_text
            )
        )

        email = (
            request.form.get(
                "email",
                ""
            ).strip()
            or extract_email(
                resume_text
            )
        )

        phone = (
            request.form.get(
                "phone",
                ""
            ).strip()
            or extract_phone(
                resume_text
            )
        )

        # ----------------------------------------------------
        # Calculate score
        # ----------------------------------------------------

        score = calculate_match_score(
            resume_text,
            job["description"],
            job["skills"],
        )

        # ----------------------------------------------------
        # Initial status
        # ----------------------------------------------------

        if score >= 75:

            status = "Shortlisted"

        elif score >= 50:

            status = "Review"

        else:

            status = "New"

        # ----------------------------------------------------
        # Insert candidate
        # ----------------------------------------------------

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
                job_id_int,
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
            )
        )

        conn.commit()

        conn.close()

        flash(
            f"Resume uploaded successfully. Match score: {score}%",
            "success"
        )

        return redirect(
            url_for(
                "job_detail",
                job_id=job_id_int
            )
        )

    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "upload_resume.html",
        jobs=jobs,
        job=job,
    )



#============================================================
# ALL CANDIDATES
# ============================================================

@app.route(
    "/candidates"
)
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

@app.route(
    "/candidate/<int:candidate_id>"
)
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
        (candidate_id,)
    ).fetchone()

    conn.close()

    if candidate is None:

        flash(
            "Candidate not found.",
            "danger"
        )

        return redirect(
            url_for("candidates")
        )

    return render_template(
        "candidate_detail.html",
        candidate=candidate,
    )


# ============================================================
# UPDATE CANDIDATE STATUS
# ============================================================

@app.route(
    "/candidate/<int:candidate_id>/status",
    methods=["POST"]
)
def update_candidate_status(
    candidate_id
):

    status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = {
        "New",
        "Review",
        "Shortlisted",
        "Rejected",
        "Selected",
    }

    if status not in allowed_statuses:

        flash(
            "Invalid candidate status.",
            "danger"
        )

        return redirect(
            url_for(
                "candidate_detail",
                candidate_id=candidate_id
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
            candidate_id
        )
    )

    conn.commit()

    candidate = conn.execute(
        """
        SELECT job_id
        FROM candidates
        WHERE id = ?
        """,
        (candidate_id,)
    ).fetchone()

    conn.close()

    flash(
        "Candidate status updated successfully.",
        "success"
    )

    if candidate and candidate["job_id"]:

        return redirect(
            url_for(
                "job_detail",
                job_id=candidate["job_id"]
            )
        )

    return redirect(
        url_for("candidates")
    )


# ============================================================
# DELETE CANDIDATE
# ============================================================

@app.route(
    "/candidate/<int:candidate_id>/delete",
    methods=["POST"]
)
def delete_candidate(candidate_id):

    conn = get_db()

    # Get candidate
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id = ?",
        (candidate_id,)
    ).fetchone()

    # Candidate not found
    if candidate is None:
        conn.close()
        flash("Candidate not found.", "error")
        return redirect(url_for("candidates"))

    # Delete resume file
    resume_filename = candidate["resume_filename"]

    if resume_filename:
        file_path = os.path.join(
            UPLOAD_FOLDER,
            resume_filename
        )

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print("Resume file delete error:", e)

    # Delete candidate from database
    conn.execute(
        "DELETE FROM candidates WHERE id = ?",
        (candidate_id,)
    )

    conn.commit()
    conn.close()

    flash("Candidate deleted successfully.", "success")

    return redirect(url_for("candidates"))

    # --------------------------------------------------------
    # Get candidate
    # --------------------------------------------------------

    candidate = conn.execute(
        """
        SELECT *
        FROM candidates
        WHERE id = ?
        """,
        (candidate_id,)
    ).fetchone()

    if candidate is None:

        conn.close()

        flash(
            "Candidate not found.",
            "danger"
        )

        return redirect(
            url_for("candidates")
        )

    job_id = candidate["job_id"]

    # --------------------------------------------------------
    # Delete uploaded resume
    # --------------------------------------------------------

    filename = candidate[
        "resume_filename"
    ]

    if filename:

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        if os.path.exists(filepath):

            try:

                os.remove(
                    filepath
                )

            except Exception as error:

                print(
                    "Could not delete resume:",
                    error
                )

    # --------------------------------------------------------
    # Delete candidate
    # --------------------------------------------------------

    conn.execute(
        """
        DELETE FROM candidates
        WHERE id = ?
        """,
        (candidate_id,)
    )

    conn.commit()

    conn.close()

    flash(
        "Candidate deleted successfully.",
        "success"
    )

    if job_id:

        return redirect(
            url_for(
                "job_detail",
                job_id=job_id
            )
        )

    return redirect(
        url_for("candidates")
    )


# ============================================================
# DELETE JOB
# ============================================================

@app.route(
    "/job/<int:job_id>/delete",
    methods=["POST"]
)
def delete_job(job_id):

    conn = get_db()

    # --------------------------------------------------------
    # Check job
    # --------------------------------------------------------

    job = conn.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    ).fetchone()

    if job is None:

        conn.close()

        flash(
            "Job not found.",
            "danger"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # Get candidates
    # --------------------------------------------------------

    candidates = conn.execute(
        """
        SELECT resume_filename
        FROM candidates
        WHERE job_id = ?
        """,
        (job_id,)
    ).fetchall()

    # --------------------------------------------------------
    # Delete candidate resume files
    # --------------------------------------------------------

    for candidate in candidates:

        filename = candidate[
            "resume_filename"
        ]

        if filename:

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            if os.path.exists(filepath):

                try:

                    os.remove(
                        filepath
                    )

                except Exception as error:

                    print(
                        "Could not delete resume:",
                        error
                    )

    # --------------------------------------------------------
    # Delete candidates
    # --------------------------------------------------------

    conn.execute(
        """
        DELETE FROM candidates
        WHERE job_id = ?
        """,
        (job_id,)
    )

    # --------------------------------------------------------
    # Delete job
    # --------------------------------------------------------

    conn.execute(
        """
        DELETE FROM jobs
        WHERE id = ?
        """,
        (job_id,)
    )

    conn.commit()

    conn.close()

    flash(
        "Job deleted successfully.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 10 MB.",
        "danger"
    )

    return redirect(
        url_for("upload_resume")
    )


@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong in the application.</p>
    """, 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("      AI SMART HIRING SYSTEM")
    print("=" * 60)
    print()
    print("Server starting...")
    print()
    print("Open your browser:")
    print("http://127.0.0.1:5000")
    print()
    print("=" * 60)
    print()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )