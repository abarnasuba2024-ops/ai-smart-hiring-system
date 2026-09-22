import os
import re

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If app.py is inside templates folder
if os.path.basename(BASE_DIR).lower() == "templates":
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    TEMPLATE_FOLDER = BASE_DIR
else:
    PROJECT_DIR = BASE_DIR
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")


UPLOAD_FOLDER = os.path.join(PROJECT_DIR, "uploads")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    template_folder=TEMPLATE_FOLDER
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB


# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# ALLOWED FILE TYPES
# =========================================================

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =========================================================
# RESUME TEXT EXTRACTION
# =========================================================

def extract_resume_text(filepath):
    extension = filepath.rsplit(".", 1)[1].lower()

    # ---------------- PDF ----------------
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
                "PyPDF2 is not installed. Run: pip install PyPDF2"
            )

    # ---------------- DOCX ----------------
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
                "python-docx is not installed. Run: pip install python-docx"
            )

    return ""


# =========================================================
# SKILL DETECTION
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
    "rest api",
]


def detect_skills(text):
    text_lower = text.lower()

    found_skills = []

    for skill in SKILLS:

        # Special handling for C++
        if skill == "c++":
            if "c++" in text_lower:
                found_skills.append(skill)
            continue

        # Special handling for Node.js
        if skill == "node.js":
            if "node.js" in text_lower:
                found_skills.append(skill)
            continue

        # Avoid matching partial words
        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


# =========================================================
# JOB ROLES AND REQUIRED SKILLS
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
    ],
}


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


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

    # -----------------------------
    # FORM DATA
    # -----------------------------

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    mobile = request.form.get("mobile", "").strip()
    location = request.form.get("location", "").strip()
    job_role = request.form.get("job_role", "").strip()

    resume = request.files.get("resume")

    # -----------------------------
    # BASIC VALIDATION
    # -----------------------------

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

    # -----------------------------
    # SAVE RESUME
    # -----------------------------

    filename = secure_filename(resume.filename)

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    resume.save(filepath)

    # -----------------------------
    # EXTRACT TEXT
    # -----------------------------

    try:
        resume_text = extract_resume_text(filepath)

    except Exception as error:
        return f"Resume processing error: {error}"

    # -----------------------------
    # DETECT SKILLS
    # -----------------------------

    found_skills = detect_skills(resume_text)

    # -----------------------------
    # REQUIRED SKILLS
    # -----------------------------

    required_skills = JOB_REQUIREMENTS.get(
        job_role,
        []
    )

    # -----------------------------
    # MATCH SKILLS
    # -----------------------------

    matched_skills = []

    for skill in required_skills:

        if skill.lower() in [
            found.lower()
            for found in found_skills
        ]:
            matched_skills.append(skill)

    # -----------------------------
    # CALCULATE SCORE
    # -----------------------------

    if len(required_skills) > 0:
        score = round(
            (len(matched_skills) / len(required_skills)) * 100
        )
    else:
        score = 0

    # -----------------------------
    # DECISION
    # -----------------------------

    if score >= 60:
        decision = "SELECT"
    else:
        decision = "REJECT"

    # -----------------------------
    # RESULT PAGE
    # -----------------------------

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
        return render_template("add_job.html")

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

    return render_template(
        "index.html"
    )


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
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    # Render provides PORT automatically.
    # Local computer uses 5000.

    port = int(
        os.environ.get("PORT", 5000)
    )

    print("=" * 60)
    print("AI SMART HIRING SYSTEM")
    print("=" * 60)

    print("App location:")
    print(BASE_DIR)

    print("Template folder:")
    print(TEMPLATE_FOLDER)

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